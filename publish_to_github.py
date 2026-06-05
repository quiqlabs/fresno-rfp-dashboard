#!/usr/bin/env python3
"""
Publish sjv_rfp_dashboard.html to a GitHub repo as index.html via the GitHub
Git Data API, so GitHub Pages serves the latest dashboard at a public URL.

Reads config from .gh_secrets (KEY=VALUE lines, kept local & private):
    GH_TOKEN=github_pat_xxx          # fine-grained PAT, Contents: Read & write
    GH_OWNER=your-github-username
    GH_REPO=fresno-rfp-dashboard
    GH_BRANCH=main                   # optional, default main
    GH_PATH=index.html               # optional, default index.html

Non-fatal by design: if .gh_secrets is missing it prints a notice and exits 0,
so the daily scheduled task never breaks before setup is finished.
"""
import base64, json, os, sys, urllib.request, urllib.error

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "sjv_rfp_dashboard.html")
SECRETS = os.path.join(DIR, ".gh_secrets")
API = "https://api.github.com"


def log(msg):
    print(f"[publish_to_github] {msg}", flush=True)


def load_secrets():
    cfg = {}
    with open(SECRETS) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def gh(method, path, token, body=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "quiq-rfp-publisher")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    if not os.path.exists(SECRETS):
        log(f"no .gh_secrets found at {SECRETS} — skipping publish (setup not finished). OK.")
        return 0
    if not os.path.exists(SRC):
        log(f"ERROR: source not found: {SRC}")
        return 1

    cfg = load_secrets()
    missing = [k for k in ("GH_TOKEN", "GH_OWNER", "GH_REPO") if not cfg.get(k)]
    if missing:
        log(f"ERROR: .gh_secrets missing keys: {', '.join(missing)}")
        return 1

    token = cfg["GH_TOKEN"]
    owner, repo = cfg["GH_OWNER"], cfg["GH_REPO"]
    branch = cfg.get("GH_BRANCH", "main")
    path = cfg.get("GH_PATH", "index.html")
    base = f"/repos/{owner}/{repo}"

    content_b64 = base64.b64encode(open(SRC, "rb").read()).decode()
    msg = "Auto-publish RFP dashboard refresh"

    # 1. current branch head (parent commit)
    st, ref = gh("GET", f"{base}/git/ref/heads/{branch}", token)
    if st == 404:
        log(f"ERROR: branch '{branch}' not found. Create the repo with an initial "
            f"commit (add a README) and enable Pages first. See PUBLISH_SETUP.md.")
        return 1
    if st != 200:
        log(f"ERROR fetching ref ({st}): {ref.get('message')}")
        return 1
    parent = ref["object"]["sha"]

    # 2. base tree
    st, commit = gh("GET", f"{base}/git/commits/{parent}", token)
    base_tree = commit["tree"]["sha"]

    # 3. blob
    st, blob = gh("POST", f"{base}/git/blobs", token,
                  {"content": content_b64, "encoding": "base64"})
    if st not in (200, 201):
        log(f"ERROR creating blob ({st}): {blob.get('message')}")
        return 1

    # 4. tree
    st, tree = gh("POST", f"{base}/git/trees", token, {
        "base_tree": base_tree,
        "tree": [{"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]}],
    })
    if st not in (200, 201):
        log(f"ERROR creating tree ({st}): {tree.get('message')}")
        return 1

    # 5. commit
    st, newc = gh("POST", f"{base}/git/commits", token,
                  {"message": msg, "tree": tree["sha"], "parents": [parent]})
    if st not in (200, 201):
        log(f"ERROR creating commit ({st}): {newc.get('message')}")
        return 1

    # 6. move branch ref
    st, upd = gh("PATCH", f"{base}/git/refs/heads/{branch}", token,
                 {"sha": newc["sha"], "force": False})
    if st not in (200, 201):
        log(f"ERROR updating ref ({st}): {upd.get('message')}")
        return 1

    log(f"published {os.path.getsize(SRC)} bytes -> {owner}/{repo}@{branch}:{path} "
        f"(commit {newc['sha'][:7]})")
    log(f"live shortly at: https://{owner}.github.io/{repo}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
