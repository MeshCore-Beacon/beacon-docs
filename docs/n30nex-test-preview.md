# Experimental n30nex-test preview

## Current: released 2.0 base and verified preview — 3 October 2026

The [Pi preview](https://canadaverse.org/beacon-dev/) runs server **8c7fbb8** and
web **7e139d5**, retaining My Atlas, Topology and node/route work on top of the
published **2.0.0** release. Experimental tags are `v2.1.0-n30nex.2` (server) and
`v2.1.1-n30nex.1` (web). Stable release and production ownership remain upstream.

At the user's request, the preview matches released defaults: **7-day raw,
90-day summaries, 31-day observer telemetry, 14-day routes**. The runtime values
were verified. The previous 30-day-summary documentation was wrong; the previous
runtime already used 90 days. Legacy history is still intact.

This patch fixes camera resets on refreshed Topology data/layout, retry/error
feedback on node and telemetry pages, and optional telemetry collections. Private
Collector alpha.4 rejects missing/null readings instead of inventing zero; its
source and intake database remain separate from Beacon core. The current signed
HTTPS path passed real companion checks with no extra RF polling or fake samples.

Validation: **753 server tests, 1,259 web tests**, native PostgreSQL/build/vet/lint,
**31 preview API checks**, exact public assets/source archives and sampled browser
journeys. Two optional backup tests and physical Safari/BLE coverage are not claimed.
All changes are preview/repository work; the earlier production inspection was
read-only and stopped when the user redirected the scope.

[Audit findings and next gates](post-20-audit-20261003.md) ·
[Merge sequence](post-140-roadmap.md) ·
[Current preview source](https://canadaverse.org/beacon-dev/source.html).


## Historical: early 2.1 experimental preview — 3 October 2026 UTC

The web branch subsequently advanced to **f7637aa** for a single trailing-blank-line cleanup. The actual deployed and full-suite-tested web source remains **4b189dff**, correctly identified by its public source archive; this formatting-only branch difference has not been relabelled as a new deployment.

The user approved **private collector repository + separate intake service**, fresh
preview history with the old database intact, and continued exclusive collector use
of the RemoteTerm radio. These direct decisions supersede older cutover/restore
holds below. RemoteTerm stays **stopped and disabled** until the user asks for it back.

`n30nex-test` is now server **fe4c4156** / web **4b189dff**, incorporating upstream
server dev **af20beb** / web dev **0924260** and main. Both application branches and
experimental tags are published to the contribution forks. My Atlas and Topology
remain experimental; server #192 and Atlas #97 remain draft. No review ping or
upstream stable release was made; daily automation remains **PAUSED**.

The Pi publicly runs those exact server/web revisions. Core uses the new
`beacon_post21_preview_20261002` database (001 baseline); the old **beacon_dev**
with its 045 ledger is intact. The old dump was restore-tested and its SHA-256
verified on/off Pi. Raw/summary retention stays 72 hours/30 days.

Beacon Collector intake **84b0d22** runs in its own container and dedicated
`beacon_collector_preview` database/role. Its repository is **private**, with the
existing license unchanged. Public telemetry routes go to this service; Beacon
core has no collector table, migration or package dependency. Never push the local
embedded prototype history (`1b10530` through `633a380`) into public Beacon refs.
The public server was composed from its clean parent instead.

753 native server checks and 1,255 frontend tests passed, plus build/lint/vet,
real PostgreSQL checks, the 3,200-input replay (zero fixture drops), exact public
assets/source hashes and automatic signed HTTPS enrollment/delivery. Two opt-in
backup/export tests were skipped. The replay exceeded its original 20-second
shared-host budget and passed at 22.80 seconds with a 60-second allowance; this
is not a production throughput guarantee.

Five configured repeaters have returned telemetry: Hilltop, Weaver, Royal City,
Starkey and Royal Relay. Reservoir still times out. Hilltop supplied real channel-2
temperature/humidity/pressure as well as battery. Missing data and timing gaps stay
visible. Normal polling keeps 1–72-hour intervals and congestion checks; no test
bypass is shipped. Hardware attestation and cross-client polling leases are not
implemented. The collector defaults to Canadaverse until a later Beacon release.

Current paired rollback: `evidence/post21-final-20261003/deploy-preview.py rollback`
on Pi; checkpoint **post21-cutover-20261003T014506Z**. It restores the retained
legacy container/config/frontend while preserving the new core and telemetry DBs.
The private DB dump is **post21-fresh-20261003T002912Z**. Old rollback commands are
historical and must not be applied directly against this pair.

Canonical state: `planning/experimental-n30nex-test.json`; public source offer:
https://canadaverse.org/beacon-dev/source.html. Final evidence is under
`evidence/post21-final-20261003`. Keep the old dirty `topology-web-2-integration`
checkout untouched. Docs changes were preserved in `docs-n30nex-test` and prepared
in `docs-telemetry-20261003` for integration.


## Prepared branch versus deployed preview — 2 October

The prepared 2.0 branch heads are server `ae328cb6` and web `9d3f9585`, including
upstream hourly rollups. They have not been deployed. The table below continues
to identify the actual running binaries/assets and their matching source offer.
[Post-2.0 feature packages and validation](post-20-integration.md) describes the
clean merge sequence. Daily compatibility checks remain paused; no database reset
or review request is authorized by this preparation.

The Pi preview now includes **Topology**, a 3D topology with animated live packet
paths, alongside My Atlas and pinned route evidence. Work remains on `n30nex-test`.
Server #192 and docs #7 stay draft, with no new review requests. There is no new
web PR, stable release or production-host change.

[Open Mesh Pulse](https://canadaverse.org/beacon-dev/?tab=Topology) ·
[YOW and scope context](https://canadaverse.org/beacon-dev/?tab=Topology&topoRegion=YOW) ·
[Source and changelog](https://canadaverse.org/beacon-dev/source.html)

| Repository | Preview source |
|---|---|
| Server | `644960e4a6d6a1c02e10ace182f6d335358d3f44` — cached catalogue API and the node-list default-scope mapping correction |
| Web | `462d49e8afb2fabf54f20832318a0f7ae0a0d77d` — My Atlas first, simpler Topology controls and camera orientation correction |
| Docs | `n30nex-test`, draft #7 — roadmap, contracts and this record |

## Topology UI and navigation — 1 October

My Atlas is the far-left desktop tab and the first mobile tab. Nodes remains in the
mobile More menu. Topology uses a compact status/count header and one region selector.
The main toolbar contains region, route window, pause and node search. Display holds
path modes, camera presets, drag mode, animation, legend, sharing and refresh.

The inspector opens when a node is selected or searched. Phones reuse the existing
focus-trapped details sheet. Closing details returns to the graph; search from full
screen first exits full screen so its input is visible and focused. Live activity,
reporters and packet details are expandable and continue receiving data while closed.
Scope metadata is fetched only when the inspector is open.

The camera now looks down from above the mesh. Its projection previously placed the
camera below the plane even for Top view. Raised points are now nearer the camera;
pan follows the corrected axes, and Fit centres projected bounds before scaling.
Pan is the default drag action, Shift-drag rotates, and Display offers Top/3D views.
The graph stays visible while a new route window loads, with an updating indicator.

All-path visibility, live packet animation, full screen, region focus/isolation and
English/French controls remain. This is a frontend-only update on `n30nex-test`.

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

The exact frontend passed native Pi build/lint and **1,079 tests in 122 files**.
Windows build, changed-file lint and all 30 focused navigation/topology tests passed.
The above-mesh regression checks depth, apparent scale and screen position of raised
nodes; framing and pan tests cover desktop and portrait dimensions.

The final native browser fixture verified Atlas first on desktop/mobile, one region
control, inspector focus (including search from full screen), French phone menus,
expanded activity, pause/resume, retained chart data during window loading, region
focus/isolation, reduced motion and 160 simultaneous animations. Static ink did not
repaint during the sampled second of packet animation. Public checks verified Atlas
navigation, Back, default all-path visibility and mobile focus/menu bounds. The
public browser loaded the view in 2.68s and received 138 real reports, 99 with
resolved paths, with no page errors. These are bounded observations, not a sustained
load-capacity guarantee. Physical iPhone/Safari qualification is not claimed.

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

The UI update changes static frontend files only. All 24 assets, both source archives
and the source/changelog match. All 24 existing containers were unchanged. Server
`644960e4`, schema 045, configuration and 72h raw/30d summary retention remain.

Latest rollback is `evidence/topology-ux-20261001/deploy-beacon-web.py rollback
--evidence-dir topology-ux-20261001`, checkpoint `web-20261002T000512Z`. It restores
web `117ee99a` without changing the server or new traffic. Use it before the previous
connected-layout and backend recovery recipes below. The checkpoint uses UTC.

The combined camera/UI patch applies cleanly to the prepared 2.0 web checkout.
The whole branch still has 14 dev conflicts at `f9ffb564`; main trial-merges cleanly.
The experiment remains on `n30nex-test`, with draft reviews held and no new web PR.

## Previous connected-layout recovery — 1 October

The connected-layout update changes only static frontend files. All 24 published
files and both corresponding-source archives match; the source/changelog is current.
Every existing container identity and restart count was unchanged by deployment.
Server `644960e4`, schema 045, configuration and the 72h raw/30d summary policy remain.

That phase’s rollback is `evidence/topology-camera-20261001/deploy-beacon-web.py rollback
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
