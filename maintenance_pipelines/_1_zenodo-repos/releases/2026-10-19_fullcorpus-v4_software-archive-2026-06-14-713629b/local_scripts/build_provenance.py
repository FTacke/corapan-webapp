"""Build the v3.2 annotation provenance supplement for Full Corpus v4 (read-only on the repository)."""
import hashlib, json, os, re, subprocess, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")
REPO = r"C:\dev\panhispanic_media_corpora\legacy\corapan"
J = "maintenance_pipelines/_0_json"
OUTDIR = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging\local_only\next"
NAME = "CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip"
ROOT = "CORAPAN_annotation-v3.2_provenance/"
DT = (2026, 1, 1, 0, 0, 0)
HEAD = subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], text=True).strip()

entries = {}  # arcname -> bytes


def add_file(arc, rel):
    entries[arc] = open(os.path.join(REPO, rel), "rb").read()


def add_git(arc, rel):
    entries[arc] = subprocess.check_output(["git", "-C", REPO, "show", f"{HEAD}:{rel}"])


# 1. code actually used (working tree, uncommitted at HEAD)
wt = [f"{J}/02_annotate_transcripts_v3.py", f"{J}/03_build_metadata_stats.py", f"{J}/tests/test_annotate_transcripts_v3_1.py"]
wt += [f"{J}/tools/{t}" for t in sorted(os.listdir(os.path.join(REPO, J, "tools"))) if t.endswith(".py")]
for rel in wt:
    add_file("code/working_tree_v3.2/" + rel, rel)
# 2. committed reference versions at HEAD
for rel in [f"{J}/02_annotate_transcripts_v3.py", f"{J}/03_build_metadata_stats.py", f"{J}/audit_transcript_annotation_quality.py",
            f"{J}/tests/test_annotate_transcripts_v3_1.py", f"{J}/README-pipeline_json.md", "maintenance_pipelines/requirements-lokal.txt"]:
    add_git("code/committed_" + HEAD[:7] + "/" + rel, rel)
# 3. run records (only CO.RA.PAN-derived; CO.PRE.PAN reference-schema files excluded: they contain text examples of another corpus)
D = f"{J}/docs/agent-runs"
runs = ["2026-06-14_corapan_annotation_v3_1_upgrade.md", "2026-06-14_corapan_annotation_v3_1_spacy_real_followup.md",
        "2026-06-14_corapan_annotation_v3_1_full_transcripts_run.md", "2026-06-14_full_annotation_preflight_after_timestamp_repair.md",
        "2026-06-14_ARG-SDE_2025-02-07_timestamp_repair.md", "2026-06-14_ARG-SDE_2025-02-07_timestamp_repair.json",
        "2026-06-14_corapan_tense_schema_coprepan_alignment.md", "2026-06-14_corapan_v3_2_inventory_check.md",
        "2026-06-14_corapan_v3_2_inventory_check.json", "2026-06-14_tense_distribution_sanity_after_v3_2.md",
        "2026-06-14_tense_distribution_sanity_after_v3_2.json", "2026-06-14_metadata_stats_verification_after_v3_2.md",
        "2026-06-14_metadata_stats_verification_after_v3_2.json",
        "audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.md", "audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_before.json",
        "audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.md", "audits/2026-06-14_corapan_vs_coprepan_tense_schema_diff_after.json",
        "audits/2026-06-14_tense_schema_migration_token_id_diff.md", "audits/2026-06-14_tense_schema_migration_token_id_diff.json",
        "audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.md",
        "audits/2026-06-14_full_transcripts_annotation_audit_coprepan_tense_compatible.json",
        "archive_commands/run_full_transcripts_annotation.ps1"]
for r in runs:
    add_file("run_records/" + r, f"{D}/{r}")
# 4. logs (PowerShell transcript header sanitised: user/machine/process lines removed)
add_file("logs/annotate_transcripts.log", f"{J}/logs/annotation/annotate_transcripts.log")
for r in ["migration_20260614T110946Z.log", "migration_20260614T110946Z.jsonl"]:
    add_file("logs/tense_schema_migration/" + r, f"{J}/logs/tense_schema_migration/{r}")
t = open(os.path.join(REPO, J, "logs/annotation/full_annotation_20260614T102552.transcript.txt"), "rb").read().decode("utf-8", "replace")
t = "\n".join(l for l in t.splitlines() if not re.match(r"^\s*(Benutzername|RunAs-Benutzer|Konfigurationsname|Computer|Hostanwendung|Prozess-ID|Username|RunAs User|Machine|Host Application|Process ID|Configuration Name|PSVersion|PSEdition|PSCompatibleVersions|BuildVersion|CLRVersion|WSManStackVersion|PSRemotingProtocolVersion|SerializationVersion)\s*:", l))
entries["logs/full_annotation_20260614T102552.transcript.sanitised.txt"] = t.encode("utf-8")
# 5. environment
sp = os.path.join(REPO, ".venv", "Lib", "site-packages")
pk = sorted(d[:-len(".dist-info")] for d in os.listdir(sp) if d.endswith(".dist-info"))
entries["environment/installed_packages.txt"] = ("# dist-info entries of the project virtualenv (.venv), read 2026-10-19; installed 2026-06-14 ~07:00 UTC, before the annotation run\n"
                                                 "# Python 3.12.10 (Windows)\n" + "\n".join(pk) + "\n").encode()
add_file("PROVENANCE.md", r"..\corapan_zenodo_staging\local_only\next\PROVENANCE.md")

# safety scan
pat = {"privkey": rb"BEGIN [A-Z ]*PRIVATE KEY", "token": rb"(gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[bap]-)", "bearer": rb"Bearer [A-Za-z0-9]{20,}",
       "email": rb"[\w.+-]+@[\w-]+\.[a-z]{2,}", "userpath": rb"Users[\\/]+[^\\/\s\"]+", "host_or_user": rb"(?i)THINKSTAT|Felix Tacke\|TACKE-", "pgpass": rb"postgres(ql)?(\+\w+)?://\w+:[^@\s$\{]{3,}@"}
hits = {}
for a, b in entries.items():
    for k, p in pat.items():
        for m in re.findall(p, b):
            hits.setdefault(k, set()).add((a, m if isinstance(m, bytes) else m))
print("scan:", {k: sorted({x[0] for x in v})[:6] for k, v in hits.items()})
for k, v in hits.items():
    print(k, sorted({x[1][:60] if isinstance(x[1], bytes) else str(x[1])[:60] for x in v})[:8])

man = {a: hashlib.sha256(b).hexdigest() for a, b in sorted(entries.items())}
entries["MANIFEST.sha256"] = ("".join(f"{h}  {a}\n" for a, h in man.items())).encode()
os.makedirs(OUTDIR, exist_ok=True)
out = os.path.join(OUTDIR, NAME)
with zipfile.ZipFile(out, "w") as z:
    for a in sorted(entries):
        zi = zipfile.ZipInfo(ROOT + a.replace("\\", "/"), DT); zi.create_system = 3; zi.external_attr = 0o100644 << 16
        z.writestr(zi, entries[a], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
print(out, os.path.getsize(out), hashlib.sha256(open(out, "rb").read()).hexdigest(), len(entries), "entries")
json.dump({"head": HEAD, "files": man}, open(os.path.join(OUTDIR, "provenance_manifest.json"), "w"), indent=1)
