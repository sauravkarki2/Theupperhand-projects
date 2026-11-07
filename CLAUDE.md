# Theupperhand-projects

## OpenSEO (SEO research tool)

`open-seo/` is OpenSEO, a self-hosted SEO tool backed by the DataForSEO API.
When the user asks for SEO work (keyword research, domain overview, backlinks,
SERP analysis, site audit), start it with:

```bash
bash openseo-cloud/start.sh
```

It serves `http://localhost:3001` with no sign-in. Details and the reason for
the DataForSEO forwarder are in `openseo-cloud/README.md`.

- The DataForSEO login lives only as a network secret on the cloud
  environment. Never write it into the repo, and never ask for it in chat.
- DataForSEO charges per request (about $0.05 per keyword search). Mention the
  cost before running many lookups.
- Do not commit `open-seo/.env.local`, `.logs/` or `.wrangler/` (git-ignored),
  or the forwarder change to `open-seo/src/server/lib/dataforseo/core.ts`
  (hidden from git by `start.sh`).
