# Publish the RFP Dashboard to GitHub Pages (one-time setup)

Goal: a permanent public URL — `https://<your-username>.github.io/fresno-rfp-dashboard/` —
that updates itself every morning when the daily task refreshes the dashboard.

You do steps 1–4 once (they need your GitHub login, which I can't do for you).
After that, the daily task publishes automatically — no manual work.

---

## 1. Create the repository
1. Go to https://github.com/new (sign in / create a free account if needed).
2. Repository name: **fresno-rfp-dashboard**
3. Visibility: **Public** (required for free GitHub Pages).
4. Check **"Add a README file"** — this matters: it creates the `main` branch with a
   first commit, which the publisher needs.
5. Click **Create repository**.

## 2. Turn on GitHub Pages
1. In the new repo: **Settings → Pages** (left sidebar).
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: **main**, folder: **/ (root)**. Click **Save**.
4. Your site URL appears at the top of that page:
   `https://<your-username>.github.io/fresno-rfp-dashboard/`
   (It 404s until the first publish — that's expected.)

## 3. Create an access token (so the task can push)
1. Go to https://github.com/settings/personal-access-tokens/new (Fine-grained tokens).
2. **Token name:** `rfp-dashboard-publisher`
3. **Expiration:** 1 year (re-create when it expires).
4. **Repository access:** *Only select repositories* → pick **fresno-rfp-dashboard**.
5. **Permissions → Repository permissions → Contents:** set to **Read and write**.
   (Leave everything else as "No access".)
6. Click **Generate token** and **copy it** (starts with `github_pat_…`). You won't see it again.

## 4. Save your settings locally
1. In this folder (`Fresno Bid Opportunities`), copy **`.gh_secrets.example`** to a new
   file named **`.gh_secrets`**.
2. Open `.gh_secrets` and fill in:
   - `GH_TOKEN=` the token you copied
   - `GH_OWNER=` your GitHub username
   - `GH_REPO=fresno-rfp-dashboard`
3. Save. **Keep this file private** — it holds your token. Don't share or upload it.

## 5. Tell me "GitHub setup done"
I'll run a test publish to confirm it works and give you the live link. From then on,
the daily 7am task publishes the fresh dashboard automatically.

---

### How it works
- `publish_to_github.py` reads `sjv_rfp_dashboard.html`, commits it to your repo as
  `index.html` via the GitHub API, and GitHub Pages serves it publicly.
- It's wired into the daily `sjv-rfp-refresh` task as a final, **non-fatal** step — if the
  token is missing or GitHub is unreachable, the refresh still succeeds; only publishing is
  skipped that run.
- The published page is a **daily snapshot** (data is baked into the HTML), not live/real-time.

### Token expired or want to rotate it?
Repeat step 3, paste the new token into `.gh_secrets`. Nothing else changes.

### Manual publish (optional)
From this folder: `python3 publish_to_github.py`
