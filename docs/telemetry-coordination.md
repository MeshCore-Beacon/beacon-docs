# Coordinated community telemetry (draft)

This optional layer shares a polling budget and accepted readings between clients
of one Beacon intake. Basic Atlas and Topology do not require it. It is not a
worldwide RF lock: independent instances, older clients and modified radios do
not share the same authority. Key possession is not hardware attestation.

## Client behavior

The Flutter collector uses its existing BLE/Wi-Fi connection, local credentials,
Android background choice and signed HTTPS enrollment. It must receive an
unexpired permit before any repeater RF command. An unavailable endpoint, denied
request or malformed response cannot fall back to independent polling.

- User intervals stay **1–72 hours**. An issued attempt consumes the cooldown even
  if the client disconnects, crashes, fails to transmit or receives no reply.
- The intake serializes reservations by the full repeater key across enrolled
  clients. Radio budgets remain at most two attempts, six reserved RF commands
  per rolling hour and one minute between attempts. Local persisted reservations
  and the existing queue/airtime checks remain necessary.
- Claims settle for 20 seconds and expire after 90 seconds without renewal.
  Selection penalizes unanswered expired attempts, then prefers fewer reported
  route hops, recent successful readings and stable tie-breakers. It does not
  infer geographical proximity or guarantee bidirectional radio reachability.
- A fresh accepted reading suppresses another poll. Backups wait through the
  elected attempt's full interval; there are no immediate failure retries.
- **Direct / one hop** is the new default. Unknown routes and visible relay-prefix
  collisions are skipped. Route checks preserve 1/2/3-byte hash widths. Unexpected
  flood SEND receipts stop subsequent commands. Repeater replies can still flood.
- **Allow discovery** retains the earlier flood-first behavior as an explicit
  option, with the same permits and budgets. Flood discovery cannot guarantee a
  one-hop or three-hop propagation cap.

Old signed reports/outboxes and retained history remain compatible. Older clients
that do not request a permit must not be described as coordinated. The retired Pi
polling worker and RemoteTerm remain disabled on Canadaverse; the independent
intake stays running for Flutter and retained history.

## Signed API

Paths below are relative to the chosen `<instance>/api/v1/node-telemetry`.
Enrollment remains automatic through `/challenge` and `/enroll`; no operator
approval is needed for each client. HTTPS is required and redirects are rejected.

Control writes use `{authorization, payload, signature}`. `payload` is base64 of
the exact JSON bytes; `signature` is hex Ed25519 over the operation's domain
prefix followed by those bytes. Session identity and all bound request fields
must match. These signatures cannot be substituted for ordinary report signatures.

| Endpoint | Signature prefix | Payload |
| --- | --- | --- |
| POST `/polls/permit` | `BEACON-POLL-PERMIT-V1\n` | schema 1; UUID requestId; instance, collectorKey, radioKey, nodeKey; intervalHours 1–72; commandBudget 3 or 4; routeMode nearby/discovery; hops -1 (unknown) or 0–3; issuedAt in epoch ms |
| POST `/polls/expect` | `BEACON-TELEMETRY-EXPECT-V1\n` | instance and enrolled identities; permitId, nodeKey; requestKind 1 (status) or 3 (environment); requestTag; replyKeySeed; issuedAt in epoch ms |
| POST `/polls/heard` | `BEACON-TELEMETRY-HEARING-V1\n` | instance and enrolled identities; hearing with observerKey equal to radioKey, receivedAt in epoch ms and raw RESPONSE packet in hex |

`\n` denotes one newline byte in the signing prefix. Keys are full lowercase
64-hex identities, never one-byte prefixes. No repeater password or primary radio
private key belongs in an ordinary report or permit request.

A granted permit echoes the request binding and returns issuedAt, expiresAt
(no more than five minutes) and nextAllowedAt (the full requested interval).
Request-ID retries are idempotent only for the same identity/settings. A denied
request returns allowed=false and retryAfterSeconds in 1–300. The client validates
the response, persists its own reservation and checks expiry before RF. New
reports retain the permit UUID as permitId; delayed delivery does not renew it.

## Reusing observer replies

This extension is for enrolled observer adapters with host-side **separate guest
identities**. Stock Flutter companion collection keeps the primary key on the
radio and reuses accepted shared readings through the permit service; it does not
export that key or change the companion's firmware identity. The CoreScope plugin
does not become a Beacon client merely by changing its server URL.

An adapter first obtains a nearby permit with commandBudget=4, reserving login,
return-route teaching, status and environment commands. The six-command hourly
budget therefore cannot fit a second such attempt. It registers the exact request
before transmitting. The requestTag must be the fresh UTC-seconds tag that
MeshCore echoes; requestKind identifies the exact expected payload. replyKeySeed
is a separate 32-byte guest seed in hex. Keys matching enrolled primary identities
are rejected. Password/admin exchanges must continue through the ordinary private
companion path, never under this shareable guest identity.

The intake derives a per-target ECDH secret, holds it only in memory until permit
expiry and neither stores nor returns the seed. At most one request of each kind
is registered per permit, with 512 pending requests maximum. A restart forgets
decryption material while retaining RF cooldowns. Registration never transmits RF;
the adapter must still enforce its command budget, route and congestion rules.
Allow at least relayWarmupSeconds before transmitting when relying on observers.

Received RESPONSE packets are considered only against active registered requests.
Acceptance requires exactly one full-key/secret/tag/type match and bounded,
well-formed measurements. A short hash, short MAC or plausible voltage alone is
insufficient. Ambiguous matches and unsolicited, stale, malformed or replayed
responses are discarded. The same payload hash cannot create another permit's
reading. Multiple observer receptions produce one sample with bounded heardBy
evidence and packet hashes. Channel-2 environmental readings retain their channel.
Atlas labels these as shared replies; attribution does not prove sensor truth.

## Beacon MQTT relay

Enable only for configured brokers that authenticate observers and enforce
publisher/topic identity:

```yaml
node_telemetry:
  gateway_url: http://beacon-collector:8090/api/v1/node-telemetry
  observer_replies: true
```

Keep matching random 32-byte hex credentials in the private server environment
(`BEACON_TELEMETRY_RELAY_TOKEN`) and intake environment
(`COLLECTOR_OBSERVER_TOKEN`). Use HTTPS when crossing hosts/untrusted networks.
These are backend service credentials, not mobile or participant credentials.
Do not commit them, put them in a public example or send them over MQTT.

The relay reuses Beacon's existing `/packets` MQTT subscriptions. It forwards only
RESPONSE packets matching expiring interest prefixes, using a 128-entry queue,
eight-packet batches and two-second HTTP deadlines. It adds no synchronous HTTP or
database work to packet ingestion and never performs RF or retries an RF command.
Outages/queue pressure can lose a supplemental hearing without blocking the normal
feed. Existing packet counts/routes are not incremented again by telemetry intake.

`GET /internal/interests` and `POST /internal/replies` require the private relay
token and are excluded from Beacon's public proxy allowlist. Independently enrolled
receivers can use the signed `/polls/heard` contract instead. Unsigned legacy
CoreScope `/battery` and `/polling` payloads are not silently treated as authenticated
Beacon samples or permissions.

## Storage, rollout and acceptance

The separate intake adds permits, claims, correlated parts and reception evidence
in journal version 2. Beacon core needs no schema migration. Existing telemetry
rows and the 30-day history contract remain intact. Pending claims expire; permits
are retained beyond their cooldown/delayed-upload window, with indexed bounded
cleanup. Failed or ambiguous writes do not authorize RF.

Deploy the compatible intake and Beacon proxy before installing the new app.
Preserve the prior application/intake binaries, private configuration and an
independently verified database backup. Older code can continue reading historical
samples with the additive tables retained; a database reset is unnecessary.

Automated acceptance must cover concurrent clients, restart/clock/session failures,
1/72-hour bounds, route ambiguity, denied/unavailable permits with zero RF,
report replay, duplicate observers, short-hash ambiguity, channel 2 and restored
history. Physical BLE/Wi-Fi polling, screen-off behavior and a real observer-adapter
recovery remain separate qualifications. Synthetic traffic must use a disposable
database, not the public preview's histories.

Design references: [Observer Plus](https://github.com/A13xB0/corescope-observer-plus)
and [ScotMesh polling election](https://github.com/A13xB0/CoreScope/blob/3280984a4f40463d33e283e58fdb78a6999d7a19/cmd/server/polling_election.go).
This implementation uses Beacon's existing intake and MeshCore protocol library;
it does not copy private Collector source into the public Beacon repositories.
