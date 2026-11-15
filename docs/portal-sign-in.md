# Sign-in through the MeshMapper portal

Instead of local accounts with an email and a password, a Beacon instance can let people sign in
with their MeshMapper portal account. Beacon is then a client of the portal. People never type a
password into Beacon, Beacon stores none, and it sends no mail.

This is `accounts.mode: portal`. Everything else about accounts in [User accounts](accounts.md)
still applies: sessions, the app sign-in, Atlas sync, and the optional
[telemetry requests](telemetry-requests.md) and [alerts](alerts.md) (portal users have no email
address, so alerts can only use push).

## What to set

```yaml
accounts:
  mode: portal
  public_url: https://beacon.example.org
  portal:
    url: https://portal.example.org
    client_id: beacon-example
```

```
BEACON_PORTAL_SECRET=...
```

| Key | What it does |
|---|---|
| `accounts.mode` | `portal`. |
| `accounts.public_url` | Required. The web app's address, as for local mode. The callback address below is built from it. |
| `accounts.portal.url` | Required. The portal's base address: `https`, no credentials, query or fragment. |
| `accounts.portal.client_id` | Required. The identifier the portal knows this Beacon instance by. |
| `BEACON_PORTAL_SECRET` | Required in the environment, never in the file. The client secret the portal issued. Startup stops if it is missing. |

Portal mode needs no SMTP. The `smtp` block is ignored and registration is always off
(`features.registration` is `false`). `features.accounts` in
[`/api/v1/info`](api-contract.md#server-info) is `"portal"` and `features.portalUrl` carries the
portal's address, so clients show a "Sign in with MeshMapper" button instead of a form.

## What the portal operator must be told

Give the MeshMapper portal operator:

- the `client_id` you chose and the callback address Beacon sends people back to:
  `<public_url>/api/v1/auth/portal/callback`, which must be registered exactly;
- a client secret for you to put in `BEACON_PORTAL_SECRET`.

Beacon expects the portal to provide two things, and nothing else is needed from it:

1. An authorize page at `<portal.url>/portal.php`, opened with `beacon_authorize=1`, `client_id`,
   `redirect_uri`, `state`, `code_challenge` and `code_challenge_method=S256`. After the person
   agrees it sends the browser to the callback with `code` and `state`. If the person cancels it may
   send `error=access_denied` and `state` with no code.
2. A token call, `POST <portal.url>/portal_beacon_api.php?action=token` with a JSON body of
   `client_id`, `client_secret`, `code`, `code_verifier` and `redirect_uri`, answering `200` with
   `{"user":{"id":...,"username":"...","display_name":"..."}}`. The id may be a string or digits.
   Beacon keeps it exactly as the user's subject (digits compare as their decimal text). A subject
   that is blank, longer than 128 bytes, not valid UTF-8 or holding a control character fails the
   sign-in, like any other failure below.

## How a sign-in goes

1. The web app sends the browser to `GET /api/v1/auth/portal/start?return=<path>`. Beacon stores a
   one-time state and a PKCE verifier for 10 minutes, sets the `beacon_portal` cookie (HttpOnly,
   `SameSite=Lax`, limited to `/api/v1/auth/portal`) and redirects to the portal. `return` must be
   a path on the same site; anything else becomes `/`.
2. The portal sends the browser back to the callback. Beacon checks the state against the cookie,
   uses it up whatever happens, and trades the code for the user at the portal with the client
   secret. The call times out after 10 seconds, follows no redirect and reads at most 64 KiB.
3. Beacon finds the user by the portal's id or creates one, signs them in with a normal web
   session cookie, and redirects to the return path.

Any failure, including the person pressing Cancel, redirects to `<public_url>/?view=signin&error=portal`.
Beacon logs a fixed reason and never the code, secret or portal answer. The state lives in the
database, so start and callback may reach different instances.

A portal user's username and display name are refreshed from the portal at each sign-in. A username
already used by another user gets a number added, and names are cut to 30 characters. There is no
password and no email, so these local routes answer `404 portal_managed`: register, verify, resend,
login, reset request, reset confirm, change password and change email. Deleting an account takes
`{"confirmUsername": "<their username>"}` instead of a password.

The app signs in as in local mode: on the web first, then a one-time code handed to the app.

## Switching modes

Users made in local mode and users made through the portal are separate records. Changing
`accounts.mode` does not link them. A portal user cannot use local sign-in and the reverse.
