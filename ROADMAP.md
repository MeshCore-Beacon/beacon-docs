# Beacon primary roadmap: 2.1–2.5

**Primary planning authority — adopted 4 October 2026.** This is the roadmap
Torchlight and the Canadaverse preview work should use going forward. It records
the operator-supplied planning discussion and MrAlderson's follow-up. It supersedes
the older parity roadmap's release priorities, not its historical evidence.

The [owner-delegated version allocation](https://discord.com/channels/1507764602253869197/1507788454774182030/1556399330699640893)
was added by **[Torchlight]** at the
[owner's request](https://discord.com/channels/1507764602253869197/1507788454774182030/1556400784885809313).
These are agreed planning targets, **not a declaration that features are implemented,
hardware-qualified, accepted upstream or deployed**, nor fixed delivery dates.
Track completion against reviewable code, tests and the actual environment. Keep
2.1 focused; move a target when its evidence, compatibility or qualification requires it.

## Versioning and status rules

- **🟢 KEEP / EXISTS:** useful or already present, not a blanket stability claim.
  **🟡 TARGET / VERIFY / DESIGN:** work or qualification remains.
  **🔴 NO SLOT:** a rejected duplicate/default, or work explicitly outside this plan.
- Small compatible fixes and enhancements can use patch releases. Substantial new
  workflows or coordinated required API changes belong at a minor-version boundary.
  Reserve major-version review for genuinely incompatible changes, not feature size;
  an additive database migration alone does not require 3.0 or a fresh-database reset.
- This allocation is informed by Beacon's history, not a claim of a comprehensive
  formal SemVer policy: [web 1.3.0](https://github.com/MeshCore-Beacon/beacon-web/releases/tag/v1.3.0)
  and [server 1.6.0](https://github.com/MeshCore-Beacon/beacon-server/releases/tag/v1.6.0)
  bundled substantial features; 2.0 introduced an incompatible database baseline;
  [web 2.0.1](https://github.com/MeshCore-Beacon/beacon-web/commit/7fb24789d1649aa079e4568d335d60b3400d87be)
  added Swedish and [server 2.0.1](https://github.com/MeshCore-Beacon/beacon-server/commit/0dca03cd4dae1b6061df5078a4390be33b9ed475)
  corrected catalogue refresh/defaults.
- The [upstream release policy](https://github.com/MeshCore-Beacon/beacon-docs/blob/f0d5632ad9833305745f54ff1bb2c0e2bb413f8f/docs/releases.md)
  keeps server and web on the same **major.minor**, with independent patch numbers.
  A web patch must not unexpectedly require a newer server patch: provide graceful
  fallback, or introduce the required contract at a minor boundary. Apply the same
  discipline to the incremental collection work. API-path versioning is separate.
- Patch numbers below are movable working slots, not simultaneous server/web tag
  promises. Release-blocking or urgent fixes go into the earliest safe release,
  including 2.1.0 where needed, rather than waiting for an allocated number.
  Official release tags and upstream acceptance remain maintainer-controlled.
- Preview versions such as `2.2.1-n30nex.1` do not mean upstream 2.2 has shipped.
  R/D/X identifiers refer to the [feature decision register](docs/post-20-feature-decisions-20261004.md).

## 🟡 2.1.0 — Foundations

- Add the basic **Atlas and Topology pages**, using the existing preview as the
  starting point rather than introducing a competing workflow.
- Include an initial **Beacon agent** implementation/scaffold. Its precise
  component responsibilities and acceptance criteria need to be written down
  before implementation; “initial” does not mean a fully completed agent.
- Have the **MQTT layout and setup working**: document the topics, message
  contracts, identity/authorization boundary and setup flow, then demonstrate an
  end-to-end accepted sample. Do not confuse MQTT intake permissions with RF
  polling permission.
- MrAlderson will help with Atlas. Keep ownership and remaining work visible
  without assuming a contributor has completed or accepted an unreviewed change.
- Preserve the current Topology approach as the baseline; gather specific feedback
  on appearance and interaction instead of expanding this release into a redesign.

## 🟡 2.1.1 — Correctness

- Target confirmed WebSocket-loss/backoff/write-lifecycle fixes (R01), API-filter
  and input validation (R02), TRACE correctness (R03), unclipped/bounded trace rows
  and reliable error states (the corrective parts of R04/R07).
- Reproduce individual cases and preserve existing working mechanisms; the supplied
  B1–B9 checklist is not nine automatically confirmed bugs. Keep changes compatible.
- Release-blocking fixes belong in 2.1.0 rather than waiting. This correctness slot
  does not displace the agreed collection programme or approve unrelated features.

## 🟡 2.1.2–2.1.9 — Telemetry and collection in Atlas

- Expand telemetry collection and its presentation within Atlas incrementally.
  These are working slots within the adopted 2.1.x collection programme, not a
  requirement to publish every numbered patch or defer work already safe to deliver.
- The **mobile application is an opt-in collector**, connecting to a companion
  radio over BLE and running in the phone background where the operating system
  permits. Background/BLE reliability must be qualified, not assumed.
- Provide the alternative **Windows/Linux USB-serial collector**, running in the
  tray/background after a simple one-time setup.
- Let users select local repeaters from the companion's contact list and supply
  guest/admin credentials locally when required. Never publish those credentials
  in dashboards, issues, source repositories or telemetry payloads.
- Use the same conservative polling contract on both clients: no more than one
  polling attempt per target per hour, a three-hop eligibility limit, initial flood
  discovery, reuse of learned/saved routes and a rate-limited flood fallback.
- Send collected readings through the agreed API/intake contract. Beacon should
  show verified, attributed samples on each node's Atlas card or its linked node
  view, with freshness, units, sensor channel and visible gaps.
- Coordinate the mobile client, desktop collector, Atlas and server API as one
  end-to-end feature, retaining their separate responsibility boundaries.
- Keep collector safety, reconnect reliability and truthful missing-data handling
  ahead of unrelated routing/search work (R05/R07/D05). Preserve cross-patch
  compatibility using the established intake contract, optional fields and fallbacks.

## 🟡 2.2.0 — Complete Atlas and refine Topology

- Complete the agreed Atlas experience, including accepted telemetry and
  collection integration.
- Refine Topology using observed usability feedback and the current implementation.
- Fix major and minor defects and address measured performance problems across
  the accepted system.
- Target the coordinated additions at this minor boundary: bounded cached topology
  links (R06), resolved packet/trace-list summaries (R04), configurable current
  IATA-membership freshness that preserves history (R09), and focused API-contract
  checks/live-cache consistency (D04).
- Qualify API/UI pairs, query costs, caps, stale/unknown data and compatibility.
  Undirected topology links are not directional SNR measurements or a route planner.

## 🟡 2.2.1 — Small usability additions

- Contact QR/deep links and bundled radio-preset names with raw-setting fallback (R08).
- URL-persisted filters, keyboard/accessibility improvements and mobile sorting over
  already-supported server ordering (D04).
- Reuse existing components and pending contributions rather than duplicating them.
  A new mandatory backend sorting contract belongs in the later minor release.

## 🟡 2.2.2 — Optional visual polish

- Mini-maps, legends, theme-aware maps, saved display preferences and bounded,
  optional Public chatter (D06), using existing APIs and honest position labels.
- Measured rendering improvements and low-power behavior, not an unrequested UI rewrite.
- Do not invent SNR quality; directional SNR-coloured links wait for the evidence
  model in 2.3.0. Optional polish is not a blocker for core 2.2.0 acceptance.

## 🟡 2.2.3 — Firmware interoperability pilot (FW01, conditional)

**🟢 Keep the direction; 🟡 partner/contract qualification remains.**
The [owner's 4 October clarification](https://discord.com/channels/1507764602253869197/1507788454774182030/1556384736522281032)
keeps collaboration with repeater and observer firmware projects open, including
projects like [MeshCore Observer](https://observer.gessaman.com/).
The earlier unassigned goal now has a **conditional 2.2.3 pilot target**, not a
partner commitment or date. If it needs a new mandatory server contract, move it
to the next minor release; if partners are not ready, defer without blocking 2.2.

Wi-Fi-capable devices should be able to opt in and configure a Beacon deployment's
telemetry collection endpoint, submitting their own readings through the shared,
versioned API/intake contract. This complements mobile/USB collectors rather than
requiring an intermediary phone or computer for a device's own telemetry. Keep the
producer contract reusable across clients; do not tie it to one firmware vendor.

Before claiming support, agree and qualify:

- Endpoint selection, explicit enable/disable and scoped enrollment, authentication
  and revocation. Wi-Fi and node administration credentials stay local, never in
  telemetry payloads; intake permissions do not grant remote radio administration.
- Device/producer identity and provenance, sample timestamps, units and optional
  sensor fields. Missing/null values must not become fabricated zero readings;
  authenticated provenance is not hardware attestation or guaranteed sensor truth.
- Bounded upload cadence, retries/backoff, offline buffering and duplicate handling,
  with honest freshness/gaps in Atlas/node cards. Transport/schema details and
  partner compatibility remain design work; no endpoint shape is promised here.
- Coexistence with existing observer MQTT packet/status ingestion. Uploading a
  device's own readings over Wi-Fi is not an RF poll. If firmware also polls peers,
  the existing polling budgets, hop constraints and qualification gates still apply.

The reference project's public setup page documents Wi-Fi and MQTT configuration;
that is not verification of native Beacon telemetry-API support or a collaboration
agreement. No partner outreach or firmware qualification has occurred in this update.
This is not a core 2.1/2.2.0 acceptance requirement, authorization to modify firmware,
or remote console/control support.

## 🟡 2.2.4+ — Maintenance

Fix defects, tune measured performance and deliver compatible refinements. Do not
use patch releases as a dumping ground for new database-heavy subsystems or let
these placeholder numbers delay an urgent fix.

## ❕ 🟡 2.3.0 — Evidence and investigation (new minor)

- Directional SNR aggregation with sample count/age, direct/inferred provenance,
  edge aging, movement invalidation and global versus contextual ambiguity (D01).
- Bounded indexed transit-node history and retained-history search, broader
  server-side sorting/keysets, and node/trace investigation capabilities (D03).
- Distinguish origin reports from attributed relay evidence and requested TRACE
  paths. Define retention/counting, indexes, migration/recovery and production-like
  query costs before selecting implementations. Terminal receiver SNR is not every hop.
- Evidence-backed SNR styling may follow only after the data model is qualified.
  Scope each contribution; this target is not permission for a monolithic rewrite.

## ❕ 🟡 2.4.0 — Calculated routing (new minor)

Best/alternative routes and MeshCore export (D02) follow the qualified 2.3 evidence
model and bounded graph/query design. Show stale snapshots, retain observed-route
history and test supported client exports. A proposed route is not proof of RF
delivery. This release does not depend on completing replay or unrelated analytics.

## ❕ 🟡 2.5.0 — Replay and deeper analysis (later review target)

Historical playback/seek, geographic analysis and deeper fleet/channel analytics
are a later, separately scoped review target. They require retained/indexed evidence,
honest coverage/gaps and measured query/rendering cost. Hourly aggregates cannot
reconstruct expired packet paths. Keep these workflows separable from routing.

## 🔴 No slot, or explicitly undecided

- X01 already-covered capabilities and X02 unsuitable imports receive no new port
  slot. Keep working upstream modules; reject their duplicates, not the capabilities.
- Remote administration, privileged owner-data feeds and firmware-region catalogue
  integration remain separately undecided pending product/privacy/producer contracts.
- No 3.0 is scheduled merely because the backlog is large. A genuinely incompatible
  API, data or configuration change requires an explicit major-version decision and
  upgrade/recovery design; no fresh-database reset is planned by this document.

## Collector safety and acceptance gates

The one-hour minimum is a maximum polling rate, not an instruction to transmit
every hour regardless of congestion. Longer intervals and deferred attempts remain
valid. Restarts, reconnects, failures, parallel collectors and manual refreshes must
not bypass the budget. Login, retries, discovery and route fallback must be counted
and bounded; uploading an already-collected sample is not a new RF poll.

The **three-hop requirement is agreed**, but a known route length does not by
itself cap flood propagation. Before promising a hard RF reach limit, verify what
the companion firmware and API can enforce. If it cannot be enforced, defer that
poll and report the limitation; do not silently change the radio configuration or
describe an unrestricted flood as “three hops.”

“Verified” means the intake contract's authenticated/validated provenance and
accepted sample checks. It must not imply hardware attestation or guaranteed sensor
truth unless those capabilities are implemented and demonstrated.

Use persistent per-target scheduling, conservative shared-radio budgets, bounded
backoff and congestion checks. Cross-client duplicate-poll protection remains a
wider-rollout qualification gate. No remote reboot, arbitrary radio CLI or general
administrative control is implied by this roadmap.

## Development and delivery

Prepare reviewable work against the agreed upstream `dev` base and keep the
Canadaverse forks/preview independently verifiable. MrAlderson requested a branch
handoff and a `dev1` image/workflow that the development host can pull. Record its
exact branch, image/tag contract and maintainer approval before changing that host.
This document does not itself enable a workflow, merge upstream or deploy to
`live.meshcore.ca` or `dev.meshcore.ca`.

Torchlight may carry out authorized preview-fork development under its existing
standing authority. It should use this roadmap to prioritize and maintain task
states, checkpoints, issues/PRs, source revisions and preview verification. Planning
allocation does not authorize starting every feature. Escalate scope/compatibility
changes instead of silently adding them to a release.

## Supporting evidence and history

- [Current preview](https://canadaverse.org/beacon-dev/) and
  [published build metadata](https://canadaverse.org/beacon-dev/build.json).
- [Torchlight Dashboard — Beacon Project Tracker](https://canadaverse.org/torchlight/).
- [Collector research and earlier design discussion](docs/beacon-21-collector-design.md):
  useful implementation evidence; conflicting earlier priorities yield to this roadmap.
- [Feature decision register](docs/post-20-feature-decisions-20261004.md): source-backed
  R/D/X recommendations and acceptance gaps; the allocation above now supplies targets.
- [Broader parity backlog](docs/post-140-roadmap.md): supporting backlog, not the
  default release sequence.
- [Roadmap before this version allocation](https://github.com/n30nex/beacon-docs-contributions/blob/41b51adbad048f69e4059d06db1c4aae2154de46/ROADMAP.md)
  preserves the original 2.1–2.2 plan and initially unscheduled FW01 clarification.
- [Previous roadmap and dated checkpoints](https://github.com/n30nex/beacon-docs-contributions/blob/483e71188fb000eeb33db080936573c06e96f8a2/ROADMAP.md)
  remain preserved in Git history. Old deployment, version and rollback statements
  are historical and must not be applied as current operating instructions.
