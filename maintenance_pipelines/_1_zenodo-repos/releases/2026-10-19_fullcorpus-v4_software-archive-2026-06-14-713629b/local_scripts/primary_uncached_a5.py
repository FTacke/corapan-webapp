"""Full UNCACHED re-read of the LEGACY primary tree (FILE_FLAG_NO_BUFFERING via the CO.RA.PAN tool) + A5 decision (archive_tree)."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\dev\panhispanic_media_corpora\corapan\src")
from corapan_playground.storage.archive_secondary import sha256_uncached  # noqa: E402
from corapan_playground.storage.target_identity import check as identity_check  # noqa: E402
from corapan_playground.crosscorpus.storage_contract import archive_tree  # noqa: E402
P = r"\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN\projects\panhispanic_media_corpora\legacy\corapan"
T = P + r"\corapan"
SP = os.path.dirname(os.path.abspath(__file__))


def lp(p):
    return "\\\\?\\UNC\\" + p[2:]


t0 = time.time()
ident = identity_check(P, holding="LEGACY", expected_id="corapan-archive-newfs-legacy")
man = json.loads(open(lp(T + r"\ARCHIVE_MANIFEST.json"), encoding="utf-8").read())
paths = []
for d, _, fs in os.walk(lp(T)):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), lp(T)).replace("\\", "/")
        if rel != "ARCHIVE_MANIFEST.json":
            paths.append(rel)


def one(rel):
    h, n, mode = sha256_uncached(T + "\\" + rel.replace("/", "\\"))
    return dict(path=rel, size=n, sha256=h), mode


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, paths))
obs = [r for r, _ in res]
modes = {}
for _, m in res:
    modes[m] = modes.get(m, 0) + 1
codes = archive_tree(corpus="corapan", holding="LEGACY", tree="corapan", target_identity_ok=ident["state"] == "IDENTITY_OK", manifest=man, observed=obs)
rep = dict(root=P, identity=ident["state"], files=len(obs), bytes=sum(o["size"] for o in obs), tree_sha256=man["tree_sha256"], codes=codes,
           state="PRESERVED" if not codes else "NOT_PRESERVED", read_modes=modes, seconds=round(time.time() - t0),
           verified_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
json.dump(rep, open(os.path.join(SP, "primary_uncached_a5.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
