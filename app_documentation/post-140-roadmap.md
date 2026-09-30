# Beacon after 1.4: parity and further development

Approved direction, 30 September 2026: deliver useful CoreScope feature parity in
small validated phases, then extend Beacon's regional and evidence-based analysis.
Post-1.4 work lives on the explicitly requested `n30nex-test` branches in server,
web and docs, with focused pull requests and the Pi preview as validation.
The branch is experimental: keep existing PRs in draft and do not request or ping
for review until the contributor asks. Daily upstream dev/main compatibility checks
are scheduled; inspect dirty work first, use isolated trial merges, and report only
new changes, conflicts or required decisions. Routine checks do not push, deploy
or merge changes automatically. Version assignments remain with maintainers. The 1.4.0 release handoff is separate
from this development queue; My Atlas remains excluded from that release, but is explicitly included in the
experimental branch and Pi preview at the contributor's request.

## Delivery order

| Phase | Deliverable | Completion evidence | Status |
|---|---|---|---|
| 1 — correctness suitable for 1.4.x | Saved-route hash-width consistency, then retention-aware time controls and remaining French/mobile/accessibility fixes | Route identity survives representation changes; evidence pagination and shared windows do not silently change path; raw and summary periods match available data | Implemented in experimental server PR #192 and the web branch; final Pi checks in progress |
| 2 — first feature after 1.4.0 | My Atlas saved-node monitoring | Carry the feature from web PR #97 into the experiment; saved identities/order survive; compact cards, expandable Heard by/statistics and existing entity links work in English/French on desktop/phone | Integrated into n30nex-test from the two feature commits; combined validation in progress |
| 3 — node and trace investigation | Node dashboard, activity/type/signal/hop analysis, trace reception timeline and complete return navigation | Separate attributed node traffic from possible prefix matches; packet → route → node/observer → map links preserve selection, filters and Back | Queued |
| 4 — find and compare | Bounded global entity search, saved views/filters, Atlas-node filters, channel activity and hearing context | Search/paging/share links agree; channel key/history availability is explicit; comparisons use aligned windows | Queued |
| 5 — network structure | Observed route segments/alternatives, topology, distance, hash ambiguity and prefix/path inspection | Count evidence at the correct grain; separate observed ambiguity from static conflicts; use valid coordinates and show unresolved hops | Queued |
| 6 — history and reach | Bounded retained map replay, observer reach and timing analysis, comparable fleet telemetry | Replay preserves ordering and retention limits; confirmed identities are separate from unresolved prefixes; timing/counter gaps are not labelled packet loss | Queued |
| Beyond parity | Regional boundary/scope crossing investigation and links between observations, discovered scopes and route changes | Each relationship links to retained evidence; distinguish reported locations from inferred paths and scope names from geography | Queued after supporting phases |

The initial Atlas cards show a bounded sample of the latest 200 retained
origin-key reports per node. Complete node totals and longer history need an
explicit aggregate contract in phase 3; do not relabel the sample as total traffic.
Browser-local cards remain the first release. Account sync or MeshMapper login
needs a separately agreed authentication and ownership contract.

## First implementation: saved-route evidence

[Server #183](https://github.com/MeshCore-Beacon/beacon-server/issues/183) remains
open, with the server correction in [PR #192](https://github.com/MeshCore-Beacon/beacon-server/pull/192). The same fully resolved node chain can arrive with different hash widths,
while its saved prefix metadata currently stays at the first representation.
That can omit newer exact-path observations from route evidence.

Keep the stable IATA/node-chain identity. Define how the latest representation is
updated and how an already-open evidence page retains its selected representation.
Cover successive 1/2/3-byte paths, unchanged repeats, malformed/missing metadata,
ambiguous identities, cursor precision and shared-window behavior. Preserve exact
bytes and the existing bounded observation index; do not replace the query with
a broad short-prefix or raw-history scan. Avoid a schema change unless the agreed
behavior requires one. This phase must include a real PostgreSQL regression and
the exact combined Pi build before its preview is called verified.

## Parallel priorities, scheduled deliberately

- Operational work: remaining admin configuration scope, browser access and
  import/restore, deployment-file coverage and remote/scheduled backup under
  [server #60](https://github.com/MeshCore-Beacon/beacon-server/issues/60) and
  [#72](https://github.com/MeshCore-Beacon/beacon-server/issues/72).
- MQTT timeout attribution under
  [#116](https://github.com/MeshCore-Beacon/beacon-server/issues/116): collect
  evidence on recurrence or a meaningful workload change. A healthy short sample
  does not identify the historical cause.
- Complete translations under
  [web #12](https://github.com/MeshCore-Beacon/beacon-web/issues/12), with touched
  interface text translated in the same feature PR.
- Reconcile older open tickets against accepted code. Several observer, packet
  and route tickets were implemented through the consolidation batch; their open
  state alone is not a new feature gap. Close only after their full scope is checked.

## Shared acceptance criteria

Every new view defines its counting unit, effective period, available history,
sample size, missing data and ambiguity. Raw packets and observations cannot be
reconstructed after expiry; longer-lived summaries must state what they preserve.
Reuse the existing observer, packet, route, map and chart components. Load only the
selected data, coalesce updates, bound requests and test query plans on
representative data. New aggregation is justified by a measured query need.

Validate source and actual running artifacts, native PostgreSQL behavior, relevant
ingestion/reconnect regressions, desktop/phone, English/French, keyboard and shared
links. Publish matching source/changelog and preserve rollback without overwriting
new traffic. Compare CPU/memory/storage and latency against the preceding build;
a fixture or short Pi sample does not certify production capacity.

Maintainers control merges, version numbers, stable artifacts and the production
switch. `live.meshcore.ca` is the planned production destination; `dev.meshcore.ca`
remains development-only. The Canadaverse Pi remains the contribution preview.
