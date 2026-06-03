# Submission review bot

Repurposes your existing Discord bot (e.g. the old deadline-reminder bot) into the
**plugin submission reviewer**. Same bot/token — just swap in this code.

When someone submits a plugin, the bot posts it to your channel. React:
- ✅ → labels the GitHub issue `approved` → the repo's Action publishes it to the marketplace.
- ❌ → closes the issue and labels it `invalid`.

It also renames itself and sets the Cursor Voice avatar on startup — no Developer
Portal needed.

## Manage the marketplace from Discord (slash commands)
- **`/plugin_list`** — show every published plugin.
- **`/plugin_add`** — publish a plugin directly: pick a name, description, kind
  (URL / shell / AppleScript), the action template (with `{{arg}}` placeholders),
  and optional comma-separated arg names. Commits to the registry → live in ~1 min.
- **`/plugin_delete`** — remove a plugin by name (deletes its file + registry entry).

> Slash commands need the bot invited with the **`applications.commands`** scope.
> If you only invited it with `bot`, re-open the OAuth2 → URL Generator with **both**
> `bot` **and** `applications.commands` checked and authorize again (no need to kick it).
> Set `APPROVER_IDS` to restrict who can add/delete.

## Setup
1. Put this `bot/` folder wherever the bot runs (same host as before is fine).
2. Install deps:
   ```sh
   pip install -r requirements.txt
   ```
3. Set environment variables:
   | var | what |
   |-----|------|
   | `DISCORD_TOKEN` | the **same token** the old bot used |
   | `GITHUB_TOKEN`  | a token with **Issues: read/write** on `cursorvoice/community` |
   | `CHANNEL_ID`    | the channel to post submissions in (right-click channel → Copy ID; needs Developer Mode) |
   | `GITHUB_REPO`   | optional, default `cursorvoice/community` |
   | `BOT_NAME`      | optional, default `Cursor Voice Submissions` |
   | `LOGO_URL`      | optional, default the Cursor Voice icon |
   | `APPROVER_IDS`  | optional, comma-separated Discord user IDs allowed to decide (empty = anyone) |
4. Run:
   ```sh
   python review_bot.py
   ```

## Notes
- **No privileged intents** required (it only posts embeds and reads reactions).
- Make sure the bot's role can **Send Messages**, **Embed Links**, **Add Reactions**,
  and **Read Message History** in that channel.
- It polls GitHub every 60s and remembers what it already posted in `posted.json`,
  so restarts won't double-post.
- Discord limits username changes (~2/hour); if the rename doesn't take immediately,
  it'll apply on a later restart — the avatar/behavior still work.
- The bot needs the issues to be labeled `plugin-submission` (the website + issue
  form already do this).
