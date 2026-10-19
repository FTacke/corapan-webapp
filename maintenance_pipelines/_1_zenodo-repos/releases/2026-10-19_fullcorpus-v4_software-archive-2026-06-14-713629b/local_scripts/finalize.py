import csv, hashlib, json, os, sys
STAGE = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging"
REP = os.path.join(STAGE, "local_only", "reports")
UP = os.path.join(STAGE, "zenodo_upload_ready")
FC = os.path.join(UP, "full-corpus")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def manifest():
    rows = json.load(open(os.path.join(REP, "stage1_rows.json")))
    ver = json.load(open(os.path.join(REP, "verify_results.json")))
    old = json.load(open(os.path.join(REP, "old_zip_inventory.json")))
    oldj = {m["recording_id"]: m["sha256"] for m in old["members"] if m["kind"] == "json"}
    oldm = {m["recording_id"]: m["sha256"] for m in old["members"] if m["kind"] == "mp3"}
    cols = ["package", "package_bytes", "package_sha256", "package_recordings", "package_audio_members", "package_json_members",
            "recording_id", "country_code", "date", "audio_member", "audio_bytes", "audio_sha256", "json_member", "json_bytes", "json_sha256",
            "segments", "word_entries", "schema_version", "annotation_version", "pipeline_version", "tense_rules_version", "spacy_model",
            "json_updated_at", "v3_json_sha256", "json_changed_vs_v3", "audio_identical_to_v3", "internal_file_id_differs_from_filename"]
    with open(os.path.join(FC, "MANIFEST.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, lineterminator="\n"); w.writeheader()
        for r in rows:
            p = ver["packages"][r["country_folder"]]
            w.writerow(dict(package=r["package"], package_bytes=p["bytes"], package_sha256=p["sha256"], package_recordings=p["recordings"],
                            package_audio_members=p["audio_members"], package_json_members=p["json_members"],
                            recording_id=r["recording_id"], country_code=r["country_code"], date=r["date"],
                            audio_member=r["audio_member"], audio_bytes=r["audio_bytes"], audio_sha256=r["audio_sha256"],
                            json_member=r["json_member"], json_bytes=r["json_bytes"], json_sha256=r["json_sha256"],
                            segments=r["segments"], word_entries=r["word_entries"], schema_version=r["schema_version"],
                            annotation_version=r["annotation_version"], pipeline_version=r["pipeline_version"],
                            tense_rules_version=r["tense_rules_version"], spacy_model=r["spacy_model"], json_updated_at=r["json_updated_at"],
                            v3_json_sha256=oldj[r["recording_id"]], json_changed_vs_v3=str(oldj[r["recording_id"]] != r["json_sha256"]).lower(),
                            audio_identical_to_v3=str(oldm[r["recording_id"]] == r["audio_sha256"]).lower(),
                            internal_file_id_differs_from_filename=str(r["internal_file_id"] + ".mp3" != r["internal_filename"] or r["internal_file_id"] != r["recording_id"]).lower()))
    inv = {"schema": "corapan-full-corpus-upload-inventory/v1", "total_packages": len(ver["packages"]), "total_recordings": len(rows),
           "total_word_entries": sum(r["word_entries"] for r in rows), "total_package_bytes": ver["total_bytes"], "packages": {}}
    for cc, p in ver["packages"].items():
        inv["packages"][cc + ".zip"] = dict(bytes=p["bytes"], sha256=p["sha256"], recordings=p["recordings"], audio_members=p["audio_members"],
                                            json_members=p["json_members"], structure="mp3-files/<id>.mp3 ; json-transcripts/<id>.json",
                                            recording_ids=[r["recording_id"] for r in rows if r["country_folder"] == cc])
    json.dump(inv, open(os.path.join(FC, "FILE_INVENTORY.json"), "w"), indent=1)
    print("manifest rows", len(rows), "differs flag:", [r["recording_id"] for r in rows if r["internal_file_id"] != r["recording_id"]])


def sums():
    for d in (FC, os.path.join(UP, "software")):
        out = []
        for f in sorted(os.listdir(d)):
            if f == "SHA256SUMS":
                continue
            out.append(f"{sha(os.path.join(d, f))}  {f}")
        open(os.path.join(d, "SHA256SUMS"), "w", newline="\n", encoding="utf-8").write("\n".join(out) + "\n")
        print(d, len(out))


{"manifest": manifest, "sums": sums}[sys.argv[1]]()
