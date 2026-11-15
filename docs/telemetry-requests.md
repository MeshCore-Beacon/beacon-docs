# Requested telemetry

A signed-in user can ask Beacon to have a repeater or room server polled, even when no observer
owner has set it as a target. Beacon hands the job to an observer that can hear the repeater and
that its operator approved. The user can give a guest password for the repeater; Beacon seals it
for the observer that does the polling.

This builds on [Repeater polling](repeater-polling.md) and [User accounts](accounts.md). Read
those first. The routes and shapes are in the [API contract](api-contract.md#telemetry-requests).

## Turn it on

Requests run only when all of these hold:

- `polling.enabled` is `true`.
- User accounts are on, in `local` or `portal` mode.
- `BEACON_SECRET_KEY` is set. It seals the guest passwords. See
  [Configuration](configuration.md#beacon_secret_key).
- `polling.requests_per_user` is not `0`.

If one of these is missing Beacon still starts, logs one line saying why requests are off, and
`features.telemetryRequests` in [`/api/v1/info`](api-contract.md#server-info) is `false`. Every
request route then answers `404 requests_disabled`, and both clients hide the section. A
`BEACON_SECRET_KEY` that is set but is not 32 bytes of base64 stops startup.

| Key | Default | What it does |
|---|---|---|
| `polling.requests_per_user` | `3` | How many requests one user may hold, 0 to 20. `0` turns requests off. |
| `polling.offline_disable_days` | `7` | Days without any observer hearing a repeater before its requests are turned off, 1 to 365. |
| `polling.request_observers` | `approved` | `approved` or `all`. Which observers may be handed a requested repeater. See below. |

## Approve observers

By default only observers you approved are given a requested repeater, and only they receive a
guest password. Approve one with the same route polling already uses:

```bash
curl -X PUT -H "Authorization: Bearer $BEACON_API_KEY" -H "Content-Type: application/json" \
  -d '{"blocked":false,"approved":true,"note":"north ridge, run by Sam"}' \
  https://beacon.example.com/api/v1/admin/polling/observers/<observer public key>
```

On a fresh instance requests therefore wait until you approve at least one observer. A request that
no approved observer can take shows as `waiting` with the reason "No observer can reach this
repeater yet."

The reason for the default: Beacon decides an observer can reach a repeater from advert evidence,
and that evidence is built from packets the observer itself uploads. With `request_observers: all`,
anyone who runs an observer could present evidence for a repeater and be handed its guest password.
Set `all` only where you know who runs every observer. Approval is checked each time an owners
answer is built, so withdrawing it stops the password going out within a minute, and blocking the
observer is faster still.

`polling.authority: approved` also applies to requests, whatever `request_observers` says.

## How a request becomes an assignment

1. The user picks a repeater or room server in the app or on the web and may enter a guest
   password. Beacon stores the request, with the password sealed (see [Security](security.md#guest-passwords)).
2. At the next election for that repeater (every minute, and at once after a request changes),
   Beacon looks at observers that have a live claim naming it, or that have a free seat for it. An
   observer takes the job only when all of these hold:
   - its claim says `accepts_requests` and has a free `request_slots` seat;
   - Beacon holds advert evidence that this observer hears the repeater directly;
   - the observer is not blocked, has no admin stop for the repeater, and is approved (unless
     `request_observers` is `all`);
   - the repeater is not in `admin_stop` or `not_direct` state for it.
3. Observers are ranked as for any polled repeater. At most one poller and two standbys are chosen.
   Seats go to the oldest requests first.
4. If an observer already polls the repeater because its owner set it as a target, it keeps the job
   and the requests ride on its readings. No password is sent.
5. The next owners answer to each chosen observer lists the repeater with `"requested": true` and,
   when a password is in use, a `pw` envelope sealed to that observer's public key. The observer
   claims the repeater as requested and polls it as it would any other.

Only one password is in use for a repeater at a time. The oldest usable request decides: its
password, or the shared blank or hello login when it has none. Several users can request the same
repeater. When the password in use fails or is deleted, the next request takes over.

## The firmware side

The observer firmware needs request support. A claim from such firmware carries `accepts_requests`,
`request_slots` (free seats, at most 8) and `requested` on each node. Firmware without request
support never reaches this path and its observer simply polls its own targets. The envelope format
and the claim fields are in the [API contract](api-contract.md#firmware-polling). Beacon never sends
a password to an observer in clear: only the envelope, which only that observer's key opens.

An observer that holds a requested repeater it is not assigned any more is left out of the next
owners answer for it, and the device drops it.

## What the user sees

| Status | Meaning | Reasons |
|---|---|---|
| `waiting` | No observer polls it yet. | `no_observer`: no observer can reach it yet. `no_seat`: every observer that can reach it is at its limit. |
| `active` | An observer polls it, or the requests ride on a poll that is already set. | none |
| `login_failed` | The repeater did not accept the guest password, or a blank or hello login. | `login_failed`, `blank_login_failed` |
| `admin_stopped` | The repeater answered with admin access. | `admin_stopped`, `blank_blocked` |
| `disabled` | Nobody heard the repeater for `polling.offline_disable_days` days. | `offline` |

The profile also shows the poller's name and when the newest trusted reading arrived. The user
fixes `login_failed` and `admin_stopped` by entering a new guest password, and restarts a `disabled`
request with `enabled: true`. Removing a request deletes its password, and when it was the last
request for the repeater observers stop polling it.

After the password changed, a `login_failed` report from an observer is ignored, so the report of an
old login does not mark the new password as failed. The grace ends after 30 minutes, or as soon as
that observer has reported any other state since the change, whichever comes first.

## Guest passwords only

A guest password is shared with the volunteer observer that polls the repeater, so it must never be
an admin password. Beacon cannot tell them apart when they are entered, and says so on the form. If
a repeater answers a login with admin access, the observer reports `admin_stop` and Beacon:

- deletes the password that was in use, and sets that request to `admin_stopped`;
- records the stop for that observer and repeater, so the observer is not offered the repeater again;
- when no password was in use (the blank or hello login got admin), blocks passwordless requests for
  that repeater, because anyone could request it and the observer would log in as admin. Such a
  user must enter a guest password. Creating a request without one answers `409 no_password_blocked`.

A report of `admin_stop`, `login_failed` or any other state counts only when it comes from an
observer that was handed that repeater as a requested assignment, and `login_failed` only from the
poller.

## Offline repeaters

Every hour Beacon turns off all requests for a repeater that no observer has heard for
`polling.offline_disable_days` days, counted from when its newest request was created or last
re-enabled. The reason reads "Not heard by any observer for N days." The user restarts a request by
hand, which restarts the clock.

## Admin routes

All need the [admin key](configuration.md#admin-api-key) and answer `503` unless polling is on and
the server is not read-only.

| Route | What it does |
|---|---|
| `GET /api/v1/admin/polling` | Adds `noPasswordBlocked` (repeater keys) and `adminStops` (`targetPublicKey`, `observerPublicKey`, `reportedAt`). |
| `GET /api/v1/admin/polling/targets` | Each repeater also shows `requested` (a request is in use) and `requests` (how many requests name it). |
| `PUT /api/v1/admin/polling/targets/{target}` | `{"noPasswordBlocked": false}` lifts the blank-login block. Only `false` is accepted. `404` for an unknown repeater. Stopped requests do not restart by themselves. |
| `DELETE /api/v1/admin/polling/admin-stops/{target}/{observer}` | Lets that observer be offered the repeater again at the next election. `204`, or `404`. The observer's own device keeps its stop until its owner runs `poll enable` on it. |

No route returns a password, and the admin routes never read one.

## If BEACON_SECRET_KEY is lost or changed

Stored passwords cannot be opened with another key. Beacon logs "requested password does not open"
for that repeater and leaves it out of the owners answer, so the observer does not poll it. Users
have to enter their guest passwords again, which seals them under the new key. Requests that use the
blank or hello login are not affected. See [Configuration](configuration.md#beacon_secret_key).

## Troubleshooting

- **Every request stays `waiting`.** In `approved` mode, approve an observer that hears the
  repeater. Check `GET /admin/polling/targets` for the candidates, their evidence and whether each
  is approved. Check the observer's firmware supports requests and has free seats.
- **`no_seat`.** Every observer that can reach the repeater already polls as many requested
  repeaters as its claim allows.
- **Requests are off.** Look for "telemetry requests are off" in the startup log. It names the
  missing piece.
