"""Zenodo new-version DRAFT preparation for Legacy CO.RA.PAN. NEVER publishes.

Usage (python -I zenodo_draft.py <cmd> <family>):
  inspect <fc|sw>   read-only: versions, drafts, metadata of latest published -> reports/zenodo_<family>_inspect.json
  draft   <fc|sw>   reuse existing unpublished draft of the concept, else actions/newversion on latest published
  files   <fc|sw>   sync draft files to local upload dir (delete inherited/mismatching, upload missing; resumable)
  meta    <fc|sw>   PUT metadata from reports/zenodo_<family>_metadata_to_apply.json
  verify  <fc|sw>   compare draft files/metadata with local; check published versions unchanged
Token: env ZENODO_ACCESS_TOKEN, else DPAPI file %LOCALAPPDATA%/corapan_zenodo/token.dpapi. Never printed or written.
"""
import ctypes, ctypes.wintypes as wt, hashlib, json, os, sys, time
import requests

API = "https://zenodo.org/api"
STAGE = r"C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging"
REP = os.path.join(STAGE, "local_only", "reports")
FAM = {
    "fc": dict(concept="15360942", latest="18782190", dir=os.path.join(STAGE, "zenodo_upload_ready", "full-corpus")),
    "sw": dict(concept="17834023", latest="19202684", dir=os.path.join(STAGE, "zenodo_upload_ready", "software")),
}


def _token():
    t = os.environ.get("ZENODO_ACCESS_TOKEN")
    if t:
        return t.strip()
    p = os.path.join(os.environ["LOCALAPPDATA"], "corapan_zenodo", "token.dpapi")
    blob = bytes.fromhex(open(p).read().strip())

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    buf = ctypes.create_string_buffer(blob, len(blob))
    inb = BLOB(len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(out)):
        raise SystemExit("token file could not be decrypted")
    data = ctypes.string_at(out.pbData, out.cbData)
    ctypes.windll.kernel32.LocalFree(out.pbData)
    return data.decode("utf-16-le").strip()


S = requests.Session()
S.headers["Authorization"] = "Bearer " + _token()


def req(method, url, retries=5, **kw):
    assert "/actions/publish" not in url, "publishing is forbidden in this run"
    for i in range(retries):
        try:
            r = S.request(method, url, timeout=kw.pop("timeout", 120), **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if i == retries - 1:
                raise
            print(f"  retry {i + 1} after error: {type(e).__name__}: {str(e)[:120]}", flush=True)
            time.sleep(min(60, 5 * 2 ** i))


def ok(r, *codes):
    if r.status_code not in codes:
        raise SystemExit(f"{r.request.method} {r.url} -> {r.status_code}: {r.text[:600]}")
    return r.json() if r.content else None


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def state_path(fam):
    return os.path.join(REP, f"zenodo_{fam}_state.json")


def load_state(fam):
    p = state_path(fam)
    return json.load(open(p)) if os.path.exists(p) else {}


def save_state(fam, st):
    json.dump(st, open(state_path(fam), "w"), indent=1)


def versions(fam):
    c = FAM[fam]["concept"]
    out = []
    for status in ("published", "draft"):
        r = ok(req("GET", f"{API}/deposit/depositions", params={"q": f"conceptrecid:{c}", "all_versions": "true", "size": 100, "status": status}), 200)
        out += r
    seen = {}
    for d in out:
        seen[d["id"]] = d
    return list(seen.values())


def inspect(fam):
    vs = versions(fam)
    summ = [dict(id=d["id"], state=d.get("state"), submitted=d.get("submitted"), doi=d.get("doi"), version=d["metadata"].get("version"),
                 publication_date=d["metadata"].get("publication_date"), modified=d.get("modified"), files=len(d.get("files", [])))
            for d in sorted(vs, key=lambda d: d["id"])]
    latest = ok(req("GET", f"{API}/deposit/depositions/{FAM[fam]['latest']}"), 200)
    rep = {"versions": summ, "latest_published_id": FAM[fam]["latest"], "latest_metadata": latest["metadata"],
           "latest_files": [dict(filename=f["filename"], filesize=f["filesize"], checksum=f["checksum"]) for f in latest.get("files", [])],
           "latest_modified": latest.get("modified")}
    json.dump(rep, open(os.path.join(REP, f"zenodo_{fam}_inspect.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))
    print("latest files:", len(rep["latest_files"]), "access:", latest["metadata"].get("access_right"))


def draft(fam):
    vs = versions(fam)
    drafts = [d for d in vs if not d.get("submitted")]
    st = load_state(fam)
    if drafts:
        d = sorted(drafts, key=lambda d: d["id"])[-1]
        print("reusing existing unpublished draft", d["id"])
    else:
        r = ok(req("POST", f"{API}/deposit/depositions/{FAM[fam]['latest']}/actions/newversion"), 201)
        url = r["links"]["latest_draft"]
        d = ok(req("GET", url), 200)
        print("created new-version draft", d["id"])
    st.update(draft_id=d["id"], bucket=d["links"]["bucket"], html=d["links"].get("html"), latest_draft_html=d["links"].get("latest_draft_html"))
    save_state(fam, st)
    print(json.dumps({k: st[k] for k in ("draft_id", "html", "latest_draft_html")}, indent=1))


def files(fam):
    st = load_state(fam)
    did = st["draft_id"]
    d = ok(req("GET", f"{API}/deposit/depositions/{did}"), 200)
    assert not d.get("submitted"), "target is published - abort"
    bucket = d["links"]["bucket"]
    local_dir = FAM[fam]["dir"]
    local = {f: dict(size=os.path.getsize(os.path.join(local_dir, f)), md5=None) for f in sorted(os.listdir(local_dir))}
    cache = st.setdefault("md5", {})
    for f in local:
        key = f"{f}:{local[f]['size']}:{os.path.getmtime(os.path.join(local_dir, f))}"
        if key not in cache:
            cache[key] = md5(os.path.join(local_dir, f))
        local[f]["md5"] = cache[key]
    save_state(fam, st)
    remote = ok(req("GET", f"{API}/deposit/depositions/{did}/files"), 200)
    for rf in remote:
        name, chk = rf["filename"], rf["checksum"].replace("md5:", "")
        if name in local and chk == local[name]["md5"] and rf["filesize"] == local[name]["size"]:
            local[name]["done"] = True
            continue
        print("delete draft file", name, flush=True)
        ok(req("DELETE", f"{API}/deposit/depositions/{did}/files/{rf['id']}"), 204)
    for name, info in local.items():
        if info.get("done"):
            print("already present", name)
            continue
        for attempt in range(4):
            print(f"upload {name} ({info['size']:,} B) attempt {attempt + 1}", flush=True)
            try:
                with open(os.path.join(local_dir, name), "rb") as fh:
                    r = S.put(f"{bucket}/{name}", data=fh, timeout=3600, headers={"Content-Type": "application/octet-stream"})
                if r.status_code in (200, 201):
                    j = r.json()
                    if j.get("checksum", "").replace("md5:", "") == info["md5"] and int(j.get("size", -1)) == info["size"]:
                        print("  ok md5", info["md5"], flush=True)
                        break
                    print("  checksum/size mismatch -> delete and retry", flush=True)
                else:
                    print("  HTTP", r.status_code, r.text[:200], flush=True)
            except (requests.ConnectionError, requests.Timeout) as e:
                print("  network error:", type(e).__name__, flush=True)
            # clean up partial/mismatching object before retry
            for rf in ok(req("GET", f"{API}/deposit/depositions/{did}/files"), 200):
                if rf["filename"] == name:
                    req("DELETE", f"{API}/deposit/depositions/{did}/files/{rf['id']}")
            time.sleep(10 * (attempt + 1))
        else:
            raise SystemExit(f"upload failed: {name}")


def meta(fam):
    st = load_state(fam)
    did = st["draft_id"]
    md = json.load(open(os.path.join(REP, f"zenodo_{fam}_metadata_to_apply.json"), encoding="utf-8"))
    r = ok(req("PUT", f"{API}/deposit/depositions/{did}", json={"metadata": md}), 200)
    print("metadata updated; version:", r["metadata"].get("version"), "access:", r["metadata"].get("access_right"))


def verify(fam):
    st = load_state(fam)
    did = st["draft_id"]
    d = ok(req("GET", f"{API}/deposit/depositions/{did}"), 200)
    remote = {f["filename"]: f for f in ok(req("GET", f"{API}/deposit/depositions/{did}/files"), 200)}
    local_dir = FAM[fam]["dir"]
    res = {"draft_id": did, "submitted": d.get("submitted"), "state": d.get("state"), "html": d["links"].get("html"),
           "access_right": d["metadata"].get("access_right"), "version": d["metadata"].get("version"),
           "license": d["metadata"].get("license"), "related_identifiers": d["metadata"].get("related_identifiers"),
           "files_local": len(os.listdir(local_dir)), "files_remote": len(remote), "problems": []}
    for f in sorted(os.listdir(local_dir)):
        p = os.path.join(local_dir, f)
        rf = remote.get(f)
        if not rf:
            res["problems"].append(f"missing remote: {f}"); continue
        if rf["filesize"] != os.path.getsize(p):
            res["problems"].append(f"size mismatch: {f}")
        if rf["checksum"].replace("md5:", "") != md5(p):
            res["problems"].append(f"md5 mismatch: {f}")
    for f in remote:
        if f not in os.listdir(local_dir):
            res["problems"].append(f"extra remote: {f}")
    insp = json.load(open(os.path.join(REP, f"zenodo_{fam}_inspect.json")))
    lp = ok(req("GET", f"{API}/deposit/depositions/{FAM[fam]['latest']}"), 200)
    res["previous_version_unchanged"] = (lp.get("modified") == insp["latest_modified"] and
                                         [f["checksum"] for f in lp.get("files", [])] == [f["checksum"] for f in insp["latest_files"]])
    json.dump(res, open(os.path.join(REP, f"zenodo_{fam}_verify.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "related_identifiers"}, indent=1))


if __name__ == "__main__":
    {"inspect": inspect, "draft": draft, "files": files, "meta": meta, "verify": verify}[sys.argv[1]](sys.argv[2])
