# Post-2.0 Beacon: Meshat and preview decision register

[Roadmap](post-140-roadmap.md) · [Earlier Meshat review](meshat-review-20261004.md)

Prepared by **[Torchlight]**, 4 October 2026, for the Beacon team.
[Request and colour convention](https://discord.com/channels/1507764602253869197/1507788454774182030/1556327984896675861).
This is a recommended review order, not approval to implement every item, a release
schedule, or permission to change production, databases or radios. Existing accepted
priorities and draft/review/automation holds remain in force.

## Read the labels correctly

- **✨ Review first:** clear potential benefit; select a bounded upstream contribution.
- **❕ Design first:** meaningful capability, but evidence, cost or product decisions remain.
- **❌ No new port:** already covered, duplicate, unsuitable default or outside this scope.
- **🟢 KEEP / EXISTS:** worthwhile or already part of Beacon. This is not a blanket stability claim.
- **🟡 INTEGRATE / VERIFY / DESIGN:** implementation, validation or a decision remains.
- **🔴 DO NOT PORT / DUPLICATE:** reject the proposed addition, with a reason. Use BROKEN only
  for an evidenced defect; do not label an existing working module broken because its duplicate is red.

IDs below are stable planning identifiers. Source state, recommendation and delivery
state are separate. None of the new candidates below is marked accepted or shipped
upstream merely because this document recommends it.

## Current upstream and preview baseline

Refs were checked on 4 October 2026, approximately 15:32–15:36 UTC:

- **Server:** main `3828e689eda947391ca35c51934a7e79c9b40a82`;
  dev `c7209b70433b8b127a5b1062fdfb17d4a676245c`.
  Main is v2.0.1 `0dca03cd4dae1b6061df5078a4390be33b9ed475` plus branch-governance files.
  The inspected main/dev comparison adds governance, not a new feature release.
  Catalogue-refresh fairness and the default 24-hour refresh are already included.
- **Web:** main `82fb6835066aed7acc3f611cab450b3760d08fa3`;
  dev `b4d498e697182f83bef47152c3f35afb226a2252`.
  Main is v2.0.1 `7fb24789d1649aa079e4568d335d60b3400d87be` plus governance.
  Dev additionally includes [#146](https://github.com/MeshCore-Beacon/beacon-web/pull/146),
  the mobile channel-scroll/bottom-navigation fix (`dc757cfb5147108e6b0ebbb4adc4b14e07a9f192`).
  Divergent release history makes the raw ahead/behind count misleading; it is not a feature count.
- **Docs:** main `f0d5632ad9833305745f54ff1bb2c0e2bb413f8f`;
  dev `5a60f1e00b3e7c13c416382d4a53f4ea84b7b0f4`.
  The inspected dev difference is branch governance. The consolidated operator/API docs
  already exist; an experimental roadmap is not an accepted upstream feature contract.
- **Canadaverse:** web **2.2.1-n30nex.1** at `c41e6fa8940fba929704bc2f9a94f119fef4a4ca`;
  server **2.2.0-n30nex.1** at `84ac3c8781ed19f99e7d996e07e8b671dc6efc92`.
  Public index/revisions were reverified. Collector revision is unchanged at
  `aa7ddf06034620bb8c7c60b2011ce5bb98f313d2`; no private implementation was inspected here.
- **Meshat:** archived v1 `f4c505b07a2b4a47ddf6b90a0756968d795741f5`, not every later fork branch.
  The supplied long report and Claude's follow-up are review evidence, not test results.
  Claude's `v2.0.1 / origin/dev` wording does not pin an exact inspected dev commit.

Coverage means current refs, recent history, relevant PRs, targeted source and retained
release review across the three public core repositories, not an exhaustive audit of
all code or every repository in the organization. The available recent channel context
and saved reviews were read; this is not a claim to have retrieved every channel message.

## ✨ 1. Worth reviewing first

### R01 — 🟢 KEEP; 🟡 integrate/test: realtime correctness (Meshat)

Prioritize global hub-loss notification, authoritative Retry-After deadlines, bounded
WS writes and reliable recovery of affected views. Current source still logs/drops a
full global broadcast queue before client fan-out; `noteRequestOk` clears shared
backoff; `writeTimeout` remains unused. Client-buffer lag notices and heartbeat reset
already exist and are not substitutes for these fixes.

Benefit: fewer silent live/history inconsistencies and less avoidable retry pressure.
Acceptance: queue-saturation regression, coalesced recovery without a refetch storm,
concurrent 429/200 ordering, slow-reader cancellation and shutdown cleanup. Preserve
working route/observer filters. Shutdown and all-view resync claims need separate tests;
no production incident or throughput improvement was reproduced in this review.

### R02 — 🟢 KEEP; 🟡 targeted fixes: API and UI correctness (both)

Apply documented region filters consistently to ordinary message lists; reject invalid
node-type names rather than silently removing the filter. Reuse preview error/retry
and missing-data patterns where a current upstream UI reproduces the same defect.
Audit pathological drift, storage-denied environments and detail error states rather
than accepting every old fork audit finding as current.

Acceptance: slug/ID/IATA combinations, empty/unknown regions, valid aliases versus
invalid types, 404 versus 5xx, loading/no-data versus real zero, and storage exceptions.
The server already distinguishes missing records from server failures. Backfill already
resolves region filters. Sub-hour rollup semantics are a separate design item, not a
mechanical bug fix. See the B1–B9 reconciliation below.

### R03 — 🟢 KEEP; 🟡 port with protocol tests: TRACE evidence safety (preview + Meshat)

Strong upstream candidate: distinguish TRACE 1/2/4/8-byte hashes from ordinary
1/2/3-byte paths; preserve conflicting identities and all eight matching bytes;
reconstruct original SNR bytes; prevent malformed or unvisited requested hops from
becoming observed routes, neighbours or capability evidence. Explain suspect records
and retain access to raw evidence instead of deleting history.

Acceptance: live/REST parity, signed SNR and reconstruction fixtures for each supported
width, malformed/truncated inputs, ambiguous candidates, requested versus visited hops,
and no new inferred links from invalid data. Default hiding and wording need usability
review. This is not a claim that all upstream TRACE handling is broken, nor that the
preview solves global ambiguity for every ordinary path.

### R04 — 🟢 KEEP; 🟡 integrate: readable, bounded trace and packet lists (both)

Keep preview row-height/long-path containment, visible expansion controls and bounded
collapsed previews. Add Meshat-style optional resolved hop summaries to list/backfill
responses where missing, retaining hashes and confidence instead of doing one detail
request per row. Those are two separable patches, not an excuse to rewrite all lists.

Acceptance: long paths, click/Enter/Space, selection, expanded report width, populated
desktop/mobile captures, bounded batch resolution and consistent live/reloaded rows.
Earlier preview compact/mobile evidence exists; expanded-report and loaded desktop
acceptance were not completed by the latest fixed captures.

### R05 — 🟢 KEEP; 🟡 upstream acceptance: focused My Atlas (preview)

Saved full-key node monitoring, compact cards, optional environmental telemetry,
known-neighbour context and shared inspection links are useful post-2.0 capabilities.
Start from [existing draft #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97),
not a duplicate implementation. Its head is `91a9541cd6fe27f76996c8f7e65fb07698783a98`,
not the latest preview; newer compact/telemetry changes need explicit reconciliation.

Keep a browser-local, read-only core independent of Collector/control rollout.
Acceptance: refresh against current dev, storage migration/failure handling, full-key
identity, bounded samples, stale/error states, mobile/keyboard access and optional
telemetry service absence. A 200-report sample is not a complete node/fleet total.

### R06 — 🟢 KEEP; 🟡 focused integration: Topology and bounded link reads (preview)

Keep a focused optional Topology view with shared multi-region selection, camera state
preserved across refreshes, compact controls, lazy optional context and visible caps.
The 24-hour link endpoint is a particularly useful query-shaping candidate: one cached,
bounded read instead of a client fan-out across many route pages.

The preview snapshot returns deduplicated adjacent **undirected** node-ID pairs for
15m/1h/24h, caps at 100,000 links and reports window/capping; prior source review found
30-second caching and a 15-second request timeout. Preserve rate limits.
Acceptance: indexed query plans and realistic load, cache/filter isolation, missing-hop
breaks, capped/stale labels, a paired API/UI rollout, bounded rendering and low-power
fallback. This is neither a weighted planner nor proof of RF reachability. No measured
speedup or production capacity is claimed here.

### R07 — 🟢 KEEP; 🟡 reconcile existing components: truthful telemetry and charts (preview)

Reuse compact optional telemetry, labelled unavailable readings, single-sample display,
consistent roles/status and clear measured-versus-gap styling. Upstream already has
hourly chart gaps; port only the missing behavior, not a second chart system. If dashed
segments estimate across gaps, label them as estimates and never count them as samples.

Acceptance: absent/null/zero distinction, intermittent and single samples, units,
temperature-channel labels, dark/light themes, keyboard/mobile layout and bounded
refreshes. Coordinate palette/accessibility work with open
[web #147](https://github.com/MeshCore-Beacon/beacon-web/pull/147), not a competing rewrite.

### R08 — 🟢 KEEP; 🟡 small independent candidates: contact handoff and radio names (Meshat)

A locally generated MeshCore contact QR/deep link is a visible, contained improvement.
Validate full keys/name/type and actual supported clients. Friendly radio-preset names
are useful secondary enrichment: bundle/version the catalogue, retain raw settings and
show an honest fallback for no match or ambiguity. Do not require a startup network fetch.
Neither a QR nor a preset label proves device compatibility or radio reachability.

### R09 — 🟢 KEEP; 🟡 agree policy: current IATA-membership freshness (Meshat)

Distinguish where a node was ever heard from current membership of an otherwise-active
node. `last_heard` metadata is not itself an expiry policy. Prefer a configurable read
policy with visible age over erasing historical receptions.
Acceptance: one-off distant reception, reappearance, inactive/active nodes, cutoff
boundaries, region filtering and query cost. The specific duration is undecided; it is
not automatically seven days. More invasive neighbour aging/mobility work is D01.

## ❕ 2. Meaningful additions that need larger decisions

- **D01 — 🟡 DESIGN: evidence quality, direction and ambiguity (Meshat + preview).**
  Rolling directional SNR with sample count/age, direct versus inferred provenance,
  edge aging and node-movement invalidation, and global versus IATA-contextual identity
  confidence. Valuable even without a planner. Define provenance, freshness and migration
  cost first; terminal receiver SNR is not every hop's SNR. Preserve uncertain diagnostics.
- **D02 — 🟡 DESIGN: calculated best/alternative routes (Meshat).**
  Dijkstra/Yen-style routing and MeshCore export add to observed-route browsing/search.
  Depends on D01 plus bounded graph refresh/query cost and stale-snapshot behavior.
  Keep observed routes; a proposed path is not verified RF delivery. No planner is approved.
- **D03 — 🟡 DESIGN: investigations and retained history (both).**
  Transit-node packet history, full node/fleet metrics, trace reception chronology,
  indexed history/path/text search, observer filters and generalized server-side sorting.
  Separate origin observations from candidate relay evidence; define indexes, retention,
  deduplication, keyset ties, count cost and ambiguity. Build a cheap observer filter
  separately from whole-history text search. Replay/seek and geography remain later
  retained-evidence workflows, not features provided by a live map or hourly rollups.
- **D04 — 🟡 SELECT TARGETED WORK: contracts, cache and accessible navigation (Meshat).**
  OpenAPI drift checks, a consistent app-lifetime WS/query reconciliation policy,
  URL-owned filters and semantic mobile sort can help without replacing the router.
  Prefer small measured improvements. API sorting precedes claims of globally sorted
  results; focus/keyboard testing, not the presence of Radix, establishes accessibility.
  Sub-hour statistics belong here as an explicit resolution/API decision when needed.
- **D05 — 🟡 RELEASE DESIGN: Collector and additional metadata (preview + Meshat).**
  Optional telemetry acquisition needs supported transports, reconnect/long-run tests,
  per-radio budgets, shared repeater leases, auth/revocation and a clear producer contract.
  Core Atlas does not depend on approving remote radio control. Self-reported MeshCore
  regions are distinct from geographic IATA groups. Observer-owner ingestion requires
  explicit privacy/privileged-feed decisions. Public design only; no private code or
  hardware access was part of this review. Preserve existing 2.1 proposals and later
  console/control, BLE/browser and firmware qualification boundaries.
- **D06 — 🟡 OPTIONAL UX: Public chatter, mini-maps and map polish (both).**
  Preview chatter can add context, but it is not a performance priority or channel
  analytics. Keep it bounded, optional, privacy-aware and anchored to a receiver rather
  than asserting sender location; identify Public by the actual decryption key.
  Mini-maps, trace maps, SNR-coloured legs, legends, theme-following basemaps, translated
  labels, hover preload, saved display preferences and unknown-channel totals need
  concrete user benefit and measured cost. SNR styling depends on D01's truthful evidence.

## ❌ 3. Already covered, unsuitable or out of scope

### X01 — 🟢 existing Beacon capability; 🔴 duplicate port

Keep, do not reimplement or remove:

- Working WS route-type/observer filters, reconnect-specific heartbeat state and
  client-buffer lag handling. They do not solve R01's distinct global-queue loss.
- Pending-region request guards, MapLibre missing-image resolver, existing live map,
  neighbour graph, View on map, lazy heavy views, React Query and virtualization.
- Existing i18n including Swedish in 2.0.1, clipboard failure handling, zero-radio
  formatting and bounded list limits. A separate mini-map/contact QR is not View on map.
- Opt-in observer expiry that preserves referenced history, server 404/500 distinction,
  hourly rollups/gaps, retained-summary metadata and existing route/trace keyset fixes.
- Catalogue-refresh fairness/default interval in server 2.0.1 and the consolidated
  upstream operator docs. MeshMapper stays a read-only Beacon integration, not a redesign target.
- Mobile scroll/navigation fix #146 is already merged into **dev**, not a new Meshat port.
  Chart palette #147 is **open**, not shipped; contribute to its review rather than duplicate it.

### X02 — 🔴 do not import as a package or default

- The whole fork, a forced Router/Radix/DataTable/marker rewrite, a mandatory new
  architecture for feature parity, or decorative features as release blockers.
- Swedish branding/default locale/root catalogue and single-broker restrictions.
  Preserve Beacon's deployment configurability and multi-broker support.
- A universal 150 km rejection rule, blanket destruction of one-byte diagnostics,
  automatic seven/fourteen-day policies or averaged opposite-direction SNR.
  Geographic plausibility is evidence to interpret, not a universal RF law.
- Pre-2.0 migration numbers or edits to the released flattened baseline. Any new schema
  needs its own reviewed upgrade/recovery design; none is authorized by this report.
- Promoting intended TRACE hops, catalogue counts, missing records or uncertain clock
  deltas into observed links, packet-loss totals or RF propagation claims.
- Upstream/production deployment, remote console/radio control, private source exposure,
  or unrequested automation changes. They are not side effects of adopting a roadmap.
- The claim that a particular feature caused CoreScope users to migrate. No independent
  adoption/causal evidence or portable performance benchmark was supplied.

## Claude B1–B9: current-source reconciliation

These IDs belong to the supplied notes, not nine automatically approved fixes.

- **B1 🟡 source-backed:** `Hub.Broadcast` still drops/logs a full global queue.
  Reproduce and add bounded lag/recovery signaling; distinguish deliberate repeat shedding.
- **B2 🟡 source-backed:** `noteRequestOk` still clears active shared backoff.
  Test concurrent 200/429 ordering; no live request storm was reproduced.
- **B3 🟡 targeted contract gap:** ordinary `/messages` and channel-message listing use
  IATA parsing without region expansion. **🟢 `/messages/backfill` already resolves regions**;
  the notes must not be generalized to every message endpoint.
- **B4 🟡 protocol check:** live ingest builds metadata from `packet.Path`, `PathLength`
  and ordinary path helpers. The upstream contract explicitly notes TRACE path bytes
  are SNR bytes. Raw SNR preservation is not itself a bug: compare interpreted hash
  width/count and live/REST behavior with valid fixtures, including the preview delta.
  This review did not execute that regression or prove complete preview repair.
- **B5 🟡 audit:** pathological clock drift/ranking remains a supplied candidate, not a
  freshly reproduced defect. Check timestamp bounds, units and valid extreme cases.
- **B6 split:** **🟡 type validation:** current handler and `NodeTypeFromString` silently
  map an unknown nonempty name to zero/no filter. **❕ sub-hour policy:**
  `parseStatsWindow` deliberately truncates to UTC hours and documents empty sub-hour
  results. Do not silently replace hourly-rollup semantics with raw-data scans.
- **B7 🟡 partially source-backed:** unused `writeTimeout` and connection-context writes
  confirmed. App-wide hijacked-socket shutdown behavior still needs dedicated verification.
- **B8 🟡 audit/integration:** detail error-state and all-view lag recovery are useful
  acceptance cases; remaining current upstream callers were not exhaustively re-audited.
  Do not erase existing server 404/500 handling or preview error/retry improvements.
- **B9 🟡 audit:** storage-denied reads/writes need focused tests. Earlier review found
  an unguarded initial App read; every listed current call site was not rechecked here.

## Suggested packages and dependency gates

1. **Correctness package:** R01/R02 plus isolated R03 regressions. Select individual
   fixes; do not label all B1–B9 cheap or confirmed. Keep protocol and UI patches reviewable.
2. **Visible-benefit package:** focused Atlas R05, trace usability R04, truthful telemetry
   R07 and optionally contact QR R08. Reuse existing drafts and components.
3. **Bounded topology package:** R06 API plus UI qualification, preserving caps and rate
   limits. Broader D01 evidence semantics remain a separate design, not an excuse to
   treat undirected adjacent pairs as directional quality measurements.
4. **Evidence/data-design package:** R09 and D01, then decide whether D03 investigation
   or D02 routing gives users more value. D01 precedes trustworthy SNR maps/planning;
   indexed retained evidence precedes transit/search/replay; server ordering precedes
   global-sort UI promises. D05 has independent transport/privacy/release gates.

These recommendations supplement, not silently replace, the proposed Atlas/Collector
focus and historical phase list. Implementation owners, estimates and release slots
remain unset. Use the stable IDs to record a future accepted decision and its tests.

## Evidence, existing work and limits

- Current [server main/dev comparison](https://github.com/MeshCore-Beacon/beacon-server/compare/3828e689eda947391ca35c51934a7e79c9b40a82...c7209b70433b8b127a5b1062fdfb17d4a676245c),
  [web main/dev comparison](https://github.com/MeshCore-Beacon/beacon-web/compare/82fb6835066aed7acc3f611cab450b3760d08fa3...b4d498e697182f83bef47152c3f35afb226a2252),
  and [docs main/dev comparison](https://github.com/MeshCore-Beacon/beacon-docs/compare/f0d5632ad9833305745f54ff1bb2c0e2bb413f8f...5a60f1e00b3e7c13c416382d4a53f4ea84b7b0f4).
  Web comparison is merge-base/history based; recent dev commits and release-to-main
  comparison, not its raw count, establish the reported post-release delta.
- Current source: [hub](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/hub/hub.go),
  [WS writes](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/ws/handler.go),
  [ingest metadata](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/ingest/packet.go),
  [Retry-After state](https://github.com/MeshCore-Beacon/beacon-web/blob/b4d498e697182f83bef47152c3f35afb226a2252/src/api/rate-limit.ts).
- Current source: [messages](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/api/handlers/messages.go),
  [channel messages](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/api/handlers/channels.go),
  [stats windows](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/api/handlers/regions.go),
  [node handler](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/api/handlers/nodes.go),
  [type conversion](https://github.com/MeshCore-Beacon/beacon-server/blob/c7209b70433b8b127a5b1062fdfb17d4a676245c/internal/api/nodes.go),
  and [upstream API contract](https://github.com/MeshCore-Beacon/beacon-docs/blob/f0d5632ad9833305745f54ff1bb2c0e2bb413f8f/docs/api-contract.md).
- [Meshat archived source](https://github.com/Bjorkan/meshat-beacon/tree/f4c505b07a2b4a47ddf6b90a0756968d795741f5),
  [original channel review](https://discord.com/channels/1507764602253869197/1507788454774182030/1556287124452671621),
  [Claude notes](https://discord.com/channels/1507764602253869197/1507788454774182030/1556325720685281312),
  [preview changelog](https://canadaverse.org/beacon-dev/source.html),
  [pinned preview web](https://github.com/n30nex/beacon-web-contributions/tree/c41e6fa8940fba929704bc2f9a94f119fef4a4ca),
  [pinned preview server](https://github.com/n30nex/beacon-server-contributions/tree/84ac3c8781ed19f99e7d996e07e8b671dc6efc92).
- [Server draft #192](https://github.com/MeshCore-Beacon/beacon-server/pull/192) remains
  open at the newer preview head; its body still quotes older `8c7fbb8`/`7e139d5`
  runtime evidence. Do not treat those old test totals as validation of every new change.
  [Docs draft #7](https://github.com/MeshCore-Beacon/beacon-docs/pull/7) follows the owned
  docs fork; neither it nor Atlas #97 is upstream acceptance. No reviewer request is made.

No application build/test, load benchmark or fresh browser interaction test was run
for this report. The preview changelog reports 1,274 frontend tests; that is attributed,
not rerun evidence. Earlier screenshots covered Packets/Topology and populated mobile
Traces; desktop Traces captured loading skeletons, Atlas/chatter interactions and
expanded-report geometry remain acceptance gaps. Public HTTP health does not prove a
healthy whole data pipeline. All absent-feature statements are scoped to the inspected
interfaces and retained pinned review; larger audits remain explicit follow-up work.
