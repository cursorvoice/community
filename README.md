# Cursor Voice — Community Plugins

Extend [Cursor Voice](https://cursorvoice.app) with your own voice commands.
Browse them at **https://community.cursorvoice.app**.

A plugin is a small JSON manifest. Cursor Voice loads every `.json` in
`~/Library/Application Support/CursorVoice/plugins/` and turns each into a tool
the assistant can call (exposed as `plugin_<name>`).

## Install a plugin
1. Download its `.json` from the [`plugins/`](plugins) folder.
2. Put it in `~/Library/Application Support/CursorVoice/plugins/`.
3. Re-summon the orb. Say what the plugin does.

## Manifest format
```json
{
  "name": "search wikipedia",
  "description": "Open a Wikipedia search for a topic in the browser.",
  "parameters": {
    "type": "object",
    "properties": { "topic": { "type": "string" } },
    "required": ["topic"]
  },
  "run": {
    "type": "open_url",
    "template": "https://en.wikipedia.org/w/index.php?search={{topic}}"
  }
}
```

`run.type` is one of:

| type | does | arg escaping |
|------|------|--------------|
| `open_url` | opens a URL | URL-encoded |
| `shell` | runs a zsh command | shell-quoted; subject to the destructive-command guard + Dry-run |
| `applescript` | runs AppleScript | quote/backslash-escaped |

`{{argument}}` placeholders are replaced with the values the model supplies
(named to match your `parameters.properties`).

## Submit your plugin

**Easiest — from the site:** open the **[Submit](https://community.cursorvoice.app/submit.html)**
page. It builds the manifest as you type. Sign in with the same Google account you
use in the app and publish it for review in one click. (You can also
[open a submission issue directly](https://github.com/cursorvoice/community/issues/new?template=plugin-submission.yml).)

The site's login + verified submissions are powered by a small free Cloudflare
Worker — see [`backend/`](backend) for the deploy runbook. Until it's configured,
the Submit page falls back to the pre-filled GitHub-issue flow.

### Automated review

Submissions are graded automatically by a GitHub Action
([`.github/workflows/grade-submission.yml`](.github/workflows/grade-submission.yml)):
it validates the manifest, runs a safety scan, and posts a grade on the issue.

- **`open_url`** plugins that pass are **published automatically** (added to
  `plugins/` + `registry.json`, issue closed) — live on the site within a minute.
- **`shell` / `applescript`** plugins are graded and labeled **`needs-review`**:
  they run code on users' Macs, so a maintainer publishes them by adding the
  **`approved`** label (which re-runs the workflow and publishes).
- Invalid or duplicate submissions are labeled **`invalid`** with the reason.

> One-time setup: Organization → Settings → Actions → General → **Workflow
> permissions → Read and write**, so the Action can comment and commit.

**Prefer a pull request?**
1. Fork this repo.
2. Add your manifest to `plugins/your-plugin.json`.
3. Add an entry to `registry.json`:
   ```json
   { "name": "...", "file": "plugins/your-plugin.json", "type": "open_url", "description": "...", "author": "your-handle" }
   ```
4. Open a pull request. Once merged, it appears on the site.

## ⚠️ Safety
Plugins run with **your** permissions. Only install manifests you trust, and
read the `run` template first — a `shell` plugin can run arbitrary commands.
Cursor Voice's destructive-command guard and **Dry-run** mode still apply.

MIT licensed. Not affiliated with or endorsed by OpenAI or Apple.
