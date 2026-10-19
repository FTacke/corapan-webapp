"""Phase C: release the local original MP3 (media/mp3-full) under A7 (D127/D128). Per-file gates: fresh local SHA-256 == the PRESERVED
tree manifest == present in the B1 backup with the same digest (uncached); global gates: primary uncached A5 PRESERVED, B1 uncached all_ok.
Keeps .gitkeep (tracked). Never touches NEW_FS, D: or the server."""
import hashlib, json, os, stat, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\dev\panhispanic_media_corpora\corapan\src")
from corapan_playground.storage.archive_secondary import sha256_uncached  # noqa: E402
L = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
BT = r"D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup\corapan"
SP = os.path.dirname(os.path.abspath(__file__))
a5 = json.load(open(os.path.join(SP, "primary_uncached_a5.json")))
b1 = json.load(open(os.path.join(SP, "b1_uncached_verify.json")))
assert a5["state"] == "PRESERVED" and not a5["codes"] and a5["identity"] == "IDENTITY_OK" and a5["read_modes"] == {"uncached": a5["files"]}, a5
assert b1["all_ok"] and b1["tree_sha256"] == a5["tree_sha256"], "B1 gate"
man = {r["path"]: r for r in json.load(open(os.path.join(BT, "ARCHIVE_MANIFEST.json"), encoding="utf-8"))["files"]}
tracked = set(subprocess.check_output(["git", "-C", L, "ls-files", "media"], text=True, encoding="utf-8").splitlines())
J = os.path.join(SP, "phasec_mp3_full_journal.jsonl")
base = os.path.join(L, "media", "mp3-full")
res = dict(deleted=[], kept=[], bytes=0)
for d, _, fs in os.walk(base):
    for f in sorted(fs):
        p = os.path.join(d, f); rel = os.path.relpath(p, L).replace(os.sep, "/")
        if rel in tracked:
            res["kept"].append((rel, "git-tracked")); continue
        m = man.get(rel)
        if not m:
            res["kept"].append((rel, "not in archive manifest")); continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        hb, nb, mode = sha256_uncached(os.path.join(BT, rel.replace("/", os.sep)))
        if not (h == m["sha256"] == hb and os.path.getsize(p) == m["size"] == nb and mode == "uncached"):
            res["kept"].append((rel, "digest mismatch")); continue
        try:
            os.chmod(p, stat.S_IWRITE); os.remove(p)
        except OSError as e:
            res["kept"].append((rel, f"delete failed: {e}")); continue
        res["deleted"].append(dict(path=rel, size=m["size"], sha256=h)); res["bytes"] += m["size"]
dirs = 0
for d in sorted((os.path.join(base, x) for x in os.listdir(base)), reverse=True):
    if os.path.isdir(d) and not os.listdir(d):
        os.chmod(d, stat.S_IWRITE); os.rmdir(d); dirs += 1
res["empty_country_dirs_removed"] = dirs; res["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
open(J, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n")
print(json.dumps(dict(deleted=len(res["deleted"]), bytes=res["bytes"], kept=res["kept"], dirs=dirs), ensure_ascii=False, indent=1))
