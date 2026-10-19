"""Uncached (FILE_FLAG_NO_BUFFERING) re-verification of the LEGACY B1 backup against the tree manifest; primary identity + manifest unchanged."""
import hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\dev\panhispanic_media_corpora\corapan\src")
from corapan_playground.storage.archive_secondary import sha256_uncached  # noqa: E402
from corapan_playground.storage.target_identity import check as identity_check  # noqa: E402
P = r"\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN\projects\panhispanic_media_corpora\legacy\corapan"
B = r"D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup"
SP = os.path.dirname(os.path.abspath(__file__))
EXPECT_TREE = "f70bcbb38899be150c30195cb5c14b14243a925f35ec98b885369fca1980ae5f"


def lp(p):
    return "\\\\?\\UNC\\" + p[2:] if p.startswith("\\\\") else "\\\\?\\" + p


t0 = time.time()
pm = open(lp(P + r"\corapan\ARCHIVE_MANIFEST.json"), "rb").read()
bm = open(lp(B + r"\corapan\ARCHIVE_MANIFEST.json"), "rb").read()
man = json.loads(bm)
ident = identity_check(P, holding="LEGACY", expected_id="corapan-archive-newfs-legacy")
bmarker = json.load(open(os.path.join(B, "BACKUP_ROOT.json"), encoding="utf-8"))
rows = man["files"]


def one(r):
    p = os.path.join(B, "corapan", r["path"].replace("/", os.sep))
    if not os.path.exists(p):
        return (r["path"], "MISSING", None)
    h, n, mode = sha256_uncached(p)
    return (r["path"], "OK" if (h == r["sha256"] and n == r["size"]) else "DIFFERS", mode)


with ThreadPoolExecutor(2) as ex:
    res = list(ex.map(one, rows))
modes = {}
for _, _, m in res:
    modes[m] = modes.get(m, 0) + 1
bad = [(p, s) for p, s, _ in res if s != "OK"]
extra = []
base = os.path.join(B, "corapan"); listed = {r["path"] for r in rows} | {"ARCHIVE_MANIFEST.json"}
for d, _, fs in os.walk(base):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), base).replace("\\", "/")
        if rel not in listed:
            extra.append(rel)
rep = dict(primary_identity=ident["state"], primary_manifest_sha256=hashlib.sha256(pm).hexdigest(), backup_manifest_sha256=hashlib.sha256(bm).hexdigest(),
           manifests_identical=pm == bm, tree_sha256=man["tree_sha256"], tree_sha256_expected=man["tree_sha256"] == EXPECT_TREE,
           backup_marker_holding=bmarker.get("holding"), files=len(rows), ok=len(rows) - len(bad), problems=bad[:20], unlisted_in_backup=extra[:20],
           read_modes=modes, seconds=round(time.time() - t0), verified_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           all_ok=not bad and not extra and pm == bm and ident["state"] == "IDENTITY_OK" and man["tree_sha256"] == EXPECT_TREE)
json.dump(rep, open(os.path.join(SP, "b1_uncached_verify.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
