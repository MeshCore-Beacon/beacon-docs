# Atlas and Topology refresh — 29 October 2026

The review lane remains one paired core candidate for basic Atlas, Topology and
backend reliability, with optional collected telemetry in separate dependent
drafts. Only Canadaverse preview is authorized for deployment. Dev, dev1 and live
are not deployment targets for this refresh.

## Source composition

| Lane | Draft PRs | Qualified application head |
| --- | --- | --- |
| Core server | [#266 → dev](https://github.com/MeshCore-Beacon/beacon-server/pull/266), [#267 → dev1](https://github.com/MeshCore-Beacon/beacon-server/pull/267) | `d313983` |
| Basic Atlas and Topology | [#182 → dev](https://github.com/MeshCore-Beacon/beacon-web/pull/182), [#183 → dev1](https://github.com/MeshCore-Beacon/beacon-web/pull/183) | `4b13e3e` |
| Optional intake proxy | [#268 → dev](https://github.com/MeshCore-Beacon/beacon-server/pull/268), [#269 → dev1](https://github.com/MeshCore-Beacon/beacon-server/pull/269) | `20fe188` |
| Optional telemetry UI | [#184 → dev](https://github.com/MeshCore-Beacon/beacon-web/pull/184), [#185 → dev1](https://github.com/MeshCore-Beacon/beacon-web/pull/185) | `ccd49cd` |
| Optional Flutter collection | [#11 → dev](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/11) and matching user-fork feature branch | `9d19413` |
| Documentation | [#43 core](https://github.com/MeshCore-Beacon/beacon-docs/pull/43), [#44 optional](https://github.com/MeshCore-Beacon/beacon-docs/pull/44) | This refresh |

Core includes org server dev/main `3c5c249`, web dev/main `0bddd6d`, and docs
dev/main `f705536`. The refreshed core application branches contain dev/main and
trial-merge cleanly with dev1. Upstream sorting, pagination, scope filtering,
regional reads, observer activity, backfill/shutdown fixes, lazy assets, stream
recovery and current dependencies are retained. Flutter includes upstream dev
`82cbe9c` and its current mobile sorting, scopes, retries and map work.

The preview candidate adds its existing optional telemetry and presentation
extras above these branches: server `19636881`, web `8b16ab12`, label
`2.5.2-n30nex.1`. It is not byte-identical to the telemetry-free core PR pair.
Private Collector history is not copied into public Beacon source.

## Performance and correctness changes

- Move measured expensive graph layout into a cancellable worker. Keep the last
  completed same-region graph during refresh, discard stale worker results, and
  retain a fallback and retry state.
- Request upstream's 2,000-node pages while retaining legacy-clamp, cursor and
  total-size safeguards. New servers need up to ten times fewer node-page round
  trips; this is not a claim that every topology load is ten times faster.
- Precompute link classifications and world-space curve controls. Cull only
  curves whose entire control hull is outside the padded viewport. Crossing
  curves remain visible.
- Batch same-style static curves during camera movement, then restore original
  overlap blending after 120 ms even with no traffic. Retain packet cores, glow,
  chatter, geometry and route limits. Stationary raster cases remain unchanged.
- Keep missing SNR and RSSI separate in upstream's in-memory observer counters.
  Average each only over its own present measurements; retain legacy zero/zero
  exclusion and verify parity with SQL.
- Preserve optional telemetry filtering across the new server-sorted paginated
  node list, including matches that only appear after the first page.
- Carry Chi 5.4.0, Vite 8.3.5, Vitest 4.1.12 and patched transitive Undici/Zod.
  The refreshed web lock reports zero known npm audit vulnerabilities.

The accepted upstream `DecryptBackfill` replaces the older candidate
`channel_history` worker. Its processing is paced and deferred, but its initial
undecrypted-packet listing is not keyset-bounded. Do not repeat the old
500-candidate/five-second claim. Bounded loading remains useful follow-up work.

## Evidence and limits

- Core server native CI passes its Go/PostgreSQL, race, vulnerability and runtime
  image checks; SQLC, mocks, Swagger and plan policy were regenerated.
- Core web passes 1,615 native tests; the complete preview passes 1,657 tests.
  Builds and type checks pass. Eight shell tests were also run through Git for
  Windows after making their file paths portable.
- Flutter analysis, 396 tests, and native debug-build CI pass. This refresh does
  not qualify a physical BLE/Wi-Fi connection, screen-off collection or an app
  rollout.
- A private real preview dump was restored off-host and upgraded from schema
  053 to 061 with the exact preview server source. Counts remained 592,102
  packets, 3,100,006 observations, 1,219,170 routes, 6,062 nodes and 12,103 channel
  messages. The node-clock fingerprint was unchanged and ICU collation exists.
- A synthetic 5,000-node/10,200-link layout took 1.13–1.30 seconds on the shared
  Windows workstation before moving off the UI thread. CPU raster timings were
  noisy; the moving-camera case improved in one run while steady cases varied.
  These are not GPU/browser FPS results or a universal speedup guarantee.

Dev1 still returns 502 because its four service containers are stopped; the
stored app/web labels are `b53e3c6`/`5345519`. They were inspected read-only and
not restarted. Dev responds over HTTPS and advertises API 2.1.0, but that does not
identify its exact deployed commit. No new production runtime audit was made.

## Promotion and recovery

Review and accept the paired core PRs first, then qualify a production-shaped
restore, migration, ingest backlog and cold/warm API workload on an operator
approved environment. Measure interaction and sustained animation on target
MacBook/Windows/mobile browsers. Keep schema, source, image and browser evidence
distinct; successful merging does not establish deployment readiness.

Schema 060 allows clock-drift values that an older int32 reader may not handle.
An image-only rollback is not universally safe after new data arrives. Keep a
fresh pre-cutover dump and retain the upgraded database. The preview recovery
helper can restore the old snapshot into a separate database and start the old
app against it with caching disabled; it never overwrites upgraded history.
That snapshot has an explicit recovery-point boundary. Newly accepted traffic
remains in the retained upgraded database for forward recovery.

Basic Atlas uses ordinary node/observer/packet APIs and full public-key pins.
See [the future phone packet contract](mobile-packet-forwarding.md). The optional
Flutter draft polls telemetry; passive phone packet forwarding is not implemented
and must not be inferred from telemetry intake availability.

## Preview completion

Canadaverse now runs server `19636881` and web `8b16ab12` (2.5.2-n30nex.1),
with schema 061. Public verification matched all 94 files, including compressed
assets, and both corresponding-source archives. Both MQTT brokers are connected;
six retained telemetry histories are readable. Invalid signatures and unenrolled
reports are rejected. No accepted test report or RF polling was generated.

Origin checks verify Brotli delivery of the exact precompressed bytes and a 404
for an absent hashed asset. The new app has zero restarts. Other running
containers, the intake, radio services, retention and private configuration are
unchanged. The header Changelog and source offer remain available at
[the preview](https://canadaverse.org/beacon-dev/source.html).

The deployment checkpoint is `atlas-topology-refresh-20261030T000621Z` (UTC;
29 October local time). A fresh stopped-writer dump was taken immediately before
cutover; the earlier dump was the one restored and migration-tested off-host.
They have distinct hashes and are not represented as the same snapshot. The old
app/container and both old and upgraded database histories are retained.

The browser loaded the 24-hour graph with 6,064 nodes and 16,897 connections,
live reports, camera controls, Changelog and no captured browser errors. Basic
Atlas was tested separately from the telemetry UI for search, full-key pinning,
reload persistence and empty-window behavior. These are functional observations,
not an overnight soak or physical-device performance certification.
