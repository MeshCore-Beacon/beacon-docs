# My Atlas and Topology after Beacon 2.0

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


Prepared on 2 October 2026 against server `98006a93645c9f8b09d2ea441a5776eecb9add02`
and web `39e921c277a8a1c8ba79db04131a6cc8fa27649d`. These are the published dev
commits introducing hourly rollups and empty-region handling. A stable 2.0 tag is
not published at this checkpoint. Recheck the final release refs before acceptance.

My Atlas and Topology remain post-release experiments. No release tag, production
deployment, database reset, retention change or review request accompanies this
preparation. Existing experimental PRs stay draft. The daily compatibility job
remains paused; this was a manually requested preparation pass.

## Small merge sequence

| Change | Focused commit | Parent and scope |
|---|---|---|
| My Atlas | [`d1eb973`](https://github.com/n30nex/beacon-web-contributions/commit/d1eb973b18d34ff4ff712992d9f5a63297431646) | Web dev `39e921c`; saved full-key cards, graphical samples, lazy details, existing inspection callbacks and English/French labels. No backend prerequisite. |
| Topology | [`8beb435`](https://github.com/n30nex/beacon-web-contributions/commit/8beb43598fc690f649a564f0efbc0dedb6af4e9d) | Apply after Atlas. Adds the canvas, bounded snapshot/live traffic, region isolation, camera controls and lazy scope metadata. |
| Optional Topology scope context | [`6ad59d3`](https://github.com/n30nex/beacon-server-contributions/commit/6ad59d31291b8abe6a7d2bd7a055de05dbeb319d) | Server dev `98006a9`; exposes cached discovered MeshMapper catalogues and the already-selected node-list default scope. No schema or query changes. |
| Exact route evidence, server | [`4fda8ed`](https://github.com/n30nex/beacon-server-contributions/commit/4fda8ed993c7fb130075c7e82fcc20c02e1fc321) | Follows the scope-context commit. Pins path bytes/width in evidence queries and cursors. Independent of either new page. |
| Exact route evidence, web | [`bc6f5c0`](https://github.com/n30nex/beacon-web-contributions/commit/bc6f5c045e1552d62c3f3ca17fbcbdf1fd13bf9e) | Follows Topology; uses upstream's combined Route Detail panel. Apply with server evidence support. |

The web feature stack lives on `codex/post-20-my-atlas`, `codex/post-20-topology`
and `codex/post-20-route-evidence` in the contribution fork. The server stack uses
`codex/post-20-topology-support` and `codex/post-20-route-evidence`. Review each
commit against its named parent rather than importing historical preview changes.
Atlas can land alone; Topology is deliberately stacked on its shared navigation
and cancellable node reads. Neither page depends on the exact-route evidence patch.

[My Atlas PR #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97) is refreshed
to `91a9541cd6fe27f76996c8f7e65fb07698783a98` and held as draft after 2.0. Its tree
is identical to the focused Atlas commit; the older PR ancestry is preserved without
a force push. There is no new Topology PR or reviewer request.

## Compatibility boundaries

- The prepared server's migrations, SQL queries, generated SQL, rollup workers,
  caches and retention configuration are identical to the named upstream baseline.
- The prepared web leaves upstream Analytics, region hooks, WebSocket manager and
  dependency manifests unchanged. Pages are lazy-loaded, use existing inspection
  panels, and do not add a rendering dependency.
- Atlas preserves `beacon-my-atlas-v1` browser storage and re-resolves an old server
  ID by the full public key after a database reset. My Atlas is first on desktop
  and mobile. Its 24h/3d displays describe a bounded raw-report sample, not durable
  rollups or a guarantee that every deployment retains three days of raw data.
- Topology uses existing node and saved-route endpoints. An empty selected region
  does not fall back to scanning global routes. Missing scope-catalogue support
  shows unavailable metadata while the graph and live traffic remain usable.
- Regional MeshMapper counts never create links or prove per-node scope membership.
  Only recorded neighbours and adjacent unambiguous path identities create edges.

## Combined experimental branches and validation

The combined `n30nex-test` heads are server `ae328cb6af31211b5935702853f09ad055d42546`
and web `9d3f95859255f4646799f7251afdeef26241364b`. Both contain their published dev
and main ancestors. The focused stacks reproduce exactly the combined source trees:
server `b7fc6bc81cb28e79e685dcb653632e10c769ed6a`, web
`26801ac745916a3fb85085cf917b4368d1683b7e`.

- Native ARM64 server build, vet and full Go suite passed: 715 top-level tests,
  including real PostgreSQL baseline/refusal, rollup, route-index and catalogue
  checks. The two separately opted-in backup/export tests were skipped.
- Native Node 24.15.0 web build, lint and all 1,180 tests across 137 files passed.
- Atlas alone builds and passes 36 focused tests; the Atlas/Topology stack builds
  and passes 14 focused Topology tests. The full prepared web also passed 77 focused
  Windows tests before the complete native run.
- Chromium checks used the exact native-built assets with recorded topology and
  WebSocket fixtures, plus a response matching the new rollup contract. They covered
  desktop and French phone layouts, keyboard focus, region isolation, all paths,
  pause/resume, full screen, reduced motion and 160 simultaneous live reports.
  The animation sample recorded zero static redraws and no page errors. This is
  fixture validation, not production-load proof or physical Safari testing.
- The dedicated validation database was created and removed. All 24 pre-existing
  Pi containers retained their IDs, start times and restart counts.

Local evidence is `F:/Beacon/evidence/release-20-prep-20261002/`. The source-tested
commits were server `4ef2712` and web `26edf55`; subsequent history-only merges have
identical Git trees. The paused web merge remains intact in its original checkout,
with an exported recovery patch and a separate clean successor.

## Preview and release handoff

The running Pi preview remains server `644960e4` / web `462d49e8`, with its existing
1.x migration ledger and history. **The prepared branches are ahead of deployment.**
Do not deploy the flattened baseline onto that ledger or relabel its source offer.
The new frontend also expects the new rollup API, so publish the compatible pair
together after the database/history decision.

Keep the existing source archives and rollback described in
[the preview record](n30nex-test-preview.md). After 2.0 is tagged, compare its exact
server/web heads with the bases above, refresh only affected packages, rerun their
checks, and obtain a separate fresh-database/history cutover decision. Maintainers
retain stable merges, release tags and the production-host switch. The earlier
1.4 handoff remains historical and is not a current 2.0 deployment instruction.
