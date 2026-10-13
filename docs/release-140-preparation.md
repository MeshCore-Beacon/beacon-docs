# Beacon 1.4.0 release and CoreScope cutover

The planned Beacon/web release is **1.4.0**, replacing the earlier 1.3.2 proposal.
Alderson reviews and releases the candidate, then controls the production switch.
This document prepares that switch; it does not claim that either MeshCore Canada
host has already changed.

## Destinations

| Destination | Intended role | Update policy |
|---|---|---|
| `https://live.meshcore.ca` | Production Beacon 1.4.0, replacing CoreScope after approval | Reviewed release images pinned by digest; changes require an owner rollout |
| `https://dev.meshcore.ca` | Development testing only, kept online | Separate application, database, cache and saved configuration; deliberate updates from `dev` |
| `https://canadaverse.org/beacon-dev/` | Contributor review candidate | Exact PR revisions, corresponding source and retained rollback; not the production endpoint |

Production REST and WebSocket traffic must terminate at the production Beacon
backend. Do not point the production frontend at `dev.meshcore.ca`. A development
restart, migration, test or data reset must not alter production data or routing.
Use separate deployment directories and persistent storage. If environments share
a host, review the existing proxy, internal port bindings and available capacity
before starting a second stack; the Type 1 defaults assume one standalone stack.

## Review candidates

| Repository | Candidate | Scope |
|---|---|---|
| Server | [#189](https://github.com/MeshCore-Beacon/beacon-server/pull/189), `61b0322a5d2041987f154b7cea3870e848723890`, based on `14354b03` | Stable image publishing and rollout documentation; includes accepted Zones API, partial-telemetry cleanup 045 and corrected counter buckets; drains readiness probes in the shared test helper |
| Web | [#105](https://github.com/MeshCore-Beacon/beacon-web/pull/105), `157525ef3dd517e74cd40a404d5512ef14603845`, based on `e2d272e0` | Package/lock version 1.4.0, explicit deployment image selection and stable publishing; includes accepted observer/sidebar/device and packet-analyzer changes through #111 |
| Docs | [#5](https://github.com/MeshCore-Beacon/beacon-docs/pull/5) | Environment roles, pinned deployment inputs, release checklist, validation and recovery |
| Web, deferred | [My Atlas #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97) | Excluded until after 1.4.0; retains its single feature PR and saved-card design, but requires conflict resolution against current dev |

The server has an independent release history with **v1.6.0 already published**.
1.4.0 identifies the Beacon/web release; do not retag or downgrade the server.
Record its approved revision, independently chosen stable version and image digest
alongside the web release. The mobile repository is outside this release's scope.

Accept the reviewed server/web changes, verify the resulting CI heads, and accept
docs #5 so the canonical operator-guide links resolve. New upstream changes after
the validation snapshot require a diff review and applicable checks before they
join the production candidate. No Atlas changes belong in either release artifact.

## Release notes draft

- Observer monitoring combines packet activity, device telemetry and comparison,
  with the shared observer sidebar and labelled device details. The duplicate
  Observer page in Analytics is removed; comparison remains available there.
- Packet, observer, node, route and map links provide retained evidence for
  investigation. Endpoint and path ambiguity remain visible rather than implying
  a uniquely identified sender, relay or delivery path. Packet analysis uses a
  single observations list.
- MeshMapper scope metadata and optional boundary imports improve regional views;
  configured fallbacks and missing/unknown scope states remain explicit.
- Hourly analytics preserve summaries after raw packet expiry. Raw packet detail
  remains limited by configured retention; expired observations are not reconstructed.
- English/French navigation, compact phone controls and on-demand packet maps
  improve presentation. Atlas remains outside this release.
- Ingestion, route maintenance, cache invalidation, location reset handling and
  partial-telemetry filtering, counter bucketing and deployment image separation
  include the accepted reliability/performance fixes.
  Production capacity still needs validation on its intended host.

## Image publishing and configuration

Both application repositories currently have `dev` as their default branch. The
release PRs remove the rule that published `latest` from that default branch.
The official metadata-action v5 bundle was exercised with these events for both
repositories; all eight cases passed without publishing any images:

| Event | Published tags |
|---|---|
| Push to `dev` | `dev`, revision tag |
| Push to `main` | revision tag |
| Stable semantic-version tag | full version, major/minor, `latest`, revision tag |
| Prerelease tag | prerelease version, revision tag; no `latest` |

Existing registry tags are not rewritten by merging the workflow. The owner must
verify the new stable Actions run, its source revision and image digest before
using its output. A local Pi binary or frontend build is preview evidence, not a
substitute for the approved production release artifacts.

The complete Type 1 deployment now requires `BEACON_SERVER_IMAGE` and
`BEACON_WEB_IMAGE`. Select the exact reviewed tags for staging, then pin the
published digests for production. Do not use `latest` or `dev` as a production
deployment input. The web repository's standalone `docker/` folder serves only
the frontend; use the complete Type 1 proxy or explicitly configure production
`/api/*` and `/ws` routing to the matching backend.

| Setting | Production | Development |
|---|---|---|
| `DOMAIN` | `live.meshcore.ca` | `dev.meshcore.ca` |
| `VITE_API_BASE` | `https://live.meshcore.ca/api/v1` | `https://dev.meshcore.ca/api/v1` |
| `VITE_WS_URL` | `wss://live.meshcore.ca/ws` | `wss://dev.meshcore.ca/ws` |
| `BEACON_WEB_IMAGE` | Approved 1.4.0 release image digest | Reviewed `dev` build or its digest |
| `BEACON_SERVER_IMAGE` | Approved matching server image digest | Reviewed `dev` build or its digest |
| Database/cache/configuration | Production-owned copies | Development-owned copies |

Frontend URLs are injected into the published web image at startup. Recreate
the frontend when changing them and verify the browser's actual destinations.
Review saved CORS and WebSocket origin settings for the appropriate host and the
existing trusted-proxy chain. Keep credentials and private connection strings in
the operator's secret/configuration store, not this document or the release notes.

## Data continuity and migration

Use a separate production Beacon database. The proposed rollout seeds it from a
fresh, restore-tested snapshot of the approved Beacon dataset, then validates and
starts its own ingest. The original development database remains with development.
An empty production start is an explicit alternative for Alderson to approve,
with its cold-start and history limits communicated before cutover.

CoreScope's schema is not a Beacon migration source. Preserve a separate CoreScope
backup and its configuration/images for recovery; no automatic CoreScope history,
settings or saved-node conversion is included. Record the earliest available raw
packets and summaries in the production copy instead of promising unavailable
history. The historical counter discrepancy is not resolved by changing products.

The agreed candidate policy remains **72-hour raw packets, 30-day hourly summaries
and 720-hour telemetry**. Migration 043 clears stale zero/omitted advert positions;
044 adds separate imported zone-boundary storage; 045 deletes partial telemetry
rows where noise floor and both airtime counters are zero. Preserve those rows in
a private export before migrating. The code skips uptime-only radio-stat updates
and ignores invalid counter dips/replays/spikes. Test migrations on a restored
copy before applying them to the production Beacon database. Verify raw counts,
retained summaries and unaffected node locations. Keep the pre-change dump,
application images, configuration and proxy route available for rollback.

The new Zones API importer is separately opt-in. When enabled, imported boundaries
override manual `borderFile` shapes; manual shapes remain the fallback where the
API has none. The contributor preview keeps its 26 reviewed manual boundary files,
scope importer and Public channel configuration. Automatic zones, public admin,
public backup and foreign-node classification are not enabled by this release prep.

## Owner cutover sequence

1. Freeze the accepted server/web revisions and verify their CI. Publish web
   `v1.4.0` through the repository's release workflow, choose the server version
   independently, and record both image digests and matching source offers.
2. Save the current `live.meshcore.ca` CoreScope routing, configuration, images and
   database backup. Confirm the rollback route before changing public traffic.
3. Stage the production Beacon pair behind the existing ingress without replacing
   CoreScope yet. Restore the approved Beacon snapshot into its separate database,
   apply and validate migrations, and verify both broker inputs and retention.
4. Check the production candidate's observer dashboard/comparison, Analytics,
   packets, channels, nodes, routes, traces and maps. Check English/French, desktop,
   physical iPhone Safari, keyboard access and Back behavior. Verify the candidate's
   requests reach its own REST/WebSocket endpoints and that older CoreScope browser
   sessions load the new assets correctly.
5. Compare a representative busy period for accepted/dropped input, database load,
   process CPU/memory and request latency. Fixture replay and a short healthy Pi
   sample do not establish production capacity. Keep any profiling private and bounded.
6. After Alderson's approval, switch the `live.meshcore.ca` web/API/WebSocket route
   together to Beacon. Keep CoreScope available for the agreed rollback window.
   Leave `dev.meshcore.ca` serving its development stack; do not redirect it to live
   or remove its service while cutting over production.
7. Verify public TLS, version 1.4.0, exact deployed digests/source, API reads, live
   subscriptions, fresh packet arrival and working regional outlines. Verify dev
   independently remains reachable and uses only its development backend/data.
8. If acceptance fails, restore the saved CoreScope route and its matching backend.
   Preserve the new Beacon database for diagnosis; do not restore an older dump over
   newly received traffic. Binary-only Beacon rollback needs a reviewed compatible
   schema; otherwise use the retained separate database checkpoint.

## Validation and remaining release decisions

The exact PR heads are deployed at the review site and its footer shows 1.4.0.
The refreshed pair is server **61b0322a** on accepted dev **14354b03**, and web
**157525ef** on accepted dev **e2d272e0** through #111. This replaces the earlier
#107 cutoff at the contributor's request. Current-base checks and published-head
CI pass; web CodeQL remains skipped under existing policy.

Native PostgreSQL tests, restored-copy migration 045 and the 3,200-input replay
pass. The restored copy removed 485 partial telemetry rows while preserving raw
counts, retained telemetry and node fingerprints. All 489 matching live rows were
saved separately before migration. The replay retained 100 packets / 800
observations / 100 decrypted messages and 800 ordinary / 2,400 opted-in events,
with zero fixture drops in 12.51 seconds. The readiness-test race is fixed in the
shared helper and both affected tests passed 100 repetitions.

Windows and Pi frontend build/lint and all **1,035 tests** pass. Prior eight
tag-generation and six configuration-rendering receipts apply to unchanged
workflow/template content. All 21 public assets, source archives and 26 boundaries
match. Desktop/French phone browser checks and live delivery pass. The 40-second
runtime sample had fresh traffic and no recorded queue overflow, SQL error,
fallback, reconnect or panic; it does not establish production capacity.
See the [exact candidate record](release-140-heads.json).

The private checkpoint is `sync140-cutover-20260930T204913Z`, restored and
checksum-verified on and off the Pi. The matching partial-row export is retained
alongside it. Combined recovery is
`python3 evidence/sync-140-20260930/deploy-server.py rollback`.
It first restores the previous frontend when necessary, then restores server
**9054acd8 / web 23945d59**. New traffic and the compatible telemetry cleanup stay
in place; use the private row export for selective recovery if needed. Do not
overwrite newly received traffic with the old full database dump.

Frontend-only recovery is
`python3 evidence/sync-140-20260930/deploy-beacon-web.py rollback --evidence-dir sync-140-20260930`,
checkpoint `web-20260930T211410Z`. It keeps server 61b0322a and restores web
23945d59. The backend update left 23 other containers unchanged; frontend
publication left all 24 unchanged. Configuration and retention were preserved.

The current upstream UI has 24h/7d/30d controls, including raw-evidence views, and
old 3d observer links select 7d. This conflicts with the earlier requested 24h/3d
raw-history controls. Alderson must resolve that requirement or explicitly accept
the changed behavior before release; the version change does not resolve it.

Production-host capacity, the actual CoreScope cutover and physical Safari
validation remain owner acceptance steps. No official host, stable tag or upstream
merge was changed by this refresh. The earlier
[1.3.2 preparation record](release-132-preparation.md) and dated receipts remain
historical; use the current recovery commands for this deployed pair.
