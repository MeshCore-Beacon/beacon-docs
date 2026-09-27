# Mesh Scopes interoperability plan

Updated 27 September 2026 UTC. The [MeshMapper Scopes API](https://wiki.meshmapper.net/scopes-api/) is published and its regional endpoint and conditional caching were checked live. The API-contract blocker is removed. Beacon's importer is still unimplemented and disabled; this document specifies the next focused scope work, not an available configuration feature.

## Published contract

`GET https://yow.meshmapper.net/get_scopes.php` returns the YOW catalogue without parameters or an API key. Use an explicitly configured regional endpoint; this is not a central API accepting an IATA query parameter. Group hosts return a combined catalogue for their enabled member regions.

The response carries `generated_at`, `region`, `zones`, regional `repeaters` and `scoped` totals, and a `scopes` array. Each scope has its exact `name`, `repeaters`, `default`, `monitored` and `wardriving` values. Zero-repeater monitored or wardriving entries are useful discovery candidates and must be retained. Do not sum per-scope counts into a unique-repeater total: memberships overlap. MeshMapper's enabled/public population also differs from its boundary-based onboarding leaderboard.

This is a names-and-counts catalogue. It supplies no repeater identities, per-repeater evidence, transport keys or channel decryption keys. A group's `zones` list does not assign every returned name or count to every member region. `monitored` and `wardriving` describe MeshMapper's configuration; they do not prove traffic or forwarding in Beacon.

Responses advertise a five-minute cache lifetime and a strong ETag. Conditional requests use `If-None-Match`; an unchanged catalogue returns HTTP 304 with no body. `generated_at` is excluded from the ETag, so keep the source generation time separately from the last successful local check. The documented errors are 404 `zone_not_found`, 429 `rate_limited` with `Retry-After` in seconds, and 503 `unavailable`. The limit is 60 requests per minute per IP; schedule conservatively alongside other consumers.

Live check on 27 September: YOW returned HTTP 200, `zones: ["YOW"]`, seven named entries including two at zero repeaters, `Cache-Control: public, max-age=300`, and an ETag. A conditional request with that ETag returned HTTP 304 and an empty body. These are point-in-time checks, not fixed regional totals or a stability test.

## Beacon implementation boundary

Beacon already has manual `scopes`, transport-code matching, node default scopes, observer scope associations, packet filters and channel SQL scope joins. Reuse them. Source audit: server candidate `99e623c5`, `internal/config/seed.go`, `internal/scopestore/scopestore.go`, `internal/ingest/packet.go` and `db/scopes.go`.

- Keep the existing manual list. Preserve source spelling and case; use Beacon's existing normalization/key derivation when registering candidate names, and test its prefix handling against a known transport-packet fixture. Plain names currently receive `#`; explicit `#` and `$` prefixes are retained. Imported names must not overwrite manual metadata or keys.
- Track imported catalogue membership separately from traffic evidence. A successful import must never create observer associations, node defaults, forwarding claims or packet counts. Match actual packet transport codes through the existing ingest path before tagging messages. An unknown identifier stays unknown until supported by that match.
- Start with explicitly mapped single-region sources for IATAs configured in Beacon. Require the response's `region` and single-entry `zones` to match the configured IATA. Reject group responses in this first importer; later group support must preserve group-level provenance without inventing per-region attribution.
- Deduplicate canonical candidate names across sources while retaining each source's membership. A fresh snapshot replaces only that source's imported memberships. Never delete scope identities referenced by retained packets, manual entries or independently observed evidence because a remote name disappears.
- A failed or invalid refresh keeps the complete last-known-good snapshot and every manual entry. Preserve that snapshot across a restart. Expose the source, source generation time, last successful check and refresh failure to operators. HTTP 304 is a successful check, not a missing or empty catalogue; a valid empty 200 snapshot is a distinct case.
- Bound response bytes, source count, name length and effective candidate count. The current transport matcher iterates candidate keys per transport packet, so measure CPU cost at the supported catalogue limit. Publish a complete validated snapshot atomically, without a remote request in the ingest path or a partial update after failure.

Proposed configuration namespace remains `meshmapper.scopes`: `enabled` defaults to false, `sources` explicitly maps an IATA to a published HTTPS endpoint, and `refresh_interval` defaults to one hour with a five-minute minimum. These names are a design proposal, not shipped YAML. Replace the earlier single-URL proposal; multiple regions need explicit mappings. No API-key setting is needed. Keep IATA metadata synchronization independently configurable.

Use bounded HTTP timeouts, cached ETags and delayed retries respecting `Retry-After`. Schedule multiple sources without request bursts. Never scrape map pages, discover unpublished endpoints, or forward credentials to this public service.

## Small delivery steps

1. **Optional catalogue import.** Implement configuration, validation, cached conditional refresh, durable source membership and last-known-good handling. Reuse the existing scope store and name derivation, preserve manual values, and refresh the effective matching catalogue safely. Add operator-visible synchronization status. Import counts remain labelled MeshMapper catalogue counts, separate from Beacon's own observations.
2. **Channel message scope tags.** Audit existing history/catch-up queries and live message events, then expose the matched packet scope consistently in REST and WebSocket payloads. Add English/French tags, filter context and an explicit unknown state. Importing names does not decrypt a channel or recover already-purged packets. Historical backfill is separate work, not an implicit full-table rescan.
3. **Evidence and regional views.** Present advertised defaults, observed forwarding and observer-reported scopes with their own timestamps. Add group catalogues only with honest group-level attribution. Per-repeater imports or app-discovery evidence require a separate published contract; this API cannot supply them.

Do not copy screenshot retention values or change MeshMapper's settings. Existing packet/analytics policies, public admin/backup restrictions and owner-controlled release/cutover remain in force.

## Acceptance

Cover 200/304, empty and zero-count entries, overlapping sources, case/prefix preservation, changed generation time with unchanged ETag, 404/429/503, timeout, malformed/oversize responses, region/group mismatch, restart during outage, and manual/imported name collisions. A failed update cannot erase the prior valid catalogue or partially activate names. An absent remote name cannot erase historical or independently observed evidence.

Prove packet matching with a known fixture, including ambiguous candidates; catalogue membership alone is insufficient. For channel tags, reconcile history, catch-up and live delivery and verify English/French desktop/phone behavior. Run bounded native Pi tests and compare ingest CPU before enabling a source. Keep all current review candidates in the preview composition; update its changelog/source and preserve rollback for each application change.

Review feedback and existing issues remain first priority. This contract makes the scope follow-up implementable; it does not imply that the importer or tagging work has shipped.
