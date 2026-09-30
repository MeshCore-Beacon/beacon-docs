# Server/web consolidation release

## 1.3.2 release preparation — 30 September

The Pi now serves server `397d76b3` / web `eb241ca7`, with Atlas excluded. All seven server release PRs are accepted in dev `89a376c2`, whose source tree exactly matches the running server; no rebuild or relabel was needed. Web #75 → #79 → #80 → #81 → #83 → #85 → #87 → #89 → #92 → #95 → #99 is published and passes checks. The native/Windows release build passes all 955 tests, and all 21 public assets and source archives match.

My Atlas #97 is held for after 1.3.2 at `66ae0cc2`, directly after #99. Its requested copy/order changes, Windows/Pi 975 tests, CI and browser checks pass; it is not deployed. External server #182 and web #93 remain separate gates.

[Current audit, exact heads, validation and recovery](app_documentation/release-132-preparation.md). [Live candidate and source](https://canadaverse.org/beacon-dev/source.html). Maintainers retain web acceptance, tags, version decisions and production rollout. Earlier dated records below are historical.

## Owner release gates for 1.3.2

- [x] Accept the seven server release PRs. Accepted dev `89a376c2` has passing CI and the same tree as the validated running server.
- [ ] Re-review and accept the eleven release web PRs through #99; check CI on the accepted merge result.
- [ ] Accept docs #5 so the canonical operator links in server #172/#174 resolve. Merge the remaining web sequence in dependency order.
- [ ] Decide separately whether server #182 and web #93 belong in the cut. The current tested composition excludes them; do not silently label an untested combination as this candidate.
- [ ] Confirm the deployed source/binary pair on the affected MeshMapper host, its packet/summary retention, broker inputs, bounded queues, and private rollback. Apply reviewed border files only where manual boundaries are missing.
- [ ] Compare matched busy periods for accepted/dropped inputs, database work, process CPU/RSS and request latency. The Pi replay and short runtime sample do not certify production capacity. If using #182, keep profiles private and bounded.
- [ ] Check the main operator journeys on desktop and physical iPhone Safari, including English/French, Back, dialogs, maps and expired records.
- [ ] Promote the accepted web source to main and cut **web v1.3.2** under the repository's release process. Choose the server version independently of its existing v1.6.0 tag. Publish matching source and retain rollback artifacts.
- [ ] Leave My Atlas #97 out of the release. Keep its one feature branch based on the accepted release work and refresh it after any squash/rebase merge before post-release acceptance.

## Historical Atlas preview — 29 September

[Web #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97), `4fd4b0de`, is the single My Atlas feature PR requested by the contributor. It follows #95 at `e1133ab5` and closes [web #96](https://github.com/MeshCore-Beacon/beacon-web/issues/96) on acceptance. Earlier application PRs remain included; no parent was rebased for this feature.

My Atlas sits in the desktop tab row and the phone More menu. Visitors save up to twelve full-key node identities, order and a 24h/3d window in this browser. Compact cards show reception bars, SNR/RSSI meters and server freshness; Heard by and statistics expand on demand. Search collapses on return visits. Node, observer/dashboard and exact packet/path investigation reuse the existing navigation. English and French ship together.

Counts are explicitly the latest **200 retained origin-key reports per node**, filtered to the selected period. Companion requests and other identified-origin packets are included as well as adverts. This is not a complete node-traffic total. Heard by describes the latest loaded packet, not lifetime reach. Missing readings, expired details and incomplete samples remain visible; no radio-health or packet-loss score is invented.

The Pi now runs unchanged server `a35cba1d` with web `4fd4b0de`. Windows and native Pi build/lint/all **960 tests** pass, along with the actual published-head CI (web CodeQL skipped). Desktop, French 390px phone, keyboard, persistence/order/removal, packet/observer links and dashboard Back checks pass. The public 19 assets and both source archives match, both MQTT feeds are connected, and all 24 container identities/restart counts are unchanged. Physical iPhone Safari and full production capacity remain separate release gates.

[My Atlas preview](https://canadaverse.org/beacon-dev/?tab=MyAtlas) · [Changelog and source](https://canadaverse.org/beacon-dev/source.html). Frontend rollback restores `e1133ab5` with server `a35cba1d`, from `web-20260930T004937Z`. For an older backend rollback, restore this frontend first, then use the existing September 29 backend recipe; its guard intentionally rejects an unknown newer frontend.

The contributor explicitly prioritized My Atlas for this phase. Next: refresh maintainer feedback and issues, then server #183 before optional MeshMapper boundaries. Broader issues and remaining parity work stay open. All eighteen application candidates are out of draft; maintainers retain acceptance, merges, stable releases and production cutover.

See [My Atlas validation and recovery](app_documentation/my-atlas-20260929.md).

## Earlier integration gate — 29 September

All six server reviews are addressed in their existing PR sequence. The fixes restore analytics indexes, consolidate unmerged migrations, preserve current partial activity buckets, align cache windows, narrow the route index, keep manual scope priority and simplify channel insertion metadata. Independent server #184 fixes RFC3339 offsets; new web #95 follows #92 and matches time choices to retained data. Existing candidates remain included.

The Pi runs server `a35cba1d` / web `e1133ab5`. All seventeen published application heads pass Check/CI (web CodeQL skipped); native Go/PostgreSQL and Windows/Pi web build/lint/all 940 tests pass. The restored-copy repair preserved raw rows and archive fingerprints, and rollback index restoration passed. A 3,200-input/504-scope replay had all expected rows/events and zero fixture drops. The one-minute live sample had no parser fallbacks, queue overflows, SQL errors, restarts or reconnects; malformed-IATA and clock-skew warnings remain.

Visible periods are **24h / 3d** for observer monitoring and route evidence, and **24h / 3d / 30d** for summary-backed Analytics. Seven-day buttons are removed. Raw comparison spans are capped at three days. Durable hourly aggregates already preserve expired packet counts; materialized views combine them with live rows. Older summaries accumulate after archiving starts, and packet detail remains unavailable after expiry. Revised labels and notes are English/French.

Current acceptance still requires maintainer re-review, especially #167/#169/#174. No upstream merge, stable release or production cutover was performed. The next focused issue is server #183 (saved-route prefix-width changes); broad partial issues remain open. External server #182 and web #93 are unmerged and not in this tested composition. Owners decide the release breakpoint and production switch.

See [review corrections, source heads and recovery](app_documentation/review-release-20260929.md). No stable release is claimed until maintainers accept the reviewed application heads and choose the release artifacts.

## Packet reception investigation — 27 September

[Web PR #83](https://github.com/MeshCore-Beacon/beacon-web/pull/83), `1d5d65e2807c2cb53a998743212d9a5b64ba80c4`, follows #81 and closes focused issue #82 when accepted. It adds grouped retained packet reports, selected-report links, observer inspection/dashboard access and a selected-path map. The initial list stays compact and keeps the selected group open. Equal prefixes are not treated as confirmed identical physical routes; empty/missing paths and TRACE intended routes have explicit labels.

Map projection omits ambiguous/unlocated identities and breaks lines at gaps. Live animations across uncertain chains are suppressed, so fewer speculative lines appear. Unavailable selected paths no longer silently show All paths. A shared-path loading race is fixed by checking the requested packet hash. Packet labels use the existing Noto Sans stack; external basemap emoji-glyph/sprite fallback warnings can still occur.

At the packet-investigation checkpoint, the Pi ran web `1d5d65e` with unchanged server `88c2c10c`. Native build/lint and all **906 tests** pass; focused Windows checks and desktop/390px phone/English/French/keyboard/Back/shared-link checks pass. Public assets and source match, both MQTT feeds are connected, and the frontend publication restarted no services. Earlier review candidates remain included. The [changelog/source](https://canadaverse.org/beacon-dev/source.html) identifies the running build. Maintainers still own merges, stable releases and production cutover.

**Historical follow-up:** route evidence, observer return navigation and MeshMapper scope import were subsequently delivered as review candidates; see the current roadmap. Broader server #60/#72/#99/#116 and web #12 remain open; this is a first connected-investigation slice, not full parity.

## Observer release checkpoint — 27 September

The observer-first release is implemented in four focused review candidates: [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) (`91b21995`, closes #168), [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) (`3a0eb4c8`, closes #76), [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) (`b3a6b088`, closes #77) and [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) (`42ae09b7`, closes #78). All are out of draft. Server #169 follows #167; web order is #75 → #79 → #80 → #81. Independent server #166 remains in the preview composition. Maintainers control acceptance and release; these issues remain open until their changes are accepted.

At the observer-release checkpoint the Pi ran composed server `88c2c10c830034cee70a46fca717af518803a544` and web `42ae09b7c6be50cd0f617bad8aea35825be9f12e`, with the [updated changelog and exact source](https://canadaverse.org/beacon-dev/source.html). Raw packets remain 72 hours, archived hourly analytics 30 days, telemetry 720 hours. All four candidates passed their native Pi suites; the final web build passes 895 tests. Server tests use actual PostgreSQL. Windows server/full destination/dashboard validation and 48 focused final comparison/API tests also pass. Desktop, 390-pixel phone, English/French, keyboard, legacy/shared links and Back/search/sort/scroll were checked. Physical iPhone Safari and production-volume capacity remain separate gates.

Migration 040 preserves original rows and repairs available archived unknown-payload counts without inventing signal samples. A restored clone passed the migration probe. A fresh private dump was copied off the Pi and its checksum verified; the original schema039 database and matching binary/config/source are retained for DB-aware rollback. Only the Beacon app restarted for the server change; 22 other containers were unchanged. Frontend publication restarted no services. Both MQTT feeds reconnected. Public admin, backup and foreign detection remain disabled.

Use the [current roadmap](ROADMAP.md) and [observer release contract](app_documentation/observer-monitoring-plan.md) for the current queue. The sections below retain earlier dated validation; their old preview/rollback identities are historical and must not be used as current deployment instructions.

## September 26 retention and endpoint fixes

The Pi was first matched to accepted dev server `91b4b457` / web `54b5093a`, including native validation and a verified restore across migrations 037/038. At that checkpoint it ran composed server `a8394f10` and web `3a18e6d1`, adding three focused review candidates:

| PR | Head | Scope / closure |
|---|---|---|
| [Server #166](https://github.com/MeshCore-Beacon/beacon-server/pull/166) | `74f16de8` | First/renamed adverts resolve after the node update; closes #164 |
| [Server #167](https://github.com/MeshCore-Beacon/beacon-server/pull/167) | `76428b1b` | 30-day hourly summaries survive raw packet expiry; closes #165 |
| [Web #75](https://github.com/MeshCore-Beacon/beacon-web/pull/75) | `3a18e6d1` | Additional-match count and all endpoint candidates on hover, keyboard or touch; closes #74 |

All are out of draft. Exact-head build CI passes, server CodeQL passes, and web CodeQL remains skipped. MrAlders0n/Claude review was requested in PR comments because formal review requests are unavailable to the contributor account. Both server PRs are independent on the same accepted dev and may merge in either order. Web #75 is also independent. The workflow records #167 plus #166 as a complete PR/head preview input; its separate manifest can be refreshed after upstream changes. No routine manual restacking is required for these non-overlapping changes. No upstream PR was merged by the contributor.

The agreed Pi policy is **72-hour raw packets, 30-day hourly analytics and 720-hour telemetry**. Migration 039 archives compact summaries as each raw packet cohort expires, atomically with deletion, without storing bodies or raw paths. Traffic, payload, top observers, talkers, advertisers, observer activity, Signal and Paths use the retained summaries. Already-purged history cannot be recovered. Packet detail, sub-hour activity and exact observer comparisons still use retained raw data; entity/scope/radio population counts keep their current meaning.

Full Windows and native Pi Go/PostgreSQL checks pass, including rollback on archive failure, retries, concurrent ingestion, late observations, distinct observers across batches, multiple IATAs, nullable/radio/path semantics and independent 30-day expiry. The full frontend build/lint and **874 tests** pass. A 1,001-packet fixture with 1KB bodies compacted to at most twelve archive rows; the first Pi run took 85ms for archive/deletion, which is a fixture measurement rather than a production-throughput guarantee. A restored copy of the actual preview database retained all eight view counts after every raw packet was deleted in a rolled-back test. Source/index hashes and the public candidate popup were verified.

Migration 039 preserved fingerprints of all 23 original application tables. The actual prior schema038 database, exact binary/configuration and private dump remain available for rollback; older pre-038 recovery is retained separately. Only the Beacon preview app restarted (about 33 seconds); 22 other containers were unchanged and both MQTT feeds reconnected. Public admin/backup and foreign detection remain disabled. [Current changelog and corresponding source](https://canadaverse.org/beacon-dev/source.html).

Current broader issues remain server #60 (admin), #72 (backup/import), #99 (packet summaries), #116 (MQTT investigation), and web #12 (remaining translations). Prioritize feedback and acceptance of these new fixes, then a focused Mesh/Talkers/Observer translation slice under #12. A measured month of accumulated history, production-scale capacity and physical Safari checks remain separate gates. Maintainers own stable releases and the owners handle production cutover.

## Historical consolidation scope (24 September)

Release the accepted account/backup/analytics batch before Channel Activity or further parity expansion. Current public tags are server v1.6.0 and web v1.3.0; maintainers choose the next versions and perform signed release commits, main promotion and tags under each repository's contribution rules.

The deployment owner performs the eventual CoreScope switch. Beacon remains at dev.meshcore.ca, CoreScope at live.meshcore.ca, and the Pi preview remains at canadaverse.org/beacon-dev/ with its changelog and corresponding source.

The release candidate includes both formerly independent follow-ups: [server #160](https://github.com/MeshCore-Beacon/beacon-server/pull/160) for offline archive verification and [server #161](https://github.com/MeshCore-Beacon/beacon-server/pull/161) for ACK/TRACE/PING summaries. Their wider issues #72 and #99 remain partial. Integrity checks do not establish archive authenticity or restorability; packet references do not establish identity or delivery.

Accepted server: `c02317a4ac7228d19cab498edfa1d61186c84626`.
Accepted web: `0f0a6ca51c7b2c3315db77954f61b30bbdeea5e2`.
The web source tree is identical to tested preview `42ba5fcb`; preserve that artifact's actual revision/source instead of relabeling it. The server differs from preview `5848d200` only in the verifier CLI/library/tests/docs; its verifier code and tests are identical to separately tested `262eae96`. The documentation additionally contains the accepted protected-download section.

## Historical review gates (24 September)

- [x] Workflow checks include every independent preview PR, not just the ordered stack. Status reports them; Check verifies their CI and source; Refresh/Publish reject changed prepared inputs. Server #161 and web #61 are covered by the normal preview checks. The standalone backup CLI #160 is checked with its separate manifest.
- [x] Server #149: document POST/DELETE browser preflights and the full admin CORS method example. Keep public read-only defaults.
- [x] Server #154: verify pg_dump/server compatibility at startup; an optional backup prerequisite failure disables only backup, with a specific operator diagnostic. Document backup.enabled and distinguish the export size limit. Native testing caught and fixed the text-versus-integer version-setting scan; CI now covers it with PostgreSQL.
- [x] Server #157: serve Signal distributions and weighted means from compact materialized data; snap polling windows to hours, preserve missing/invalid/legacy sample semantics, and measure refresh/storage costs.
- [x] Server #159: materialize path classification, share window parsing, guard database-derived array indexes and retain all 256 decoder-header checks.
- [x] Web #60: shared map-location validation in independent #61 omits reset/invalid markers and links while preserving valid zero-axis locations and stored records. Native and real-data browser checks pass.
- [x] Web #58: distinct navigation glyphs in #59, plus dedicated RF/Signal and Paths glyphs in #55/#57.
- [x] Refresh #55/#57 after the accepted #52/#53 squash. Their source trees were identical after the September 20 refresh; that history-only update needs no replacement Pi artifact.
- [x] All eight application PRs pass their required checks on the published heads. Native PostgreSQL tests ran. The upstream web CodeQL job remains skipped under its existing policy and is not counted as a scan.

All original six server and four web PRs are merged. The September 25 translation batch is accepted through web #70, with #63/#64/#65/#66/#69 closed as included; #68/#72 also merged and #67/#71 are closed. New server #162/#163 and web #73 are accepted. At that checkpoint only docs #5 remained open. Active application manifests are empty, acceptance history remains, and no application branch was rewritten.

## Storage and retention boundary

The September 17 drop-and-reset observation-partitioning design and implementation plan were explicitly superseded on September 19. They are historical reference only. Do not implement their table drop, history reset or process-local dedup replacement.

Accepted server #162 now supplies batched retention deletes, per-table autovacuum tuning in migration 037 and a seven-day default packet/chat retention when unset. #163 adds migration 038, dropping per-observation endpoint snapshots and resolving against current nodes at read time. The earlier partition/reset proposal remains superseded. Compression changes were not added by these two migrations.

A consolidation release must document its actual retention behavior and capacity limits. A future production parity cutover also needs verified durable history coverage and recovery copies. Do not infer either from example configuration or the Pi's short history.

Current dev is server `91b4b457` / web `54b5093a`, with passing CI/image builds (server coverage/CodeQL pass; web CodeQL skipped). The Pi still runs server `c02317a4` / web `9d96b943`, equivalent to web source accepted through #72, with prior 867-test native evidence. It lacks server #162/#163 and web #73. The current frontend rollback is `300ee974`. No new deployment/migration occurred in the September 26 audit. Before upgrading, verify a database recovery checkpoint and explicit retention policy: old server queries reference the column removed by 038, so restoring only the old binary afterward is not a valid rollback.

## Accepted-dev verification - 24 September

- [x] Exact dev CI/image builds pass at server `c02317a4` and web `0f0a6ca5`; server CodeQL/coverage pass and web CodeQL remains skipped.
- [x] Server `c02317a4` built/tested natively on the Pi with real PostgreSQL: 1,194 passing test/subtest results. Signal, Paths, observer comparison, migration recovery, packet summaries and NULL observations ran. Two opt-in backup export/download integration suites were skipped; prior private restore/TLS checks remain separately dated evidence.
- [x] Accepted server is running on the preview. Source/asset hashes match; both feeds advance. Signal/Paths reconcile with SQL for global/regional 1/7/30-day selections, at 2-19 ms origin latency. Only three complete hours are populated; this does not prove 7/30-day history coverage.
- [x] Browser Signal/Paths charts and map load with LIVE status and no captured warnings/errors. Unchanged frontend assets keep their actual `42ba5fcb` build/source identity and prior 786-test evidence; accepted `0f0a6ca5` has the identical tree.
- [x] Only the Beacon app restarted; the other 22 containers and configuration/migration journal were preserved. Immediate rollback is server `5848d200` with unchanged web. The separate verifier retains its real `262eae96` binary/source identity.
- [x] Accepted review queues/overlays were retired, including the translation ancestors verified as included in #70. All application PRs are accepted. Only docs #5 and the five broader issues remain open.

## Earlier combined-candidate evidence - 20 September

- [x] September 20 unmodified Pi stability sample: 600 seconds / 41 samples, both feeds connected, 2,169 retained observations and no MQTT disconnect/deadline or HTTP 5xx. App/PostgreSQL CPU averaged 2.14%/3.96% of one core. This is a bounded health sample, not callback timing, #116 root-cause proof or a production-volume gate. [Result and limits](https://github.com/MeshCore-Beacon/beacon-server/issues/116#issuecomment-5753626821).
- [x] Native Pi build/test of server `6be0f762` and web `42ba5fc`, including real PostgreSQL-to-HTTP checks and migration retry/concurrent refresh; 786 web tests pass.
- [x] One-million-row request/initial-population/refresh/storage measurements; request plans read only the new views. Signal: 1.8–77.5 ms reads, 14.4 s initial population, 16.8 s refresh, 6.5 MB. Paths: 3.5–141.9 ms reads, 8.4 s population, 6.2 s refresh, 11.3 MB.
- [ ] Measure the full operator workload and sustained refresh/ingest load before a production parity claim. The million-row fixture does not establish that limit.
- [x] Backup client mismatch and unsupported-DSN cases leave the public API available; valid client export/restore used disposable data only and restored all 35 source migrations. Public preview admin/backup remains disabled.
- [x] Real preview analytics reconcile with SQL for the materialized window. Browser charts, complete-hour text, small screens and error/empty/retry states are verified. Both MQTT feeds advance and the public browser reports LIVE.
- [x] Current and rollback server/web artifacts, exact source offers and visible changelog match the running pair. Only the Beacon app restarted; the other 20 containers were preserved. Additive rollup migrations retain observations and are compatible with the previous binary.

The historical pre-retention rollback restored combined frontend `300ee974` with server `c02317a4`. Restore accepted frontend `42ba5fcb` before using the older consolidation server rollback to `5848d200`; its metadata describes the accepted frontend. The September 20 packet-reference rollback to `6be0f762` is an older recovery point. Exact artifacts/runners are retained; application rollback keeps additive rollup views and does not remove history.

## Maintainer release handoff

1. Review current server #166/#167/#169 and web #75/#79/#80/#81. Preserve dependencies; choose an explicit release freeze and validate its actual heads. Ready for review is not owner approval or a published release.
2. Review migration 039/040 and the verified database-aware recovery boundary. Deploy server metrics before dependent observer pages; retain packet/summary counting definitions and approved retention settings.
3. Follow each contribution guide for signed version/API commits, main promotion, tags and release CI. Reconcile stable web history instead of overwriting main. No versions or tags were chosen by this contribution.
4. Verify exact Actions-built release artifacts, corresponding source, upgrade/retention guidance and rollback on the intended deployment. Owners perform the eventual production switch.
5. Keep broader #60/#72/#99/#116 and web #12 open for their remaining scope. Continue connected investigations after feedback, with the scope-import draft separate. Physical Safari, sustained production workload and a measured month of retained history remain validation gates.
