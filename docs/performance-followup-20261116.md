# Beacon cancellation and animation lifetime fixes — 16 November 2026

This follows the [system audit](https://github.com/MeshCore-Beacon/beacon-docs/pull/65)
with four independent fixes to existing behavior. Each code PR targets `dev` as a
draft. They are patch-class candidates because the affected paths also exist on
released main; a backport still needs qualification against its intended base.
No new release number, date or signed artifact is assigned here.

## Fixes and evidence

| Component | Small draft PR | Before | After |
| --- | --- | --- | --- |
| Web | [#221 cancel obsolete paged reads](https://github.com/MeshCore-Beacon/beacon-web/pull/221) | Changing region or leaving a page let its HTTP request continue. Three rapidly replaced regions retained three active reads. | Nodes, Map and Routes forward query cancellation to HTTP. The regression retains only the current read. Completed pages and a request still used by another subscriber are preserved. |
| Backend | [#328 cancel analytics revision waiters](https://github.com/MeshCore-Beacon/beacon-server/pull/328) | A slow revision query held a mutex; a waiter with a 20 ms deadline remained blocked beyond one second. | A context-aware gate lets the waiter leave without starting a second database read. Healthy callers still share one refresh and its ten-second memo. |
| Flutter | [#35 elapsed map flow lifetime](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/35) | Packet flow arrival/expiry used wall time, so clock changes could leave the animation timer alive after the visible flow should expire. | Animation uses one elapsed-time stopwatch. Regression coverage includes expiry, overlapping arrivals, timer restart, delayed callbacks and fresh arrivals after an event-loop stall. |
| Flutter | [#37 ignore background flow events](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/37) | A late packet after pause cleanup could start a new 50 ms animation timer in the background. | Paused screens do not accept flow events. Resume and explicit flow controls remain usable. |

These changes address wasted work and incorrect lifetimes. They do not establish
a percentage reduction in production CPU, battery consumption or database load.
No dependency, schema, retention, API shape, telemetry policy or radio operation
is needed. The independent collector and retired Topology/scope experiments remain
retired; these fixes do not restore them.

## Regression coverage

- Web: a delayed request, rapid query-key changes, two shared subscribers,
  completed-cache reuse, cancellation of a later page, exact cursor resumption,
  row deduplication and the existing page-budget/rate-limit behavior.
- Backend: a blocked revision owner with a canceled waiter; concurrent healthy
  callers sharing one refresh; recovery when the owner's own read is canceled.
  The fix creates no detached task and preserves the owner's request context.
- Mobile: controlled elapsed time independent of wall time, overlapping packets,
  expiry and restart, stop, pause/resume, late events and screen disposal.

The app uses the standard-library [Stopwatch](https://api.dart.dev/stable/latest/dart-core/Stopwatch-class.html)
for both arrival and rendering time. Reading the last timer tick at arrival is
insufficient: the next overdue callback can advance that tick past a fresh
packet's lifetime. An independent VM reproduction caught this in the initial
candidate (5 ms actual age versus 2,000 ms inferred age); it was corrected before
fork promotion. The final regression preserves fresh arrivals across that ordering.

An isolated browser test delays only its own real Nodes request, then navigates
to Packets. The previous preview kept the request alive on both desktop and
390 × 844 touch layouts. The exact candidate bundle aborts it in both layouts,
without application errors. This test sends no fabricated packet or RF traffic
and never opens the user's browser profile.

## Deployment and qualification

Only the Canadaverse preview was deployed. The qualified source revisions are:

| Target | Revision | Qualification |
| --- | --- | --- |
| Preview server | `a71f09f20cd6` | [Full CI](https://github.com/n30nex/beacon-server-contributions/actions/runs/43836326027), PostgreSQL endpoints/query plans, backup/recovery checks, race tests and exact ARM64 artifact/source identity |
| Preview web | `66eadd79da83` | [Full CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/43836360920): **2,248 tests / 212 files**, exact Actions bundle and **85 public assets** plus source archive |
| App fork `dev` | `2989f141e61d` | [Full CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/43838405161): **882 tests**, 16 optional screenshot tests skipped; **74 map tests** in the combined focused suite; exact Android artifact/checksum/signature verified |

The deployed web passes **36 page checks** across English/French, desktop
1440 × 900 and touch/mobile 390 × 844. Atlas add/reload persistence, Nodes,
Packets, Channels, Observers, Routes, Traces, Analytics and Map remain usable,
without application errors, API failures or horizontal page overflow. Both
desktop and mobile public navigation tests now abort the delayed abandoned
Nodes request. CSV and contact-file downloads add no node requests.
The existing content-security policy continues to block Cloudflare's optional
injected analytics script; it was not weakened to remove that browser notice.

Real live-map traffic was exercised on desktop and mobile. Language changes
preserve the same map canvas; region and style controls, Play/Stop, return
navigation and reduced-motion visits pass. Sampled animation-source updates
remain within the existing 30 Hz budget, with no continuing animation-source
updates after Stop or leaving the page. These are bounded browser observations,
not a physical GPU/frame-rate benchmark. No synthetic RF packets were sent.

Public backend checks confirm the exact revision/source archive, both MQTT
connections, five malformed-filter rejections and six ordinary reads including
statistics. Schema, retention, credentials/configuration, optional feature
policy, historical data, inactive radio services and unrelated containers were
preserved. Normal ingest continues; universal losslessness is not inferred from
a healthy process replacement. Org dev/dev1/live were not deployed or merged.

The APK remains a debug build (`meshcorebeacon.app`, version 2.2.0/code 2).
Its signing certificate differs from the previous artifact, so this is **not an
in-place upgrade promise**; [signing/version policy #33](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33)
remains open. No phone installation, physical clock-change/background-OS test,
companion collection, RF test or signing-credential change occurred.

### Recovery

From the existing Pi preview root `/opt/canadaverse/beacon-dev-20260906`, restore
the web first, then the backend if required:

```sh
sudo python3 evidence/perf-followup-20261116/web-runtime/deploy-web.py rollback
sudo python3 evidence/perf-followup-20261116/backend/deploy-server.py rollback
```

Web checkpoint **performance-web-20261116T092216Z** restores web `b2af1b05c555`
while keeping the new server. Backend checkpoint **perf-server-20261116T092121Z**
then restores server `4f4f833f7e50` while preserving the current web and data.
Both helpers enforce source identity and retain recovery copies. No database
downgrade is needed, and a live rollback rehearsal was not performed.

## Follow-up

Keep [native live-consumer profiling #32](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/32)
as an evidence-led task: measure path-resolution demand and actual low-end device
cost before changing subscriptions or animation fidelity. Continue using focused
PRs with reproduction checks, current-base CI, exact preview artifacts and a
recoverable cutover. Production speed claims need representative workload and
hardware measurements rather than extrapolation from a passing regression.
