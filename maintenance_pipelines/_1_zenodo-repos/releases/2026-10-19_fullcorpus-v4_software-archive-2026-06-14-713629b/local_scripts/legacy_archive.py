"""Archive the Legacy CO.RA.PAN retention set as ONE write-once tree of the LEGACY holding (crosscorpus-storage/v1 rev. 2, D127, A2-A5).

python -I -B legacy_archive.py init      create the LEGACY primary root + T1 marker (once)
python -I -B legacy_archive.py copy      copy every listed file (write-once, resumable; never overwrites a different file)
python -I -B legacy_archive.py manifest  re-read every file FROM THE PRIMARY, then write ARCHIVE_MANIFEST.json last
python -I -B legacy_archive.py verify    A5 decision with the contract implementation (archive_tree) on a fresh re-read
Journal and reports stay in the scratchpad (a tree holds no unlisted file).
"""
import csv, hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
V3 = r"C:\dev\panhispanic_media_corpora\corapan"
sys.path.insert(0, os.path.join(V3, "src"))
from corapan_playground.storage.target_identity import write_marker, check as identity_check  # noqa: E402
from corapan_playground.crosscorpus.storage_contract import archive_tree, namespace, ARCHIVE_MANIFEST  # noqa: E402
from corapan_playground.crosscorpus.release_contract import record_set_sha256  # noqa: E402

NEWFS = r"\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN"
ROOT = "\\".join(namespace(NEWFS.split("\\"), "corapan", "LEGACY"))
TREE = "corapan"
TREE_DIR = ROOT + "\\" + TREE
TARGET_ID = "corapan-archive-newfs-legacy"
SRC = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
MANIFESTS = [SRC + r"\docs\agent-runs\2026-10-19_legacy_retention_manifest.csv", SRC + r"\docs\agent-runs\2026-10-19_legacy_retention_supplement_manifest.csv"]
EXCLUDE = {"docs/agent-runs/2026-10-19_legacy-retention-integration-and-local-cleanup.md"}   # still being written; in Git
SP = os.path.dirname(os.path.abspath(__file__))
JOURNAL = os.path.join(SP, "archive_journal.jsonl")
BY = "Felix Tacke (operator brief 'Vertrags-Gate beobachten, danach Retention und Cleanup autonom abschliessen', 2026-10-19), carried out by the agent run"

# hard guards: only the NEW_FS project share, never K: / the FREMDSPRACHEN group share
assert ROOT.lower().startswith(NEWFS.lower() + "\\projects\\panhispanic_media_corpora\\legacy\\corapan".lower()), ROOT
assert "fremdsprachen" not in ROOT.lower() and not ROOT.lower().startswith("k:"), ROOT


def lp(p):
    return "\\\\?\\UNC\\" + p[2:] if p.startswith("\\\\") else "\\\\?\\" + p


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def listing():
    rows = {}
    for m in MANIFESTS:
        for r in csv.DictReader(open(m, encoding="utf-8")):
            if r["path"] in EXCLUDE:
                continue
            rows[r["path"]] = dict(path=r["path"], size=int(r["bytes"]), sha256=r["sha256"])
    folded = {}
    for p in rows:
        assert p.casefold() not in folded, ("PATH_COLLISION", p)
        folded[p.casefold()] = p
    return [rows[k] for k in sorted(rows)]


def log(**k):
    k["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(json.dumps(k, ensure_ascii=False) + "\n")


def init():
    os.makedirs(lp(ROOT), exist_ok=True)
    st = identity_check(ROOT, holding="LEGACY", expected_id=TARGET_ID)
    if st["state"] != "IDENTITY_OK":
        doc = write_marker(ROOT, target_id=TARGET_ID, holding="LEGACY", created_by=BY,
                           statement="identity of the PRESERVATION root of the archive holding LEGACY of CO.RA.PAN (crosscorpus-storage/v1 revision 2, "
                                     "D127). It names the root, not its trees; each archived tree carries its own ARCHIVE_MANIFEST.json")
        log(step="init", marker=doc["target_id"], root=ROOT)
    print(json.dumps(identity_check(ROOT, holding="LEGACY", expected_id=TARGET_ID), ensure_ascii=False))


def copy():
    assert identity_check(ROOT, holding="LEGACY", expected_id=TARGET_ID)["state"] == "IDENTITY_OK"
    assert not os.path.exists(lp(TREE_DIR + "\\" + ARCHIVE_MANIFEST)), "tree already sealed (A4): no further writes"
    rows = listing()
    res = {"COPIED": 0, "PRESENT_IDENTICAL": 0, "SOURCE_CHANGED": [], "CONFLICT": [], "FAILED": []}

    def one(r):
        src = os.path.join(SRC, r["path"].replace("/", os.sep))
        dst = TREE_DIR + "\\" + r["path"].replace("/", "\\")
        s = sha(src)
        if s != r["sha256"] or os.path.getsize(src) != r["size"]:
            return ("SOURCE_CHANGED", r["path"])
        if os.path.exists(lp(dst)):
            return ("PRESENT_IDENTICAL", r["path"]) if sha(lp(dst)) == s else ("CONFLICT", r["path"])
        os.makedirs(os.path.dirname(lp(dst)), exist_ok=True)
        tmp = lp(dst) + ".corapan-part"
        try:
            with open(src, "rb") as fi, open(tmp, "xb") as fo:
                for b in iter(lambda: fi.read(8 << 20), b""):
                    fo.write(b)
                fo.flush(); os.fsync(fo.fileno())
            os.rename(tmp, lp(dst))
        except Exception as e:
            try:
                os.remove(tmp)
            except OSError:
                pass
            return ("FAILED", f"{r['path']}: {type(e).__name__}: {e}")
        return ("COPIED", r["path"])
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        for i, (st, p) in enumerate(ex.map(one, rows), 1):
            if isinstance(res[st], int):
                res[st] += 1
            else:
                res[st].append(p)
            if i % 250 == 0:
                print(i, "/", len(rows), round(time.time() - t0), "s", flush=True)
    log(step="copy", files=len(rows), bytes=sum(r["size"] for r in rows), **{k: (v if isinstance(v, int) else len(v)) for k, v in res.items()})
    print(json.dumps({k: (v if isinstance(v, int) else v[:20]) for k, v in res.items()}, ensure_ascii=False, indent=1))
    return res


def observe():
    """Re-read every file below the tree FROM THE PRIMARY (no manifest)."""
    out = []
    base = lp(TREE_DIR)
    for d, _, fs in os.walk(base):
        for f in fs:
            full = os.path.join(d, f)
            rel = os.path.relpath(full, base).replace("\\", "/")
            if rel == ARCHIVE_MANIFEST:
                continue
            out.append(full)
    with ThreadPoolExecutor(4) as ex:
        hs = list(ex.map(sha, out))
    return [dict(path=os.path.relpath(p, base).replace("\\", "/"), size=os.path.getsize(p), sha256=h) for p, h in zip(out, hs)]


def manifest():
    mpath = lp(TREE_DIR + "\\" + ARCHIVE_MANIFEST)
    assert not os.path.exists(mpath), "manifest exists (A4: written once)"
    rows = listing()
    obs = {o["path"]: o for o in observe()}
    want = {r["path"]: r for r in rows}
    diff = sorted(set(obs) ^ set(want)) + sorted(p for p in want if p in obs and obs[p] != want[p])
    assert not diff, ("primary does not equal the listing", diff[:10])
    files = [dict(path=r["path"], size=r["size"], sha256=r["sha256"]) for r in rows]
    doc = {"schema": "crosscorpus-storage/v1/archive-manifest", "corpus": "corapan", "holding": "LEGACY", "tree": TREE,
           "source": "recorded original location C:\\dev\\panhispanic_media_corpora\\legacy\\corapan (named root legacy_corapan, "
                     "CORAPAN_LEGACY_ROOT): the former CO.RA.PAN web-application repository; selection = its retention manifest "
                     "(1,402 files) and supplement manifest (historic index builds, exports, annotation intermediate states, processing "
                     "evidence, release records) of 2026-10-19; Git-tracked source code is not part of the tree (it is in Git and on Zenodo)",
           "decision": "D127 (crosscorpus-storage/v1 revision 2) and the operator brief 'Legacy-CO.RA.PAN - Vertrags-Gate beobachten, "
                       "danach Retention und Cleanup autonom abschliessen' (2026-10-19)",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": files,
           "tree_sha256": record_set_sha256(files), "supersedes": None}
    data = (json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")
    with open(mpath, "xb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    log(step="manifest", files=len(files), bytes=sum(r["size"] for r in files), tree_sha256=doc["tree_sha256"])
    print("manifest written", len(files), doc["tree_sha256"])


def verify():
    ident = identity_check(ROOT, holding="LEGACY", expected_id=TARGET_ID)
    man = json.loads(open(lp(TREE_DIR + "\\" + ARCHIVE_MANIFEST), encoding="utf-8").read())
    obs = observe()
    codes = archive_tree(corpus="corapan", holding="LEGACY", tree=TREE, target_identity_ok=ident["state"] == "IDENTITY_OK", manifest=man, observed=obs)
    rep = dict(root=ROOT, tree=TREE, identity=ident["state"], files=len(man["files"]), bytes=sum(r["size"] for r in man["files"]),
               observed=len(obs), tree_sha256=man["tree_sha256"], codes=codes, state="PRESERVED" if not codes else "NOT_PRESERVED",
               verified_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    json.dump(rep, open(os.path.join(SP, "archive_verify.json"), "w"), indent=1)
    log(step="verify", **{k: v for k, v in rep.items() if k != "codes"}, codes=codes)
    print(json.dumps(rep, indent=1))


{"init": init, "copy": copy, "manifest": manifest, "verify": verify}[sys.argv[1]]()
