"""Controlled removal of the OLD local Full Corpus ZIP generation (25 files) after re-checking every gate. Deletes nothing else."""
import csv, hashlib, json, os, sys
REPO = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
STAGE = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging"
REP = os.path.join(STAGE, "local_only", "reports")
OLD = os.path.join(REPO, "maintenance_pipelines", "_1_zenodo-repos", "Zenodo Full Corpus")
DOLD = r"D:\projects\panhispanic_media_corpora\corapan\archive\protected_secondary\legacy_corapan\maintenance_pipelines\_1_zenodo-repos\Zenodo Full Corpus"
NEW = os.path.join(STAGE, "zenodo_upload_ready", "full-corpus")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


inv = json.load(open(os.path.join(REP, "old_zip_inventory.json")))
ver = json.load(open(os.path.join(REP, "verify_results.json")))
c = inv["checks"]
gates = {
    "G1 list+sha256 of old zips recorded": len(inv["zips"]) == 25,
    "G2 all members captured, only mp3/json": c["members"] == 292 and c["other_members"] == [] and c["testzip_ok"] == 25,
    "G3 146/146 old audio == local mp3-full == D: mp3-full == new package audio": c["mp3_equal_local"] == c["mp3_equal_D"] == c["mp3_equal_new_pkg"] == 146,
    "G4 146/146 old JSON == pre-v3_1 backup (local and D:)": c["json_equal_local_backup"] == c["json_equal_D_backup"] == 146,
    "G6 no extra members in old zips": c["other_members"] == [],
    "G7 byte-identical D: secondary copy of all 25 old zips": c["d_zip_copies_identical"] == 25,
    "G8 new packages complete + validated": len(ver["packages"]) == 25 and not ver["problems"] and ver["determinism_probe"]["identical"],
}
# fresh re-check immediately before deleting
live = {}
for f, v in inv["zips"].items():
    p, d = os.path.join(OLD, f), os.path.join(DOLD, f)
    live[f] = os.path.exists(p) and os.path.exists(d) and sha(p) == v["sha256"] == sha(d)
gates["G7b fresh re-hash: C: == inventory == D: for all 25"] = all(live.values()) and len(live) == 25
for f in ver["packages"]:
    gates.setdefault("G8b new packages present with recorded sha", True)
    gates["G8b new packages present with recorded sha"] &= os.path.exists(os.path.join(NEW, f + ".zip")) and sha(os.path.join(NEW, f + ".zip")) == ver["packages"][f]["sha256"]
print(json.dumps(gates, indent=1))
log = {"gates": gates, "deleted": []}
if all(gates.values()):
    for f, v in sorted(inv["zips"].items()):
        p = os.path.join(OLD, f)
        os.remove(p)
        log["deleted"].append({"file": f, "bytes": v["bytes"], "sha256": v["sha256"]})
    log["deleted_count"] = len(log["deleted"]); log["deleted_bytes"] = sum(x["bytes"] for x in log["deleted"])
    log["remaining_in_dir"] = sorted(os.listdir(OLD))
    log["status"] = "DELETED"
else:
    log["status"] = "KEPT (gate failed)"
json.dump(log, open(os.path.join(REP, "deletion_log.json"), "w"), indent=1)
print(log["status"], log.get("deleted_count"), log.get("deleted_bytes"), log.get("remaining_in_dir"))
