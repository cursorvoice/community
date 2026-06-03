#!/usr/bin/env python3
"""
Cursor Voice — submission review bot (Discord).

Repurposed from the deadline-reminder bot: same Discord application/token, new
behavior. It watches GitHub for new plugin submissions (issues labeled
`plugin-submission`), posts each one to a channel, and lets a reviewer approve or
deny with a ✅ / ❌ reaction:

  ✅  → adds the `approved` label to the issue, which triggers the repo's
        grade-submission Action to publish the plugin to the marketplace.
  ❌  → closes the issue and labels it `invalid`.

On startup it also renames itself and sets its avatar (no Developer Portal
needed). Fully self-contained: just env vars + `python review_bot.py`.

Env:
  DISCORD_TOKEN   the bot token (same one the old bot used)
  GITHUB_TOKEN    a token with Issues: read/write on the repo
  CHANNEL_ID      numeric ID of the channel to post submissions in
  GITHUB_REPO     default "cursorvoice/community"
  BOT_NAME        default "Cursor Voice Submissions"
  LOGO_URL        default the Cursor Voice orb icon
  APPROVER_IDS    optional comma-separated Discord user IDs allowed to decide
                  (empty = anyone in the channel)
"""
import os, json, asyncio, aiohttp, discord

TOKEN       = os.environ["DISCORD_TOKEN"]
GH_TOKEN    = os.environ["GITHUB_TOKEN"]
CHANNEL_ID  = int(os.environ["CHANNEL_ID"])
REPO        = os.environ.get("GITHUB_REPO", "cursorvoice/community")
BOT_NAME    = os.environ.get("BOT_NAME", "Cursor Voice Submissions")
LOGO_URL    = os.environ.get("LOGO_URL", "https://cursorvoice.app/favicon-180.png")
APPROVERS   = {int(x) for x in os.environ.get("APPROVER_IDS", "").replace(" ", "").split(",") if x}
STATE_FILE  = os.path.join(os.path.dirname(__file__), "posted.json")
GH_API      = "https://api.github.com"
ACCENT      = 0x8C4CF2

intents = discord.Intents.default()          # includes guild reactions; no privileged intents needed
bot = discord.Client(intents=intents)

# issue_number -> message_id, persisted so restarts don't repost
posted = {}
if os.path.exists(STATE_FILE):
    try: posted = {int(k): v for k, v in json.load(open(STATE_FILE)).items()}
    except Exception: posted = {}

def save_state():
    json.dump(posted, open(STATE_FILE, "w"))

def gh_headers():
    return {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json",
            "User-Agent": "cv-review-bot"}

async def gh(session, method, path, **kw):
    async with session.request(method, f"{GH_API}{path}", headers=gh_headers(), **kw) as r:
        return r.status, (await r.json() if r.content_type == "application/json" else await r.text())

def manifest_from(body: str):
    if not body or "```json" not in body: return None
    try: return json.loads(body.split("```json", 1)[1].split("```", 1)[0])
    except Exception: return None

async def post_new_submissions(session):
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None: return
    status, issues = await gh(session, "GET",
        f"/repos/{REPO}/issues?labels=plugin-submission&state=open&per_page=30")
    if status != 200 or not isinstance(issues, list): return
    for issue in reversed(issues):
        num = issue["number"]
        if num in posted or "pull_request" in issue:  # skip already-posted + PRs
            continue
        man = manifest_from(issue.get("body", "")) or {}
        run = man.get("run", {})
        embed = discord.Embed(
            title=f"🧩 {man.get('name', issue['title'])}",
            description=man.get("description", "")[:300] or "(no description)",
            color=ACCENT, url=issue["html_url"])
        embed.add_field(name="Type", value=f"`{run.get('type','?')}`", inline=True)
        embed.add_field(name="By", value=issue["user"]["login"], inline=True)
        if run.get("template"):
            embed.add_field(name="Action", value=f"```{run['template'][:300]}```", inline=False)
        embed.set_footer(text=f"Issue #{num} · react ✅ to publish · ❌ to deny")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        posted[num] = msg.id
        save_state()

async def poll_loop():
    await bot.wait_until_ready()
    async with aiohttp.ClientSession() as session:
        while not bot.is_closed():
            try: await post_new_submissions(session)
            except Exception as e: print("poll error:", e)
            await asyncio.sleep(60)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    # Rename + set avatar to the Cursor Voice brand (best-effort; Discord limits
    # username changes, so ignore failures).
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(LOGO_URL) as r:
                avatar = await r.read() if r.status == 200 else None
        await bot.user.edit(username=BOT_NAME, **({"avatar": avatar} if avatar else {}))
        print(f"Identity set: {BOT_NAME}")
    except Exception as e:
        print("identity update skipped:", e)
    bot.loop.create_task(poll_loop())

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:                 # ignore our own ✅/❌
        return
    if APPROVERS and payload.user_id not in APPROVERS:  # optional allow-list
        return
    num = next((n for n, mid in posted.items() if mid == payload.message_id), None)
    if num is None:
        return
    emoji = str(payload.emoji)
    channel = bot.get_channel(payload.channel_id)
    async with aiohttp.ClientSession() as session:
        if emoji == "✅":
            await gh(session, "POST", f"/repos/{REPO}/issues/{num}/labels",
                     json={"labels": ["approved"]})
            note = "✅ Approved — publishing to the marketplace."
        elif emoji == "❌":
            await gh(session, "POST", f"/repos/{REPO}/issues/{num}/labels",
                     json={"labels": ["invalid"]})
            await gh(session, "PATCH", f"/repos/{REPO}/issues/{num}", json={"state": "closed"})
            note = "❌ Denied — submission closed."
        else:
            return
    try:
        msg = await channel.fetch_message(payload.message_id)
        await msg.reply(note)
    except Exception:
        pass
    # Stop tracking once decided.
    posted.pop(num, None); save_state()

if __name__ == "__main__":
    bot.run(TOKEN)
