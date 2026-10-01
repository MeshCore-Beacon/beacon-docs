# Experimental n30nex-test preview

The Pi preview now includes **Mesh Pulse**, a 3D topology with animated live packet
paths, alongside My Atlas and pinned route evidence. Work remains on `n30nex-test`.
Server #192 and docs #7 stay draft, with no new review requests. There is no new
web PR, stable release or production-host change.

[Open Mesh Pulse](https://canadaverse.org/beacon-dev/?tab=Topology) ·
[YOW and scope context](https://canadaverse.org/beacon-dev/?tab=Topology&topoRegion=YOW) ·
[Source and changelog](https://canadaverse.org/beacon-dev/source.html)

| Repository | Preview source |
|---|---|
| Server | `644960e4a6d6a1c02e10ace182f6d335358d3f44` — cached catalogue API and the node-list default-scope mapping correction |
| Web | `117ee99a60e6f7da352bb27a442eaae7f056706d` — connected layout, regional camera, saved routes and live trails; Atlas retained |
| Docs | `n30nex-test`, draft #7 — roadmap, contracts and this record |

## Mesh Pulse

- Native canvas perspective projection with connection-driven regional placement,
  separate islands sized for their populations, and connected-node spacing. Region
  labels and the camera selector focus a region; Isolate loads it alone. Pan/orbit,
  pinch/scroll zoom, keyboard controls, top/3D views and full screen are included.
  Focus and isolation survive shared URLs and Back/reload.
- Live packet reports animate only adjacent, single-candidate resolved hops. Missing
  or ambiguous identities leave gaps. Packet, node and reporting-observer actions
  open Beacon's existing investigation panels.
- Cross-IATA links and matching advertised default scopes have separate styles.
  MeshMapper regional catalogue metadata annotates matching scope context, without
  assigning aggregate counts to individual repeaters. The API lacks per-repeater
  identities. YOW is the currently configured source; other regions retain Beacon's
  observed defaults and explicit unavailable-catalogue state.
- The node-list correction exposes a field its SQL already selected. It adds no
  query per node. `/scope-catalogues` serves the existing importer's immutable cache;
  viewing or refreshing this page does not initiate upstream MeshMapper HTTP.
- All paths is the default: every loaded neighbour link plus adjacent resolved
  saved-route segments. The route window is 15 minutes by default, with one-hour
  and 24-hour choices. Live trails persist for 60 seconds. Region bundles and
  selected-node views are optional; live animations continue in every display mode.
- Bounded to 20,000 nodes, 60,000 recent routes, 100,000 links/live segments,
  10,000 reports per browser 60-second window and 512 simultaneous animations.
  A reached limit is visible. Static ink is cached separately from live motion,
  animation targets 30 fps, UI updates are coalesced and queries are cancellable.
  Pause, reduced motion, hidden-tab cleanup and English/French controls remain.
  No rendering dependency or database migration was added.

Groups use the latest receiving IATA, not geographic position; isolation includes
all loaded nodes heard in that IATA. Connection-driven placement reduces clutter
but does not guarantee zero projected crossings in a dense, fully visible graph.
Curve height is presentation only, not physical altitude. Stored neighbour
links have no selected time window. Motion illustrates a path, not measured RF
travel time, delivery or loss. Reports count packet/observer pairs received in this
view, with windowed deduplication and explicit pauses/reconnect gaps.

## Validation

The exact frontend passed native Pi build/lint and **1,078 tests in 122 files**.
The final native assets passed desktop and French 390px browser checks: all-path
visibility, 160 simultaneous report animations, no static redraws during a sampled
second of animation, full screen, regional camera, pan/zoom/fit, isolation,
Back/reload and reduced motion. The public site returned 1,991 nodes and 4,220
connections in the default window, or 5,041 connections after the 24-hour query
completed, with no cap warning. A fresh browser loaded the default view in 2.31s;
loading the longer route history took about 11s. These are observations, not a
load-capacity guarantee. The live check received 112 real reports, including 84
with resolved paths, and no page errors.

Windows builds and browser checks passed. One local Node 22 validation process
exited with an access violation; the unfinished Windows full suite was stopped.
The exact candidate's complete suite passed using Node 24.15.0 on the Pi.
Physical iPhone/Safari and sustained production-load qualification are not claimed.

Native Go/PostgreSQL tests pass for the server, including scope cache freshness,
concurrent snapshot readers, disabled/invalid sources and node-list scope projection.
The first combined replay passed all 3,200 inputs in 12.73 seconds after frontend
validation was serialized. The earlier missing-fixture setup failure and concurrent
20-second drain timeout are retained in the evidence. The final response-mapping
patch passed the native suite and replay in 16.28 seconds, with all 3,200 inputs and zero fixture drops. These fixtures do
not establish universal losslessness or production capacity.

Public verification checks all 24 frontend files, both corresponding sources,
26 boundaries, the Public channel and both MQTT feeds. The scope catalogue check
returned nine YOW names. Source generation/check times and stale errors remain
visible. The short initial runtime sample showed app CPU of 3.22–6.25% and about
40–42 MiB memory. Database activity varied, including a brief one-core spike; a
follow-up sample was lower. A 355-second full-mesh browser sample measured about
19.5% main-thread task time and 19.3 MB JS heap. These samples are not a controlled
before/after benchmark or a physical-phone performance certification.

## Current frontend recovery — 1 October

The connected-layout update changes only static frontend files. All 24 published
files and both corresponding-source archives match; the source/changelog is current.
Every existing container identity and restart count was unchanged by deployment.
Server `644960e4`, schema 045, configuration and the 72h raw/30d summary policy remain.

Latest rollback is `evidence/topology-camera-20261001/deploy-beacon-web.py rollback
--evidence-dir topology-camera-20261001`, checkpoint `web-20261001T231151Z`. It restores
web `4b2497df` while keeping the server and new traffic. Use this frontend rollback
before the older backend recovery recipes below.

The new patch applies cleanly to the prepared 2.0 web checkout. The whole experimental
branch still has 14 dev merge conflicts inherited from the 2.0 transition; main
trial-merges cleanly. The earlier prepared-integration receipts below apply to their
recorded upstream revisions and do not establish compatibility with newer dev.

## Upstream 2.0 landed during this phase

Upstream server `3ac4035` replaces the migration chain with `001_baseline.sql` and
explicitly refuses legacy databases. Web `6de673b` prepares 2.0.0 and adds the
maintainer's analyzer/scope corrections. The live preview retains its 1.x database
and source pair; no history reset or migration-ledger relabelling was performed.

The new upstream bases conflict with the legacy preview branches. Clean integration
commits are prepared **locally and separately** on `codex/topology-2-integration`:
server `835d1cdd4887576a6ca0cb687ef8077b73640f33`, web
`f2317febb5775234c5b684115685871544aecdff`.
Trial merges pass against current dev and main. The server was checked against a
separate fresh PostgreSQL database, including baseline installation, refusal of the
old ledger, pinned route evidence and the scope changes. Web build and 47 affected
checks pass. These integration commits are not deployed or submitted for review.

Server CI passed on the initial `a5c8d28` head. The later legacy head has no new
GitHub checks because the upstream migration change conflicts with its base; do
not describe that head as CI-green or merge-ready. The separately prepared
integration resolves those conflicts. Choosing a fresh preview database and the
availability of retained history is the next cutover decision. The raw-retention
proposal (24h dev / 7d production) has not changed this Pi's 72h raw / 30d summaries.

## Recovery

All backups remain private, restored and checksum-verified on and off the Pi.
The response-mapping fix uses
`evidence/topology-scope-list-20261001/deploy-server.py rollback`, checkpoint
`scope-list-20261001T020111Z`, to restore server `a5c8d28` with web `c5265037`.
To undo the whole Mesh Pulse phase, run that recovery first, then
`evidence/mesh-topology-20261001/deploy-server.py rollback`, checkpoint
`mesh-topology-20261001T010811Z`, restoring `af2604a6` / `b99b6e77`.

The previous frontend-only recovery is
`evidence/topology-scope-list-20261001/deploy-beacon-web.py rollback --evidence-dir topology-scope-list-20261001`,
checkpoint `web-20261001T022604Z`, restoring web `c5265037` with server `644960e4`.
The backend rollback above applies that frontend recovery first when necessary.

The earlier frontend-only rollback for Mesh Pulse is
`evidence/mesh-topology-20261001/deploy-beacon-web.py rollback --evidence-dir mesh-topology-20261001`,
checkpoint `web-20261001T014625Z`; it is paired with server a5c8d28, so undo the later
response-mapping fix first. All recoveries preserve new traffic. No schema or
configuration change was made, and unrelated containers were preserved.

Daily checks at 09:00 America/Toronto remain checks only. See the
[phased roadmap](post-140-roadmap.md) for the 2.0 integration decision, constrained
live follow, label/detail refinement, shared display preferences and bounded replay.
