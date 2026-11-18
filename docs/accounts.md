# User accounts

Accounts let a person sign in to Beacon Web and BEACON Mobile with a username, an email address and
a password. They are off by default. With `accounts.mode: off` every account route answers `404`
with code `accounts_disabled`, no cookie is ever set, `features.accounts` in
[`/api/v1/info`](api-contract.md#server-info) is `"off"`, and both clients show no sign-in entry.
Nothing that works signed out changes either way. Everything public stays public.

There are two ways to turn them on. `local` is this page: username, email and password, with mail.
`portal` lets people sign in with their MeshMapper portal account instead, see
[Sign-in through the MeshMapper portal](portal-sign-in.md). Signed-in users also get the synced
[Atlas](atlas.md), and, when the operator turns them on, [requested telemetry](telemetry-requests.md)
and [alerts](alerts.md).

These are not the operator records behind `/api/v1/admin/accounts`. Those are named API keys for
the operator. User accounts live in their own tables and routes, called `users`.

## Turn them on

Accounts need an SMTP server that can send mail, because sign-up, password reset and email changes
all work by a mailed link. Add this to `config.yaml`. The mail server is a top-level `mail` block,
because email alerts send through it too:

```yaml
mail:
  host: smtp.example.org
  port: 587
  username: beacon@example.org
  from: "Beacon <no-reply@example.org>"
  starttls: true

accounts:
  mode: local
  public_url: https://beacon.example.org
  registration: open
```

Put the SMTP password in the environment, never in the file:

```
BEACON_SMTP_PASSWORD=...
```

In the Docker stacks that is the `.env` of the host that runs the server. Then recreate the app container. `config.yaml` is read at startup only.

| Key | Default | What it does |
|---|---|---|
| `mode` | `off` | `off`, `local` or `portal`. Anything else stops startup. The rest of the block is not checked while this is `off`. The rest of this page is about `local`; see [portal sign-in](portal-sign-in.md) for `portal`. |
| `public_url` | none | Required when `mode` is `local`. The address people use for the web app: `http` or `https`, no path, query, fragment or credentials. Plain `http` is allowed only for `localhost` and `127.0.0.1`. Every link in a mail is built from it, never from a request header. |
| `registration` | `open` | `open` or `closed`. When closed, `POST /auth/register` answers `403 registration_closed` and `features.registration` is `false`. People who already have an account keep signing in. |
| `mail.host` | none | Required. |
| `mail.port` | `587` | 1 to 65535. |
| `mail.username` | empty | Empty means no authentication. When set, Beacon uses AUTH PLAIN, and the server must offer AUTH. |
| `mail.from` | none | Required, one address, for example `"Beacon <no-reply@example.org>"`. |
| `mail.starttls` | `true` | When true the send fails if the server does not offer STARTTLS; Beacon never falls back to plain text. Set `false` only for a trusted local relay. |

`BEACON_SMTP_PASSWORD` is the only account secret that comes from the environment. A mistake in the
block stops startup with an error naming the key. An `smtp` block left under `accounts` stops startup
too, with a message saying it moved to `mail`. Port 465 (implicit TLS) is not supported; use a
submission port that offers STARTTLS.

Mail is sent in the background from a small queue. A request never waits for the mail server, so a
failed send shows up only in the log (user id, kind of mail and the recipient's domain, never the
address) and the user asks for another link. If the queue is full a mail is dropped and logged.

Mail names the instance with the `VITE_APP_NAME` value, the same text as the web wordmark, for example
`Confirm your email address for Beacon - Ottawa`. The server reads it from its own environment, so the
variable must be visible to the server container as well as the web container (a shared `.env` does
this). Unset, blank or `BEACON` gives `Beacon`. When `mail.from` is a bare address, the name is also the
sender's display name; an explicit display name in `mail.from` is kept as it is. Alert mail uses the same
name in its subject.

The mailed links are `<public_url>/?view=verify#token=...` and `<public_url>/?view=reset#token=...`
(an email-change link is a verify link). The token is in the URL fragment, which a browser never
sends to a server, so no proxy or access log sees a live token. Links mailed before this change used
`?token=...` and Beacon Web still accepts them. The links open the web app, so `public_url` must be
where Beacon Web is served.

On a read-only server (`server.read_only`) every account write answers `503 read_only`, sign-in
included. The hourly cleanup and the operator user routes are off.

## Same site, and a web app on another origin

The session cookie is `beacon_session`. It is `HttpOnly`, `SameSite=Lax`, `Path=/`, has no `Domain`
and is `Secure` unless `public_url` is `http://localhost...` or `http://127.0.0.1...`. A browser sends
it only to the host that set it, and `SameSite=Lax` means only from a page on the same site.

- **Same origin** (deployment type 1: the web app at `/` and the API at `/api/*` on one host):
  nothing to configure.
- **Another origin**, which includes deployment type 2 where the web app is on `WEB_DOMAIN` and the API on `DOMAIN`, such as the web app on `beacon.example.org` and the API on
  `api.example.org`: the two must still be the same site (one registrable domain), or the browser
  drops the cookie. Then set the CORS block for the web origin:

```yaml
cors:
  allowed_origins: [https://beacon.example.org]
  allowed_methods: [GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE]
  allowed_headers: [Accept, Authorization, Content-Type, X-Beacon-CSRF]
  allow_credentials: true
```

`allowed_origins` must list the web origin, not `*`: a browser refuses credentials with a wildcard,
and Beacon's forgery check never accepts `*`. The default methods are read-only and the default
headers lack `X-Beacon-CSRF`, so without these keys the preflight for a sign-in fails. The web
client also has to send its requests with credentials. See [Configuration](configuration.md#accounts)
and [Reverse proxy](reverse-proxy.md).

The app does not use the cookie. It holds a bearer token (see below), so CORS does not apply to it.

## How people use it

- **Sign up.** The person gives a username, an email and a password. Beacon always answers
  `202 check_email`, whether or not the address is registered. A link is mailed and lasts 24 hours.
  The account exists only after the link is used, and the mail names the username it activates.
- **Several sign-ups for one address.** Each sign-up against an address that is not yet verified gets
  its own link, carrying its own username and password. The link that is clicked decides which
  credentials the account gets, so a stranger who typed someone else's address cannot set the
  password the owner ends up with. A username that is already taken, verified or pending, is refused
  with `username_taken` whatever the address. "Send the link again" repeats the newest pending
  sign-up, even after its link expired, as long as the cleanup has not yet removed the unconfirmed
  sign-up (a week after it was made). It never builds a link from the user row.
- **Sign in.** With a username or an email and the password. A person whose email is not yet
  confirmed gets `email_unverified`, only after the password was right.
- **Reset a password.** A mailed link that lasts 1 hour. Using it ends every session of that user and
  clears the sign-in throttle. A refused new password does not use up the link. The link is bound to
  the address it was mailed to: if the account's address changes first, the link stops working. The
  link is spent in the same step as the password change, under the per-user lock, so a second
  outstanding link fails once one has been used, and a password change made first revokes the link.
  Beacon mails the account address when a password was changed, by reset or from the profile.
- **Profile.** Change the display name, the password (ends every other session), the email (the new
  address is held as `pendingEmail` and changes only when its mailed link is used; the old address is
  mailed that it changed, and outstanding reset links are removed), list and end sessions, and delete
  the account with the current password.
- **The app.** The person signs in on the web first. The web asks for a one-time code, bound to a
  PKCE challenge (S256 only), and hands it to the app through `meshcorebeacon://auth`. The app swaps
  code and verifier for a bearer token. Beacon mails the user whenever an app signs in, and the
  Devices list shows it so it can be ended.

## What Beacon stores about a user

| Data | Detail |
|---|---|
| Username, display name | The display name starts as the username. Usernames are unique ignoring case. |
| Email | One address, lower case, unique. A pending new address is held until confirmed. |
| Password | Only an argon2id hash (19 MiB memory, 2 passes, 1 lane, random 16-byte salt). A hash made with older settings is upgraded at the next sign-in. |
| Sessions | A SHA-256 hash of the token, kind (`web` or `app`), a label (such as "Firefox on macOS"), the IP address and User-Agent, and created, last used and expiry times. |
| One-time tokens | SHA-256 hashes only. A pending sign-up's token also holds that sign-up's username and password hash until it expires or is used. |
| Times | Created, last login, and whether the user is disabled. |

A user also owns, when those features are on, an Atlas (range and up to twelve pins), telemetry
requests with their sealed guest passwords, alert rules and registered push devices. Deleting the
user removes all of them in the same transaction.

Passwords, tokens and codes are never logged and never stored in clear text. Request bodies on the
`/auth` and `/me` routes are never logged. Account responses carry `Cache-Control: no-store`.

Session lengths:

| Session | Lasts | Notes |
|---|---|---|
| Web | 30 days, rolling | Each use extends it, written at most once every 5 minutes. |
| App | 180 days, rolling | Hard end 365 days after creation. At most 10 per user; a new one ends the oldest. |

One-time lifetimes: verify and email-change links 24 hours, reset links 1 hour, app codes 5 minutes.
All are single use. An email-change link is replaced when the user asks for another change, and the
older link then fails as `token_invalid`. A link whose address another user has taken meanwhile also
fails, and it is not used up.

Passwords are 12 or more characters and at most 128 bytes. Beacon converts a password to Unicode
normal form NFC before it checks or hashes it, on every path (sign-up, sign-in, change, reset and the
current-password checks), so a password typed with a combined or a separate accent is one password.
The 12 characters are counted after that conversion, so an emoji or an accented letter counts as one
character; the 128 bytes are the UTF-8 length of the converted password. A password is refused when it
is one repeated character, contains the username or the part of the email before the `@` (ignoring
case), or is on the bundled list of common passwords. The email check is skipped when that part is
shorter than 3 characters: a name such as `al` would otherwise refuse a large share of ordinary
passwords. This exemption is deliberate. There are no other composition rules. Usernames are 3 to 30 of `A-Z a-z 0-9 _ . -`
and `admin`, `root`, `beacon`, `system`, `support`, `moderator` and `operator` are reserved.

## Credential changes and sign-in

Sign-in, a password reset, a password change, an email change, deleting the account and the app
code exchange each run under a per-user lock and check that the password they verified is still the
current one. A sign-in that races a reset therefore never leaves a live session behind, an app code
minted before a reset or password change no longer exchanges (`token_invalid`), and a user never
holds more than ten app sessions. When Beacon cannot look a session up (the database is busy), the
`/me` and other signed-in routes answer `503 service_unavailable` with `Retry-After: 5` instead of
`401`, so a client does not throw away a token that is still good. Public routes carry on as signed
out.

## Busy hashing

Checking or hashing a password uses about 19 MiB of memory and real CPU time, so Beacon runs at most
4 of them at once, for sign-up, sign-in, reset confirm, password change, email change and
account delete. (The app code exchange checks no password, so it never waits for a turn.) A request that cannot get a turn within 5 seconds answers
`503 service_unavailable` with `Retry-After: 5` and the message "The server is busy. Try again in a
moment.". It is not a wrong password and counts nothing against the password throttle below. The
user (or the client) tries again; nobody is signed out by it. A sign-in for a name that does not
exist takes a turn too, so the answer does not reveal whether the name exists.

## Limits and throttles

Per client address, as `requests / window`:

| Route | Limit |
|---|---|
| `POST /auth/register` | 5 / 5 min |
| `POST /auth/login` | 10 / 1 min |
| `POST /auth/verify` | 30 / 1 min |
| `POST /auth/verify/resend`, `POST /auth/reset/request` | 5 / 5 min |
| `POST /auth/reset/confirm` | 10 / 5 min |
| `POST /auth/app/token` | 10 / 1 min |
| Every other `/auth` and `/me` write | 60 / 1 min (one shared budget) |

Over a limit the answer is `429 rate_limited` with `Retry-After`. These count the client address, so
behind a proxy set `server.trusted_proxies` (see [Reverse proxy](reverse-proxy.md)) or every user
shares one budget.

Separately, 10 wrong passwords within 15 minutes, counted for the typed name and for the account it
resolves to, refuse further password checks for 15 minutes with `429 too_many_attempts` and
`Retry-After`. A username and an email for the same account share one budget. A successful password
reset clears it. The counters are in memory, so a restart clears them. Because they also count
against the account, someone who knows a username can keep that account locked out for 15 minutes at
a time; the per-address limits bound how fast. If many addresses try made-up names the table can
fill, and new names are then refused for a minute.

## Managing users as the operator

These routes need the [admin key](configuration.md#admin-api-key) and answer `503` when accounts are
off or the server is read-only.

```
GET    /api/v1/admin/users?search=&cursor=&limit=
PUT    /api/v1/admin/users/{id}      {"disabled": true}
DELETE /api/v1/admin/users/{id}
```

- The list is newest first, 50 a page by default, up to 200. `search` matches part of the username
  or email, ignoring case (up to 100 characters). Pass `nextCursor` as `cursor` for the next page; it
  is missing on the last page. No password hash is ever returned.
- `PUT` with `disabled: true` ends every session of the user at once and refuses new sign-ins.
  `disabled: false` lifts it. The user is returned, with `disabled` and `lastLoginAt`. While a user
  is disabled, a password reset link or an email-change link for it is refused as `token_invalid`
  and its credentials do not change.
- `DELETE` removes the user and everything it owns (Atlas, telemetry requests, alert rules, devices)
  in one transaction: `204`, or `404` if unknown. The transaction takes the same locks as a
  telemetry request change (the user's targets first, then the user) and removes the user's requests
  through the same state rules as a request deleted by the user, so no request is left half
  removed. A disabled user can still be deleted.

Example:

```
curl -H "Authorization: Bearer $BEACON_API_KEY" \
  "https://beacon.example.org/api/v1/admin/users?search=ridge"
```

There is no operator route to set a password. A user who forgot theirs uses the reset link.

## Cleanup

An hourly task (`users_cleanup`) deletes, once they are more than a week past their end:

- sessions that were ended or have expired (including past their hard end);
- one-time tokens that were used or have expired;
- sign-ups nobody confirmed: local users never verified, created more than a week ago, with no live
  verify link left. This frees the username and address;
- stale portal sign-in states, in portal mode.

A live session or token is never touched by it.

## Disabling accounts again

Set `accounts.mode: off` and restart. The routes answer `404 accounts_disabled` and clients hide
sign-in. The stored users, sessions and tokens stay in the database and are used again if you turn
accounts back on; the cleanup does not run while they are off.
