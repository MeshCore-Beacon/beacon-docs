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
offered for a repeater only while Beacon is polling it, meaning an observer holds it as a polling
assignment right now; the user is told to request telemetry for it first (see
[Requested telemetry](telemetry-requests.md)).

| Kind | Radios | Threshold |
|---|---|---|
| `gone_quiet` | all | Hours: 12, 24 or 48. Also 3 and 6 for observers and polled repeaters. |
| `back_online` | all | None. Needs an enabled `gone_quiet` rule on the same radio. Notifies when that rule recovers. |
| `clock` | repeaters, room servers | Seconds of drift: 300, 3600 or 86400. Fires after two adverts in a row beyond it. Beacon keeps the drift of each repeater's last 16 adverts, so a breach that came and went between two passes still fires once. |
| `battery_low` | with a battery reading | Millivolts, 2500 to 5000. |
| `battery_falling` | with a battery reading | Millivolts per day: 100, 200 or 300. |
| `rebooted` | with an uptime reading | None. Notifies on each new reboot seen. Every reading since the rule's last pass is examined, not only the newest few. |
| `temperature` | with a temperature reading | Tenths of a degree C, -500 to 1500. A low limit (`threshold`), a high limit (`thresholdHigh`) or both; low must be below high. With both set on a rule that is on, the high limit must be at least 20 tenths (2.0 degrees C) above the low one, or the change is refused with `422 invalid_threshold`; a rule being turned off is not held to it. |
| `noise_high` | with a noise floor reading | dBm, -130 to -50. |
| `observer_offline` | observers | Minutes without a status report: 30, 60, 180 or 360. |

On an instance with `display.temperature_unit: f` ([Display units](configuration.md#display-units)), alert mail and push text give temperatures in F, and clients take and show the temperature limits in whole degrees F. The API still stores and sends tenths of a degree C.

A sixth announcement, `request_attention`, is not a rule. Every user who has a telemetry request
gets one notice when it moves to `login_failed`, `admin_stopped` or `disabled`, and another if it
recovers and fails again. It is sent whenever alerts are on.

A rule is `ok`, `firing`, `inactive` (the data it needs is gone, for instance a repeater no
observer polls any more) or `unknown` (not enough data yet).
Changing a threshold or turning a rule on resets it to `unknown` and starts from now, so there is
no alert about the past. Taking a radio off the Atlas deletes its rules. A `back_online` rule whose
`gone_quiet` rule is turned off or deleted reads `inactive` and sends nothing.

The overview marks each radio `polled` while it has a current source of telemetry, which is what
offers the 3 and 6 hour `gone_quiet` thresholds and the telemetry kinds. A repeater is polled while
an observer holds it as a polling assignment (a standby counts). An observer is polled only if it
sent status telemetry in the last 24 hours. Old readings alone do not count, so a radio that was
polled can turn `polled: false`; its telemetry kinds then move to `unavailable` with code
`not_polled` (repeater) or `observer_no_data` (observer), and its telemetry rules read `inactive`.
With `polling.enabled: false` no repeater is polled: every repeater reads `polled: false`, its
telemetry kinds are `unavailable` with `not_polled` and its telemetry rules read `inactive`. Observer
status alerts do not depend on polling and carry on. When a kind is not offered
the overview gives the reason as an English sentence and as a stable code (`unavailableCodes`), so
clients can translate it. The codes are listed in the [API contract](api-contract.md#alerts).

## How often, and the limits

- Rules are evaluated every 5 minutes. Only one instance does it at a time. A pass is bounded, so it
  continues where the last one ended and starts over only after it has reached the last rule; the
  position is kept in the database. Every enabled rule is evaluated in the end.
- A rule notifies when it changes into `firing`, and at most once every 6 hours. `rebooted` and
  `back_online` notify on the event itself, under the same 6 hour limit.
- A rule goes back to `ok` only when the reading is clear of the threshold by some margin: 100 mV
  for battery, 3 dB for noise, 1 degree for temperature. This stops a value at the edge from
  flapping.
- Notices are sent every minute, and only for an evaluation pass that has finished, so the notices
  of one pass reach a user together. Notices of a pass that never finished (the process stopped) are
  sent once that pass is 15 minutes old. A notice not delivered within 2 hours is dropped, and a
  notice that failed 5 times is dropped. Delivered notices are kept a day.
- Evaluation reads at most the newest 12 readings per radio within 14 days, except for `rebooted`:
  that rule starts from the last reading it has seen and reads forward in pages of 200 readings per
  pass, so every reading counts. A backlog longer than 200 readings takes several 5 minute passes
  (the notice comes late, not never).
- Each advert's clock drift is kept for the radio's last 16 adverts. The `clock` rule judges every
  pair of adverts since its last pass, so a drift past the limit that was back inside it by the next
  pass still fires once, and then recovers.

## Email

One message per user for each evaluation pass: subject "Beacon: 1 alert" or "Beacon: n alerts",
one plain sentence per alert, and a link to `<public_url>/?tab=Atlas`. The alert sender sends it
directly, not through the account mail queue, with a 30 second timeout for each message. A notice
counts as delivered only once the SMTP server accepted the mail. A failed send is retried after 1,
2, 4 and 8 minutes, at most 5 attempts in all, and within the 2 hour limit above; it also ends that
minute's run, so one dead mail server costs one timeout a minute. At most 16 mails go out per run,
and the notices of one user and pass are never split across mails. A user with no verified address
gets nothing.

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

Each live app session with a registered token gets one message per notice. Delivery is tracked per
device: a retry goes only to the devices that do not have the notice yet, and a notice is delivered
once every device has it. The title is the
radio's name and the body is one English sentence; the app opens the radio from the message data
(`targetKind`, `publicKey` and, when the radio is known, its `id`). A token Google reports as no longer registered is deleted. A user
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
