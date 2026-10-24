# Core performance and Atlas/Topology candidate

Review this as a paired server/web candidate before promoting it from `dev` or
`dev1` to a stable release. The collected-telemetry intake, mobile collection and
Atlas sensor cards are a separate dependent change. Basic Atlas and Topology do
not require that optional service.

See the [21 October qualification record](release-qualification-20261021.md)
for the paired drafts, exact preview build, measurements and remaining gates.

## What the core changes

| Area | Result |
| --- | --- |
| Database baseline | Retains current upstream bigint cursors, exact pagination, workload pools, route/index cleanup, regional read models and trust/recovery rules |
| First-fill work | Preserves duty pacing while bounding individual boot writes, serializing their disk work and retrying smaller ranges on statement pressure |
| Channel history | HTTP/MQTT startup no longer waits for a full historical decrypt scan. A scheduled job scans at most 500 primary-key candidates per tick, within a five-second work context, saving its cursor after successful work |
| Imported channel keys | A changed key-set fingerprint restarts the resumable history pass. Metadata changes alone do not start another scan. Backfilled messages remain historical and are not broadcast as new chat |
| Cache outage | Concurrent misses and Redis read failures share bounded database work. A canceled caller can leave without canceling useful work for other callers. Cache operations have short network deadlines and no internal retry multiplication |
| Signal quality | Missing, malformed, non-finite or out-of-range RSSI/SNR remain absent. Measured zero is retained. Stored observations, neighbor evidence and live events use the same validity distinction |
| Input work | Oversized MQTT envelopes/topics and oversized neighbor snapshots are rejected before expensive processing |
| Live stream | Control-message rates, filter lengths and active subscriptions are bounded. Every socket write has a deadline. Global queue gaps notify clients and have counters, alongside existing slow-client gaps |
| Topology | Keeps indexed minute-window route snapshots, exact node cursors, quality labels and live Public chatter. Query-plan fixtures cover global/regional windows. Animated segment geometry is reused between frames and invalidated when the camera moves |
| API failures | JSON is encoded before success is committed; known temporary query failures use the common 503/Retry-After contract |
| Provenance | `/info` keeps its API-version meaning and adds optional `buildVersion` and `buildRevision` for the actual artifact |
| Runtime image | Moves off Alpine 3.19, keeps the PostgreSQL 16 client and runs the app as UID/GID 65532 |

The history scan advances through all packet candidates, including pages without
undecrypted group text. That bounds database work rather than merely limiting
the number of matches returned. A failed page leaves its cursor unchanged;
idempotent message inserts make a retry safe. A completed pass is restored after
restart. Existing live ingest decrypts newly received messages. This job is
disabled in read-only server mode.

The core has no new database migration beyond the current 001-053 baseline.
It adds a `channel_history` entry to the existing `background_state` table.
It does not delete raw observations, rewrite old signal readings, change
retention or initiate RF traffic.

## Configure the deployment deliberately

### Cache

Set `REDIS_ADDR` in the app environment; a running Redis container and YAML TTLs
alone do not activate the reader cache. Give Redis a memory bound and an eviction
policy suitable for a disposable cache. Start with short TTLs for live-facing
data and longer reference-data TTLs, then measure freshness and hit rate:

```yaml
cache:
  ttl: 30s
  ttls:
    stats: 30s
    reference: 5m
    nodes: 30s
    observers: 30s
```

Keep ingestion invalidation and outage tests in the acceptance run. Do not
silently apply a one-hour status TTL from an older configuration.

### Pools and first fills

The default `custom_all` layout has eight API connections, two slow connections,
four maintenance connections and at least six ingest connections (one per CPU
when there are more than six CPUs). The split layout adds four API connections.
A `pool_max_conns` DSN parameter does not cap their combined total.

Reserve PostgreSQL capacity for every app instance, optional intake, backups,
migrations and operator sessions. On shared storage use the supported fill
pacing controls, for example:

```yaml
readmodels:
  fill:
    duty: 0.25
    packet_sites_slice: 100000
```

Connection separation does not isolate disk/WAL bandwidth. Observe ordinary
API latency and ingestion lag during a fill. Keep read-model trust checks;
temporary 503s are preferable to presenting incomplete regional history as
complete.

### Private measurements

Enable `server.admin_listen` only on a listener reachable through a private
network or a loopback-bound container port. Do not add `/metrics` to the public
reverse proxy. Scrape the existing metrics and the additional bounded series:

| Metric | Meaning |
| --- | --- |
| `beacon_cache_requests_total{outcome}` | Hit, miss, invalid cached value or read error |
| `beacon_ingest_rejected_total{reason}` | Input rejected for a bounded shape/size reason |
| `beacon_stream_dropped_total{queue}` | Global, per-client or best-effort repeat event drops |
| `beacon_channel_history_scanned_total` | Packet candidates examined by resumable historical decryption |
| `beacon_job_rows_total{job="channel_history"}` | Newly decrypted historical messages, distinct from scanned candidates |

Also monitor the existing pool waits, statement families, queue depth/drops,
read-model trust/age and job durations. PostgreSQL `pg_stat_statements` requires
the preload library and a planned database restart as well as the extension.
Measure `track_io_timing` overhead before enabling it broadly. Preserve reset
timestamps when comparing counters. Never expose raw query values or message
contents in metric labels.

### File ownership and privileges

The candidate image runs as `65532:65532`. Before updating, check mounted
configuration, borders and any enabled backup/export directories. Configuration
must be readable by that user; directories the application must write need
explicit ownership/permissions. Keep secrets private and preserve a rollback
copy. Do not make all mounts world-writable to work around an ownership error.

Database privilege separation is a distinct operator task. The existing normal
boot/maintenance path performs schema/index work, so replacing its superuser
with a DML-only role without a migration/maintenance ownership design is not a
qualified deployment. Test the intended role model on a restored copy. The
candidate does not automatically revoke roles or edit production credentials.

## Preserve honest data contracts

- Raw observations, unique stored packets, broker reports and radio counters
  have different grains. Keep their labels and reset/window semantics distinct.
- A missing signal is not zero. Clients must tolerate absent `rssi`/`snr` in live
  observation events, just as retained observations can have missing readings.
- Prefix matches and plausible geography are not proof of a physical route.
  Keep TRACE warnings, original wire values and the optional questionable-evidence
  view. Unvisited requested hops must not become observed edges.
- Topology gaps are notices to refresh/reconcile authoritative state. A healthy
  WebSocket and QoS1 subscription do not establish lossless persisted ingestion.
- Atlas's recent-report chart is a labeled sample, not a complete lifetime or
  24-hour total. Optional telemetry must not be required for basic cards.

## Qualify the exact paired candidate

1. Record server/web revisions, trees, config hash, schema journal and artifact
   hashes. A source branch or container tag alone is insufficient provenance.
2. Run build, vet, unit/race tests, PostgreSQL integration, plan policy/corpus,
   backup checks, and web lint/tests/build against the combined heads. Test
   signal null/zero, interrupted history pages, cache failure/cancellation,
   stream control limits/global gaps and Topology exact boundaries.
3. Use separate disposable databases for functional tests and the large plan
   fixture. Concurrent index creation can wait for older snapshots even when
   another fixture is loading different tables in the same database.
4. Rehearse 2.0.x-to-2.1 migration/recovery on a representative restored copy.
   See [Upgrading](upgrading.md). Schema 053 is not compatible with an image-only
   rollback to an older application expecting the removed route stamp.
5. Exercise global/regional packet/message pages, observer comparisons, saved
   Atlas cards, Topology 15m/1h/24h, TRACE evidence and live reconnection. Test
   cold and warm caches separately and preserve camera state during refresh.
6. Record a maintenance-cycle soak with API latency, input acceptance/lag,
   database WAL/temp work and model trust together. Synthetic plan checks are
   not a production throughput benchmark.

A read-only audit of the prior preview measured a 24h snapshot at about four
seconds cold and tens of milliseconds for the same cached window. This is a
baseline, not a promised universal latency or an FPS measurement. The updated
renderer keeps moving cores, glow and chatter while avoiding repeat geometry
work; test on the intended devices before claiming an interaction/FPS gain.

## Keep optional collection separate

The telemetry draft stack adds companion enrollment/collection, optional intake
proxy/history/availability and sensor cards. Its mobile and headless clients
must use a shared receipt and RF-budget contract. A signed companion challenge
is key-possession evidence, not hardware attestation or proof that a report is
truthful. Completing that optional stack is not a reason to delay a verified
standalone bigint or backend reliability fix.

Production rollout, final acceptance, workload-specific SLOs, an off-host
restore/RPO/RTO drill, and physical mobile overnight collection remain explicit
release gates. A draft PR or successful CI run does not close those gates.
