"""Phase B local release (A7): delete local originals only when (a) listed in the PRESERVED tree's ARCHIVE_MANIFEST with the same
SHA-256 (fresh re-hash), (b) not Git-tracked, (c) in a released class. mp3-full and transcripts are NOT released (v3 readers)."""
import hashlib, json, os, stat, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
L = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
MAN = r"D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup\corapan\ARCHIVE_MANIFEST.json"   # byte copy of the primary's manifest (A5 on both)
SP = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(SP, "phaseb_cleanup_journal.jsonl")
RELEASED = ["data/blacklab/quarantine/", "data/blacklab/backups/", "data/blacklab/export/tsv/tsv_for_index/", "data/exports/",
            "data/blacklab/export/tsv_json_test/", "maintenance_pipelines/_0_json/backups/"]
NEVER = ["media/mp3-full/", "media/transcripts/"]
man = {r["path"]: r for r in json.load(open(MAN, encoding="utf-8"))["files"]}
tracked = set(subprocess.check_output(["git", "-C", L, "ls-files"], text=True, encoding="utf-8").splitlines())


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


res = {"deleted": 0, "bytes": 0, "kept_tracked": [], "kept_not_in_manifest": [], "kept_mismatch": []}
by = {}
for pre in RELEASED:
    root = os.path.join(L, pre.replace("/", os.sep))
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, L).replace(os.sep, "/")
            assert not any(rel.startswith(n) for n in NEVER)
            if rel in tracked:
                res["kept_tracked"].append(rel); continue
            if rel not in man:
                res["kept_not_in_manifest"].append(rel); continue
            if sha(p) != man[rel]["sha256"] or os.path.getsize(p) != man[rel]["size"]:
                res["kept_mismatch"].append(rel); continue
            sz = os.path.getsize(p)
            os.chmod(p, stat.S_IWRITE); os.remove(p)
            res["deleted"] += 1; res["bytes"] += sz
            k = by.setdefault(pre, [0, 0]); k[0] += 1; k[1] += sz
# remove directories left empty (bottom-up), never a directory that still holds a file
removed_dirs = 0
for pre in RELEASED:
    root = os.path.join(L, pre.replace("/", os.sep))
    for d, ds, fs in sorted(os.walk(root), key=lambda x: -len(x[0])):
        if not os.listdir(d) and os.path.normcase(d) != os.path.normcase(os.path.join(L, "maintenance_pipelines", "_0_json", "backups")):
            os.chmod(d, stat.S_IWRITE); os.rmdir(d); removed_dirs += 1
res["by_class"] = by; res["empty_dirs_removed"] = removed_dirs; res["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
open(J, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n")
print(json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:8])) for k, v in res.items()}, ensure_ascii=False, indent=1))
