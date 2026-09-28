# Beacon parity and analytics roadmap

Updated 27 September 2026 UTC. This is the working roadmap for n30nex's ongoing contributions toward CoreScope feature parity. Maintainers decide acceptance and merge order; deployment owners handle the production switch.

Refresh GitHub issues, PR feedback and branch state before starting a phase. This document is a snapshot, and linked issues/PRs are the current source of truth.

Release-check correction, 21 September UTC: the workflow now includes independent preview PRs in Status and Check, applies the same CI/head/fork/target requirements to them, and rechecks the prepared independent inputs before publication. This covers packet summaries #161 and map correction #61 without adding them to the ordered stacks. The backup CLI #160 retains its separate check. Twenty-three offline regressions cover these gates and the existing no-rebase/cache behavior. See [the contributor workflow](CONTRIBUTOR_WORKFLOW.md).

Final upstream refresh note: server #177 merged as `90f9b506` during channel-phase verification. The published server candidates and Pi composition below remain based on `dec643a2`. Their exact-head CI passes, but the stack helper requires one batch refresh before the next server publication; the validated running artifacts have not been relabelled. Web Check is current.

## Channel scope investigation and Public channel — 27 September

[Server #176](https://github.com/MeshCore-Beacon/beacon-server/pull/176) (`7fc631e8`, follows #174, closes #175) and [web #89](https://github.com/MeshCore-Beacon/beacon-web/pull/89) (`e7618fd7`, follows #87, closes #88) expose first-recorded packet scope consistently in history, catch-up and live messages. The interface adds scope filtering, packet inspection, distinct unknown/unavailable/unscoped states and English/French explanations. Duplicate broker messages and live arrivals during a history request preserve the existing page cursor and message counts. Imported catalogue names alone are not forwarding evidence.

The current Pi preview is composed server `7c9599b167bcad2b416ef03304ff27909ab3021b` / web `e7618fd7d40aff4e01f581999fdbb21d10de2e67`, with every earlier review candidate included. Native server/PostgreSQL tests, all 935 web tests, build/lint and published-head CI pass (web CodeQL is skipped). Browser checks cover live/history filtering, keyboard inspection, English/French and a 390px phone. The public page is LIVE, both MQTT inputs are connected, and all 18 assets plus both source archives match the [changelog/source offer](https://canadaverse.org/beacon-dev/source.html).

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

Current preview backend is composed `99e623c56477fd9b667d5f56bfb1a0eff34ecb2b`. Its complete native Pi/PostgreSQL suite passed. Restoring a fresh private dump and adding migration 041 preserved all 31 table fingerprints. The live switch retained the original schema040 database as `beacon_pre041_20260927`; rollback directory is `route-cutover-20260927T190644Z`. Both MQTT feeds reconnected and 22 unrelated containers were unchanged. Packets remain 72h, archived summaries 30d, telemetry 720h. Public admin, backup and foreign detection remain disabled.

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

## Current observer-first release

The observer-first release is implemented in four focused review candidates: [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) (`91b21995`, closes #168), [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) (`3a0eb4c8`, closes #76), [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) (`b3a6b088`, closes #77) and [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) (`42ae09b7`, closes #78). All are out of draft. Server #169 follows #167; web order is #75 -> #79 -> #80 -> #81. Independent server #166 remains in the preview composition. Maintainers control acceptance and release; these issues remain open until their changes are accepted.

At the observer-release checkpoint the Pi ran composed server `88c2c10c830034cee70a46fca717af518803a544` and web `42ae09b7c6be50cd0f617bad8aea35825be9f12e`, with the [updated changelog and exact source](https://canadaverse.org/beacon-dev/source.html). Raw packets remain 72 hours, archived hourly analytics 30 days, telemetry 720 hours. All four candidates passed their native Pi suites; the final web build passes 895 tests. Server tests use actual PostgreSQL. Windows server/full destination/dashboard validation and 48 focused final comparison/API tests also pass. Desktop, 390-pixel phone, English/French, keyboard, legacy/shared links and Back/search/sort/scroll were checked. Physical iPhone Safari and production-volume capacity remain separate gates.

Migration 040 preserves original rows and repairs available archived unknown-payload counts without inventing signal samples. A restored clone passed the migration probe. A fresh private dump was copied off the Pi and its checksum verified; the original schema039 database and matching binary/config/source are retained for DB-aware rollback. Only the Beacon app restarted for the server change; 22 other containers were unchanged. Frontend publication restarted no services. Both MQTT feeds reconnected. Public admin, backup and foreign detection remain disabled.

See the [observer implementation and subsequent UX releases](app_documentation/observer-monitoring-plan.md) and the separate [Mesh Scopes interoperability plan](app_documentation/mesh-scopes-plan.md).

## Accepted consolidation batch

All ten original server/web contributions merged on September 24. The September 25 web batch is also accepted: #70 contains translations #63/#64/#65/#66/#69 plus Timestamp wording; #68 and #72 merged separately and closed #67/#71. The five earlier translation PRs were closed as included, with exact ancestry/tree equivalence verified. Web #73 and server #162/#163 then landed. That acceptance batch cleared the application queue. The new September 26 retention/endpoint PRs and docs #5 are now in review, as listed below.

Current accepted dev is server `dec643a2ade712cd60feb2bc761a5654c7c82714` / web `54b5093ac0302c7db9d51e1d7fe23570eae7cdb5`. Exact-head CI/image builds pass; server coverage/CodeQL pass and web CodeQL remains skipped. Stable releases are still server **v1.6.0** and web **v1.3.0**. The original September 24 freeze (`c02317a4` / `0f0a6ca5`) remains historical evidence, not proof that the newer server migrations are Pi-validated.

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

Current broader issues remain server #60 (admin), #72 (backup/import), #99 (packet summaries), #116 (MQTT investigation), and web #12 (remaining translations). Current priorities are the observer release and following investigation work described above. A measured month of accumulated history, production-scale capacity and physical Safari checks remain separate gates. Maintainers own stable releases and the owners handle production cutover.

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

The September 20 review correction moves both new aggregate APIs onto materialized hourly snapshots, preserving reception/region semantics and normalizing polling windows to UTC hours. In a rolled-back million-row Pi fixture, Signal request queries took 1.8Ã¢â‚¬â€œ77.5 ms and Paths 3.5Ã¢â‚¬â€œ141.9 ms across custom/generic plans. Initial population took 14.4/8.4 seconds, refresh 16.8/6.2 seconds, and view/index storage was 6.5/11.3 MB respectively. These measurements cover the fixture, not the full production workload. See the [release consolidation checklist](RELEASE-CHECKLIST.md) for remaining gates.

September 20 validation covered native Go/PostgreSQL/HTTP behavior and **786 web tests**, plus private backup compatibility, feature-only startup failure, TLS/password files, cancellation and schema/data/sequence restoration. That review update passed 390/1280px browser checks, with ten distinct glyphs and complete-hour text; earlier chart checks also covered 320/768px. This is historical evidence for the unchanged feature code. Current revisions and corresponding-source archives are on the preview's changelog page.

The September 24 consolidation check built accepted server `c02317a4` and retained web `42ba5fcb`, identical in source to accepted `0f0a6ca5`. Its native PostgreSQL and public/browser evidence remains in the release checklist. The Pi frontend contains the now-accepted translations and #68/#72 as documented above; the prior combined preview is retained for rollback. The three-hour retained analytics sample does not establish 7/30-day history or production capacity.

## Next phases

The September 20 #116 investigation has a new [current-build result](https://github.com/MeshCore-Beacon/beacon-server/issues/116#issuecomment-5753626821): a 600-second unmodified Pi capture kept both feeds connected and retained 2,169 new observations, with no ping timeout, disconnect, deadline, SQLSTATE error or HTTP 5xx response. App/PostgreSQL CPU averaged 2.14%/3.96% of one core. The preceding 3h39 log likewise has no MQTT loss or deadline error. Timestamp warnings were classified separately. This did not measure callback or pool-acquisition duration and does not establish the original cause or production capacity. No application, ordering, acknowledgement or service change was made; #116 remains open. Further capture should follow a recurrence or meaningful workload change, rather than repeatedly sampling the same healthy state.

1. **Review the current retention/endpoint and observer candidates.** Keep the ordered server #167 -> #169 -> #172 -> #174 and web #75 -> #79 -> #80 -> #81 -> #83 -> #85 -> #87 stacks; #166 is independent. Refresh with the existing workflow after acceptance. Maintainers choose the release breakpoint, versions, tags and main promotion.
2. **Connected investigation.** Connect packets, exact observed paths/routes, reporting observers and map actions with reliable Back navigation and visibly ambiguous identities. Continue focused issue #99/#12 work where it overlaps this accepted scope.
3. **Node/route/trace presentation, then distinct analytics questions and quality of life.** Follow the approved observer plan's subsequent releases; this phase does not claim full parity.
4. **Mesh Scopes interoperability.** Optional cached import is implemented in server #174; continue with consistent channel scope tags, using the [integration plan](app_documentation/mesh-scopes-plan.md). Retain manual names and separate observed/default/imported evidence. No API key is required; importer acceptance and release remain with maintainers.

## Listed work still open

| Issue | Remaining scope |
|---|---|
| [Server #116](https://github.com/MeshCore-Beacon/beacon-server/issues/116) | No recurrence in the September 20 retained log / ten-minute capture; still needs an attributable event with callback/pool timing |
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
