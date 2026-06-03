// Cursor Voice community site config.
// Fill these in AFTER deploying the Cloudflare Worker (see backend/README.md).
// While they're blank, the site stays fully functional: login is hidden and
// submissions fall back to the pre-filled GitHub-issue flow.
window.CV = {
  // Cloudflare Worker base URL, e.g. "https://cv-community.<you>.workers.dev"
  API_BASE: "",
  // Google "Web application" OAuth client ID (…apps.googleusercontent.com).
  // Must be the SAME Google project as the app so accounts match.
  GOOGLE_CLIENT_ID: "",
  REPO: "cursorvoice/community"
};
