"""Read-only probe for the v3 legacy-reader-retirement report. Exit 0 when the report exists in the main checkout and states READY."""
import glob, json, os, re, subprocess, sys
B = r"C:\dev\panhispanic_media_corpora"
NAME = "2026-10-19_legacy-reader-retirement-and-c-release.md"
main = os.path.join(B, "corapan", "docs", "agent-runs", NAME)
out = {"main_report": os.path.exists(main)}
if out["main_report"]:
    t = open(main, encoding="utf-8").read()
    m = re.search(r"LEGACY_C_RELEASE_READY\s*[=:]\s*`?\*{0,2}(true|false)", t, re.I)
    out["ready"] = m.group(1).lower() if m else None
wts = [p for p in glob.glob(os.path.join(B, "worktrees", "corapan", "*")) if os.path.exists(os.path.join(p, "docs", "agent-runs", NAME))]
out["worktrees_with_report"] = [os.path.basename(p) for p in wts]
try:
    out["main_head"] = subprocess.check_output(["git", "-C", os.path.join(B, "corapan"), "log", "-1", "--format=%h %ci %s"], text=True, timeout=20).strip()[:110]
except Exception as e:
    out["main_head"] = f"ERR {type(e).__name__}"
print(json.dumps(out, ensure_ascii=False))
sys.exit(0 if out.get("ready") == "true" else 1)
