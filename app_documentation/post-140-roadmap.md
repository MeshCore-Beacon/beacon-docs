# Beacon roadmap: 2.0 integration and CoreScope parity

## Current status — checked 2 October 2026

| Surface | Verified state |
|---|---|
| Upstream server | `dev` **98006a9** includes the 2.0 baseline and hourly rollups; `main` remains **201cd9e**. Latest published release is still **v1.6.0**. |
| Upstream web | `dev` **39e921c** consumes hourly rollups and handles empty regions; `main` remains **5ac36ce**. Latest published release is still **v1.3.0**. |
| Upstream docs | `main` **24d2e5f**; our experimental roadmap remains in draft PR #7. |
| Prepared experiment | `n30nex-test`: server **ae328cb6**, web **9d3f9585**. Both incorporate the named upstream dev/main heads. Server #192 and My Atlas #97 are draft, mergeable and pass their published-head CI; web CodeQL is skipped. |
| Pi preview | Still server **644960e4** / web **462d49e8**, confirmed by the public source offer. Its legacy database, 72h raw/30d summary retention and rollback are unchanged. |
| Official sites | `live.meshcore.ca` serves Beacon and displays **2.0.0**. `dev.meshcore.ca` also displays **2.0.0**, with a development-only banner linking everyday users to live. Backend revisions and operator rollout acceptance were not verified by this read-only browser check. |
| Release boundary | **No stable 2.0 GitHub release/tag yet.** A frontend version label is not a published release. My Atlas and Topology remain held for post-2.0 acceptance. |

The prepared code passed native server build/vet/PostgreSQL validation and web
build/lint/**1,180 tests**. Two opt-in backup/export tests were skipped. Browser
checks covered desktop, French phone layouts, region isolation, all loaded paths
and 160 animated packet reports. This roadmap-only refresh did not rerun those
unchanged-code checks or deploy anything. Daily compatibility automation remains
**paused**, and no review request is authorized.

[Exact post-2.0 packages and merge order](post-20-integration.md) ·
[Actual preview and rollback](n30nex-test-preview.md) ·
[Pi source offer](https://canadaverse.org/beacon-dev/source.html).

## Comparison baseline and scope

This inventory compares Beacon's published dev code plus the prepared experiment
with [CoreScope master `093e320`](https://github.com/Kpa-clawbot/CoreScope/tree/093e320c2bda99d1fef317d7fc21fc1240a8cd12),
checked on 2 October. CoreScope's latest release is
[v3.12.0](https://github.com/Kpa-clawbot/CoreScope/releases/tag/v3.12.0);
master contains later fixes, so this is a source-backed workflow comparison,
not a claim that every reference feature is deployed on every CoreScope instance.
The old `live.meshcore.ca` CoreScope screenshots are historical references now.

Parity means useful user workflows with honest counting and bounded cost. It does
not require matching CoreScope's architecture, copying every tab, or reproducing
its performance claims on different storage and workloads. The remaining feature
list is separated from release acceptance and production-load qualification.

## What is already covered

| Capability | Beacon state | Remaining boundary |
|---|---|---|
| Live packet feed and decoding | Upstream: filters, byte/payload inspection, per-observer receptions, signal values, shared links and mapped packet paths | A graphical reception timeline can still improve investigation. |
| Live map and neighbour graph | Upstream: live packet animation, node/role controls, map links, neighbour view and IATA borders | Live animation does not provide historical replay. |
| Channels and scope context | Upstream: decrypted messages, Public/hashtag keys, regional channel/scope filters and MeshMapper catalogue discovery/import | Per-channel historical analytics are still missing; unknown names cannot be inferred from a short hash alone. |
| Observer monitoring | Upstream: unified sidebar/dashboard, activity/type/signal charts, telemetry and comparison | Reach by confirmed node/hop, fleet comparisons and timing interpretation need deeper work. |
| Network analytics | Upstream: traffic, signal, path/hop/hash-width distributions, scopes, talkers, clock drift and neighbour graph; hourly summaries survive raw expiry | These aggregate views do not replace node or channel dashboards. |
| Navigation and localization | Upstream: entity inspection, shareable routes/packets/observers, mobile layouts and English/French | Global search, saved filter presets and cross-page Atlas filtering remain. |
| My Atlas | Implemented in the Pi experiment and prepared as a focused post-2.0 feature; PR #97 is refreshed, draft and clean | Acceptance after 2.0 remains. Cards use up to 200 retained origin-key reports, not complete node totals. |
| 3D Topology | Implemented in the Pi experiment; a focused prepared commit follows Atlas | Acceptance after 2.0 remains. All paths, live animation, camera controls, region focus/isolation and lazy scope context are implemented. Follow mode, saved display preferences and replay are later work. |
| Exact route evidence | Upstream already fixes saved-prefix refresh. The experiment adds pinned bytes/width, cursors and shared windows in separate patches | Accept the paired server/web evidence patches separately; neither new page depends on them. |

## Remaining CoreScope parity

| Area | What is left | Reference and current Beacon limit |
|---|---|---|
| **Node and repeater dashboards** | Full-key activity history, packet-type mix, signal/hop distributions, hearing coverage, activity heatmaps, peer relationships and comparable repeater/fleet metrics | [Node analytics source](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/node-analytics.js), [fleet/relay analysis](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/analytics.js). Beacon has node details/recent reports and Atlas samples, but no equivalent complete dashboard. |
| **Packet/trace chronology and observer reach** | A graphical reception timeline, observer-to-observer spread, confirmed reach by hop/node, and a consistent return path into packets, routes and map | [CoreScope tracing overview](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/README.md#and-more). Beacon already shows first/last times, per-observer signal and trace hop chains; the gap is richer analysis, not basic packet inspection. |
| **Global search and saved mesh filters** | Ctrl+K-style search across nodes, observers, packets and channels; use Atlas selections across views; saved filter/layout presets | [Global search and favorites](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/app.js). Beacon searches individual lists and saves cards, but has no shared search or site-wide saved-node filter. |
| **Channel analytics** | Messages over time, channel comparisons, per-channel senders and hearing context, with explicit key/history availability | [Analytics guide](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/docs/user-guide/analytics.md#channels). The decoded message viewer and general talker statistics already exist. |
| **Hash and prefix tools** | Collision/usage matrix, role-aware prefix-width analysis and a prefix checker with explicit ambiguity | [Hash and prefix analysis](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/analytics.js). Beacon already displays width distributions and ambiguous candidates; it lacks the dedicated tools. |
| **Distance and route patterns** | Valid-coordinate hop/path distances, signal-versus-distance views, common subpath rankings and evidence-linked route alternatives/inspection | [Distance and route-pattern analysis](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/analytics.js). Existing route search, detail and 3D layout do not supply geographic-distance analytics. |
| **Historical replay** | Play/pause/seek, stepping and speed controls over retained observations; one time controller for map and Topology, with visible gaps | [Live/VCR guide](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/docs/user-guide/live.md#vcr-mode). Beacon's live pause and static route-history windows are not replay. Hourly rollups cannot recreate expired packet paths. |
| **Geographic area filtering** | Filter nodes and their attributed traffic by advertised location/polygon across views, separately from receiving-IATA groups | [Area filter](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/docs/user-guide/area-filter.md). Beacon's IATA groups, boundary overlay and optional foreign-node classification do not provide this complete workflow. |

Smaller parity items remain below those analysis workflows: node/channel QR sharing,
more table/layout preferences, an in-browser theme editor with import/export, and
operator-facing performance diagnostics. Existing theme selection and deployment
configuration are not a theme editor. See
[CoreScope customization](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/docs/user-guide/customization.md),
[channel QR](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/channel-qr.js)
and [performance UI](https://github.com/Kpa-clawbot/CoreScope/blob/093e320c2bda99d1fef317d7fc21fc1240a8cd12/public/perf.js).
Audio/Lab and decorative exhibition modes are optional, not blockers for the core
analysis roadmap. Account synchronization/MeshMapper login is a separate ownership
and authentication decision, not a prerequisite for browser-local Atlas.

## Delivery order

| Phase | Next package | Completion gate |
|---|---|---|
| **0 — stable baseline** | Recheck the actual 2.0 release refs, then decide the Pi's fresh-database/history cutover | Keep existing data and recovery; publish a compatible server/web pair only after that decision. Official hosts remain owner-controlled. |
| **1 — accept prepared work** | My Atlas, then Topology; optional scope context and exact-route evidence remain separate | Refresh only changed bases; keep the focused merge sequence, current-head checks, paired API compatibility and draft hold until review is requested. |
| **2 — node and trace investigation** | Full-key node dashboard first, then packet/trace chronology and fleet comparisons | Define origin reports versus confirmed relay evidence; share counting/window rules across cards/charts. Reuse existing rollups where their dimensions fit; measure before adding a node aggregate. |
| **3 — finding and channel analysis** | Global search, Atlas-node filters/saved views, channel activity and sender/hearing comparisons | Bounded queries, stable entity keys, aligned windows, keyboard access and share/Back behavior. |
| **4 — network tools** | Hash/prefix ambiguity, distance, repeated subpaths and route alternatives | Keep unknown identities and invalid coordinates visible; every route claim links to recorded evidence. |
| **5 — history and geography** | Retained packet replay, observer reach/timing and GPS-area filtering | Ordered bounded cursors, explicit retention/gaps, no invented paths or clock-based claims of RF propagation. |
| **Beyond parity** | Evidence-linked MeshMapper scope/boundary crossings, region changes and guided live follow | Distinguish a receiving-IATA change, advertised location, scope label and a geometric crossing; never manufacture neighbour links from catalogue counts. |

**Recommended next new implementation after 2.0:** the node dashboard/trace phase.
It builds on the existing node inspector and Atlas instead of adding another
independent page with different counts. Replay is the largest remaining live-view
capability gap and needs its retained-evidence contract before UI implementation.
This update schedules work; it does not start new feature implementation.

## CartoLite-derived follow-ups

[CartoLite `f2b4bdf`](https://github.com/n30nex/CartoLite/tree/f2b4bdff314094c22749819ddc6817d545aa0fa0)
remains a design reference. Stable regional groups, actual-link placement, finder,
neighbour emphasis, region isolation, compact controls, above-mesh camera and
separate static/live rendering are already delivered experimentally. The current
limits remain 20,000 nodes, 60,000 recent routes, 100,000 links/live segments,
10,000 reports and 512 simultaneous animations, with background cleanup and
reduced-motion support. These are ceilings, not claims of a complete network view.

Next Topology-specific refinements are constrained live follow, saved camera/display
preferences and measured adaptive quality. Cross-view selection belongs with phase
3; replay belongs with phase 5. Scope metadata stays optional and lazy. Upstream
now discovers regional scope/channel sources through MeshMapper zone lists; that
is already implemented and must not remain listed as a future importer feature.
The unchanged legacy Pi still has its recorded YOW importer configuration.

## Issue reconciliation and operational work

- [Server #183](https://github.com/MeshCore-Beacon/beacon-server/issues/183) is
  **closed**: upstream `6cd03e7` refreshes saved-route prefix metadata. The prepared
  pinned-evidence changes are additional work, not a still-open prefix fix.
- [Server #116](https://github.com/MeshCore-Beacon/beacon-server/issues/116) and
  [web #12](https://github.com/MeshCore-Beacon/beacon-web/issues/12) are **closed**.
  Reopen investigation only for new MQTT evidence or a specific localization defect;
  continue translation/accessibility checks on every new UI change.
- [Web #96](https://github.com/MeshCore-Beacon/beacon-web/issues/96) remains tied to
  held My Atlas PR #97. Experimental delivery is not stable acceptance.
- [Server #60](https://github.com/MeshCore-Beacon/beacon-server/issues/60) and
  [#72](https://github.com/MeshCore-Beacon/beacon-server/issues/72) remain open for
  admin and local/remote backup scope. Existing protected settings/accounts/exports
  are partial delivery; public admin and backup access remain disabled on our Pi.
- Sustained production-like ingest/query load, recovery/export qualification and
  physical Safari checks remain operational acceptance work. Passing fixtures or
  CoreScope's published benchmarks do not establish Beacon production capacity.

## Shared acceptance rules

Every view states its counting unit, effective time window, sample cap, missing
history and identity ambiguity. Receptions, unique packets, origins and relay
candidates are different metrics. A missing record or unsynchronized clock does
not establish packet loss or RF delay. Raw chart choices follow actual deployment
retention; durable summaries only expose dimensions that were retained.

Reuse Beacon's inspection panels, region model, query cache, chart components and
new hourly-rollup contract. Keep bounded indexed queries, lazy loading and coalesced
refreshes; do not fetch separately per chart or add a blanket materialized-view
refresh job. Native database and relevant replay/browser checks precede deployment.
No feature patch in this queue should alter the flattened baseline migration.

Keep source offers and rollback tied to the actual running pair, preserve unrelated
work, and retain the paused merge recovery. Prepared 2.0 branches must not be
applied automatically to the Pi's 1.x ledger. Earlier 1.4/1.7 planning is historical;
server/web major and minor versions track maintainer decisions, with independent
patches. Merges, stable tags and official-host operations remain maintainer-controlled.
