# Optional companion telemetry collection

Enable this alongside the core performance, basic Atlas and Topology candidate
only when the intake service and client qualification are ready. Basic Atlas,
Topology and ordinary observer telemetry continue to work without it.

## Components

| Component | Responsibility |
| --- | --- |
| Beacon Flutter app | User-selected BLE or Wi-Fi/TCP companion, saved repeater selection, optional local password/admin requirement, polling budgets and signed delivery |
| Beacon server | Optional bounded proxy and `/info` capability for the selected instance |
| Telemetry intake | Automatic enrollment validation, sample validation/deduplication, quotas, separate storage, retention, history and availability |
| Beacon web | Repeaters-with-telemetry filter, attributed battery/environmental series and explicit gaps/partial history |
| Headless Collector | Alternate polling client for unattended USB/BLE use; it uses the same intake contract |

The app replaces the user-operated polling client, not the intake/storage service.
The current intake is packaged in the separate Collector project. The org
`beacon-agent` scaffold is not a deployable replacement for that implementation.
Software distribution/access for the alpha is separate from client enrollment:
there is no per-user operator approval list.

## Enable an instance

Run intake with its own PostgreSQL database. Its canonical `COLLECTOR_INSTANCE`
must equal the HTTPS Beacon URL the app selects, including any installation
subpath and excluding a trailing slash, query string or credentials. A session
issued for the Canadaverse preview is not a session for another Beacon instance.

Point the optional server setting at the intake over the private service network:

```yaml
node_telemetry:
  gateway_url: http://collector:8081/api/v1/node-telemetry
```

Replace `collector` with that deployment's actual private service hostname. The
public client uses the Beacon instance's existing HTTPS API. The core proxy
accepts only the enrollment/report/read routes, bounds bodies/responses/deadlines,
does not follow redirects and does not forward caller cookies or authorization
headers. Set the intake's trusted proxy CIDR to the core app's actual private
peer address; never trust a caller-provided forwarding header unconditionally.

When configured, `/api/v1/info` includes `collectedNodeTelemetry: true`. This is
a capability statement, not an assertion that every companion or sensor is
currently healthy. If intake is disabled, optional history is unavailable and
basic cards still work. A configured service failure must remain a visible,
retryable error rather than an empty successful collection.

## Client workflow

In the app, select the Beacon instance, open Telemetry sharing, connect the
companion, choose saved repeaters and an interval from 1 to 72 hours. Optional
repeater/admin passwords stay on the client. The companion private key is never
exported. First use starts with flood discovery; subsequently learned routes are
used within the client's hop/congestion policy. Environmental decoding preserves
channel numbers, including channel 2, and explicit zero values.

The mobile client reserves attempts before transmitting, applies a shared
two-attempt/six-command hourly companion budget and checks airtime/queue state.
An interval is a minimum; selecting more nodes can make the effective interval
longer. Upload retries resend the same saved report and do not poll again.
There is no automatic burst to catch up missed RF intervals.

For Android, background collection is an explicit remembered choice. The
connected-device service has an ongoing notification with Stop/Disconnect
actions and optional counts. Expired saved reports are counted separately from
accepted reports. Loss of the connection/process stops collection; a foreground
service is not an exact-time or uninterrupted-work guarantee. iOS collection is
foreground-only in this draft.

No global cross-instance RF lease or hardware attestation is claimed. Cooperating
clients still need coordination before a broad rollout. The server validates
key possession and report structure; public data remains attributed community
measurements rather than independently verified sensor truth.

## HTTP and MQTT acceptance

The version-1 routes are under `/api/v1/node-telemetry`:

| Method/path | Contract |
| --- | --- |
| POST `/challenge` | Short-lived instance/radio/client-bound challenge |
| POST `/enroll` | Both companion and client sign the prefixed challenge; returns an intake session |
| POST `/reports` | Validates the signed sample and returns acceptance only after storage/deduplication |
| GET `/availability` | Full node keys with retained data, 30-day retention and explicit directory truncation |
| GET `/{full-public-key}` | At most 500 retained samples, chronological output, cap/coverage metadata |

Sample IDs are idempotent only for identical validated samples. A reused ID with
different data is rejected. Session secrets currently rotate when intake restarts;
clients re-enroll and retry the same queued sample, preserving RF cooldowns.

The app uses HTTPS. The headless client's optional MQTT publish is followed by
idempotent HTTPS confirmation of the same signed sample. Broker PUBACK alone
does not remove the outbox. This protects against an unavailable consumer or an
intake rejection without adding an RF request. MQTT still needs the existing
enrollment API and appropriate topic/TLS credentials.

## History, capacity and retention

History responses include `limit`, `truncated`, `retentionDays`, `windowStart`
and `windowEnd`. A cap is not a complete 30-day history. The web labels partial
history and keeps missing measurements distinct from zero; dashed bridges are
visual estimates, not new samples. Full node keys separate identities and
collector/radio attribution keeps different sources from silently joining.

Availability is coalesced and cached for at most a minute, invalidated by new
accepted reports and retention maintenance. Concurrent first reads share one
bounded aggregation. Default intake pool capacity is four connections unless an
operator explicitly overrides it; budget these alongside core pools.

Retention runs in short minute-spaced passes, with a five-second context and at
most four indexed batches of 5,000 expired rows. Monitor the oldest retained
timestamp/backlog on larger deployments. The separate
`collector_schema_migrations` ledger records intake initialization; it is not a
core Beacon migration. Keep core and intake backup/recovery identities distinct.

## Qualification and deployment gates

Use the exact paired optional server/web commits above the accepted core stack,
the matching app branch and the identified intake build. Do not merge an older
telemetry PR wholesale over newer config, read-model or virtualization changes.

Validate signatures, instance binding, null/range handling, replay/different-data
IDs, concurrent quotas, expiry, history/directory caps, cache invalidation and
outage recovery on an isolated database. Synthetic signed samples belong in that
isolated test instance, not in the shared preview's public repeater history.

Then verify the preview's actual retained data, API proxy, web filter/cards and
normal collector acceptance without resetting RF cooldowns. Preserve the
exclusive radio lease and unrelated services during updates. Check before/after
source/binary/asset hashes, database/configuration identity and recovery copies.

Physical qualification remains separate: a real selected companion/repeater,
status plus channel-2 readings, intake acceptance, matching Atlas display, locked
screen intervals, notification actions and transport/network failure. The current
consolidation found no Android device attached, so these new physical runs are
not claimed. Build/unit/API success does not replace them.
