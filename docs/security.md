# Securing a deployment

Beacon is a read-mostly public service. The things worth protecting are the admin key, the API
listener, your broker and MeshMapper credentials, and the database, which holds decrypted
channel messages.

## The admin key

The `/api/v1/admin/*` endpoints are the only operator-authenticated part of the API. User accounts, when enabled, add signed-in `/api/v1/auth` and `/api/v1/me` routes. Generate the key
with `openssl rand -hex 32`, set it as `BEACON_API_KEY`, and send it only in the
`Authorization: Bearer` header over HTTPS, never in a URL or a request body. Keep it out of
source control and logs. The rules Beacon enforces (16 characters minimum, no whitespace,
environment wins over the file) are in [Configuration](configuration.md#admin-api-key).

If you do not need the admin endpoints, do not set a key. They answer `503` and nothing else
changes.

## The MeshMapper API key

Obtain a regional or grouped-region API key from your local MeshMapper admin and keep it
in `MESHMAPPER_API_KEY` in the backend environment. Never use the mobile App key, publish
the key through a `VITE_*` setting, or commit it. Beacon sends it only as `X-API-Key` to
the supported HTTPS MeshMapper API endpoints and refuses redirects. This is separate
from Beacon's admin authentication. See [MeshMapper API key](configuration.md#meshmapper-api-key).

## Keep the API listener private

beacon-server listens on `:8080` with no TLS. In the Docker deployments it is only reachable
from the compose network and from the host's loopback; Caddy is the only thing on a public
port. If you run it another way, bind `LISTEN_ADDR` to a private address and terminate HTTPS
at the proxy.

## Browser origins

Only the page's own host may open `/ws` unless other origins are listed under
`websocket.allowed_origins`. REST CORS allows any origin by default but only the read-only
methods (`GET`, `HEAD`, `OPTIONS`). An admin UI on another origin needs `cors.allowed_origins`
restricted to that UI, the write methods added, and the `Authorization` and `Content-Type`
headers allowed, or its preflight requests fail. A web app that signs users in from another origin
also needs `X-Beacon-CSRF` in `allowed_headers` and `allow_credentials: true`. CORS controls what browsers may do, not who
is authenticated.

## User accounts

Accounts are off by default; see [User accounts](accounts.md). When they are on:

- Passwords are stored only as argon2id hashes. Session tokens, mailed links and app codes are random
  and stored only as SHA-256 hashes. None of them, and no request body on `/auth` or `/me`, is
  logged.
- The session cookie is `HttpOnly`, `SameSite=Lax` and `Secure` (except for a localhost `public_url`).
  Sessions end on logout, password change or reset, disabling the user, and expiry.
- A request authenticated by the cookie that writes (`POST`, `PUT`, `PATCH`, `DELETE`) must send
  `X-Beacon-CSRF: 1`, and if it has an `Origin` header that must be the origin of
  `accounts.public_url` or one of `cors.allowed_origins` (never `*`). Otherwise it gets `403
  csrf_rejected`. Requests with a bearer token skip this check; only a cookie lets a foreign page act
  for the user.
- Sign-up, resend and reset never say whether an address is registered. Sign-in gives one failure for
  an unknown name and a wrong password. Failed sign-ins are throttled per account and per address.
- Set `server.trusted_proxies` behind a proxy, or the per-address limits count the proxy.
- The SMTP password belongs in `BEACON_SMTP_PASSWORD`, not in `config.yaml`.

## Rate limits and bans

REST is limited to 600 requests a minute per client by default, WebSocket upgrades to 10 a
minute, with 5 open sockets per client. Behind a proxy none of that works until
`server.trusted_proxies` is set; see
[Reverse proxy](reverse-proxy.md#rate-limits-and-connection-caps). For repeat offenders, the
fail2ban jails and block list in [`app_config/fail2ban/`](../app_config/fail2ban/README.md)
ban at the edge.

## What Beacon logs and returns

Query strings and WebSocket hello payloads are never logged. HTTP completion records carry
the validated client address, route, status and duration. `GET /api/v1/admin/config` returns
no credentials, broker addresses, channel material or database settings. The backup export,
if you enable it, contains everything the database holds, so keep archives private; see
[Backup and export](backup-export.md).

## Secrets in files

`.env` holds the database password, broker credentials, admin key, and MeshMapper API key. It is gitignored in
the deployment folders; keep it that way, and keep its permissions tight on the host.
`data/app/config.yaml` holds channel keys. Neither belongs in a public backup.
