"""(1) A5 decision on the BACKUP copy of the tree (every file re-read from D:, against the tree's ARCHIVE_MANIFEST.json);
(2) stratified read-back: restore samples per data class FROM THE BACKUP into an empty scratch dir and compare SHA-256."""
import hashlib, json, os, random, shutil, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\dev\panhispanic_media_corpora\corapan\src")
from corapan_playground.crosscorpus.storage_contract import archive_tree  # noqa: E402
B = r"D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup\corapan"
SP = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(SP, "readback_scratch")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


man = json.load(open(os.path.join(B, "ARCHIVE_MANIFEST.json"), encoding="utf-8"))
obs = []
for d, _, fs in os.walk(B):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), B).replace("\\", "/")
        if rel != "ARCHIVE_MANIFEST.json":
            obs.append(dict(path=rel, size=os.path.getsize(os.path.join(d, f)), sha256=sha(os.path.join(d, f))))
codes = archive_tree(corpus="corapan", holding="LEGACY", tree="corapan", target_identity_ok=True, manifest=man, observed=obs)
classes = {"original_audio": "media/mp3-full/", "annotation_v3_2": "media/transcripts/", "annotation_v3": "maintenance_pipelines/_0_json/backups/pre-v3_1-transcripts/",
           "annotation_v3_1_intermediate": "maintenance_pipelines/_0_json/backups/pre-tense-schema-migration/", "manual_repairs": "maintenance_pipelines/_0_json/backups/manual-repairs/",
           "active_index": "data/blacklab/index/", "historic_index_builds": "data/blacklab/quarantine/", "index_backups": "data/blacklab/backups/",
           "export_tsv": "data/blacklab/export/tsv/", "old_exports": "data/exports/", "public_data": "data/public/", "processing_evidence": "maintenance_pipelines/_0_json/docs/",
           "release_records": "maintenance_pipelines/_1_zenodo-repos/releases/", "smoke_states": "maintenance_pipelines/_0_json/backups/smoke-tests/"}
assert not os.path.exists(SCR) or not os.listdir(SCR)
os.makedirs(SCR, exist_ok=True)
rnd = random.Random(20261019)
cases = []
for cls, pre in classes.items():
    rows = [r for r in man["files"] if r["path"].startswith(pre)]
    for r in rnd.sample(rows, min(3, len(rows))):
        dst = os.path.join(SCR, cls, os.path.basename(r["path"]))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(B, r["path"].replace("/", os.sep)), dst)
        got = sha(dst)
        cases.append(dict(cls=cls, path=r["path"], size=r["size"], ok=got == r["sha256"] and os.path.getsize(dst) == r["size"]))
counts = {}
for c in cases:
    k = counts.setdefault(c["cls"], [0, 0]); k[0] += 1; k[1] += int(c["ok"])
ok = all(c["ok"] for c in cases)
if ok:
    shutil.rmtree(SCR)
rep = dict(backup_tree=B, a5_codes_on_backup=codes, backup_files=len(obs), manifest_files=len(man["files"]), tree_sha256=man["tree_sha256"],
           readback_cases=len(cases), readback_ok=sum(c["ok"] for c in cases), per_class=counts, all_ok=ok and not codes,
           tested_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), cases=cases)
json.dump(rep, open(os.path.join(SP, "backup_readback.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != "cases"}, indent=1))
