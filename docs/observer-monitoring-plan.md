# Observer monitoring release and following UX work

Updated 27 September 2026 UTC. This records the approved observer-first plan and review implementation, not a production release or complete CoreScope parity claim.

The observer-first release is implemented in four focused review candidates: [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) (`60ed339c`, closes #168), [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) (`3a0eb4c8`, closes #76), [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) (`b3a6b088`, closes #77) and [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) (`42ae09b7`, closes #78). All are out of draft. Server #169 follows #167; web order is #75 → #79 → #80 → #81. Independent server #166 remains in the preview composition. Maintainers control acceptance and release; these issues remain open until their changes are accepted.

The Pi preview now runs composed server `88c2c10c830034cee70a46fca717af518803a544` and web `42ae09b7c6be50cd0f617bad8aea35825be9f12e`, with the [updated changelog and exact source](https://canadaverse.org/beacon-dev/source.html). Raw packets remain 72 hours, archived hourly analytics 30 days, telemetry 720 hours. All four candidates passed their native Pi suites; the final web build passes 895 tests. Server tests use actual PostgreSQL. Windows server/full destination/dashboard validation and 48 focused final comparison/API tests also pass. Desktop, 390-pixel phone, English/French, keyboard, legacy/shared links and Back/search/sort/scroll were checked. Physical iPhone Safari and production-volume capacity remain separate gates.

Migration 040 preserves original rows and repairs available archived unknown-payload counts without inventing signal samples. A restored clone passed the migration probe. A fresh private dump was copied off the Pi and its checksum verified; the original schema039 database and matching binary/config/source are retained for DB-aware rollback. Only the Beacon app restarted for the server change; 22 other containers were unchanged. Frontend publication restarted no services. Both MQTT feeds reconnected. Public admin, backup and foreign detection remain disabled.

## Four review slices

| Slice | Delivered behavior | Dependency |
|---|---|---|
| Trustworthy metrics, server #169 | Packet-arrival bookkeeping is separate from status/neighbour presence. Activity returns its complete-bucket window, generation time, selected-window stored total, last complete hour and latest retained packet. Unknown payloads count; non-finite signal is unknown. The legacy presence counter remains API-compatible. | #167; compose independent #166 |
| Unified destination, web #79 | `?tab=Observers&observer=<id>&range=7d`; directory selection opens the dashboard. Legacy Analytics/Stats aliases, quick inspection with Open dashboard, copied links and Back state remain compatible. | #75 |
| Dashboard, web #80 | Identity and separate freshness, six summary cards, searchable observer picker, activity/type/signal first, device telemetry below and expandable model/firmware/client/radio/brokers/key. Two-column phone cards; English/French text. | #79 and server #169 metadata |
| In-context comparison, web #81 | Current observer preselected as A; shared activity anchor/window/axes, six-metric table and retained flood-packet overlap. Invalid/self/missing/mismatched windows are explicit. Shared reader accepts legacy encoded status JSON; current noise floor and freshness remain usable. | #80 and server #169 |

Use the existing stack refresh/publish/check helper after merges. Shared navigation/API changes stay serial; independent #166 can still merge separately. Focused parent-to-head diff links are in each PR. A history-only refresh with an identical source tree does not require a new Pi artifact.

## Counting and discrepancy audit

Dashboard totals count stored packet/observer records under Beacon's existing deduplication, not every RF reception or every MQTT delivery. Status/neighbour messages affect general presence and the legacy counter but never new packet-arrival timestamps. Complete bucket bounds are visible; longer ranges use coarser buckets, so their effective end can precede a shorter range's end. Summary charts may outlive raw packet details. Comparison uses the same effective window for both observers; its overlap counts retained distinct flood hashes across all received regions. Current device values/latest complete hour have their own freshness and hour bounds.

For Orleans-Observer, the matched public key and first-seen date were verified. At the captured comparison, CoreScope's cumulative count was 358,010 versus Beacon's legacy count 356,200: **1,810 remains unexplained**. In the common completed UTC hour 2026-09-27 01:00–02:00, CoreScope showed 388 reception rows and Beacon 113 deduplicated records. These are different grains. Matching public broker names does not prove identical broker inputs, ACLs, reconnect history or persistence; the comparison is not proof of packet loss and does not close server #116. Private aligned delivery ledgers would be needed to attribute the remaining difference. No historical counter was rewritten.

## Subsequent releases

1. **Connected investigation:** packet → exact observed path/route → reporting observer → map. Consistent actions and return navigation; distinguish exact retained evidence from possible prefix matches. Route details need named clickable hops, related retained packets/observers, map action and shareable selection.
2. **Node, route and trace presentation:** reuse readable summaries and expandable detail. Separate current identity/location from historical activity; place a reception timeline beside traces and explain missing replies/uncertain timing without declaring loss.
3. **Additional analytics:** observer reach/timing, channel activity, route patterns and hash ambiguity, each with counting definitions and useful drill-down. Confirmed identities and unresolved prefixes must be separate; path/endpoint identifiers are not all unique nodes heard.
4. **Quality of life:** global entity search, favourites, saved packet/channel filters, explicit pause/resume/time controls and bounded retained replay. Keep map position/selection and add age/layer legends, fit-selected-path and contextual investigation. Channel key/history availability and empty-state reasons must be clear.

Review open issues and feedback first. Broader server #60/#72/#99/#116 and web #12 remain partial. Observer translations do not close all of #12. The new [Mesh Scopes draft](mesh-scopes-plan.md) is a separate interoperability follow-up, not part of the observer PRs.

## Acceptance retained for review

- Six summary cards and charts reconcile to the returned effective window; recent packet traffic and stale/missing status are distinct.
- PostgreSQL regressions cover status-only messages, duplicate records, unknown payloads, archived expiry/repair and invalid samples. Existing telemetry reset/missing-data coverage remains in the full suite.
- No previous observer/range data is shown under a new selection. Invalid/old-server comparison windows show an explicit unavailable state.
- Lazy charts and shared bounded queries remain; there is no separate request per card. Observer refreshes coalesce through the query cache.
- Exact native source, public assets/source offer/changelog and rollback are recorded for the preview. Already-purged history, physical Safari, production load and owner-controlled releases remain explicit limits.
