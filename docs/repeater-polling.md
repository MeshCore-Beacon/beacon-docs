# Repeater polling

Some observers can ask nearby repeaters for their battery, uptime, noise floor and packet
counters, and publish the answers. Beacon decides which observer asks which repeater, so two
observers that both hear a repeater do not both spend airtime on it, and stores the readings.
Polling is off by default.

This page is for an operator who runs Beacon and for someone who owns an observer. Beacon only
coordinates and stores. It does not talk to repeaters itself, and in this release nothing in the
web app or the mobile app shows the readings yet. Charts come in a later release.

## How it works

1. The owner sets a repeater as a target on the observer. The observer can poll direct
   neighbours only, up to 8 targets.
2. The observer asks Beacon for its policy (`GET /api/guest-polling/policy`) and its owners
   answer (`GET /api/guest-polling/owners`). Until it has a policy it neither polls nor reports.
3. The observer publishes a claim to the MQTT broker, listing its targets and how its last
   polls went.
4. Every minute Beacon ranks the observers that claimed each repeater. Observers that heard the
   repeater's zero-hop adverts in the last 24 hours rank by mean SNR, then by number of adverts.
   One observer is the poller. The others are standbys.
5. The observer reads its role from the owners answer. The poller asks the repeater when the
   newest reading is older than the poll window. A standby waits the window plus one grace period
   for each rank, so it only polls if the poller has not.
6. The poller publishes the reading to the broker. Beacon stores it. The next owners answer
   carries the new reading time, which tells every observer the repeater is fresh.

An observer that reports 3 or more misses in a row for a repeater ranks below every healthy
observer, and a healthy poller keeps the job unless another healthy observer beats it by 3 dB.
So a poller that stops getting answers hands over, and takes the job back once it recovers and is
the stronger signal.

## What Beacon needs

Set `polling` in `config.yaml`. See [Configuration](configuration.md#repeater-polling) for every key.
The minimum is:

```yaml
polling:
  enabled: true
  mqtt_hosts: [mqtt1.example.com]
```

Then recreate the app container. A change to `config.yaml` is read at startup only.

- `mqtt_hosts` are the broker hosts observers publish to, without a port. A device uses them to
  pick which of its MQTT slots to poll through, so each must equal the host in that slot. The
  match is exact. Beacon lowercases the list.
- Beacon must be subscribed to that broker. Claims and readings arrive on the same topics as
  packets, so the [account Beacon already needs](getting-packets-in.md#the-account-beacon-needs)
  is enough.
- The observer must reach Beacon over https at the site root. It calls `/api/guest-polling/...`
  on the host you give it. The stock Caddy configs send `/api/*` to the server, so nothing changes
  there. Behind your own proxy, forward `/api/*` without rewriting the path.
- Beacon answers these routes on every instance, even with polling off. With polling off the
  policy says `paused: true` and the observer stays idle. A missing route would make the
  firmware fall back to a different mode, so do not block them.

## What an observer owner does

The device must be an ESP32 board with PSRAM, with the MQTT bridge on, publishing to a broker
Beacon reads. It needs MeshCore observer firmware with repeater polling. On the device:

```text
set poll.url https://beacon.example.com
poll add <repeater public key>
set poll on
```

- `poll.url` is the Beacon site, with `https://` and no path. Changing it makes the device wait
  for a fresh policy before it polls again.
- `poll add` takes the repeater's 64 character public key. Repeat it for each repeater, up to 8.
  The repeater must be a direct neighbour that the observer heard in the last day. The observer
  never floods to reach one.
- `set poll.slot` is optional. It names the MQTT slot the device uses when it has several. Leave
  it out and the device picks the slot whose host is in Beacon's `mqtt_hosts`.

The poll interval comes from Beacon's policy (`direct_window`), so the owner does not set one.

## What Beacon stores

| Data | Kept for |
|---|---|
| Each observer's latest claim and its target list | Used while the claim is under 65 minutes old. Removed 24 hours after it was received. |
| Who polls and who stands by for each repeater | Rebuilt every minute. |
| Readings: battery, temperature, the repeater's counters, raw sensor bytes and which observer sent them | `polling.reading_retention`, 31 days by default. |
| Operator flags per observer | Until you change them. |

A reading is stored once per repeater, observer and sample. The same reading arriving twice, for
example over two brokers, is ignored. Beacon also counts how many other observers heard the
repeater's reply. That count is informational. A reading is never refused for lacking it.

Beacon accepts a reading only when all of these hold:

- The topic key and the message's `origin_id` are the same observer.
- That observer has a claim under 65 minutes old that lists the repeater.
- `sampled_at` is not in the future and not older than 2 hours.
- The observer is not blocked.

## Pause, exclude and block

The admin routes need the [admin API key](configuration.md#admin-api-key). They exist only while
`polling.enabled` is true and the server is not [read-only](configuration.md#read-only-mode).
Otherwise they answer `503`. The same shapes are in the [API contract](api-contract.md#admin).

| Route | What it does |
|---|---|
| `GET /api/v1/admin/polling` | Returns the pause state, the excluded repeaters and every observer with a flag set. |
| `PUT /api/v1/admin/polling/state` | Replaces the pause state and the excluded repeaters. |
| `PUT /api/v1/admin/polling/observers/{publicKey}` | Replaces one observer's `blocked`, `approved` and `note`. |

```bash
curl -X PUT -H "Authorization: Bearer $BEACON_API_KEY" -H "Content-Type: application/json" \
  -d '{"paused":true,"pausedUntil":null,"excludedNodes":[]}' \
  https://beacon.example.com/api/v1/admin/polling/state
```

- Pausing tells every observer to stop. Set `pausedUntil` to an epoch millisecond time in the
  future to pause until then, or `null` to pause until you resume. `polling.paused: true` in the
  config pauses regardless of what the route says.
- Excluded repeaters (at most 16, 64 hex characters each) are never polled. `polling.excluded_nodes`
  and the route's list are added together.
- A blocked observer is ignored. Beacon drops its claims and readings, its owners answer is empty
  and its policy has `observer_blocked: true`, so the device stops. Unblock it by setting
  `blocked` to `false`.
- `approved` is stored for a later release and changes nothing now.
- Runtime changes survive a restart. They live in the database, not in `config.yaml`.

## Troubleshooting

- **The device polls nothing.** No MQTT slot on the device matches `mqtt_hosts`. Compare the
  host in the slot with the list, and set `poll.slot` if needed.
- **The device acts like it never got a policy.** Open
  `https://<your-domain>/api/guest-polling/policy` in a browser. It must answer `200` with
  `"reading_format":"telemetry"`. A `404` means the proxy is not forwarding `/api/*`, and the
  device then switches to a mode Beacon does not support.
- **Readings stop arriving.** A claim expires 65 minutes after Beacon received it, and an
  observer refreshes it every 30 minutes. If the observer is offline or its broker link is down,
  its readings are dropped as soon as the claim expires.
- **Readings arrive but are not stored.** Readings need a live claim from the same observer that
  lists the repeater. Check the observer sent a claim after its last `poll add`, and that it is
  not blocked.
- **Everything is paused.** Check `polling.paused`, then `GET /api/v1/admin/polling`.
- **An old firmware is refused.** If `polling.min_client_version` is set, the policy tells
  observers below it that `version_ok` is false.
