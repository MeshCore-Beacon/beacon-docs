# Beacon resource lifetime fixes — 16 November 2026

This follows the [earlier performance handoff](https://canadaverse.org/beacon-dev/performance-followup-20261116.md).
Each proposal targets `dev` separately as a draft. These are patch-class changes
to existing behavior, not a new release number or a combined org implementation
PR. The Canadaverse preview is qualified as a separate composition.

## Focused changes

| Area | Draft to dev | Confirmed problem and correction |
| --- | --- | --- |
| Live-event hub | [Server #330](https://github.com/MeshCore-Beacon/beacon-server/pull/330) | Removal could overtake registration on another queue, leaving a closed client's hub state behind; unsubscribe could overtake subscribe. One FIFO now orders all client controls. |
| Area Borders | [Web #223](https://github.com/MeshCore-Beacon/beacon-web/pull/223) | Switching the overlay off left its HTTP reads active. The view now releases its query subscriptions and forwards cancellation, preserving other consumers and completed cached geometry. |
| Neighbor graph | [Web #225](https://github.com/MeshCore-Beacon/beacon-web/pull/225) | A canceled job could still run synchronous fallback layout or handle a queued worker callback. Cancellation now suppresses work that has not started and prevents late delivery. |
| Native live paths | [Flutter #38](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/38) | Every screen requested detailed live paths although only map animation uses them. A shared demand stream requests that data only for visible, resumed maps with Play enabled. Ordinary events remain available on the same socket. |
| Covered native maps | [Flutter #40](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/40) | Opening an opaque route over an enabled map left its custom animation timer running. Route visibility now clears and gates that animation; returning to the map preserves Play preference and starts fresh on the next packet. |

The hub change replaces three 64-entry queues with one shared 64-entry queue.
Backpressure remains bounded; the aggregate buffer capacity is intentionally not
claimed to be identical. The event loop handles removal directly, without
re-enqueuing controls, and fan-out remains nonblocking. Existing global-gap
notifications and counters are preserved in the preview composition. A completely
stalled/stopped hub can still block callers because its existing API has no
per-call cancellation or shutdown signal; this change fixes ordering, not that
separate lifetime contract.

Border cancellation is consumer-aware: another subscribed view keeps its read;
overlapping regions do not restart; completed polygons remain reusable under the
normal cache lifetime. An unfinished canceled polygon is fetched again when
needed. Null/204 responses and geometry refresh semantics remain intact.

Graph cancellation keeps the existing terminated-worker promise contract. It
cannot interrupt a synchronous layout that has already started, and does not add
a new exception contract for active worker-error fallback. The real graph path
uses a worker above 500 rendered regional nodes, including disconnected or
unlocated nodes, and retains its 1,000-node cap. All-regions graph loading remains
deliberately gated.

## Measured evidence and limits

- A controlled graph fixture used the existing 1,000-node cap, ring edges and mesh
  parameters. Three runs took 1,748.54 / 1,722.07 / 1,722.54 ms, median **1,722.54 ms**,
  on Node 22.18.0, Windows x64, Intel i5-4690K. Canceling before fallback starts
  avoids that otherwise discarded calculation. This is local algorithm cost,
  not a production latency or universal-device benchmark.
- Two concurrent, read-only YKF subscriptions on the preview observed **52 matched
  observations over 40 seconds** at 14:02 UTC, with identical non-resolution fields and
  no reported gaps. Base JSON totaled **82,635 bytes**, versus **103,273 bytes** with
  path resolution: **20,638 bytes / 19.98% less decoded UTF-8 message data**. This
  does not measure TLS/compressed-wire bytes, CPU or database savings. The backend
  currently prebuilds both event variants, so this client change does not establish
  reduced ingestion resolution work.
- Hub regressions reproduce immediate-close and unsubscribe ordering failures,
  verify optional-variant counters clear, and exercise a full control queue draining.
  No production memory-growth/load percentage is inferred from those tests.

Independent review found and corrected two app compatibility edges before
promotion: a standalone single-subscription event stream must not gain a second
listener, and replacing only the optional flow stream must not rebind the unchanged
base stream. The final stream contract is covered alongside handshake timing,
overlapping consumers, last-listener cancellation, reconnect, region changes,
rapid Stop/Play, lifecycle transitions and disposal.

The two visibility proposals remain independently based on dev. Their composition
preserves both actions on a visibility change: clear existing flow/timer state and
refresh the dedicated demand subscription. It does not rebind the unchanged base
event stream. App pause while covered must not resume work merely because the
covering route is popped; both visibility and resumed state are required. The
previously qualified Stopwatch timing is retained in the moved flow handler.

## Qualification and recovery

The qualified preview and app fork now identify:

| Target | Source | Qualification |
| --- | --- | --- |
| Preview server | `b241a3457ce6` | [Full CI](https://github.com/n30nex/beacon-server-contributions/actions/runs/43881900047), PostgreSQL endpoints/plans, backup/recovery checks, hub/WS race tests and exact ARM64 artifact/source |
| Preview web | `f25a9a45d95c` | [Full CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/43882780583): **2,257 tests / 214 files**, exact Actions bundle and **85 public assets** plus source archive |
| App fork dev | `84fa7df118ac` | [Full CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/43886386783): **887 tests**, 16 optional screenshot tests skipped; combined transport/map regressions and exact Android artifact/signature/checksum |

The deployed site passes **36 page checks** across English/French, desktop
1440 × 900 and touch/mobile 390 × 844, including Atlas persistence. No application
errors, API failures or horizontal page overflow were recorded. The existing CSP
still blocks Cloudflare's optional injected analytics; it was not weakened to
silence that notice.

The public boundary test now aborts the delayed YKF border request when switched
Off on desktop and mobile. Real YYJ graph data exercises the >500-node worker
path and the worker-unavailable compatibility path in both layouts. Graph search
does not restart layout, and navigation completes without late errors. This uses
actual regional data, not synthetic packets. CSV and contact-file exports still
make no additional node reads.

Real live-map checks pass language/region/style changes, Play/Stop, return
navigation and reduced-motion visits. Sampled animated-source work stays within
the existing 30 Hz budget and stops after Stop/navigation. These are bounded
browser observations, not physical GPU/frame-rate or battery measurements.

Public backend checks confirm source identity, both MQTT connections, malformed
filter rejections and ordinary reads. A native-ticket WebSocket check receives
real packets, unsubscribes, clears options, exchanges ping/pong and closes normally;
a second immediate-close session also closes normally. The app's native Dart
transport independently receives hello/configured/subscribed and 16 events over
10 seconds from the updated backend. An initial Python WebSocket-client upgrade
ended in EOF before hello; that harness limitation remains recorded, and was not
reproduced by the browser, native Node or native Dart clients. No runtime setting
was relaxed to make the probe pass.

Configuration/credentials, schema, retention, optional feature policy, historical
data, inactive radio services and unrelated containers are preserved. Normal ingest
continues; a healthy replacement is not universal losslessness proof. Only
Canadaverse was deployed. Org dev/dev1/live and release tags were not changed.

The final app composition restores four map-label lines to their original UTF-8
text; the superseded artifact is not promoted. It remains a debug APK with a
certificate differing from the prior build, so no in-place upgrade is promised.
No device install, physical OS/clock/battery test, RF polling or signing-secret
change was performed. Native policy/telemetry behavior remains unchanged.

### Recovery

From `/opt/canadaverse/beacon-dev-20260906`, restore the web first and then the
backend if required:

```sh
sudo python3 evidence/performance-round2-20261116/web-runtime/deploy-web.py rollback
sudo python3 evidence/performance-round2-20261116/backend/deploy-server.py rollback
```

Web checkpoint **performance-round2-web-20261116T142619Z** restores web
`66eadd79da83` while retaining the new server. Backend checkpoint
**round2-server-20261116T142440Z** then restores server `a71f09f20cd6`, preserving
the current web and data. Helpers enforce source identity and retain recovery
copies. No database downgrade is required; no live rollback rehearsal was run.

## Review and next steps

Keep the small org proposals separate. When overlapping app changes are accepted,
refresh the remaining PRs against current dev and rerun their regressions; the
qualified fork demonstrates the intended combined behavior. Maintain existing
telemetry/account policy and preserve historical data during promotion.

Further work should measure backend variant construction separately from client
payload size, and define the hub shutdown/cancellation contract before changing
its API. Stable app package/signing/version policy remains tracked in
[Flutter #33](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33).
