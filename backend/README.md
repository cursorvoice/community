# Community backend — deploy runbook

A tiny Cloudflare Worker (free tier) that powers login + verified submissions on
[community.cursorvoice.app](https://community.cursorvoice.app). It:

1. Verifies a Google ID token (the **same Google account** used in the app).
2. Checks the account is **known** (the app registered it — see step 6).
3. Creates a GitHub **issue** with the submitted plugin manifest for review.

No plugin is ever auto-merged — submissions land as issues you approve.

---

## What you need (all free)
- A **Cloudflare account** (you already have one for DNS).
- A **Google "Web application" OAuth client** in the *same* Google Cloud project as the app's Desktop client.
- A **GitHub token** that can open issues on `cursorvoice/community`.

## 1 — Install Wrangler
```sh
npm install -g wrangler
wrangler login          # opens the browser; approve
```

## 2 — Create the KV namespace
```sh
cd backend
wrangler kv namespace create KNOWN
```
Copy the printed `id` into `wrangler.toml` under `[[kv_namespaces]]`.

## 3 — Make the Google Web OAuth client
Google Cloud Console → *APIs & Services → Credentials → Create credentials →
OAuth client ID → Web application*:
- **Authorized JavaScript origins:** `https://community.cursorvoice.app`
- Save, copy the **Client ID** (`…apps.googleusercontent.com`).

Put both client IDs in `wrangler.toml` → `GOOGLE_AUDS` (web client id **and** the
app's existing Desktop client id, comma-separated).

## 4 — Add the GitHub token (secret)
Create a fine-grained token (Settings → Developer settings → Fine-grained tokens)
scoped to **only** `cursorvoice/community` with **Issues: Read and write**. Then:
```sh
wrangler secret put GITHUB_TOKEN     # paste the token when prompted
```

## 5 — Deploy
```sh
wrangler deploy
```
Copy the deployed URL (e.g. `https://cv-community.<you>.workers.dev`).

## 6 — Point the site at it
Edit `config.js` in the repo root:
```js
window.CV = {
  API_BASE: "https://cv-community.<you>.workers.dev",
  GOOGLE_CLIENT_ID: "WEB_CLIENT_ID.apps.googleusercontent.com",
  REPO: "cursorvoice/community"
};
```
Commit & push — the site switches from the GitHub-issue fallback to real login.

## 7 — Connect the app (next app release)
The app posts the user's Google ID token to `POST {API_BASE}/register` on sign-in,
which marks that email "known" so the site recognizes it. (Shipped in the app
update that adds the `cursorvoice://install` deep link.)

---

### Endpoints
| route | who calls it | does |
|-------|--------------|------|
| `POST /register` | the app | mark this Google account known |
| `POST /me` | the site | is this account known? |
| `POST /submit` | the site | verified + known → open a plugin issue |

### Notes
- Until `config.js` is filled in, the site stays fully working: login is hidden and
  submissions fall back to a pre-filled GitHub issue (no backend needed).
- Free-tier limits (100k Worker requests/day, generous KV) are far beyond what a
  plugin marketplace needs.
