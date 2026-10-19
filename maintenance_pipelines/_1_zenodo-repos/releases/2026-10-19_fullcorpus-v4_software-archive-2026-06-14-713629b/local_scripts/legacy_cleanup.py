"""Legacy CO.RA.PAN local cleanup (operator brief 2026-10-19). plan: hash gates + retention manifest; apply: gated deletions with journal."""
import csv, hashlib, json, os, shutil, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
L = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
D = r"D:\projects\panhispanic_media_corpora\corapan\archive\protected_secondary\legacy_corapan"
ST = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging"
REL = os.path.join(L, "maintenance_pipelines", "_1_zenodo-repos", "releases", "2026-10-19_fullcorpus-v4_software-archive-2026-06-14-713629b")
SP = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(SP, "cleanup_plan.json"); JOURNAL = os.path.join(SP, "cleanup_journal.jsonl")
BK = r"maintenance_pipelines\_0_json\backups"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def files(rel, base=L):
    root = os.path.join(base, rel); out = []
    for d, _, fs in os.walk(root):
        for f in fs:
            out.append(os.path.relpath(os.path.join(d, f), base))
    return sorted(out)


def hmap(rels, base=L):
    with ThreadPoolExecutor(6) as ex:
        return dict(zip(rels, ex.map(lambda r: sha(os.path.join(base, r)), rels)))


def size(rels, base=L):
    return sum(os.path.getsize(os.path.join(base, r)) for r in rels)


def plan():
    t0 = time.time(); P = {"gates": {}, "classes": {}}
    # --- retention set: local vs D: secondary (SHA-256 per file)
    ret_roots = [r"media\mp3-full", r"media\transcripts", BK + r"\pre-v3_1-transcripts", BK + r"\pre-tense-schema-migration",
                 BK + r"\manual-repairs", r"data\blacklab\index", r"data\blacklab\export\tsv\tsv_for_index", r"data\blacklab\export\metadata",
                 r"data\db\public", r"data\public"]
    rows = []; ok = miss = diff = 0
    for root in ret_roots:
        rels = files(root); hl = hmap(rels)
        hd = hmap([r for r in rels if os.path.exists(os.path.join(D, r))], D)
        for r in rels:
            st = "MATCH" if hd.get(r) == hl[r] else ("MISSING_ON_D" if r not in hd else "DIFFERENT_ON_D")
            ok += st == "MATCH"; miss += st == "MISSING_ON_D"; diff += st == "DIFFERENT_ON_D"
            rows.append(dict(path=r.replace("\\", "/"), bytes=os.path.getsize(os.path.join(L, r)), sha256=hl[r], d_secondary=st))
        print("retention", root, len(rels), round(time.time() - t0), flush=True)
    P["retention"] = dict(files=len(rows), bytes=sum(x["bytes"] for x in rows), match=ok, missing_on_d=miss, different_on_d=diff)
    with open(os.path.join(SP, "retention_manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["path", "bytes", "sha256", "d_secondary"], lineterminator="\n"); w.writeheader(); w.writerows(rows)
    # --- class: mp3-split (local == D:, fulls present local and on D:)
    sp = [r for r in files(r"media\mp3-split") if not r.endswith(".gitkeep")]
    hs = hmap(sp); hsd = hmap([r for r in sp if os.path.exists(os.path.join(D, r))], D)
    full_ok = all(x["d_secondary"] == "MATCH" for x in rows if x["path"].startswith("media/mp3-full/") and x["path"].endswith(".mp3"))
    P["classes"]["mp3_split"] = dict(paths=sp, bytes=size(sp), gate=all(hsd.get(r) == hs[r] for r in sp) and full_ok and len(sp) == 2705,
                                     detail=dict(files=len(sp), equal_on_d=sum(hsd.get(r) == hs[r] for r in sp), fulls_match_d=full_ok))
    # --- class: tsv_for_index.bak_* (identical to tsv_for_index)
    base = r"data\blacklab\export\tsv"; ref = {os.path.basename(r): h for r, h in hmap(files(base + r"\tsv_for_index")).items()}
    for bak in ("tsv_for_index.bak_20260117_002730", "tsv_for_index.bak_20260117_005855"):
        rels = files(base + "\\" + bak); hb = hmap(rels)
        P["classes"][bak] = dict(paths=rels, bytes=size(rels), gate=len(rels) == len(ref) == 146 and all(ref.get(os.path.basename(r)) == h for r, h in hb.items()))
    # --- class: quarantine/index.build (identical to active index)
    ri = {os.path.relpath(r, r"data\blacklab\index"): h for r, h in hmap(files(r"data\blacklab\index")).items()}
    rb = hmap(files(r"data\blacklab\quarantine\index.build"))
    P["classes"]["index_build"] = dict(paths=list(rb), bytes=size(list(rb)),
                                       gate=len(rb) == len(ri) and all(ri.get(os.path.relpath(r, r"data\blacklab\quarantine\index.build")) == h for r, h in rb.items()))
    # --- class: tmp (classified: 108 copies of retained files, 6 synthetic test files)
    tr = files("tmp"); P["classes"]["tmp"] = dict(paths=tr, bytes=size(tr), gate=True, detail="copies of retained files + synthetic sync-test files (classified 2026-10-19)")
    # --- class: smoke/multicountry backup files byte-identical to retained JSON
    refj = set(x["sha256"] for x in rows)
    cand = files(BK + r"\smoke-tests") + files(BK + r"\multicountry-smoke"); hc = hmap(cand)
    dup = [r for r in cand if hc[r] in refj]
    P["classes"]["smoke_backup_duplicates"] = dict(paths=dup, bytes=size(dup), gate=True, kept_unique=len(cand) - len(dup))
    # --- class: .venv
    vr = files(".venv"); P["classes"]["venv"] = dict(paths=None, root=".venv", files=len(vr), bytes=size(vr), gate=True)
    # --- staging: gates = published equal to local (zenodo_final_housekeeping.json) + MANIFEST sources unchanged
    hk = json.load(open(os.path.join(ST, r"local_only\reports\zenodo_final_housekeeping.json")))
    man = list(csv.DictReader(open(os.path.join(ST, r"zenodo_upload_ready\full-corpus\MANIFEST.csv"), encoding="utf-8")))
    cur = {x["path"]: x["sha256"] for x in rows}
    src_ok = all(cur.get(f"media/mp3-full/{m['package'][:-4]}/{m['recording_id']}.mp3") == m["audio_sha256"] and
                 cur.get(f"media/transcripts/{m['package'][:-4]}/{m['recording_id']}.json") == m["json_sha256"] for m in man)
    stf = files("", ST)
    P["classes"]["staging"] = dict(root=ST, files=len(stf), bytes=size(stf, ST), gate=hk["fc"]["equal_to_local"] and hk["sw"]["equal_to_local"] and src_ok and len(man) == 146,
                                   detail=dict(zenodo_fc=hk["fc"]["equal_to_local"], zenodo_sw=hk["sw"]["equal_to_local"], sources_equal_manifest=src_ok))
    for k, v in P["classes"].items():
        print(k, "gate", v["gate"], round(v["bytes"] / 2**30, 3), "GiB", v.get("detail", ""))
    print("retention", P["retention"], round(time.time() - t0), "s")
    json.dump(P, open(PLAN, "w"), indent=1)


def log(**k):
    k["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S"); open(JOURNAL, "a", encoding="utf-8").write(json.dumps(k) + "\n")


def apply():
    P = json.load(open(PLAN))
    assert P["retention"]["missing_on_d"] == 0 and P["retention"]["different_on_d"] == 0, "retention set not fully on D:"
    # 1. staging -> compact release record in the repo, then remove staging
    c = P["classes"]["staging"]
    if c["gate"]:
        keep = [r"zenodo_upload_ready\ZENODO_UPLOAD_GUIDE.md", r"README_STAGING.md"]
        for sub in (r"zenodo_upload_ready\full-corpus", r"zenodo_upload_ready\software", r"zenodo_upload_ready\zenodo_metadata", r"local_only\reports", r"local_only\scripts"):
            keep += [r for r in files(sub, ST) if not r.lower().endswith(".zip") or "provenance" in r.lower()]
        keep = [r for r in keep if not r.endswith(("determinism_probe.zip",))]
        for r in keep:
            dst = os.path.join(REL, r.replace("zenodo_upload_ready\\", "").replace("local_only\\", "local_"))
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(os.path.join(ST, r), dst)
            assert sha(dst) == sha(os.path.join(ST, r))
        log(cls="staging", action="release_record_copied", files=len(keep), dest=REL)
        shutil.rmtree(ST); log(cls="staging", action="removed", files=c["files"], bytes=c["bytes"])
        print("staging removed; release record files:", len(keep))
    # 2. path classes
    for cls in ("tsv_for_index.bak_20260117_002730", "tsv_for_index.bak_20260117_005855", "index_build", "tmp", "smoke_backup_duplicates", "mp3_split"):
        c = P["classes"][cls]
        if not c["gate"]:
            log(cls=cls, action="kept_gate_failed"); print(cls, "KEPT (gate)"); continue
        n = b = 0
        for r in c["paths"]:
            p = os.path.join(L, r)
            if os.path.exists(p):
                b += os.path.getsize(p); os.remove(p); n += 1
        for root in {"tsv_for_index.bak_20260117_002730": [r"data\blacklab\export\tsv\tsv_for_index.bak_20260117_002730"],
                     "tsv_for_index.bak_20260117_005855": [r"data\blacklab\export\tsv\tsv_for_index.bak_20260117_005855"],
                     "index_build": [r"data\blacklab\quarantine\index.build"], "tmp": ["tmp"]}.get(cls, []):
            if os.path.isdir(os.path.join(L, root)):
                shutil.rmtree(os.path.join(L, root))
        if cls == "mp3_split":  # remove now-empty country dirs, keep media/mp3-split/.gitkeep
            for d in os.listdir(os.path.join(L, r"media\mp3-split")):
                q = os.path.join(L, r"media\mp3-split", d)
                if os.path.isdir(q) and not os.listdir(q):
                    os.rmdir(q)
        if cls == "smoke_backup_duplicates":
            for root in (BK + r"\smoke-tests", BK + r"\multicountry-smoke"):
                for d, ds, fs in sorted(os.walk(os.path.join(L, root)), key=lambda x: -len(x[0])):
                    if d != os.path.join(L, root) and not os.listdir(d):
                        os.rmdir(d)
        log(cls=cls, action="removed", files=n, bytes=b); print(cls, "removed", n, round(b / 2**30, 3), "GiB", flush=True)
    # 3. .venv
    c = P["classes"]["venv"]
    if c["gate"]:
        shutil.rmtree(os.path.join(L, ".venv")); log(cls="venv", action="removed", files=c["files"], bytes=c["bytes"]); print("venv removed")
    # 4. zip_process.log: historical log separated from resume state
    src = os.path.join(L, r"maintenance_pipelines\_1_zenodo-repos\zip_process.log")
    dst = os.path.join(L, r"maintenance_pipelines\_1_zenodo-repos\zip_process.history_v3_2026-02-26.log")
    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst); log(cls="zip_process_log", action="renamed", to=os.path.basename(dst)); print("zip_process.log renamed")


{"plan": plan, "apply": apply}[sys.argv[1]]()
