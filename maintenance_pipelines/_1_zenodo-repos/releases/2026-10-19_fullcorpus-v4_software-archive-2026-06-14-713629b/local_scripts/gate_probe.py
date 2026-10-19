"""Read-only, cheap probe of the LEGACY contract gate. Prints one JSON line. Exit 0 = candidate signal (needs full manual check), 1 = not yet."""
import hashlib, json, os, re, sys
B = r"C:\dev\panhispanic_media_corpora"
BASE = "8d17fc214076b21e47774d228e016dfe36484b29ce0ecad693456c07f9018fb3"


def pin(repo):
    try:
        d = json.load(open(os.path.join(B, repo, "config", "crosscorpus", "contract_pins.json"), encoding="utf-8"))
        c = d["contracts"].get("crosscorpus-storage/v1") or {}
        return c.get("bundle_sha256"), c.get("status")
    except Exception as e:
        return None, f"ERR {type(e).__name__}"


def contract_has_legacy(repo):
    p = os.path.join(B, repo, "contracts", "crosscorpus-storage-v1", "CONTRACT.md")
    if not os.path.exists(p):
        return None
    t = open(p, encoding="utf-8").read()
    return bool(re.search(r"panhispanic_media_corpora/legacy/", t)) or bool(re.search(r"\bLEGACY\b.*(holding|archive)", t, re.I))


r = {}
for repo in ("corapan", "coprepan"):
    r[repo] = dict(pin=pin(repo), contract_legacy=contract_has_legacy(repo))
    wt = os.path.join("worktrees", repo, "legacy-archive-contract")
    if os.path.isdir(os.path.join(B, wt)):
        import subprocess
        try:
            head = subprocess.check_output(["git", "-C", os.path.join(B, wt), "log", "-1", "--format=%h %ci %s"], text=True, timeout=20).strip()[:120]
        except Exception as e:
            head = f"ERR {type(e).__name__}"
        r[repo]["worktree"] = dict(head=head, pin=pin(wt)[0], contract_legacy=contract_has_legacy(wt))
a, b = r["corapan"]["pin"][0], r["coprepan"]["pin"][0]
r["changed"] = bool(a and a != BASE)
r["signal"] = bool(a and b and a == b and a != BASE and r["corapan"]["contract_legacy"])
print(json.dumps(r))
sys.exit(0 if (r["signal"] or r["changed"] or r["corapan"]["contract_legacy"]) else 1)
