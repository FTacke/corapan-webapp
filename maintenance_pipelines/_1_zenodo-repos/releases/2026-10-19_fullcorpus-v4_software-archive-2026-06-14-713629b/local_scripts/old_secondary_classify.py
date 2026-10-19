"""Classify every object of the old D: secondary (protected_secondary/legacy_corapan, 2026-10-15) by CONTENT (SHA-256 from its own
uncached journal) against: the PRESERVED LEGACY tree (NEW_FS, = B1), the old Zenodo-v3 ZIP inventory, Git blobs, regenerable classes."""
import collections, csv, hashlib, json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
OLD = r"D:\projects\panhispanic_media_corpora\corapan\archive\protected_secondary\legacy_corapan"
L = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
MAN = r"D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup\corapan\ARCHIVE_MANIFEST.json"
SP = os.path.dirname(os.path.abspath(__file__))

journal = {}
for line in open(os.path.join(OLD, "_secondary", "journal.jsonl"), encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        journal[r["rel"]] = r
rows = {k: v for k, v in journal.items() if v.get("status") == "COPIED"}
tree = json.load(open(MAN, encoding="utf-8"))["files"]
tree_sha = {r["sha256"] for r in tree}
oldzip = list(csv.DictReader(open(os.path.join(L, "docs", "agent-runs", "2026-10-19_old_full_corpus_zip_inventory.csv"), encoding="utf-8")))
zip_sha = {r["zip_sha256"] for r in oldzip}
member_in_tree = all(r["member_sha256"] in tree_sha for r in oldzip)

# git blobs (sha256 of content) for every path tracked in any local commit of interest
revs = ["713629b", "legacy/v3.2-provenance-and-retention"]
git_sha = set()
paths = set()
for rev in revs:
    paths |= set(subprocess.check_output(["git", "-C", L, "ls-tree", "-r", "--name-only", rev], text=True, encoding="utf-8").splitlines())
proc = subprocess.Popen(["git", "-C", L, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
for rev in revs:
    for p in sorted(paths):
        proc.stdin.write(f"{rev}:{p}\n".encode("utf-8")); proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) == 2 and header[1] == b"missing":
            continue
        size = int(header[2]); data = proc.stdout.read(size); proc.stdout.read(1)
        git_sha.add(hashlib.sha256(data).hexdigest())
proc.stdin.close(); proc.wait()

REGEN = [("media/mp3-split/", "REGENERABLE (splits; regenerable from mp3-full; production server keeps its own)"),
         (".venv/", "REGENERABLE (virtualenv; package list in docs/agent-runs)"), ("tmp/", "DISPOSABLE (sync-test material, classified 2026-10-19)"),
         ("app/.ruff_cache/", "CACHE"), ("data/db/restricted/", "DEV_DATABASE (not scientific; not archived on purpose; current copy on C:)")]
cls = collections.Counter(); size = collections.Counter(); unique = []
for rel, r in rows.items():
    s = r["sha256"]
    if s in tree_sha:
        c = "IN_LEGACY_TREE"
    elif s in zip_sha:
        c = "ZENODO_V3_ZIP (every member byte-identical in the LEGACY tree)"
    elif rel.startswith(".git/"):
        c = "GIT_DIRECTORY"
    elif s in git_sha:
        c = "GIT_TRACKED_IDENTICAL"
    elif "/__pycache__/" in rel or rel.endswith(".pyc") or "/.pytest_cache/" in rel:
        c = "CACHE"
    else:
        c = next((label for pre, label in REGEN if rel.startswith(pre)), "UNMATCHED")
    cls[c] += 1; size[c] += int(r["size"])
    if c == "UNMATCHED":
        unique.append((rel, int(r["size"])))
# git: are all refs of the old .git present in the current repository?
refs = []
pr = os.path.join(OLD, ".git", "packed-refs")
if os.path.exists(pr):
    refs += [l.split()[0] for l in open(pr, encoding="utf-8") if l[:1] not in "#^" and l.strip()]
for d, _, fs in os.walk(os.path.join(OLD, ".git", "refs")):
    for f in fs:
        refs.append(open(os.path.join(d, f), encoding="utf-8").read().strip())
refs.append(open(os.path.join(OLD, ".git", "HEAD"), encoding="utf-8").read().strip())
missing_refs = []
for ref in set(x for x in refs if len(x) == 40):
    if subprocess.run(["git", "-C", L, "cat-file", "-e", ref + "^{commit}"], capture_output=True).returncode != 0:
        missing_refs.append(ref)
rep = dict(objects=len(rows), bytes=sum(int(r["size"]) for r in rows.values()), zip_members_all_in_tree=member_in_tree,
           classes={k: dict(files=cls[k], bytes=size[k]) for k in cls}, unmatched=sorted(unique, key=lambda x: -x[1]),
           git_refs_checked=len(set(x for x in refs if len(x) == 40)), git_refs_missing_in_current_repo=missing_refs)
json.dump(rep, open(os.path.join(SP, "old_secondary_classification.json"), "w"), indent=1)
print(json.dumps({**rep, "unmatched": [(len(unique), sum(b for _, b in unique))] + unique[:60]}, indent=1, ensure_ascii=False))
