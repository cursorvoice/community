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
