"""Final Zenodo housekeeping (operator brief 2026-10-19): (1) verify published v4/software files against the local staging,
(2) discard ONLY the open unsaved edit session of the old Full Corpus version 17828582, then prove the published record is unchanged."""
import importlib.util, json, os, sys
sys.argv = [sys.argv[0]] + sys.argv[1:]
spec = importlib.util.spec_from_file_location("z", os.path.join(os.path.dirname(__file__), "zenodo_draft.py"))
z = importlib.util.module_from_spec(spec); spec.loader.exec_module(z)
OUT = {}


def published_vs_local():
    for fam, rid in (("fc", 23470771), ("sw", 23470763)):
        d = z.ok(z.req("GET", f"{z.API}/deposit/depositions/{rid}"), 200)
        rem = {f["filename"]: (int(f["filesize"]), f["checksum"].replace("md5:", "")) for f in z.ok(z.req("GET", f"{z.API}/deposit/depositions/{rid}/files"), 200)}
        loc_dir = z.FAM[fam]["dir"]
        loc = {f: (os.path.getsize(os.path.join(loc_dir, f)), z.md5(os.path.join(loc_dir, f))) for f in sorted(os.listdir(loc_dir))}
        OUT[fam] = dict(id=rid, doi=d.get("doi"), submitted=d["submitted"], state=d["state"], files=len(rem), equal_to_local=(rem == loc))
        print(fam, OUT[fam], flush=True)


def snapshot(rid):
    d = z.ok(z.req("GET", f"{z.API}/deposit/depositions/{rid}"), 200)
    files = sorted((f["filename"], int(f["filesize"]), f["checksum"]) for f in z.ok(z.req("GET", f"{z.API}/deposit/depositions/{rid}/files"), 200))
    pub = z.ok(z.S.get(f"{z.API}/records/{rid}", headers={"Authorization": ""}, timeout=60), 200)  # anonymous published view
    return d, files, pub


def discard_old_edit():
    rid = 17828582
    d, files, pub = snapshot(rid)
    print("before:", dict(state=d["state"], submitted=d["submitted"], doi=d.get("doi"), files=len(files)), flush=True)
    if not (d["submitted"] and d["state"] == "inprogress"):
        OUT["discard"] = dict(action="none", reason=f"state={d['state']} submitted={d['submitted']}")
        print(OUT["discard"]); return
    r = z.S.post(f"{z.API}/deposit/depositions/{rid}/actions/discard", timeout=120)
    print("discard HTTP", r.status_code, flush=True)
    d2, files2, pub2 = snapshot(rid)
    OUT["discard"] = dict(http=r.status_code, state_before=d["state"], state_after=d2["state"], submitted_after=d2["submitted"],
                          doi_unchanged=d2.get("doi") == d.get("doi"), files_unchanged=files2 == files,
                          published_metadata_unchanged=pub2.get("metadata") == pub.get("metadata"),
                          published_files_unchanged=pub2.get("files") == pub.get("files"),
                          published_revision=(pub.get("revision"), pub2.get("revision")))
    print(json.dumps(OUT["discard"], indent=1))


published_vs_local()
discard_old_edit()
json.dump(OUT, open(os.path.join(z.REP, "zenodo_final_housekeeping.json"), "w"), indent=1)
