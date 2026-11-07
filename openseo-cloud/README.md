# OpenSEO in Claude Code cloud sessions

`open-seo/` is [OpenSEO](https://openseo.so), an open-source SEO tool (keyword
research, domain overview, backlinks, rank tracking, site audits) that uses the
DataForSEO API.

## Run it in a cloud session

```bash
bash openseo-cloud/start.sh
```

Then open `http://localhost:3001`. No sign-in (`AUTH_MODE=local_noauth`).

Requirements, set on the `theupperhand-projects` cloud environment:

- `api.dataforseo.com` reachable (allowed host or network secret).
- The DataForSEO API login saved as a network secret for `api.dataforseo.com`
  (Basic auth: API login + API password from
  https://app.dataforseo.com/api-access). It is never stored in the repo.

Why the forwarder: the app runs inside Cloudflare's local runtime (workerd),
which can't use the session's HTTPS proxy. `start.sh` points the app's
DataForSEO calls at `dfs-forwarder.mjs` on localhost, which relays them through
the proxy. That one-line change in `open-seo/src/server/lib/dataforseo/core.ts`
is hidden from git, so it is never committed.

## Run it on your own computer

No forwarder needed:

```bash
cd open-seo
corepack enable
pnpm install --frozen-lockfile
pnpm run db:migrate:local
printf 'AUTH_MODE=local_noauth\nDATAFORSEO_API_KEY=%s\n' "$(printf '%s' 'LOGIN:PASSWORD' | base64)" > .env.local
pnpm run dev
```

## Costs

DataForSEO is pay-as-you-go; one keyword research search costs about $0.05.
