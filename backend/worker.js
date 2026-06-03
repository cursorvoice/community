/**
 * Cursor Voice — community backend (Cloudflare Worker).
 *
 * Endpoints (all JSON, POST):
 *   /register  { idToken }            — the APP calls this on Google sign-in to
 *                                       mark the account "known". Stored in KV.
 *   /me        { idToken }            — the SITE calls this after sign-in to check
 *                                       whether the account is known. -> { known }
 *   /submit    { idToken, manifest, link }
 *                                     — the SITE calls this to publish. Requires a
 *                                       known account; opens a GitHub issue for review.
 *
 * Bindings (wrangler.toml):
 *   KV  KNOWN                         — known accounts (key "known:<email>")
 *   var REPO          = "cursorvoice/community"
 *   var GOOGLE_AUDS   = "<web-client-id>,<desktop-client-id>"   (allowed token audiences)
 *   var ALLOW_ORIGIN  = "https://community.cursorvoice.app"
 *   secret GITHUB_TOKEN                — repo-scoped token used to create issues
 */

export default {
  async fetch(req, env) {
    const origin = env.ALLOW_ORIGIN || "*";
    const cors = {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });

    const json = (obj, status = 200) =>
      new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", ...cors } });

    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "");

    if (req.method !== "POST") return json({ error: "POST only" }, 405);

    let body;
    try { body = await req.json(); } catch { return json({ error: "bad JSON" }, 400); }

    // Verify the Google ID token via Google's tokeninfo (validates signature + expiry).
    const claims = await verifyGoogle(body.idToken, env);
    if (!claims) return json({ error: "invalid or expired sign-in" }, 401);
    const email = (claims.email || "").toLowerCase();
    if (!email || claims.email_verified === "false") return json({ error: "email not verified" }, 401);

    if (path.endsWith("/register")) {
      await env.KNOWN.put("known:" + email, JSON.stringify({ name: claims.name || "", at: Date.now() }));
      return json({ ok: true });
    }

    if (path.endsWith("/me")) {
      const known = !!(await env.KNOWN.get("known:" + email));
      return json({ known, email, name: claims.name || "" });
    }

    if (path.endsWith("/submit")) {
      const known = !!(await env.KNOWN.get("known:" + email));
      if (!known) return json({ error: "account not connected to the app" }, 403);

      const m = body.manifest || {};
      if (!m.name || !m.description || !m.run || !m.run.template)
        return json({ error: "incomplete manifest" }, 400);

      const title = "[plugin] " + String(m.name).slice(0, 80);
      const issueBody =
        `**Plugin:** ${m.name}\n` +
        `**Submitted by:** ${claims.name || ""} <${email}> (verified, connected account)\n` +
        `**Link:** ${body.link || "—"}\n` +
        `**Type:** ${m.run.type}\n\n` +
        "Manifest:\n```json\n" + JSON.stringify(m, null, 2) + "\n```\n\n" +
        "_Submitted via community.cursorvoice.app_";

      const gh = await fetch(`https://api.github.com/repos/${env.REPO}/issues`, {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + env.GITHUB_TOKEN,
          "Accept": "application/vnd.github+json",
          "User-Agent": "cv-community-worker",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, body: issueBody, labels: ["plugin-submission"] }),
      });
      if (!gh.ok) {
        const t = await gh.text();
        return json({ error: "GitHub error " + gh.status + ": " + t.slice(0, 200) }, 502);
      }
      const issue = await gh.json();
      return json({ ok: true, url: issue.html_url });
    }

    return json({ error: "not found" }, 404);
  },
};

/** Validate a Google ID token. Returns claims, or null if invalid. */
async function verifyGoogle(idToken, env) {
  if (!idToken || typeof idToken !== "string") return null;
  const r = await fetch("https://oauth2.googleapis.com/tokeninfo?id_token=" + encodeURIComponent(idToken));
  if (!r.ok) return null;
  const c = await r.json();
  const auds = (env.GOOGLE_AUDS || "").split(",").map(s => s.trim()).filter(Boolean);
  if (auds.length && !auds.includes(c.aud)) return null;          // must be one of our clients
  if (c.iss && !/accounts\.google\.com$/.test(c.iss.replace(/^https?:\/\//, ""))) return null;
  if (c.exp && Date.now() / 1000 > Number(c.exp)) return null;    // expired
  return c;
}
