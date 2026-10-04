# Beacon primary roadmap: 2.1–2.2

**Primary planning authority — adopted 4 October 2026.** This is the roadmap
Torchlight and the Canadaverse preview work should use going forward. It records
the operator-supplied planning discussion and MrAlderson's follow-up. It supersedes
the older parity roadmap's release priorities, not its historical evidence.

These are agreed goals, **not a declaration that the features are implemented,
hardware-qualified, accepted upstream or deployed**. Track completion against
reviewable code, tests and the actual environment. Keep the 2.1 scope focused.

## 2.1.0 — Foundations

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

## 2.1.1–2.1.9 — Telemetry and collection in Atlas

- Expand telemetry collection and its presentation within Atlas incrementally.
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

## 2.2 — Complete Atlas and refine Topology

- Complete the agreed Atlas experience, including accepted telemetry and
  collection integration.
- Refine Topology using observed usability feedback and the current implementation.
- Fix major and minor defects and address measured performance problems across
  the accepted system. Broader feature ideas remain separately prioritized backlog.

## Future interoperability — firmware-direct telemetry (FW01)

**🟢 Keep the direction; 🟡 design and integration remain. No release assigned.**
The [owner's 4 October clarification](https://discord.com/channels/1507764602253869197/1507788454774182030/1556384736522281032)
keeps collaboration with repeater and observer firmware projects open, including
projects like [MeshCore Observer](https://observer.gessaman.com/).

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
This future direction does not add a new 2.1/2.2 delivery requirement, authorize
firmware changes or imply remote console/control support.

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
states, checkpoints, issues/PRs, source revisions and preview verification. Future
ideas do not automatically become 2.1 requirements. Escalate scope changes instead
of silently adding them to a release.

## Supporting evidence and history

- [Current preview](https://canadaverse.org/beacon-dev/) and
  [published build metadata](https://canadaverse.org/beacon-dev/build.json).
- [Torchlight project dashboard](https://canadaverse.org/torchlight/).
- [Collector research and earlier design discussion](docs/beacon-21-collector-design.md):
  useful implementation evidence; conflicting earlier priorities yield to this roadmap.
- [Broader parity backlog](docs/post-140-roadmap.md): supporting backlog, not the
  default release sequence.
- [Previous roadmap and dated checkpoints](https://github.com/n30nex/beacon-docs-contributions/blob/483e71188fb000eeb33db080936573c06e96f8a2/ROADMAP.md)
  remain preserved in Git history. Old deployment, version and rollback statements
  are historical and must not be applied as current operating instructions.
