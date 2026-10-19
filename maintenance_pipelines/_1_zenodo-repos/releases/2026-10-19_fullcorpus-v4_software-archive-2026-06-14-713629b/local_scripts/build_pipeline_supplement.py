"""Snapshot (read-only) of the UNCOMMITTED v3.2 annotation pipeline sources, for provenance. Local-only; NOT part of the software release."""
import hashlib, json, os, subprocess, zipfile
REPO = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
OUT = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging\local_only\provisional_uncommitted_pipeline_v3.2_snapshot.zip"
files = ["maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py",
         "maintenance_pipelines/_0_json/03_build_metadata_stats.py",
         "maintenance_pipelines/_0_json/tests/test_annotate_transcripts_v3_1.py"]
tools = sorted(os.listdir(os.path.join(REPO, "maintenance_pipelines/_0_json/tools")))
files += ["maintenance_pipelines/_0_json/tools/" + t for t in tools if t.endswith(".py")]
head = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], text=True).strip()
man = {"purpose": "provenance snapshot of working-tree (uncommitted) sources that produced the corapan-transcript-ann-v3.2 annotation; NOT committed, NOT in the software release",
       "based_on_head": head, "files": {}}
with zipfile.ZipFile(OUT, "w") as z:
    for f in files:
        data = open(os.path.join(REPO, f), "rb").read()
        man["files"][f] = hashlib.sha256(data).hexdigest()
        zi = zipfile.ZipInfo(f, (2026, 1, 1, 0, 0, 0)); zi.create_system = 3; zi.external_attr = 0o100644 << 16
        z.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    zi = zipfile.ZipInfo("SNAPSHOT_MANIFEST.json", (2026, 1, 1, 0, 0, 0)); zi.create_system = 3; zi.external_attr = 0o100644 << 16
    z.writestr(zi, json.dumps(man, indent=1), compress_type=zipfile.ZIP_DEFLATED)
print(json.dumps(man, indent=1)); print(hashlib.sha256(open(OUT, "rb").read()).hexdigest())
