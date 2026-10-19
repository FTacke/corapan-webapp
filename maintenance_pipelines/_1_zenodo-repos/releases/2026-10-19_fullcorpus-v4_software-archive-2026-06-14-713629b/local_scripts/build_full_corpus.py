#!/usr/bin/env python3
"""Build + verify the Full Corpus v4 upload packages (read-only on all sources).

Usage: python -I build_full_corpus.py <stage1|verify|old_inventory>
Sources are only READ. Outputs go to the staging directory next to the repository.
"""
import csv, hashlib, json, os, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor

REPO = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
STAGE = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging"
D_ROOT = r"D:\projects\panhispanic_media_corpora\corapan\archive\protected_secondary\legacy_corapan"
OLD_ZIPS = os.path.join(REPO, "maintenance_pipelines", "_1_zenodo-repos", "Zenodo Full Corpus")
BACKUP = os.path.join(REPO, "maintenance_pipelines", "_0_json", "backups", "pre-v3_1-transcripts", "20260614T080916Z", "transcripts")
MP3 = os.path.join(REPO, "media", "mp3-full")
TR = os.path.join(REPO, "media", "transcripts")
OUT = os.path.join(STAGE, "zenodo_upload_ready", "full-corpus")
REP = os.path.join(STAGE, "local_only", "reports")
FIXED_DT = (2026, 1, 1, 0, 0, 0)  # deterministic member timestamp


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pmap(fn, items, workers=4):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))


def list_sources():
    rec = {}
    for cc in sorted(os.listdir(TR)):
        d = os.path.join(TR, cc)
        if not os.path.isdir(d):
            continue
        js = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        mp = sorted(f for f in os.listdir(os.path.join(MP3, cc)) if f.lower().endswith(".mp3"))
        assert [f[:-5] for f in js] == [f[:-4] for f in mp], cc
        rec[cc] = [(f[:-5], os.path.join(MP3, cc, f[:-5] + ".mp3"), os.path.join(d, f)) for f in js]
    return rec


def stage1():
    t0 = time.time()
    rec = list_sources()
    # --- hash sources
    jobs = [(cc, rid, kind, p) for cc, rs in rec.items() for rid, a, j in rs for kind, p in (("mp3", a), ("json", j))]
    hashes = dict(zip([(c, r, k) for c, r, k, _ in jobs], pmap(lambda x: sha256_file(x[3]), jobs)))
    print("sources hashed", len(jobs), round(time.time() - t0), "s", flush=True)
    # --- annotation meta
    rows = []
    for cc, rs in rec.items():
        for rid, a, j in rs:
            d = json.load(open(j, encoding="utf-8"))
            am = d.get("ann_meta", {})
            words = sum(len(s.get("words", [])) for s in d["segments"])
            rows.append(dict(
                package=f"{cc}.zip", country_folder=cc, recording_id=rid,
                audio_member=f"mp3-files/{rid}.mp3", audio_bytes=os.path.getsize(a), audio_sha256=hashes[(cc, rid, "mp3")],
                json_member=f"json-transcripts/{rid}.json", json_bytes=os.path.getsize(j), json_sha256=hashes[(cc, rid, "json")],
                date=d.get("date"), country_code=d.get("country_code"), internal_file_id=d.get("file_id"),
                internal_filename=d.get("filename"), segments=len(d["segments"]), word_entries=words,
                schema_version=am.get("schema_version"), pipeline_version=am.get("pipeline_version"),
                tense_rules_version=am.get("tense_rules_version"), annotation_version=am.get("version"),
                spacy_model=am.get("spacy_model"), json_updated_at=am.get("updated_at"),
            ))
    json.dump(rows, open(os.path.join(REP, "stage1_rows.json"), "w"), indent=1)
    # --- build zips
    os.makedirs(OUT, exist_ok=True)
    pk = {}
    for cc, rs in rec.items():
        zp = os.path.join(OUT, cc + ".zip")
        tmp = zp + ".tmp"
        build_zip(tmp, rs)
        os.replace(tmp, zp)
        pk[cc] = dict(path=zp, bytes=os.path.getsize(zp), sha256=sha256_file(zp), recordings=len(rs))
        print("built", cc, pk[cc]["bytes"], flush=True)
    json.dump(pk, open(os.path.join(REP, "stage1_packages.json"), "w"), indent=1)
    print("stage1 done", round(time.time() - t0), "s")


def build_zip(zp, rs):
    with zipfile.ZipFile(zp, "w", allowZip64=True) as z:
        for rid, a, j in rs:
            for arc, src, comp in ((f"mp3-files/{rid}.mp3", a, zipfile.ZIP_STORED), (f"json-transcripts/{rid}.json", j, zipfile.ZIP_DEFLATED)):
                zi = zipfile.ZipInfo(arc, FIXED_DT)
                zi.create_system = 3
                zi.external_attr = 0o100644 << 16
                zi.compress_type = comp
                with open(src, "rb") as f:
                    data = f.read()
                z.writestr(zi, data, compress_type=comp, compresslevel=9 if comp == zipfile.ZIP_DEFLATED else None)


def verify():
    t0 = time.time()
    rows = json.load(open(os.path.join(REP, "stage1_rows.json")))
    pk = json.load(open(os.path.join(REP, "stage1_packages.json")))
    by = {}
    for r in rows:
        by.setdefault(r["country_folder"], []).append(r)
    res = {"packages": {}, "problems": []}
    for cc, rs in by.items():
        zp = os.path.join(OUT, cc + ".zip")
        z = zipfile.ZipFile(zp)
        bad = z.testzip()
        names = [i.filename for i in z.infolist()]
        exp = sorted([r["audio_member"] for r in rs] + [r["json_member"] for r in rs])
        ok = bad is None and sorted(names) == exp and len(names) == len(set(names))
        ok_hash = 0
        for r in rs:
            for m, key in (("audio_member", "audio_sha256"), ("json_member", "json_sha256")):
                h = hashlib.sha256()
                with z.open(r[m]) as f:
                    for b in iter(lambda: f.read(8 << 20), b""):
                        h.update(b)
                if h.hexdigest() == r[key]:
                    ok_hash += 1
                else:
                    res["problems"].append((cc, r[m], "member sha mismatch"))
        if not ok:
            res["problems"].append((cc, "structure/testzip", bad))
        pkg_sha = sha256_file(zp)
        if pkg_sha != pk[cc]["sha256"]:
            res["problems"].append((cc, "package sha changed after build"))
        res["packages"][cc] = dict(bytes=os.path.getsize(zp), sha256=pkg_sha, recordings=len(rs), members=len(names),
                                   audio_members=sum(1 for n in names if n.startswith("mp3-files/")),
                                   json_members=sum(1 for n in names if n.startswith("json-transcripts/")),
                                   testzip_ok=bad is None, member_hash_ok=ok_hash, member_hash_expected=2 * len(rs), structure_ok=ok)
        print("verified", cc, ok, ok_hash, 2 * len(rs), flush=True)
    # determinism probe: rebuild smallest package twice-from-scratch and compare
    cc = min(pk, key=lambda k: pk[k]["bytes"])
    rec = list_sources()
    tmp = os.path.join(REP, "determinism_probe.zip")
    build_zip(tmp, rec[cc])
    res["determinism_probe"] = dict(package=cc, identical=sha256_file(tmp) == pk[cc]["sha256"])
    os.remove(tmp)
    res["total_bytes"] = sum(p["bytes"] for p in res["packages"].values())
    res["seconds"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(REP, "verify_results.json"), "w"), indent=1)
    print("problems:", len(res["problems"]), "determinism:", res["determinism_probe"], "total", res["total_bytes"])


def old_inventory():
    """Inventory of the OLD zip generation + identity checks against retained sources (read-only)."""
    t0 = time.time()
    rows = json.load(open(os.path.join(REP, "stage1_rows.json")))
    cur = {r["recording_id"]: r for r in rows}
    # pre-v3_1 backup + D: copies
    def bk_path(rid):
        cc = rid.split("_")[1]
        return os.path.join(BACKUP, cc, rid + ".json")
    inv = {"zips": {}, "members": [], "checks": {}}
    zips = sorted(f for f in os.listdir(OLD_ZIPS) if f.endswith(".zip"))
    zsha = dict(zip(zips, pmap(lambda f: sha256_file(os.path.join(OLD_ZIPS, f)), zips)))
    dsha = dict(zip(zips, pmap(lambda f: sha256_file(os.path.join(D_ROOT, "maintenance_pipelines", "_1_zenodo-repos", "Zenodo Full Corpus", f)), zips)))
    print("old zips hashed (C: and D:)", round(time.time() - t0), flush=True)
    bk_cache, d_mp3, d_tr, d_bk = {}, {}, {}, {}
    probs = []
    extra = []
    for f in zips:
        z = zipfile.ZipFile(os.path.join(OLD_ZIPS, f))
        cc = f[:-4]
        mem = z.infolist()
        inv["zips"][f] = dict(bytes=os.path.getsize(os.path.join(OLD_ZIPS, f)), sha256=zsha[f], d_copy_sha256=dsha[f], d_copy_identical=zsha[f] == dsha[f],
                              members=len(mem), testzip=z.testzip() is None)
        for i in mem:
            h = hashlib.sha256()
            with z.open(i) as fh:
                for b in iter(lambda: fh.read(8 << 20), b""):
                    h.update(b)
            rid = os.path.basename(i.filename).rsplit(".", 1)[0]
            kind = "mp3" if i.filename.startswith("mp3-files/") else "json" if i.filename.startswith("json-transcripts/") else "other"
            if kind == "other":
                extra.append((f, i.filename))
            inv["members"].append(dict(zip=f, member=i.filename, kind=kind, bytes=i.file_size, sha256=h.hexdigest(), recording_id=rid))
    print("old members hashed", len(inv["members"]), round(time.time() - t0), flush=True)
    mp3_c, js_bk, mp3_d, js_bkd = {}, {}, {}, {}
    for m in inv["members"]:
        rid = m["recording_id"]; cc = rid.split("_")[1]
        if m["kind"] == "mp3":
            mp3_c[rid] = cur[rid]["audio_sha256"]
            mp3_d[rid] = os.path.join(D_ROOT, "media", "mp3-full", cur[rid]["country_folder"], rid + ".mp3")
        elif m["kind"] == "json":
            js_bk[rid] = os.path.join(BACKUP, cur[rid]["country_folder"], rid + ".json")
            js_bkd[rid] = os.path.join(D_ROOT, "maintenance_pipelines", "_0_json", "backups", "pre-v3_1-transcripts", "20260614T080916Z", "transcripts", cur[rid]["country_folder"], rid + ".json")
    rids_m = sorted(mp3_d); rids_j = sorted(js_bk)
    h_d_mp3 = dict(zip(rids_m, pmap(lambda r: sha256_file(mp3_d[r]), rids_m)))
    h_bk = dict(zip(rids_j, pmap(lambda r: sha256_file(js_bk[r]), rids_j)))
    h_bkd = dict(zip(rids_j, pmap(lambda r: sha256_file(js_bkd[r]), rids_j)))
    print("retention copies hashed", round(time.time() - t0), flush=True)
    for m in inv["members"]:
        rid = m["recording_id"]
        if m["kind"] == "mp3":
            m["equals_local_mp3_full"] = m["sha256"] == mp3_c[rid]
            m["equals_D_mp3_full"] = m["sha256"] == h_d_mp3[rid]
            m["equals_new_pkg_audio"] = m["sha256"] == cur[rid]["audio_sha256"]
        elif m["kind"] == "json":
            m["equals_local_pre_v3_1_backup"] = m["sha256"] == h_bk[rid]
            m["equals_D_pre_v3_1_backup"] = m["sha256"] == h_bkd[rid]
            m["equals_current_json"] = m["sha256"] == cur[rid]["json_sha256"]
    mm = [m for m in inv["members"] if m["kind"] == "mp3"]; jj = [m for m in inv["members"] if m["kind"] == "json"]
    inv["checks"] = dict(
        zips=len(zips), members=len(inv["members"]), mp3_members=len(mm), json_members=len(jj), other_members=extra,
        mp3_equal_local=sum(m["equals_local_mp3_full"] for m in mm), mp3_equal_D=sum(m["equals_D_mp3_full"] for m in mm),
        mp3_equal_new_pkg=sum(m["equals_new_pkg_audio"] for m in mm),
        json_equal_local_backup=sum(m["equals_local_pre_v3_1_backup"] for m in jj), json_equal_D_backup=sum(m["equals_D_pre_v3_1_backup"] for m in jj),
        json_equal_current=sum(m["equals_current_json"] for m in jj),
        d_zip_copies_identical=sum(v["d_copy_identical"] for v in inv["zips"].values()),
        testzip_ok=sum(v["testzip"] for v in inv["zips"].values()),
        total_zip_bytes=sum(v["bytes"] for v in inv["zips"].values()),
    )
    json.dump(inv, open(os.path.join(REP, "old_zip_inventory.json"), "w"), indent=1)
    print(json.dumps(inv["checks"], indent=1), round(time.time() - t0), "s")


if __name__ == "__main__":
    {"stage1": stage1, "verify": verify, "old_inventory": old_inventory}[sys.argv[1]]()
