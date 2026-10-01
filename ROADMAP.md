# Beacon parity and analytics roadmap

## Beacon 1.4.0 combined candidate — 30 September

The requested refresh now includes Alderson's latest accepted server **14354b03** and web **e2d272e0**, plus our release PRs. The Pi review site runs **server 61b0322a / web 157525ef**, from server #189 and web #105. This supersedes the earlier #107 cutoff. Web #108–#111 provide the shared observer sidebar, labelled device details, unified packet observations and removal of the duplicate Observer page in Analytics. The server includes the partial-telemetry and counter-bucketing corrections.

**Beacon/web remains 1.4.0**, replacing the planned 1.3.2 release. My Atlas #97 is excluded until after 1.4.0 and still needs conflict resolution against the accepted release head. Alderson controls acceptance, stable tags and the production switch from CoreScope at `live.meshcore.ca`; `dev.meshcore.ca` remains development-only. Neither official host was changed. Server versions remain independent.

Current-base checks and published-head CI pass. Native Go/PostgreSQL tests, restored-copy migration 045, the 3,200-input replay, and Windows/Pi web build/lint/**1,035 tests** pass. All **21 public assets**, both sources, **26 boundaries**, live packet delivery and desktop/French phone checks pass. The test-helper readiness race was fixed by draining probes through a unique marker; 100 repetitions of each affected test passed. Live ingestion behavior is unchanged by that helper fix. Existing image-tag and Compose receipts remain applicable to unchanged workflow/template content.

Migration 045 removed **485 partial telemetry rows on the restored copy**, preserving raw counts, retained telemetry and node fingerprints. Immediately before live migration, **489 matching rows** were separately saved in the private checkpoint. The full restored/checksummed dump and this row export are retained on and off the Pi.

Backend recovery is `evidence/sync-140-20260930/deploy-server.py rollback`, checkpoint `sync140-cutover-20260930T204913Z`. It restores **9054acd8 / 23945d59**, rolling back the new frontend first when needed. It preserves new traffic and the compatible telemetry cleanup; the private row export retains deleted rows for selective recovery. Frontend-only recovery is `evidence/sync-140-20260930/deploy-beacon-web.py rollback --evidence-dir sync-140-20260930`, checkpoint `web-20260930T211410Z`. Configuration remains b3d96f52 / mode 0644. The server update preserved the other 23 containers; the frontend preserved all 24. Automatic zones, public admin/backup and foreign classification stay disabled.

**Remaining owner gates:** review/acceptance, the requested 24h/3d raw-history controls versus upstream 7d/30d controls, physical Safari, production-host capacity/data verification, approved Actions images/tags and the CoreScope switch. The bounded replay and 40-second live sample do not establish production capacity.

[Current release/cutover plan](app_documentation/release-140-preparation.md) · [Exact candidate record](app_documentation/release-140-heads.json).

## Historical 1.3.2 preparation

## 1.3.2 release preparation — 30 September

The Pi now serves exact merged dev server `689bc232` / web `00d859d9`, with Atlas excluded. The web stack landed through #99, followed by #100–#103. Server #182 and the maintainer ingestion, caching and location fixes are included. Native PostgreSQL tests, the 3,200-input replay, and web build/lint/all **1,017 tests** pass. All 21 public assets, both source archives and 26 boundaries match.

My Atlas #97 remains held at `66ae0cc2` for after 1.3.2 and needs conflict resolution against the new dev branch. Web #93 is closed without merge. Upstream #101 restored 7d/30d controls and maps old 3d observer links to 7d; this conflicts with the requested 24h/3d raw-history controls and remains a release follow-up. Migration 043 was restore-tested: 273 stale location records cleared, raw counts and other located nodes preserved. The prior server/frontend and a verified on/off-Pi dump remain recoverable.

[Current audit, exact heads, validation and recovery](app_documentation/release-132-preparation.md). [Live candidate and source](https://canadaverse.org/beacon-dev/source.html). Maintainers retain web acceptance, tags, version decisions and production rollout. Earlier dated records below are historical.

Updated 29 September 2026 (Toronto). This is the working roadmap for n30nex's ongoing contributions toward CoreScope feature parity. Maintainers decide acceptance and merge order; deployment owners handle the production switch.

Refresh GitHub issues, PR feedback and branch state before starting a phase. This document is a snapshot, and linked issues/PRs are the current source of truth.

Release-check correction, 21 September UTC: the workflow now includes independent preview PRs in Status and Check, applies the same CI/head/fork/target requirements to them, and rechecks the prepared independent inputs before publication. This covers packet summaries #161 and map correction #61 without adding them to the ordered stacks. The backup CLI #160 retains its separate check. Twenty-three offline regressions cover these gates and the existing no-rebase/cache behavior. See [the contributor workflow](CONTRIBUTOR_WORKFLOW.md).

The following sections preserve dated historical checkpoints. Use the 30 September release record above for current source, acceptance and rollback.

## Historical Atlas preview — 29 September

[Exact feature, validation and recovery](app_documentation/my-atlas-20260929.md).

[Web #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97), `4fd4b0de`, is the single My Atlas feature PR requested by the contributor. It follows #95 at `e1133ab5` and closes [web #96](https://github.com/MeshCore-Beacon/beacon-web/issues/96) on acceptance. Earlier application PRs remain included; no parent was rebased for this feature.

My Atlas sits in the desktop tab row and the phone More menu. Visitors save up to twelve full-key node identities, order and a 24h/3d window in this browser. Compact cards show reception bars, SNR/RSSI meters and server freshness; Heard by and statistics expand on demand. Search collapses on return visits. Node, observer/dashboard and exact packet/path investigation reuse the existing navigation. English and French ship together.

Counts are explicitly the latest **200 retained origin-key reports per node**, filtered to the selected period. Companion requests and other identified-origin packets are included as well as adverts. This is not a complete node-traffic total. Heard by describes the latest loaded packet, not lifetime reach. Missing readings, expired details and incomplete samples remain visible; no radio-health or packet-loss score is invented.

The Pi now runs unchanged server `a35cba1d` with web `4fd4b0de`. Windows and native Pi build/lint/all **960 tests** pass, along with the actual published-head CI (web CodeQL skipped). Desktop, French 390px phone, keyboard, persistence/order/removal, packet/observer links and dashboard Back checks pass. The public 19 assets and both source archives match, both MQTT feeds are connected, and all 24 container identities/restart counts are unchanged. Physical iPhone Safari and full production capacity remain separate release gates.

[My Atlas preview](https://canadaverse.org/beacon-dev/?tab=MyAtlas) · [Changelog and source](https://canadaverse.org/beacon-dev/source.html). Frontend rollback restores `e1133ab5` with server `a35cba1d`, from `web-20260930T004937Z`. For an older backend rollback, restore this frontend first, then use the existing September 29 backend recipe; its guard intentionally rejects an unknown newer frontend.

The contributor explicitly prioritized My Atlas for this phase. Next: refresh maintainer feedback and issues, then server #183 before optional MeshMapper boundaries. Broader issues and remaining parity work stay open. All eighteen application candidates are out of draft; maintainers retain acceptance, merges, stable releases and production cutover.

## Earlier review corrections and history windows — 29 September

All six server reviews are addressed in their existing PR sequence. The fixes restore analytics indexes, consolidate unmerged migrations, preserve current partial activity buckets, align cache windows, narrow the route index, keep manual scope priority and simplify channel insertion metadata. Independent server #184 fixes RFC3339 offsets; new web #95 follows #92 and matches time choices to retained data. Existing candidates remain included.

The Pi runs server `a35cba1d` / web `e1133ab5`. All seventeen published application heads pass Check/CI (web CodeQL skipped); native Go/PostgreSQL and Windows/Pi web build/lint/all 940 tests pass. The restored-copy repair preserved raw rows and archive fingerprints, and rollback index restoration passed. A 3,200-input/504-scope replay had all expected rows/events and zero fixture drops. The one-minute live sample had no parser fallbacks, queue overflows, SQL errors, restarts or reconnects; malformed-IATA and clock-skew warnings remain.

Visible periods are **24h / 3d** for observer monitoring and route evidence, and **24h / 3d / 30d** for summary-backed Analytics. Seven-day buttons are removed. Raw comparison spans are capped at three days. Durable hourly aggregates already preserve expired packet counts; materialized views combine them with live rows. Older summaries accumulate after archiving starts, and packet detail remains unavailable after expiry. Revised labels and notes are English/French.

Current acceptance still requires maintainer re-review, especially #167/#169/#174. No upstream merge, stable release or production cutover was performed. The next focused issue is server #183 (saved-route prefix-width changes); broad partial issues remain open. External server #182 and web #93 are unmerged and not in this tested composition. Owners decide the release breakpoint and production switch.

[Exact current heads, validation and recovery](app_documentation/review-release-20260929.md).

## Ingest integration delivered — 28 September

The upstream ingest queue and bounded route-reconfirmation changes are integrated with all pending features. Independent server #166 was updated to preserve advert-name freshness and optional repeat-path delivery together. Suppressed duplicates perform no live-only endpoint work; repeats do not overwrite current names with older adverts. The rest of the queue refreshed without source conflicts.

All fifteen published application heads pass checks (web CodeQL remains skipped). The composed native Pi server/PostgreSQL suite passes. With 504 scope candidates and blocked route maintenance, an isolated 3,200-input replay preserved the expected 100 packets, 800 observations, 100 decrypted messages and 2,400 opt-in live events with zero queue drops. Native web build/lint and all 935 tests pass. All 18 public assets and both source archives match; English desktop, French phone, scoped packet rows, Public history and packet inspection pass. This is bounded fixture evidence, not proof of universal production losslessness.

Both real MQTT feeds advanced during the 63-second runtime observation with no restarts or queue-overflow errors. Malformed region and timestamp warnings remain. Valid whole-second timestamps with numeric UTC offsets expose a pre-existing parser gap, now [server #181](https://github.com/MeshCore-Beacon/beacon-server/issues/181). That parser correction is now in #184; see the September 29 record for current priority. The older CoreScope legacy-counter gap remains unexplained.

September 28 checkpoint: server `2ed2e03117f6c88795d446456e6d74c20c485d28` / web `6b6884951a3dac01b592dfec83f0191879c5696c`. Configuration, schema042, Public key, 504 exact-case candidates, YOW importer and 72h/30d/720h retention are unchanged. A fresh dump restored successfully and was checksum-verified off the Pi. Only Beacon restarted; the other 22 containers were unchanged. Same-schema rollback retains new data and restores server `7c9599b1` / web `dfeb2777` from `ingest-cutover-20260928T222830Z`; frontend-only recovery is `web-20260928T224458Z` paired with the new backend. Exact procedures and current PR heads are in the integration record below.

The shared UTF-8 corrections and merge guidance remain in place. Both application repos still disable merge commits; the contributor has READ access, so a maintainer must enable that setting. The helper remains optional for maintainers and unrelated to ingestion. Owners retain upstream merges and production release.

[Current PR heads, validation and recovery](app_documentation/ingest-integration-20260928.md).

## Earlier Canada/US scope and packet-layout checkpoint — 28 September

The preview now has **504 exact-case scope candidates**: 261 distinct names from all 237 published Canadian/US regional scope catalogues, plus lowercase IATA/group, province/state, district/territory and country fallbacks. It covers 244 currently known region codes, all 13 Canadian province/territory codes, all 50 US states, DC and five US territories, and includes `#ca`, `#can`, `#us`, `#usa` and `#na`. Counts overlap; do not add these categories together. Published mixed-case names are preserved because case changes the key. Named scopes are not geographic boundaries or evidence of repeater use.

The reported “Test 4” packet uniquely matches `#ykf`; its original unresolved label remains unchanged. Fresh “Ykf test” and “This is scoped to ykf only” messages now resolve as `#ykf`. A read-only audit of 932 retained transport packets found 670 unique candidate matches, 255 without a known match and seven short-code collisions. Unknown custom names cannot be recovered from these codes alone. Observer/neighbor reports currently contained only the wildcard `*`, so they supplied no additional names. No historical labels were rewritten. The native Pi matcher passes the captured-packet regression and measured a median 0.55ms for a full 504-name scan; this is not a production-capacity claim.

See the [candidate snapshot and provenance](app_documentation/north-american-scope-candidates.json). This is a recorded catalogue snapshot, with the existing automatic YOW importer still active. For subsequent scope work, refresh Canadian/US published catalogues and observed IATA/report names within API cache/rate limits, retain manual fallbacks and surface unresolved/ambiguous codes. Do not claim an undisclosed recurring all-region discovery service. Arbitrary private names still require a published catalogue or an explicit supplied/reported name.

[Web #92](https://github.com/MeshCore-Beacon/beacon-web/pull/92), `dfeb2777`, follows #89 and closes #90. It gives the route label and scope separate lines within a 128px track, preserving 37px rows and exact scope case. Long tags remain inside phone cards. A real browser geometry check reproduced the spill before the fix and passed afterward, including the user's `BB2F2752` row. Desktop, 768px table, 390px phone, keyboard and English/French public checks pass. All 935 tests pass on Windows and the Pi, as does exact-head CI; existing warnings remain and web CodeQL is skipped.

At that earlier checkpoint, the Pi served web `dfeb277756b1a9b230d7e7e0f2d45d62713bf45b` with unchanged server `7c9599b1`, every prior candidate, and the updated [source/changelog](https://canadaverse.org/beacon-dev/source.html). All 18 assets and both source archives match. Both inputs and public LIVE are verified; frontend publication restarted no containers. Application merges/releases remain owner-controlled. The later coordinated refresh above integrates #177–#180 and web #91; this paragraph records the earlier validation.

## Channel scope investigation and Public channel — 27 September

[Server #176](https://github.com/MeshCore-Beacon/beacon-server/pull/176) (`7fc631e8`, follows #174, closes #175) and [web #89](https://github.com/MeshCore-Beacon/beacon-web/pull/89) (`e7618fd7`, follows #87, closes #88) expose first-recorded packet scope consistently in history, catch-up and live messages. The interface adds scope filtering, packet inspection, distinct unknown/unavailable/unscoped states and English/French explanations. Duplicate broker messages and live arrivals during a history request preserve the existing page cursor and message counts. Imported catalogue names alone are not forwarding evidence.

At the channel-scope checkpoint, the Pi preview was composed server `7c9599b167bcad2b416ef03304ff27909ab3021b` / web `e7618fd7d40aff4e01f581999fdbb21d10de2e67`, with every earlier review candidate included. Native server/PostgreSQL tests, all 935 web tests, build/lint and published-head CI pass (web CodeQL is skipped). Browser checks cover live/history filtering, keyboard inspection, English/French and a 390px phone. The public page is LIVE, both MQTT inputs are connected, and all 18 assets plus both source archives match the [changelog/source offer](https://canadaverse.org/beacon-dev/source.html).

The standard MeshCore Public channel key is enabled at the user's request, matching the known non-hashtag hash-11 channel on dev.meshcore.ca. A restored-copy trial recovered 2,735 retained messages in 16.127 seconds; public decoded history and a new incoming message were verified. Expired packets remain unavailable. Schema042 is unchanged. Rollback retains server `eb99f752`, web `98f820d2`, configuration and source without discarding new database rows; the older schema041 recovery remains separately available. Packets stay 72h, summaries 30d and telemetry 720h. Public admin, backups and foreign detection remain disabled.

See the [boundary integration plan](app_documentation/meshmapper-boundaries-plan.md).

**Next:** refresh review feedback and listed issues first, then optional MeshMapper boundary synchronization using the published Zones API and existing map layer. Preserve manual boundaries and cached geometry; keep cross-boundary packet/route investigation in a later focused contribution. Group scope catalogues, regional evidence, existing translations and broader parity work remain open. Maintainers control acceptance, merge order and production release.

## Regional scope import — 27 September

[Server #174](https://github.com/MeshCore-Beacon/beacon-server/pull/174), `71e4e871`, follows #172 and closes focused issue #173 on acceptance. It imports public MeshMapper catalogue names into the existing matcher, keeps manual settings, persists last-known-good data and retry timing, and reports synchronization status in operator logs. Regional candidate limits and short-code ambiguity checks prevent a catalogue entry from becoming a forwarding claim. The feature defaults off; channel tags remain a separate slice.

At the scope-import checkpoint, the Pi ran composed server `eb99f7523727b7e4208667e201f50ad235ce2c5f` with unchanged web `98f820d2`. Every prior review candidate remains included. Its explicit Ottawa/YOW source imported seven names; the public filter and actual incoming `#yow` adverts were verified. Native PostgreSQL tests and published-head CI/race/security checks pass. The maximum-catalogue matcher fixture took about 0.15ms per transport packet on the Pi; this is a microbenchmark, not a production-capacity claim. Pi ThreadSanitizer cannot run with the host's address layout, so race validation is on Linux CI.

Migration 042 preserved all 31 existing table fingerprints in a restored copy. Immediate rollback retains original schema041 database `beacon_pre042_20260927` and backup `scopes-cutover-20260927T221330Z`; a checksum-verified private dump is also off the Pi. Only Beacon restarted, 22 other containers were unchanged, and both feeds reconnected. The [changelog and source](https://canadaverse.org/beacon-dev/source.html), 18 web assets and English/French-mode desktop/phone scope filtering were checked. Existing untranslated packet controls remain under #12; web source is unchanged. Retention remains 72h/30d/720h, and public admin/backup/foreign detection stay disabled.

**Follow-up delivered above:** channel tags are in #176/#89. Group catalogues and regional evidence remain separate future slices. Maintainers retain merges, stable releases and production cutover.

## Observer investigation navigation — 27 September

[Web #87](https://github.com/MeshCore-Beacon/beacon-web/pull/87), final candidate `98f820d2b2af5a69faf3f9aaf30d5f14b45feea8`, follows #85 and closes focused issue #86 on acceptance. Escape/Close dismisses the active panel and restores focus. Observer adverts are keyboard buttons and select the exact packet observation; embedded packet inspection preserves its originating URL. Revisiting an open entity returns to its existing panel, while tab/region/entity changes discard obsolete panels.

Opening an observer dashboard keeps one originating screen mounted under its original Router location. Period, picker, comparison and directory detours stay within that visit; Back or the translated return action restores route/packet/node/map/Analytics state. A real route retained its typed filter, sort and 720px scroll position; a panned map's copied centre/zoom/layer/node link was identical after return. The Analytics leaderboard uses the same handler and provides keyboard buttons beside the canvas, using existing data. Direct/copied/reloaded dashboards remain standalone; arbitrary in-memory state is not persisted across reload.

At the observer-navigation checkpoint, the Pi served web `98f820d2b2af5a69faf3f9aaf30d5f14b45feea8` on server `99e623c5`. Final native build/lint and **929 tests in 106 files** pass; exact-head CI passes (web CodeQL remains skipped). All 18 public assets and both source archives match. Public LIVE, both MQTT feeds and return/keyboard journeys pass. A real packet-list regression is fixed: the retained origin stays invisible/inert with its layout intact. Final public checks preserve 442px scroll and 506px viewport height throughout the visit, plus the selected report URL. No containers restarted. Immediate web rollback is `5a261162` at `web-20260927T210108Z`; the phase-start `3b3abdcc` recovery remains at `web-20260927T202233Z`. Existing database recovery and 72h/30d/720h retention policies are unchanged. All prior review candidates remain included.

**Observer follow-up:** web #12 still covers the observer directory and quick-detail translations. Node/trace presentation and further reach/timing analytics follow the approved roadmap. Scope import #174 and channel tags #176/#89 are implemented above. Maintainers control merges, stable releases and production cutover.

## MeshMapper scopes contract — 27 September

The [public API](https://wiki.meshmapper.net/scopes-api/) is available. The documented YOW endpoint returned HTTP 200 and a successful conditional HTTP 304; it requires no API key. The [scope integration plan](app_documentation/mesh-scopes-plan.md) now specifies explicit per-IATA sources, cached refresh, durable last-known-good data, manual-name preservation and separate imported/observed evidence. Group results cannot be attributed to individual member IATAs. The former unpublished-endpoint blocker is removed; importer #174 and channel tags #176/#89 are now deployed for review. Review feedback and listed issues retain priority. That contract-only update preceded the tested importer deployment recorded above.

## Saved-route evidence — 27 September

[Server #172](https://github.com/MeshCore-Beacon/beacon-server/pull/172) (`f473b165`) and [web #85](https://github.com/MeshCore-Beacon/beacon-web/pull/85) (`3b3abdcc`) implement the next connected-investigation slice. They close focused server #171 / web #84 on acceptance. A full saved route now links to paged retained reports, exact packet inspection, reporting observers and named hops. Existing packet inspection leads to the selected report's map. Shared route links pin the effective server time window; browser Back and in-place inspection preserve the route/filter context.

Matching uses the complete saved prefix bytes, width and IATA, not confirmed physical identity. Other widths, subsegments, TRACE and unclassified records are excluded. Retained reports are separate from distinct-packet or historical route totals. Empty/expired evidence and unavailable prefixes are explained. Requests default to 24 hours, permit at most 30 days and fetch 50 reports per page; the interface caps each investigation at 500. New interface text is English/French, with a compact phone layout and expandable counting definitions.

The stack was refreshed once for accepted server #170 (`dec643a2`): optional exact WebSocket origins and opt-in observer public-key fields, not authentication. Updated server order: #167 (`02743704`) -> #169 (`91b21995`) -> #172 (`f473b165`); independent #166 (`2c5ad5fc`) remains included. Web order: #75 -> #79 -> #80 -> #81 -> #83 -> #85. All candidates remain reviewable separately; do not rebase every child independently. Deploy the server API before its web consumer.

At the saved-route checkpoint, the preview backend was composed `99e623c56477fd9b667d5f56bfb1a0eff34ecb2b`. Its complete native Pi/PostgreSQL suite passed. Restoring a fresh private dump and adding migration 041 preserved all 31 table fingerprints. The live switch retained the original schema040 database as `beacon_pre041_20260927`; rollback directory is `route-cutover-20260927T190644Z`. Both MQTT feeds reconnected and 22 unrelated containers were unchanged. Packets remain 72h, archived summaries 30d, telemetry 720h. Public admin, backup and foreign detection remain disabled.

At the route-evidence checkpoint, the Pi served web `3b3abdcc5bfa85b60c8959715736ea42c3d0bbd8`. The final native build/lint and all **915 tests** pass; exact-head CI passes (web CodeQL remains skipped). Desktop and 390px phone, English/French, copied/shared links, Back, keyboard Close/focus, exact report/node/observer and selected-map journeys were verified. All 18 public assets and both source archives match the tested artifacts. The public page is LIVE; both MQTT feeds are connected. Frontend publication restarted no containers. Web rollback retains `1d5d65e` in `web-20260927T192154Z`; the [source/changelog](https://canadaverse.org/beacon-dev/source.html) lists the complete review composition.

**Follow-up implemented above:** [web #86](https://github.com/MeshCore-Beacon/beacon-web/issues/86): observer quick-inspection Escape handling and broader cross-tab/overlay return navigation. That earlier Escape limitation is addressed by #87; acceptance remains with the maintainer. Node/trace evidence and additional reach/timing analytics follow that connection work. MeshMapper scope import #174 is now implemented and recorded above; its later channel/UI slices remain open. Broad server #60/#72/#99/#116 and web #12 remain open; this phase does not claim full parity or production capacity. Maintainers retain merges, stable releases and production cutover.

## Packet reception investigation — 27 September

[Web PR #83](https://github.com/MeshCore-Beacon/beacon-web/pull/83), `1d5d65e2807c2cb53a998743212d9a5b64ba80c4`, follows #81 and closes focused issue #82 when accepted. It adds grouped retained packet reports, selected-report links, observer inspection/dashboard access and a selected-path map. The initial list stays compact and keeps the selected group open. Equal prefixes are not treated as confirmed identical physical routes; empty/missing paths and TRACE intended routes have explicit labels.

Map projection omits ambiguous/unlocated identities and breaks lines at gaps. Live animations across uncertain chains are suppressed, so fewer speculative lines appear. Unavailable selected paths no longer silently show All paths. A shared-path loading race is fixed by checking the requested packet hash. Packet labels use the existing Noto Sans stack; external basemap emoji-glyph/sprite fallback warnings can still occur.

At the packet-investigation checkpoint, the Pi ran web `1d5d65e` with server `88c2c10c`. Native build/lint and all **906 tests** pass; focused Windows checks and desktop/390px phone/English/French/keyboard/Back/shared-link checks pass. Public assets and source match, both MQTT feeds are connected, and the frontend publication restarted no services. Earlier review candidates remain included. The [changelog/source](https://canadaverse.org/beacon-dev/source.html) identifies the running build. Maintainers still own merges, stable releases and production cutover.

**Follow-up:** the saved-route evidence phase above implements this API and interface. Remaining work is observer return navigation. Non-packet overlay return navigation remains a separate follow-up. The separate MeshMapper scope plan now has importer #174 and channel tags #176/#89 implemented. Broader server #60/#72/#99/#116 and web #12 remain open; this is a first connected-investigation slice, not full parity.

## Direction

Bring useful CoreScope investigation and analytics features into Beacon's existing ingest, database, API, cache and web components. Prioritize review regressions and measured stability/performance problems, then useful analytics pages. Keep each API or page a focused contribution with explicit counting semantics and validation.

Current sites:

- [Beacon reference deployment](https://dev.meshcore.ca/)
- [CoreScope reference deployment](https://live.meshcore.ca/)
- [Development preview](https://canadaverse.org/beacon-dev/) and its [changelog/source](https://canadaverse.org/beacon-dev/source.html)

| Repository | Responsibility | Contribution target |
|---|---|---|
| [beacon-server](https://github.com/MeshCore-Beacon/beacon-server) | Ingest, storage, read models and public/protected APIs | `dev` |
| [beacon-web](https://github.com/MeshCore-Beacon/beacon-web) | Investigation tools and analytics pages | `dev` |
| [beacon-docs](https://github.com/MeshCore-Beacon/beacon-docs) | Shared contracts, operator guidance and this roadmap | `main` |
| [beacon-mobile](https://github.com/MeshCore-Beacon/beacon-mobile) | Mobile client; coordinate API compatibility | `main` |

## Observer-first release delivered for review

The observer-first release is implemented in four focused review candidates: [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) (`91b21995`, closes #168), [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) (`3a0eb4c8`, closes #76), [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) (`b3a6b088`, closes #77) and [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) (`42ae09b7`, closes #78). All are out of draft. Server #169 follows #167; web order is #75 -> #79 -> #80 -> #81. Independent server #166 remains in the preview composition. Maintainers control acceptance and release; these issues remain open until their changes are accepted.

At the observer-release checkpoint the Pi ran composed server `88c2c10c830034cee70a46fca717af518803a544` and web `42ae09b7c6be50cd0f617bad8aea35825be9f12e`, with the [updated changelog and exact source](https://canadaverse.org/beacon-dev/source.html). Raw packets remain 72 hours, archived hourly analytics 30 days, telemetry 720 hours. All four candidates passed their native Pi suites; the final web build passes 895 tests. Server tests use actual PostgreSQL. Windows server/full destination/dashboard validation and 48 focused final comparison/API tests also pass. Desktop, 390-pixel phone, English/French, keyboard, legacy/shared links and Back/search/sort/scroll were checked. Physical iPhone Safari and production-volume capacity remain separate gates.

Migration 040 preserves original rows and repairs available archived unknown-payload counts without inventing signal samples. A restored clone passed the migration probe. A fresh private dump was copied off the Pi and its checksum verified; the original schema039 database and matching binary/config/source are retained for DB-aware rollback. Only the Beacon app restarted for the server change; 22 other containers were unchanged. Frontend publication restarted no services. Both MQTT feeds reconnected. Public admin, backup and foreign detection remain disabled.

See the [observer implementation and subsequent UX releases](app_documentation/observer-monitoring-plan.md) and the separate [Mesh Scopes interoperability plan](app_documentation/mesh-scopes-plan.md).

## Accepted consolidation batch

All ten original server/web contributions merged on September 24. The September 25 web batch is also accepted: #70 contains translations #63/#64/#65/#66/#69 plus Timestamp wording; #68 and #72 merged separately and closed #67/#71. The five earlier translation PRs were closed as included, with exact ancestry/tree equivalence verified. Web #73 and server #162/#163 then landed. That acceptance batch cleared the application queue. The new September 26 retention/endpoint PRs and docs #5 are now in review, as listed below.

At the September 27 consolidation checkpoint, accepted dev was server `dec643a2ade712cd60feb2bc761a5654c7c82714` / web `54b5093ac0302c7db9d51e1d7fe23570eae7cdb5`. Exact-head CI/image builds pass; server coverage/CodeQL pass and web CodeQL remains skipped. Stable releases are still server **v1.6.0** and web **v1.3.0**. The original September 24 freeze (`c02317a4` / `0f0a6ca5`) remains historical evidence, not proof that the newer server migrations are Pi-validated.

| Accepted PR | Scope | Merge commit |
|---|---|---|
| [Server #149](https://github.com/MeshCore-Beacon/beacon-server/pull/149) | add protected account lifecycle endpoints | `4d2642ab` |
| [Server #154](https://github.com/MeshCore-Beacon/beacon-server/pull/154) | add protected database and config download | `a25e2675` |
| [Server #157](https://github.com/MeshCore-Beacon/beacon-server/pull/157) | add bounded reception signal analytics | `6107578c` |
| [Server #159](https://github.com/MeshCore-Beacon/beacon-server/pull/159) | add bounded path and hash-width analytics | `8a3fa7e6` |
| [Server #160](https://github.com/MeshCore-Beacon/beacon-server/pull/160) | verify native archives offline without extraction | `20691dc5` |
| [Server #161](https://github.com/MeshCore-Beacon/beacon-server/pull/161) | summarize ACK and trace references | `c02317a4` |
| [Web #55](https://github.com/MeshCore-Beacon/beacon-web/pull/55) | add RF and signal analytics | `2405e1ac` |
| [Web #57](https://github.com/MeshCore-Beacon/beacon-web/pull/57) | add Paths and Hashes analytics | `929ba83c` |
| [Web #59](https://github.com/MeshCore-Beacon/beacon-web/pull/59) | distinguish analytics navigation icons | `c2ab29a5` |
| [Web #61](https://github.com/MeshCore-Beacon/beacon-web/pull/61) | omit reset and invalid node locations | `0f0a6ca5` |

Server #156/#158 and web #54/#56/#58/#60 are closed. Server #60/#72/#99/#116 and web #12 remain open for their remaining scope. Web #67/#71 are closed following #68/#72. Archive verification establishes structure and integrity, not authenticity, SQL safety or restorability. Packet-carried ACK/TRACE/PING references are not identity or delivery guarantees.

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

Current broader issues remain server #60 (admin), #72 (backup/import), #99 (packet summaries), #116 (MQTT investigation), and web #12 (remaining translations). Current priorities are review feedback and server #181, followed by boundaries and the remaining investigation work. A measured month of accumulated history, production-scale capacity and physical Safari checks remain separate gates. Maintainers own stable releases and the owners handle production cutover.

## Delivered foundations

- Faster bounded node, route, trace and clock-stat queries; list-limit validation and NULL-observation handling. Representative changes: [#111](https://github.com/MeshCore-Beacon/beacon-server/pull/111), [#118](https://github.com/MeshCore-Beacon/beacon-server/pull/118), [#120](https://github.com/MeshCore-Beacon/beacon-server/pull/120), [#122](https://github.com/MeshCore-Beacon/beacon-server/pull/122), [#124](https://github.com/MeshCore-Beacon/beacon-server/pull/124).
- MQTT client isolation, proxy identity handling, API/WebSocket limits and interrupted-index recovery. Timeout attribution in #116 remains separate from these accepted fixes.
- Observer age-out, advert summaries, batched endpoint resolution and companion matching (snapshots superseded by #163), stable channel paging, packet search and shared packet links.
- Observer activity/telemetry and comparison, regional scope statistics, runtime administration, optional foreign-repeater detection and the backup-export foundation.

## Analytics delivery and counting rules

| Page | Current behavior | Important interpretation |
|---|---|---|
| [Traffic](https://canadaverse.org/beacon-dev/?tab=Analytics&statsTab=traffic&range=24h) | UTC hourly heatmap, IATA trends, reception share and exact counts | Counts reported receptions; missing hourly records remain gaps |
| [Scopes](https://canadaverse.org/beacon-dev/?tab=Analytics&statsTab=scopes) | Regional packet, observer-membership and default-scope-node charts | Retained counts have no rolling date filter; memberships can overlap |
| [RF / Signal](https://canadaverse.org/beacon-dev/?tab=Analytics&statsTab=signal&range=24h) | SNR/RSSI distributions, hourly means, sample coverage and exact tables | Missing/non-finite and unavailable zero/zero readings are excluded per metric; a measured zero SNR remains valid |
| [Paths & Hashes](https://canadaverse.org/beacon-dev/?tab=Analytics&statsTab=paths&range=24h) | Hash-width share, received header-entry distribution, hourly trends and coverage | Empty paths never vote for width; TRACE paths hold signal readings; unusable metadata is unclassified |

The path page counts stored receptions, not unique devices. Flood paths accumulate entries, while direct routes carry remaining entries. Observed widths do not establish device capability or collision rates. Signal readings describe reception at the reporting observer rather than a complete end-to-end link.

The September 20 review correction moves both new aggregate APIs onto materialized hourly snapshots, preserving reception/region semantics and normalizing polling windows to UTC hours. In a rolled-back million-row Pi fixture, Signal request queries took 1.8–77.5 ms and Paths 3.5–141.9 ms across custom/generic plans. Initial population took 14.4/8.4 seconds, refresh 16.8/6.2 seconds, and view/index storage was 6.5/11.3 MB respectively. These measurements cover the fixture, not the full production workload. See the [release consolidation checklist](RELEASE-CHECKLIST.md) for remaining gates.

September 20 validation covered native Go/PostgreSQL/HTTP behavior and **786 web tests**, plus private backup compatibility, feature-only startup failure, TLS/password files, cancellation and schema/data/sequence restoration. That review update passed 390/1280px browser checks, with ten distinct glyphs and complete-hour text; earlier chart checks also covered 320/768px. This is historical evidence for the unchanged feature code. Current revisions and corresponding-source archives are on the preview's changelog page.

The September 24 consolidation check built accepted server `c02317a4` and retained web `42ba5fcb`, identical in source to accepted `0f0a6ca5`. Its native PostgreSQL and public/browser evidence remains in the release checklist. The Pi frontend contains the now-accepted translations and #68/#72 as documented above; the prior combined preview is retained for rollback. The three-hour retained analytics sample does not establish 7/30-day history or production capacity.

## Next phases

The September 20 #116 investigation has a new [current-build result](https://github.com/MeshCore-Beacon/beacon-server/issues/116#issuecomment-5753626821): a 600-second unmodified Pi capture kept both feeds connected and retained 2,169 new observations, with no ping timeout, disconnect, deadline, SQLSTATE error or HTTP 5xx response. App/PostgreSQL CPU averaged 2.14%/3.96% of one core. The preceding 3h39 log likewise has no MQTT loss or deadline error. Timestamp warnings were classified separately. This did not measure callback or pool-acquisition duration and does not establish the original cause or production capacity. No application, ordering, acknowledgement or service change was made; #116 remains open. Further capture should follow a recurrence or meaningful workload change, rather than repeatedly sampling the same healthy state.

1. **Reviews and listed issues first.** The #181 correction is submitted as #184. Next address [server #183](https://github.com/MeshCore-Beacon/beacon-server/issues/183), preserving honest saved-route evidence when prefix widths change. Recheck maintainer feedback first; broad partial issues remain open.
2. **Accept the current queue in dependency order.** Server #167 -> #169 -> #172 -> #174 -> #176; independent #166. Web #75 -> #79 -> #80 -> #81 -> #83 -> #85 -> #87 -> #89 -> #92 -> #95. Independent server #184 follows dev. Use the published-head table in the integration record. Maintainers choose merges, the release breakpoint, versions, tags and main promotion.
3. **Optional MeshMapper boundaries.** Scope import and channel tags are already implemented in #174/#176/#89. Next use the [boundary plan](app_documentation/meshmapper-boundaries-plan.md), preserving manual boundary priority, cached valid geometry and separate scope/forwarding evidence. Crossing analytics remain a later focused slice.
4. **Connected investigation and presentation.** Packet/route/observer links and return navigation are delivered for review. Continue node/trace presentation, distinct analytics questions and quality of life under the approved observer plan; address #99/#12 where the work overlaps. Full parity is not yet claimed.

## Listed work still open

| Issue | Remaining scope |
|---|---|
| [Server #181](https://github.com/MeshCore-Beacon/beacon-server/issues/181) | Fixed by #184; awaits maintainer acceptance |
| [Server #183](https://github.com/MeshCore-Beacon/beacon-server/issues/183) | Saved-route hash-prefix metadata can lag a change of width; next focused issue |
| [Web #94](https://github.com/MeshCore-Beacon/beacon-web/issues/94) | Corrected periods/labels in #95; awaits acceptance |
| [Server #116](https://github.com/MeshCore-Beacon/beacon-server/issues/116) | #179/#180 are integrated and pass bounded replay/route-lock checks; attributing the historical incident still requires matching evidence |
| [Server #99](https://github.com/MeshCore-Beacon/beacon-server/issues/99) | Advert names and ACK/TRACE/PING references are accepted; define any remaining packet-type formats |
| [Server #60](https://github.com/MeshCore-Beacon/beacon-server/issues/60) | Remaining administration/worker/persistence behavior; account records do not establish login sessions |
| [Server #72](https://github.com/MeshCore-Beacon/beacon-server/issues/72) | Download #154 and archive validation #160 are accepted; import, browser access, deployment-file coverage and remote/scheduled backup remain |
| [Web #12](https://github.com/MeshCore-Beacon/beacon-web/issues/12) | Foundation and translations through #70 are accepted; Mesh/Talkers fixes are merged. Remaining analytics/screens/dialogs/formatting still need translation |

The six completed analytics/icon/map issues are closed. Refresh all currently open issues and PR feedback first at every continuation; accepted partial contributions are not grounds to close broader issues. Use closing references only when a PR completes the issue's accepted scope; use related references for partial work.

## Production parity matrix

Matching tab names is not acceptance. Each capability needs verified semantics, time/region behavior, empty/partial data, performance and browser evidence.

| Capability | Coverage / remaining evidence |
|---|---|
| Overview | Mesh overview and Traffic; reconcile packet/reception grain and retained windows |
| RF / Signal | New distributions, weighted means and sample coverage; production-volume measurements remain |
| Topology / route patterns | Existing routes, traces and neighbour graph; deeper edge/subpath/connectivity analysis remains |
| Channels | Directory/chat/talkers exist; traffic statistics, unknown-channel and history behavior remain |
| Hash statistics | Paths & Hashes covers observed ordinary widths and entries; trace-payload widths are distinct |
| Hash issues | Endpoint/path ambiguity primitives exist; observed ambiguity and static conflicts need separate views |
| Node analytics | Existing directory/detail/observations; richer attributed activity, signal, payload and peer analysis remains |
| My Repeaters | Owner selection/watchlist behavior and grouped analytics need an agreed contract |
| Repeater metrics | Observer telemetry overlaps partially; units, resets and role attribution need reconciliation |
| Distance | Coordinates/maps exist; valid link/path distances, unknown positions and confidence remain |
| Neighbour graph | Existing graph needs retained scaling, filter and accessible-fallback acceptance evidence |
| RF health | Noise/airtime/error telemetry exists; comparable health views need real samples and valid deltas |
| Clock health | Existing clock-drift endpoint/UI; retain role, threshold and history semantics |
| Roles | Node-type census exists; activity and unknown-role interpretation need acceptance evidence |
| Scopes | Regional API and new page exist; reconcile against populated retained data |
| Prefix tool | Public-prefix inspection/simulation remains unverified |
| Observer monitoring/comparison | Unified dashboard and contextual comparison in #169/#79/#80/#81; see the current release above. Shared windows and deduplication remain explicit; raw overlap can expire earlier than summaries |
| Other workflows | Validate decoder/search/sharing, live map/replay, settings, optional clients and legacy links |

## Release gates

- Inventory actual CoreScope retention, earliest/latest durable data, configuration and recovery copies. Example retention settings and public in-memory counts are not production history evidence.
- Reconcile Beacon's deduplication, identity, encryption/key and time semantics. Document whether migration or sufficient parallel ingestion supplies each historical window.
- Complete backup recovery scope with private disposable restore tests, including schema/data/sequence continuation and the deliberately excluded deployment files.
- Measure cold start, reconnects, ingest freshness, CPU/memory/storage, query latency and maintenance against representative production volume. Long-window raw aggregates may need rollups.
- Validate keyboard/mobile/browser behavior, chart readability and sharing. Physical iPhone Safari and a sustained load/connection soak remain open validation gaps.
- Verify release artifacts from reviewed source and applicable CI. The upstream web CodeQL workflow is currently disabled; its skipped job does not count as a security scan.
- Publish matching source, configuration guidance, known limitations and a verified rollback procedure. The deployment owner performs the production switch.

The development preview still has limited accumulated history; configured 30-day retention does not mean a measured month is available. MeshMapper catalogue import is enabled only for the explicitly configured YOW preview source. Its public admin/backup and foreign detection are disabled. These limitations remain explicit until configuration and validation support enabling them.

## Keeping this roadmap useful

Update this file when a phase is delivered, a dependency merges, an issue closes or the next priority changes. Keep private configuration and host-specific operational records outside this repository. Link current GitHub work and the public source/changelog so another contributor can continue without a private workstation path.
