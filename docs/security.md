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

- Passwords are converted to Unicode NFC and stored only as argon2id hashes. A password is 12 or
  more characters (counted after the conversion) and at most 128 bytes. The rule that refuses a
  password containing the first part of the email address is skipped when that part is shorter than
  3 characters; this is deliberate, since a name such as `al` would refuse a large share of ordinary
  passwords.
- At most 4 password hashes or checks run at once, each holding about 19 MiB. A request that waits
  more than 5 seconds for a turn answers `503 service_unavailable` with `Retry-After: 5`, so a flood
  of sign-in attempts cannot exhaust the memory of the server; it only makes some of them wait or
  fail. The 503 is not a wrong password and is not counted by the throttle.
- Session tokens, mailed links and app codes are random
  and stored only as SHA-256 hashes. None of them, and no request body on `/auth` or `/me`, is
  logged.
- The session cookie is `HttpOnly`, `SameSite=Lax` and `Secure` (except for a localhost `public_url`).
  Sessions end on logout, a password change (every other session; the one that made it stays), a
  password reset (every session), disabling the user, and expiry.
- A request authenticated by the cookie that writes (`POST`, `PUT`, `PATCH`, `DELETE`) must send
  `X-Beacon-CSRF: 1`, and if it has an `Origin` header that must be the origin of
  `accounts.public_url` or one of `cors.allowed_origins` (never `*`). Otherwise it gets `403
  csrf_rejected`. Requests with a bearer token skip this check; only a cookie lets a foreign page act
  for the user.
- Mailed links carry their token in the URL fragment (`/?view=reset#token=...`). A browser does not
  send the fragment to the server, so the token stays out of proxy and access logs, and the web app
  removes it from the address bar as soon as it has read it.
- Sign-up, resend and reset never say whether an address is registered. Sign-in gives one failure for
  an unknown name and a wrong password. Failed sign-ins are throttled per account and per address.
- Set `server.trusted_proxies` behind a proxy, or the per-address limits count the proxy.
- Every password check, reset, password change, email change, delete and app code exchange runs
  under a per-user lock, so a sign-in racing a reset cannot leave a session behind. A reset link is
  bound to the address it was mailed to. Beacon mails the account address when the password changes
  and the old address when the email changes.
- When a session cannot be looked up, signed-in routes answer `503` rather than `401`, so a client
  does not discard a good token.
- The SMTP password belongs in `BEACON_SMTP_PASSWORD`, not in `config.yaml`.

## Guest passwords

[Requested telemetry](telemetry-requests.md) lets a user give Beacon a guest password for a
repeater, which an observer then uses to log in.

- **At rest.** Passwords are encrypted with AES-256-GCM under `BEACON_SECRET_KEY` before they are
  stored. Each row is bound to its request id and repeater key, so a copied row does not open for
  another request. No route, log line, error, metric or cache holds a password; the API says only
  whether one is set. Whoever has the database and the key has the passwords, so keep the key out of
  the database backup and the repo. Losing or changing the key makes the stored passwords
  unreadable (see [BEACON_SECRET_KEY](configuration.md#beacon_secret_key)).
- **To an observer.** Beacon does not send the password itself. It sends an envelope: the password
  sealed to the public key of the one observer that asked, with a fresh key and tag on every owners
  answer. The owners route has no login, so anyone can ask for an answer in an observer's name, but
  only the holder of that observer's private key can open the envelope. The route is on the
  observers' own `https` link, so keep the proxy on `https`.
- **Who can receive one.** By default (`polling.request_observers: all`) any observer that Beacon
  has heard the repeater through directly can be handed that repeater's guest password, sealed to
  that observer's key. Beacon also requires that the observer's claim accepts requests, that it has
  a free seat, that it has no admin stop for that repeater and is not blocked. The evidence that an
  observer hears the repeater directly comes from packets the observer uploads itself, so it is
  not proof: anyone who runs an observer could present evidence and be handed a password. If you
  want to choose who receives passwords, set `polling.request_observers: approved` and approve
  observers with `PUT /api/v1/admin/polling/observers/{publicKey}`. The body is
  `{"approved": true, "blocked": false, "note": "..."}` (`note` up to 200 characters; all three
  fields are replaced each time):

  ```bash
  curl -X PUT -H "Authorization: Bearer $BEACON_API_KEY" -H "Content-Type: application/json" \
    -d '{"approved":true,"blocked":false,"note":"north ridge, run by Sam"}' \
    https://beacon.example.com/api/v1/admin/polling/observers/<observer public key>
  ```

  In `approved` mode only approved observers receive a password, and withdrawing approval stops it
  going out at the next answer. Advert evidence is required in both modes.
- **Guest only, never admin.** A password given to Beacon is shared with a volunteer's observer, so
  it must be a guest password. Beacon cannot tell an admin password from a guest one when it is
  entered, and says so on the form. When a repeater answers a login with admin access, the observer
  reports `admin_stop`; Beacon deletes the password that observer was given (a newer password for the same repeater stays), marks the request `admin_stopped`, records that
  observer as stopped for that repeater, and, if the login had no password, blocks passwordless
  requests for the repeater until you lift it. An admin password is never stored after that and never
  forwarded again.
- **Who is believed.** A state report for a requested repeater counts only from the observer that
  holds that assignment, and `login_failed` only from its poller.

## Alerts and push

- Alert text holds only a radio's name, a figure and fixed words. Radio names come from adverts and
  are untrusted, so Beacon removes control and formatting characters and line breaks, collapses
  whitespace and cuts the name to 40 characters before it goes into a mail subject, a mail body or a
  push notice. A push notice carries the facts, not text, and the app writes the sentence.
- A push device handle and its payload key are possession secrets. A handle belongs to one account:
  registering it removes it from every other session and user. No route returns either and neither
  is ever logged.
- `BEACON_PUSH_SECRET` lets anyone who holds it send push notifications as this server. Keep it in
  the environment, out of the repo and backups. If it leaks, register the server again for a new one.
  Notification contents are encrypted per device, so the push server, Apple
  (APNs, for iPhones) and Google (FCM, for Android) cannot read them. iPhone notices never pass
  through Google.

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

`.env` holds the database password, broker credentials, admin key, MeshMapper API key, and, when those
features are on, `BEACON_SECRET_KEY`, `BEACON_PUSH_SECRET` and `BEACON_SMTP_PASSWORD`. It is gitignored in
the deployment folders; keep it that way, and keep its permissions tight on the host.
`data/app/config.yaml` holds channel keys. Neither belongs in a public backup.
