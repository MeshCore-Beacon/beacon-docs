# Meshat review candidates for Beacon

Status: review options only, 4 October 2026. Adding an item here is not implementation
approval, an assigned task or a promised release. Return to the [project roadmap](post-140-roadmap.md).

## Baseline and evidence

The supplied Meshat report describes archived v1 at
[`f4c505b`](https://github.com/Bjorkan/meshat-beacon/tree/f4c505b07a2b4a47ddf6b90a0756968d795741f5).
Its [upstream integration record](https://github.com/Bjorkan/meshat-beacon/blob/f4c505b07a2b4a47ddf6b90a0756968d795741f5/beacon-docs/UPSTREAM_SYNC.md)
separates imported Beacon capabilities from retained fork work. The report's
39 headings include supporting API/migration/PR summaries, not 39 independent gaps.

The comparison used released server
[`0015430`](https://github.com/MeshCore-Beacon/beacon-server/tree/001543032f4da4c532b59491f643f4e6911c4011)
and web
[`7a9770e`](https://github.com/MeshCore-Beacon/beacon-web/tree/7a9770e71399d1235359802b046111876e547d6c)
(v2.0.0), plus the v2.0.1 deltas: server `0dca03c`, web `7fb2478`.
It is a source-level review, not a live/dev deployment audit. The reported CoreScope
user migration and fork benchmarks are not independently verified causal/performance evidence.

## Review first

- **Realtime correctness:** inspect global broadcast loss, per-write WS deadlines and
  Retry-After shared state. Released `Broadcast` logs/drops before fan-out when its
  queue is full; client-buffer lag notices are not the same case. `noteRequestOk`
  clears the shared rate-limit state on any successful response. These are candidates
  for focused reproduction/regressions, not claimed production incidents.
- **Resolved list-hop names:** bounded optional REST packet/backfill and trace-summary
  enrichment, preserving raw hashes/confidence and avoiding one detail fetch per row.
  Existing detail/WS resolution and captured endpoint snapshots are not absent.
- **Current IATA-membership freshness:** distinguish current membership from historical
  reception. Last-heard metadata alone is not an expiry policy for an otherwise active node.
- **Contact QR/deep links:** a small client-side MeshCore handoff candidate. Validate
  full keys/name/type, generate locally and qualify real supported clients.

## Larger choices and dependencies

- **Global collision/confidence semantics:** released resolution/reconfirmation is
  IATA-scoped; existing confidence labels and breaks at unmappable hops already help.
  Decide how global ambiguity and useful contextual diagnostics coexist.
- **Directional neighbor SNR and provenance:** replace last-valid-value dependence
  with bounded samples, counts, age and explicit receive direction where justified.
  Separate fresh direct confirmation from inferred edges. An observer's terminal
  receive SNR is not every hop's SNR; opposite directions are not interchangeable.
- **Calculated route planner:** weighted best/alternative graph routes and export are
  additional to known-route search/cross-IATA composition. Define confidence,
  direction, freshness, bounded computation and stale-snapshot behavior first.
  Retain observed-route history; a proposed route is not proof of RF reachability.
- **Transit-node packet history:** additional to originating-node observations. Needs
  indexed retained evidence, ambiguity-aware attribution and separate TRACE semantics.
- **Retained-history search:** broader path/payload/observer search, not only loaded
  client rows. Bound/index it and disclose expired evidence.
- **Generalized server-side sorting/keysets:** cursor paging already exists; extend
  full-dataset ordering, tie-breakers and filter-bound cursors where required.

Dependencies: confidence/provenance and directional freshness precede a trustworthy
planner; indexed evidence precedes traversal/search; server ordering precedes a UI
promise of globally sorted results. Sizes and implementation owners remain undecided.

## Optional or targeted improvements

Consider API contract generation/drift checks, app-lifetime WS-to-query cache policy,
URL-owned list filters and intent preloading as focused maintainability work rather
than mandatory framework migration. Lightweight node mini-maps, radio-setting titles,
scoped unknown-channel totals and semantic mobile sorting need concrete user benefit.
A firmware-reported MeshCore region model is separate from IATA geography and transport
scope. Privileged observer-owner ingestion needs an explicit producer/privacy contract.

Observer expiry is not wholly missing: released Beacon already has opt-in cleanup
that preserves observers referenced by retained observations, telemetry or ownership.
Meshat's snapshot-before-delete policy is a separate lifecycle decision. Treat its
visual/a11y/runtime audit as reproducible test cases, not dozens of proven current bugs.

## Already covered or unsuitable for wholesale import

Released Beacon already has the MapLibre 6 missing-image resolver, pending-region
guards, reconnect-specific heartbeat state, React Query, virtualization, lazy heavy
views and localization. Swedish is in v2.0.1. It also wires and matches WS route-type
and observer filters: importing Meshat's removal would discard working functionality.
View on map already exists; a node mini-map and MeshCore contact handoff are separate.

Do not copy the whole router/Radix/DataTable/marker stack, Swedish deployment defaults,
single-broker restriction, a hard 150 km RF cutoff, fixed seven/fourteen-day retention,
or pre-2.0 migration numbers. Preserve useful uncertainty, unknown/zero distinctions,
historical evidence, license/author attribution and deployment-specific choices.

## Reconcile against the current preview before implementation

The [4 October preview checkpoint](post-140-roadmap.md#current-preview-checkpoint-4-october-2026)
now documents TRACE wire validity, conflicting identity handling, suspect-observation
filtering and protection against promoting requested/unvisited hops into observed
routes. Recheck that source before treating every Meshat TRACE/collision item as a
remaining preview gap. Ordinary-path resolution, full global confidence policy and
rolling directional link quality remain separate review topics.

The new bounded Topology link snapshot is an undirected adjacent-pair read model,
not Meshat's weighted route planner or proof of radio delivery. Public chatter is
not general channel analytics. Compact Atlas telemetry is not complete node/fleet
history. Experimental delivery does not establish upstream release acceptance.

## Evidence anchors and selection gate

- [Released routing handlers](https://github.com/MeshCore-Beacon/beacon-server/blob/001543032f4da4c532b59491f643f4e6911c4011/internal/api/handlers/routes.go) and
  [node handlers](https://github.com/MeshCore-Beacon/beacon-server/blob/001543032f4da4c532b59491f643f4e6911c4011/internal/api/handlers/nodes.go).
- [Neighbor/membership/retention queries](https://github.com/MeshCore-Beacon/beacon-server/blob/001543032f4da4c532b59491f643f4e6911c4011/db/sqlc/queries.sql.go).
- [Hub filtering/overflow](https://github.com/MeshCore-Beacon/beacon-server/blob/001543032f4da4c532b59491f643f4e6911c4011/internal/hub/hub.go),
  [WS handler](https://github.com/MeshCore-Beacon/beacon-server/blob/001543032f4da4c532b59491f643f4e6911c4011/internal/ws/handler.go) and
  [client rate-limit state](https://github.com/MeshCore-Beacon/beacon-web/blob/7a9770e71399d1235359802b046111876e547d6c/src/api/rate-limit.ts).
- [Existing MapLibre resolver](https://github.com/MeshCore-Beacon/beacon-web/blob/7a9770e71399d1235359802b046111876e547d6c/src/features/map/useMapLibre.ts).
- [Meshat planner API](https://github.com/Bjorkan/meshat-beacon/blob/f4c505b07a2b4a47ddf6b90a0756968d795741f5/beacon-server/internal/api/handlers/routes.go) and
  [additional node APIs](https://github.com/Bjorkan/meshat-beacon/blob/f4c505b07a2b4a47ddf6b90a0756968d795741f5/beacon-server/internal/api/handlers/nodes.go).

Before selecting work: verify the current target branch and existing issues/PRs,
identify remaining preview versus upstream gaps, define the counting/evidence and
compatibility contract, agree bounded acceptance tests, and assign an owner. Nothing
in this brief starts implementation or removes existing release/automation holds.
