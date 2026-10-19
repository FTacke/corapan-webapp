"""Publish ONLY the two operator-approved drafts (2026-10-19), after a fresh pre-publish verification. Then verify the published records."""
import importlib.util, json, os, sys, hashlib
sys.argv = [sys.argv[0]] + sys.argv[1:]
spec = importlib.util.spec_from_file_location("z", os.path.join(os.path.dirname(__file__), "zenodo_draft.py"))
z = importlib.util.module_from_spec(spec); spec.loader.exec_module(z)
APPROVED = {"fc": 23470771, "sw": 23470763}
EXPECT = {"fc": dict(access="restricted", files=31), "sw": dict(access="open", files=4, license="mit-license")}
REP = z.REP


def local_md5s(fam):
    d = z.FAM[fam]["dir"]
    return {f: (os.path.getsize(os.path.join(d, f)), z.md5(os.path.join(d, f))) for f in sorted(os.listdir(d))}


def precheck(fam, did, loc):
    d = z.ok(z.req("GET", f"{z.API}/deposit/depositions/{did}"), 200)
    assert d["id"] == APPROVED[fam] and not d["submitted"], f"{fam}: not an unpublished approved draft"
    assert d["metadata"]["access_right"] == EXPECT[fam]["access"]
    if "license" in EXPECT[fam]:
        assert d["metadata"].get("license") == EXPECT[fam]["license"]
    rem = {f["filename"]: (int(f["filesize"]), f["checksum"].replace("md5:", "")) for f in z.ok(z.req("GET", f"{z.API}/deposit/depositions/{did}/files"), 200)}
    assert rem == loc and len(rem) == EXPECT[fam]["files"], f"{fam}: files differ from local"
    return d


def publish(fam):
    did = APPROVED[fam]
    loc = local_md5s(fam)
    precheck(fam, did, loc)
    url = f"{z.API}/deposit/depositions/{did}/actions/publish"
    r = z.S.post(url, timeout=600)  # deliberate, operator-approved publish (bypasses the draft-only guard in zenodo_draft.req)
    if r.status_code != 202:
        raise SystemExit(f"publish {fam} failed: HTTP {r.status_code} {r.text[:500]}")
    j = r.json()
    print(fam, "published:", j.get("doi"), j.get("doi_url"), j["links"].get("html"), flush=True)
    return loc


def post_verify(fam, loc):
    did = APPROVED[fam]
    d = z.ok(z.req("GET", f"{z.API}/deposit/depositions/{did}"), 200)
    m = d["metadata"]
    rem = {f["filename"]: (int(f["filesize"]), f["checksum"].replace("md5:", "")) for f in z.ok(z.req("GET", f"{z.API}/deposit/depositions/{did}/files"), 200)}
    rec = z.ok(z.req("GET", f"{z.API}/records/{did}"), 200)
    pub = z.ok(z.S.get(f"{z.API}/records/{did}", headers={"Authorization": ""}, timeout=60), 200)  # anonymous view
    vers = sorted(((v["id"], v.get("submitted"), v["metadata"].get("version")) for v in z.versions(fam)))
    res = dict(id=did, submitted=d["submitted"], state=d["state"], doi=d.get("doi"), conceptdoi=d.get("conceptdoi"),
               html=rec["links"].get("self_html") or rec["links"].get("html"), version=m.get("version"), access=m.get("access_right"),
               license=m.get("license"), files=len(rem), files_match_local=(rem == loc),
               anonymous_access_status=pub.get("metadata", {}).get("access_right") or pub.get("access", {}).get("status"),
               anonymous_files_visible=len(pub.get("files", []) or []), is_latest=rec.get("links", {}).get("latest", "").endswith(str(did)),
               versions=vers, related=[(x["relation"], x["identifier"]) for x in m.get("related_identifiers", [])],
               relations=rec.get("metadata", {}).get("relations"))
    json.dump(res, open(os.path.join(REP, f"zenodo_{fam}_published_verify.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("related", "relations")}, indent=1))


if __name__ == "__main__":
    fam = sys.argv[1]
    assert fam in APPROVED
    if sys.argv[2] == "publish":
        loc = publish(fam)
        post_verify(fam, loc)
    else:
        post_verify(fam, local_md5s(fam))
