# Alerts

A signed-in user can ask Beacon to tell them when a radio on their [Atlas](atlas.md) needs
attention: it went quiet, its battery is low, it rebooted. Alerts go by email or by push
notification to the mobile app, depending on what the operator sets up. Alerts are off by default.

Routes and shapes are in the [API contract](api-contract.md#alerts).

## Turn them on

Alerts need [user accounts](accounts.md), because a rule belongs to a user and to a radio they
have pinned.

```yaml
alerts:
  delivery: email   # off, push or email
```

| `alerts.delivery` | What it needs |
|---|---|
| `off` | Nothing. Default. Every alert route answers `404 alerts_disabled`. |
| `email` | `accounts.mode: local` with working SMTP. Portal mode is refused at startup because portal users have no address. |
| `push` | The credential file named by `BEACON_PUSH_CREDENTIALS`, see [Push](#push). Without it Beacon does not start. |

Any other value stops startup. With accounts off, alert routes answer `404 accounts_disabled`.
`features.alerts` and `features.alertDelivery` in [`/api/v1/info`](api-contract.md#server-info) tell
clients whether to show the section. A read-only server never evaluates or sends alerts.

## Alert kinds

A user sets rules per radio on their Atlas. A radio has one rule per kind. Which kinds a radio
offers depends on what it is and what Beacon has seen it report. Kinds that need readings are
offered for a repeater only while Beacon is polling it, meaning trusted readings arrived in the
last 14 days; the user is told to request telemetry for it first (see
[Requested telemetry](telemetry-requests.md)).

| Kind | Radios | Threshold |
|---|---|---|
| `gone_quiet` | all | Hours: 12, 24 or 48. Also 3 and 6 for observers and polled repeaters. |
| `back_online` | all | None. Needs a `gone_quiet` rule on the same radio. Notifies when that rule recovers. |
| `clock` | repeaters, room servers | Seconds of drift: 300, 3600 or 86400. Fires after two adverts in a row beyond it. |
| `battery_low` | with a battery reading | Millivolts, 2500 to 5000. |
| `battery_falling` | with a battery reading | Millivolts per day: 100, 200 or 300. |
| `rebooted` | with an uptime reading | None. Notifies on each new reboot seen. |
| `temperature` | with a temperature reading | Tenths of a degree C, -500 to 1500. A low limit (`threshold`), a high limit (`thresholdHigh`) or both; low must be below high. |
| `noise_high` | with a noise floor reading | dBm, -130 to -50. |
| `observer_offline` | observers | Minutes without a status report: 30, 60, 180 or 360. |

A sixth announcement, `request_attention`, is not a rule. Every user who has a telemetry request
gets one notice when it moves to `login_failed`, `admin_stopped` or `disabled`, and another if it
recovers and fails again. It is sent whenever alerts are on.

A rule is `ok`, `firing`, `inactive` (the data it needs is gone) or `unknown` (not enough data yet).
Changing a threshold or turning a rule on resets it to `unknown` and starts from now, so there is
no alert about the past. Taking a radio off the Atlas deletes its rules.

## How often, and the limits

- Rules are evaluated every 5 minutes. Only one instance does it at a time.
- A rule notifies when it changes into `firing`, and at most once every 6 hours. `rebooted` and
  `back_online` notify on the event itself, under the same 6 hour limit.
- A rule goes back to `ok` only when the reading is clear of the threshold by some margin: 100 mV
  for battery, 3 dB for noise, 1 degree for temperature. This stops a value at the edge from
  flapping.
- Notices are sent every minute. A notice not delivered within 2 hours is dropped, and a notice
  that failed 5 times is dropped. Delivered notices are kept a day.
- Evaluation reads at most the newest 12 readings per radio within 14 days.

## Email

One message per user for each evaluation pass: subject "Beacon: 1 alert" or "Beacon: n alerts",
one plain sentence per alert, and a link to `<public_url>/?tab=Atlas`. Mail uses the account mail
queue. A notice counts as delivered when it is queued, so a mail the SMTP server later refuses is
logged and not retried. A user with no verified address gets nothing.

## Push

Push goes to the mobile app through Firebase Cloud Messaging (the HTTP v1 API). The publisher of
the app, not each operator of a Beacon server, owns the Firebase project the app is built with, so
push works only on a server the publisher sets up with a key for that project. The steps:

1. Create the Firebase project for the app and add the Android and iOS apps to it. For iOS, add the
   Apple push key in the project.
2. Create a service account key for the project that may send messages. The file is JSON with
   `project_id`, `client_email` and `private_key` (and optionally an https `token_uri`).
3. Mount the file into the server container and set its in-container path:

```
BEACON_PUSH_CREDENTIALS=/app/push-credentials.json
```

```yaml
alerts:
  delivery: push
```

With `push` and no `BEACON_PUSH_CREDENTIALS`, startup stops with an error: otherwise users would set
rules that never send. A file that cannot be read or is not a service account key also stops
startup, and the message names neither the path nor the content. Keep the file private.

Each live app session with a registered token gets one message per notice. The title is the
radio's name and the body is one English sentence; the app opens the radio from the message data
(`targetKind` and `publicKey`). A token Google reports as no longer registered is deleted. A user
with no app signed in gets no push alerts. Only an app session can register a token; a browser
session gets `403 app_session_required`.

A push token belongs to one account. Registering a token removes it from every other session and
user, because one phone has one account. The token is never returned by any route and never
logged.

## Names in alerts

A radio's name comes from its own adverts, so it is untrusted. Beacon uses the user's own pin name,
or else the radio's name, with control and formatting characters and line breaks removed,
whitespace collapsed and the length cut to 40 characters. An empty name becomes the first 8 hex
characters of the key. A name therefore cannot inject a mail header or hide text.
