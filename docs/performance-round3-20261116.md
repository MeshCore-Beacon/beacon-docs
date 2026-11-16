# Beacon live updates and background reads — 16 November 2026

This follows the [resource lifetime handoff](https://canadaverse.org/beacon-dev/performance-round2-20261116.md).
Five behavior fixes/improvements and one source-comment correction remain small,
separate draft PRs to `dev`. The preview is qualified as a distinct composition;
no combined implementation PR or release version/date is assigned to the org.

## Review units

| Area | Draft | Change | Release class |
| --- | --- | --- | --- |
| Live message formatting | [Server #333](https://github.com/MeshCore-Beacon/beacon-server/pull/333) | Construct optional resolved/keyed JSON variants only for connection option classes that request them. Preserve a base payload for safe in-flight fallback. | Patch |
| Analytics transport | [Web #228](https://github.com/MeshCore-Beacon/beacon-web/pull/228) | Forward the already-consumed query cancellation signal through eight statistics API helpers; discarded queries no longer leave their HTTP reads running. | Patch |
| Selected neighbors | [Web #229](https://github.com/MeshCore-Beacon/beacon-web/pull/229) | Forward cancellation from node details, Map and the neighbor graph while preserving shared active consumers and completed cache. | Patch |
| Map telemetry views | [App #42](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/42) | Stop telemetry HTTP/label refresh scheduling beneath covered routes and reject obsolete retries/results after visibility or region/server changes. | Minor: native telemetry is unreleased |
| Native chart reads | [App #44](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/44) | Suppress periodic and parameter-triggered HTTP reads while hidden/inactive; perform the latest eligible deferred read on return. | Patch |
| Polling default comment | [Server #331](https://github.com/MeshCore-Beacon/beacon-server/pull/331) | Correct the stale `approved` default comment to match the existing `all` resolver and operator documentation. Actual policy is unchanged. | Minor: documentation for native telemetry |

## Evidence and contracts

### Backend formatting

Database path-hash resolution, route/capability detection, endpoint resolution,
persistence and REST evidence remain unconditional and unchanged. Only the
live-display transformation and optional JSON serialization are gated. The hub
maintains exact option-class counts and publishes one atomic demand snapshot;
ingestion acquires no new lock. A resolved-only client plus a key-only client does
not require the combined path-and-key representation unless a client requests it.

A configure change between construction and fan-out can leave a newly interested
client with the safe base fields for an in-flight event. It must never receive
unrequested observer keys or fabricated resolution. Regression coverage includes
exact mixed-class demand, repeated configure, registration/removal bookkeeping,
privacy and transition fallback. The preview retains the separately reviewed
FIFO lifecycle fix [#330](https://github.com/MeshCore-Beacon/beacon-server/pull/330);
refresh overlapping hub changes against accepted dev when merging.

Controlled local 12-hop fixture results (Windows/amd64, three samples,
`GOMAXPROCS=1`):

| Delivery demand | Before bytes / allocations per event | After |
| --- | ---: | ---: |
| Plain | 7,808 / 53 | 800 / 2 |
| Key only | 13,056 / 69 | 1,728 / 4 |
| Resolved only | Required resolution retained | Allocation cost unchanged |

Plain-case median formatting time was approximately 15.5 µs to 2.5 µs. These are
bounded synthetic formatting measurements, not whole-ingestion, SQL, production
throughput or capacity claims. Actual benefit depends on subscriber demand.

### Browser cancellation

Before the fix, Analytics' readiness wrapper already consumed the query signal:
unmounting discarded the query result, but eight builders failed to pass the
signal to HTTP. Tests distinguish query cancellation from actual transport abort,
while retaining readiness gates, scope, time windows, rankings and limits.
Never-observed intentional prefetch and shared/completed cache behavior stay covered.

The neighbor fix covers all three production callers. A second active subscriber
keeps the shared read; changing selection or removing the final consumer cancels
unfinished work. Completed cached data remains reusable. This is not a claim
that every disabled query observer is removed.

### App refresh eligibility

The map reproduction made two unnecessary HTTP refreshes during eleven simulated
minutes under an opaque route. A separate 503-retry reproduction showed an old
request running after a newer refresh: three calls instead of two. Visibility and
request-generation checks prevent those obsolete reads/results, preserve cached
measurements and update label age when the map becomes visible again.

The shared chart fix covers periodic and hidden parameter/API changes, initial
inactive mounts, disposal and cached-404 behavior. Its small timer may remain
scheduled while HTTP is suppressed; do not infer that all hidden work, timers,
CPU use or battery cost is eliminated. Deferred refreshes are coalesced rather
than replaying every missed interval. These changes do not alter RF polling,
telemetry enrollment, server policy or base live event delivery.

Native telemetry remains disabled by preview policy. Its new coverage is fixture
and lifecycle testing, not a claim of live RF/device collection acceptance.

## Qualification and recovery

The qualified preview and app fork identify:

| Target | Source | Qualification |
| --- | --- | --- |
| Preview server | `821a76dc90d0` | [Full CI](https://github.com/n30nex/beacon-server-contributions/actions/runs/43894060599), PostgreSQL endpoints/plans, backup/recovery, hub/ingest/WS race checks and exact ARM64 artifact/source |
| Preview web | `bf872c6e1c7c` | [Full CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/43894938078): **2,272 tests / 216 files**, exact Actions bundle and **85 public assets** plus source archive |
| App fork dev | `340be6c28ef9` | [Full CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/43897816432): **899 tests**, 16 optional screenshot tests skipped; **108 combined targeted tests**, analysis and exact Android artifact/signature/checksum |

The actual public site passes **36 page checks** across English/French, desktop
1440 × 900 and touch/mobile 390 × 844, including Atlas persistence. No application
errors, failed API responses or horizontal page overflow were recorded. The
existing CSP still blocks Cloudflare's optional injected analytics; it was not
weakened to silence that notice.

Four delayed-read scenarios reproduce the old failure and now pass on the public
build: leaving a mounted Analytics Mesh view and closing node details, each on
desktop and mobile. The real underlying fetch is aborted. Intentional prefetch,
shared consumers and completed cache have separate regression coverage. CSV and
contact exports remain usable without additional node reads.

Real live-map traffic exercises resolution opt-in, language/region/style changes,
Play/Stop, navigation/return and reduced-motion visits. Sampled animated-source
work remains within the existing 30 Hz budget and stops on Stop/navigation.
This is bounded browser acceptance, not physical GPU/battery measurement.

Public backend identity, source archive, both MQTT connections, malformed filters
and ordinary API/statistics reads pass. Four fresh native-ticket profiles—plain,
resolved, key-only and both—receive their requested representations, exclude
unrequested key/path fields, unsubscribe, exchange ping/pong and close normally.
Only counts are retained; no packet contents or RF transmissions were used.
The native Dart client also connects successfully to the updated preview.

The native telemetry feature remains off on preview, so its visibility/retry
acceptance is fixture-based rather than live RF collection. No dev/dev1/live
deployment or org merge occurred. Configuration/credentials, schema, retention,
historical data, inactive radio services and unrelated containers are retained.
Normal ingest continues; healthy replacement does not prove universal losslessness.

The app artifact is a debug build with a different signing certificate from its
predecessor. It is not an in-place upgrade promise; no device installation,
physical OS lifecycle/battery test or signing-secret change occurred. The final
composition retains prior Stopwatch, visibility, base-stream and UTF-8 behavior.

### Recovery

From `/opt/canadaverse/beacon-dev-20260906`, restore web first and backend second
if needed:

```sh
sudo python3 evidence/performance-round3-20261116/web-runtime/deploy-web.py rollback
sudo python3 evidence/performance-round3-20261116/backend/deploy-server.py rollback
```

Web checkpoint **performance-round3-web-20261116T153733Z** restores `f25a9a45d95c`
while retaining the new server. Backend checkpoint **round3-server-20261116T153610Z**
then restores `b241a3457ce6`, preserving the current web and data. Exact recovery
copies and identity checks are retained; no database downgrade or live rollback
rehearsal was performed.

## Maintainer handoff

Review each proposal separately, preserve the final composed visibility callbacks
and Stopwatch behavior, and rerun regressions after overlapping PRs land. The
native telemetry and its documentation correction belong with that feature's minor
release; the other changes are patch candidates. Maintainers own release numbering
and signed release acceptance.

Stable app signing/package/version policy remains an explicit gate under
[App #33](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33).
Do not equate a debug APK, a fixture benchmark or healthy preview endpoints with
physical-device or production-load acceptance.
