# Repeater polling

Some observers can ask nearby repeaters for their battery, uptime, noise floor and packet
counters, and publish the answers. Beacon decides which observer asks which repeater, so two
observers that both hear a repeater do not both spend airtime on it, and stores the readings.
Polling is off by default.

This page is for an operator who runs Beacon and for someone who owns an observer. Beacon only
coordinates and stores. It does not talk to repeaters itself. Users can also ask for a repeater to be polled that no owner set up, see
[Requested telemetry](telemetry-requests.md). See [Seeing the readings](#seeing-the-readings)
for where the readings show up.

## How it works

1. The owner sets a repeater as a target on the observer. The observer can poll direct
   neighbours only, up to 8 targets.
2. The observer asks Beacon for its policy (`GET /api/guest-polling/policy`) and its owners
   answer (`GET /api/guest-polling/owners`). Until it has a policy it neither polls nor reports.
3. The observer publishes a claim to the MQTT broker, listing its targets and how its last
   polls went.
4. Every minute Beacon ranks the observers that claimed each repeater. Observers it saw hear the
   repeater's zero-hop adverts in the last 24 hours (advert evidence) come first, by mean SNR,
   then by number of adverts. Observers without evidence come after, by the signal they claim.
   One observer is the poller. The others are standbys. With `polling.authority: approved` only
   observers you approved take part (see [Trust](#trust)).
5. The observer reads its role from the owners answer. The poller asks the repeater when the
   newest reading is older than the poll window. A standby waits the window plus one grace period
   for each rank, so it only polls if the poller has not.
6. The poller publishes the reading to the broker. Beacon stores it. The next owners answer
   carries the new reading time, which tells every observer the repeater is fresh. Only readings
   from a ranked observer with advert evidence, poller or standby, move that time. A poller
   without evidence still polls, but its readings do not hold the standbys back.

Evidence comes before health. An observer with advert evidence always ranks above one without,
even when it reports misses. Within each group, an observer that reports 3 or more misses in a row
for a repeater ranks below every healthy one, and a healthy poller keeps the job unless another
healthy observer with evidence beats it by 3 dB. So a poller that stops getting answers hands over
to another observer Beacon has heard the repeater through, and takes the job back once it recovers
and is the stronger signal. An observer without evidence never takes the job from one with it.

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

### An RSA certificate for the devices

Observers and pollers run on ESP32 chips, which verify an RSA certificate chain much faster
than an ECDSA one. On the project's test server the polling firmware needed 9.5 to 9.9 seconds
of its 12 second limit for the HTTPS request against the default ECDSA P-384 chain, and an RSA
certificate fixed it. Serve an RSA certificate on the host observers put in `poll.url`. The
same reasoning applies to the MQTT brokers they connect to, though that was not measured. For
Caddy, see [RSA certificate for observers](reverse-proxy.md#rsa-certificate-for-observers).

## What an observer owner does

The device must be an ESP32 board with PSRAM running the MeshCore repeater observer firmware
with repeater polling, with the MQTT bridge on, publishing to a broker Beacon reads. The polling
firmware is in the [observer flasher](https://observer.gessaman.com): pick the version tagged
`-poll` when you flash. It is a test build and is still in testing. The room server firmware has no polling. On the device:

```text
set poll.url https://beacon.example.com
poll add <repeater public key>
set poll on
```

- `poll.url` is the Beacon site, with `https://` and no path. Changing it makes the device wait
  for a fresh policy before it polls again.
- `poll add` takes the repeater's 64 character public key, or a key prefix that matches exactly
  one neighbour the device has heard. Repeat it for each repeater, up to 8. The repeater must be
  a direct neighbour that the observer heard in the last day. The observer never floods to reach
  one. The firmware's neighbour table holds repeaters only, so this build cannot poll a room
  server.
- The device logs in to the repeater as a guest. It tries a blank password, then `hello`. For a
  repeater with another guest password run `poll pw <key> set <password>` (1 to 15 printable
  characters); that is then the only one tried. `poll pw <key> auto` goes back to blank and
  `hello`. Never give it an admin password.
- If a repeater answers the login with admin access, the device stops polling it, discards a
  password you set, and removes the access it was given. The repeater stays stopped, across
  reboots, until you run `poll enable <key>`.
- `set poll.slot` is optional. It names the MQTT slot the device uses when it has several. Leave
  it out and the device picks the slot whose host is in Beacon's `mqtt_hosts`.
- Beacon's window (`polling.direct_window`, sent to the device as `direct_s`) is the shortest
  time between polls of one repeater. The device's own `set poll.interval` (30 to 1440 minutes,
  default 60) can only make it slower. With `direct_window: 30m` a device still polls hourly
  until its owner runs `set poll.interval 30`.
- Nothing is polled until the device has set its clock from NTP after a boot.

To check it works: `get poll` shows the switch, the mode (`telemetry` with Beacon), the slot,
the target count and the clock. `get poll.status` has one line per target with its last result,
and `get poll.status <n>` the details of target n. `poll now <key>` sends one poll right away,
at most once a minute per target.

## What Beacon stores

| Data | Kept for |
|---|---|
| Each observer's latest claim and its target list | Used while the claim is under 65 minutes old. Removed 24 hours after it was received. |
| Who polls and who stands by for each repeater | Rebuilt every minute. |
| Readings: battery, temperature, the repeater's counters, raw sensor bytes and which observer sent them | `polling.reading_retention`, 31 days by default. |
| Operator flags per observer | Until you change them. |

A reading is stored once per repeater, observer and sample. The same reading arriving twice, for
example over two brokers, is ignored. Beacon also keeps:

- at most one new reading per observer, repeater and method every 5 minutes,
- at most 120 readings per observer in any hour, across all its repeaters,
- at most 8 readings in one message.

A claim can list at most 32 repeaters, and a claim that arrives less than 30 seconds after the
same observer's last one is dropped. These limits still hold when two messages from one observer
arrive at the same moment, for example over two brokers, because Beacon checks them as it stores
each one. The firmware stays well inside all of them. Anything over a limit is dropped, not queued.

Beacon also counts how many other observers heard the repeater's reply, using the reading's
8-byte `packet_hash`. A hash of any other length is ignored and the reading is kept without it.
That count is informational. A reading is never refused for lacking it.

Beacon accepts a reading only when all of these hold:

- The topic key and the message's `origin_id` are the same observer.
- That observer has a claim under 65 minutes old that lists the repeater.
- `sampled_at` is at most 1 minute ahead of Beacon's clock and not older than 2 hours.
- The observer is not blocked.

## Seeing the readings

With polling enabled, a repeater's or room server's detail view in Beacon Web and in the mobile
app shows charts of its readings. An Atlas card for a repeater that is polled, or that has
readings from the last 30 days, gets a Telemetry tab with four tiles, see
[Atlas](atlas.md#the-tab-a-card-opens-on). With polling off, none of them appear. Beacon stores
and shows readings for room servers too, but the current polling firmware polls repeaters only.

Only trusted readings are charted. A reading is trusted when its observer was assigned to the
repeater and Beacon had itself heard the repeater directly through that observer when the reading
was stored. Readings from any other observer are kept but left out of the charts. To see them,
call the API with `include=untrusted`, for example
`/api/v1/nodes/{nodeId}/telemetry?range=168h&include=untrusted`. The answer also says how many
readings it left out. See the [API contract](api-contract.md#node-telemetry).

A Poller tag means a stored claim exists for that observer, whether or not it is assigned a repeater. The hourly cleanup removes a claim about a day after the last one received, and the tag goes with it. Claims from a blocked observer are not stored. An observer blocked after claiming keeps the tag until its claim is cleaned up. With polling off no new claims are stored, so existing tags clear within about a day. The API carries it as `isPoller` on nodes, and `GET /nodes` takes `poller=true|false`.

A gap in a chart means there is no usable value for that series in that bucket. The cause can be the poll cadence (status values arrive every few hours), a field the repeater does not report, a counter that was inconsistent and was dropped, or a missed poll. It does not mean the repeater was down.

## Pause, exclude and block

The admin routes need the [admin API key](configuration.md#admin-api-key). They exist only while
`polling.enabled` is true and the server is not [read-only](configuration.md#read-only-mode).
Otherwise they answer `503`. The same shapes are in the [API contract](api-contract.md#admin).

| Route | What it does |
|---|---|
| `GET /api/v1/admin/polling` | Returns the pause state, the excluded repeaters and every observer with a flag set. `paused` turns `false` once `pausedUntil` has passed. `configPaused`, `configExcludedNodes` and `authority` show `polling.paused`, `polling.excluded_nodes` and `polling.authority` from the config. |
| `GET /api/v1/admin/polling/targets` | Lists up to 500 repeaters, newest claim first, with every observer that claims each one, its rank (`null` when it has none), its advert evidence, whether you approved it, its state and misses, and the newest trusted and newest overall reading times. Use it to see who polls what. |
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
- Excluded repeaters (64 hex characters each) are never polled. `polling.excluded_nodes` and the
  route's list are added together, and the two may name at most 16 different repeaters, which is
  all the firmware takes. A `PUT` that would go over answers `400` and changes nothing. A key
  already in the config adds nothing to the count. If you later add keys to the config and the
  two lists go over 16, Beacon sends only the first 16, config first, and logs the error
  `polling exclusions do not fit the policy` each time it builds a policy. Shorten one of the
  lists.
- A repeater that is also an observer, with status sent in the last 7 days, is not polled. It
  reports its own readings over MQTT.
- A blocked observer is ignored. Beacon drops its claims and readings, its owners answer is empty
  and its policy has `observer_blocked: true`, so the device stops. Unblock it by setting
  `blocked` to `false`.
- `approved` matters only with `polling.authority: approved`. Then only approved observers can
  be elected. See [Trust](#trust).
- Runtime changes survive a restart. They live in the database, not in `config.yaml`.

## Trust

Claims and readings are statements by whoever runs the observer. Beacon authenticates them only
through that observer's broker login and the topic it publishes on. An owner could claim a
repeater the observer cannot hear, or publish made-up readings.

Beacon ranks observers on advert evidence: the repeater's zero-hop adverts it saw the observer
hear. That evidence also comes from the observer, through its own packet uplink. An owner who
captures a real advert and republishes it as heard directly, with a good signal, can make up
evidence. So evidence guides ranking but is not proof.

With the default `polling.authority: evidence`, anyone who runs an observer can be elected, and
an observer with made-up evidence can become the poller or a trusted standby and hold others
back. Use it where you know the observers. Set `polling.authority: approved` when you do not want
unknown observers to coordinate, then approve the ones you trust with
`PUT /api/v1/admin/polling/observers/{publicKey}`.

In `approved` mode an observer you have not approved:

- can still send claims and readings. They are stored and attributed to it.
- can still poll its own repeaters. Where an approved observer polls the repeater it is told to
  wait last in line. Where no approved observer claims the repeater it is told to poll.
- is never elected poller or ranked standby, and its readings never count toward the reading time
  that stands other observers down. It cannot hold anyone back.

Approval is checked when a repeater's election runs. Elections are scheduled every minute, so
new answers from Beacon normally stop trusting the observer within about a minute, once an election
has succeeded. Devices that already fetched an answer keep acting on it until their next successful
refresh, which can be ten minutes or more. Until its old assignment is replaced, that observer's
readings can still count toward the newest reading time. Blocking an observer takes effect on its
next message, and is the faster remedy.

`polling.authority` governs observers polling their own targets. Requested repeaters have their own
setting, `polling.request_observers`, which defaults to `all`: any observer with advert evidence for
the repeater can be handed it and its guest password. Set it to `approved` and only observers you
approved are. See
[Approve observers](telemetry-requests.md#approve-observers).

In both modes:

- An observer without advert evidence never outranks one with it, and its readings never stand
  anyone down.
- Claims and readings are rate limited and capped in size per observer, including an hourly
  limit on readings across all its repeaters.
- Each reading records how many other observers heard the repeater's reply. It is not checked
  against anything, but a reading nobody else heard is worth a look.

The remedy for an observer that misbehaves is to block it (see above). Its claims and readings
are then dropped, and the election moves its repeaters to other observers.

## Troubleshooting

- **Nothing from the observer is stored at all.** The observer's IATA code is outside the
  ingest filter. The filter drops claims and readings as well as packets. Add its country to
  `ingest.allow_countries` or its code to `ingest.allow_iatas`, then restart.
- **The device polls nothing.** No MQTT slot on the device matches `mqtt_hosts`. Compare the
  host in the slot with the list, and set `poll.slot` if needed. `get poll` on the device shows
  the mode, the slot and whether the clock is set. Nothing is polled before the clock is set
  from NTP, and a repeater the device has not heard directly in the last day shows `not_direct`
  in `get poll.status`.
- **The policy request times out.** The device has 12 seconds for it, and an ECDSA certificate
  chain can use nearly all of that on an ESP32. See
  [An RSA certificate for the devices](#an-rsa-certificate-for-the-devices).
- **The device polls but the charts stay empty.** Only trusted readings are charted, and a
  reading is trusted only when its observer was assigned to the repeater and Beacon had advert
  evidence for the pair when the reading was stored. `GET /api/v1/admin/polling/targets` shows
  each observer's rank and evidence. Add `include=untrusted` to the node telemetry request to
  see the readings that were left out.
- **A repeater is never polled after a login.** It answered the device with admin access, so
  the device stopped. Fix the repeater's guest password, then run `poll enable <key>` on the
  device.
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
- **Standbys poll a repeater the poller already polls.** The poller has no advert evidence for
  it, so its readings do not count as fresh for the others. Once Beacon sees it hear the
  repeater's adverts directly, they do. In `approved` mode, check the poller is approved.
- **Everything is paused.** Check `polling.paused`, then `GET /api/v1/admin/polling`.
- **An old firmware is refused.** If `polling.min_client_version` is set, the policy tells
  observers below it, and observers that send no version, that `version_ok` is false. The value
  must be `X.Y.Z` (for example `1.18.0`) or empty; anything else stops Beacon at startup.
- **The device keeps its old settings.** When Beacon cannot read its database the policy and
  owners routes answer `503` with `Retry-After: 60`. The device keeps the policy and roles it
  already has until Beacon answers again.
