# Alerts

A signed-in user can ask Beacon to tell them when a radio on their [Atlas](atlas.md) needs
attention: it went quiet, its battery is low, it rebooted. Alerts go by email or by push
notification to the mobile app. The operator decides which channels the server offers, and each user
chooses email, push or both in their profile. Alerts are off by default.

Routes and shapes are in the [API contract](api-contract.md#alerts).

## Turn them on

Alerts need [user accounts](accounts.md), because a rule belongs to a user and to a radio they
have pinned.

```yaml
alerts:
  email:
    enabled: true
  push:
    enabled: true
    id: inst_7f3k2m9qxa
```

| Channel | What it needs |
|---|---|
| `email.enabled` | `accounts.mode: local` with the [`mail` block](configuration.md#user-accounts) set. Any other mode stops startup. |
| `push.enabled` | A Push ID in `push.id` and the Push secret in `BEACON_PUSH_SECRET`, from registering the server with the push server. See [Push](#push). Without them Beacon does not start. |

With both off (the default) every alert route answers `404 alerts_disabled`. With accounts off,
alert routes answer `404 accounts_disabled`. The old `alerts.delivery` key stops startup with a
message saying what replaced it. `features.alerts` and `features.alertChannels` in
[`/api/v1/info`](api-contract.md#server-info) tell clients whether to show the section. A read-only
server never evaluates or sends alerts.

Each user has an email switch and a push switch, both on by default; registering the app turns push
on. A channel reaches the user only while the server offers it and the user's switch is on. Email
and push are delivered and retried apart: a retry repeats only the channel that failed, and a
failing channel never holds back the other.

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
| `rebooted` | with an uptime reading | None. Notifies on each new reboot seen. Every reading since the rule's last pass is examined, not only the newest few. An observer's reboot is stored as soon as it reports, at most once per `telemetry.resolution` window, so a radio in a boot loop notifies about once per window, not once per boot. |
| `temperature` | with a temperature reading | Tenths of a degree C, -500 to 1500. A low limit (`threshold`), a high limit (`thresholdHigh`) or both; low must be below high. With both set on a rule that is on, the high limit must be at least 20 tenths (2.0 degrees C) above the low one, or the change is refused with `422 invalid_threshold`; a rule being turned off is not held to it. |
| `noise_high` | with a noise floor reading | dBm, -130 to -50. |
| `observer_offline` | observers | Minutes without a status report: 30, 60, 180 or 360. |

On an instance with `display.temperature_unit: f` ([Display units](configuration.md#display-units)), alert mail and the app's push text give temperatures in F, and clients take and show the temperature limits in whole degrees F. The API still stores and sends tenths of a degree C.

One more announcement, `request_attention`, is not a rule. Every user who has a telemetry request
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
  sent once that pass is 15 minutes old.
- Email and push each have their own 5 attempts. A failed channel waits 1, 2, 4 and then 8 minutes
  before its next try (longer when the push server asks for it) and gives up after the fifth
  failure. A push failure never uses up or delays the mail, and the other way round.
- A notice is finished once both channels are done: sent, not wanted (the server does not offer
  the channel, the user's switch is off, there is no verified address or no app device), or out of
  attempts. A notice not finished within 2 hours is dropped, whatever attempts it has left. A notice
  that went out on every channel it needed is kept a day; one that ran out of attempts is deleted
  once it is finished.
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
counts as mailed only once the SMTP server accepted it, and a mail that went out is never sent again,
even when the push of the same notice is retried. A failed send is retried on the email channel's
own schedule above. It also ends the mail part of that minute's run, so one dead mail server costs
one timeout a minute; push still goes out. At most 16 mails go out per run, and the notices of one
user and pass are never split across mails. A user with no verified address gets nothing.

## Push

Only the app's publisher can send push notifications to the Beacon app, so every Beacon server sends
push through the MeshCore Beacon push server at `https://push.meshcorebeacon.ca`, which the project
runs. It sends iPhone notices straight to Apple and Android notices through Firebase, so no
Beacon server holds an Apple or Firebase key. To turn push on:

1. Register the server at `https://push.meshcorebeacon.ca/register`. It takes a name (shown on every
   notification), your email and, optionally, the server's public URL. Give the URL: the push
   server then checks `<url>/.well-known/beacon-push` daily and raises the server's limits once it
   passes (see Limits below). Your proxy must send that path to beacon-server; the stock Caddy
   configs do, and [Reverse proxy](reverse-proxy.md) shows nginx and Apache. Open the emailed link
   to get a **Push ID** and a **Push secret**. The secret is shown once. If you lose it, or want to
   remove a server to register another, use `https://push.meshcorebeacon.ca/manage`: it emails a
   link that lets you get a new secret (the old one stops working at once) or remove a server.
2. Put the secret in the environment and the ID in `config.yaml`:

```
BEACON_PUSH_SECRET=...
```

```yaml
alerts:
  push:
    enabled: true
    id: inst_7f3k2m9qxa
    # server: https://push.meshcorebeacon.ca   (the default; leave it)
```

3. Recreate the app container. At startup Beacon logs that push goes through the push server and
   which limits apply, and it checks in again every hour.

To check connectivity, open the [push server health endpoint](https://push.meshcorebeacon.ca/healthz).
An HTTP 200 response with the text `ok` confirms the public relay answered. On your own Beacon
instance, check `features.alertChannels.push` in `/api/v1/info` to see whether it offers push.
To verify delivery all the way to a phone, use an enrolled app session and confirm receipt on that device.

You must use the official push server: the Beacon app only receives notifications sent through it.
`push.server` exists only in case the project announces a new address; any other value logs a
warning. `push.enabled` without `push.id` or `BEACON_PUSH_SECRET` stops startup with a message
pointing to the registration page.

**What the push server sees.** It identifies this server as the sender of every notification, puts
the server's registered name on it, enforces rate limits and keeps usage records (server, time,
device handle, size) to catch abuse. Servers that abuse it may be rate-limited, suspended or banned.
It cannot read the notifications: each one is encrypted for its device with a key only the app and
this server have.

**Limits.** A newly registered server may send 30 notifications a minute and 500 a day, and each
device 10 a minute and 200 a day. If the server's public URL was given, the push server checks it
daily at `<url>/.well-known/beacon-push` (Beacon answers it while push is on; the stock
Caddy configs route it, and in deployment type 2 the URL to register is the API host), and a server that
passes may send 300 a minute and 10,000 a day. Daily counts start again at midnight UTC. When the
push server refuses a message for a limit, or the whole call with `429`, Beacon holds that push for
as long as the push server asks (a minute when it gives no time), and the wait does not use up an
attempt. Only the push waits: the mail of the same notice goes out as usual. A server over its daily
limit keeps its push notices until the quota resets or they pass the 2 hour limit, whichever comes
first. A suspended or banned server's calls fail and use up the push attempts; mail is not affected.

**Devices.** Each app session that registered a device gets one message per notice. Messages go in
batches of up to 100 per call; a notice whose push failed before goes in smaller ones, half the size
for each failure, so a batch that timed out is not sent again the same way. No new batch starts after
2 minutes of a run, and the rest waits for the next one. Each message carries an id made of the
notice and the device, the same on every retry, so the push server does not send a message twice
when Beacon repeats it after a lost answer. Delivery is tracked per device: a retry goes only to the
devices that do not have the notice yet. A device the push server reports as gone is deleted, and a
message it refuses as invalid or too large is not sent to that device again. A call that fails as a
whole uses up an attempt for its notices. If the push server refused the call with an error status,
every notice still to send in that run uses one up too. If it could not be reached, gave no answer
within 30 seconds, or sent a `200` that was cut short, unreadable or had the wrong number of results,
only that batch uses an attempt and the rest is left for the next run. A message that failed on its
own waits at least as long as the push server asks before its next try.

A user with no app signed in gets no push alerts. Only an app session can register a device; a
browser session gets `403 app_session_required`. A device handle belongs to one account: registering
it removes it from every other session and user. Handles and keys are never returned by any route
and never logged.

The push message carries the notice, not ready-made text; the app writes the sentence. The format is
in the [API contract](api-contract.md#push-delivery).

## Names in alerts

A radio's name comes from its own adverts, so it is untrusted. Beacon uses the user's own pin name,
or else the radio's name, with control and formatting characters and line breaks removed,
whitespace collapsed and the length cut to 40 characters. An empty name becomes the first 8 hex
characters of the key. A name therefore cannot inject a mail header or hide text.
