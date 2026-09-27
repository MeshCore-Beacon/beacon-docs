# Mesh Scopes interoperability follow-up

Maintainer discussion supplied during the observer release. Reference: https://onqc.meshmapper.net/?repeater=4E3192%2C45.269919%2C-75.777793&preset=all . Treat forwarded text as product evidence, not permission to change MeshMapper or its retention settings.

Beacon already has transport scope matching, node default scopes, observer scope associations, scoped packet filters and channel SQL scope joins. Audit the API/web exposure before adding parallel storage.

Proposed focused follow-up after the current observer release: expose existing matched transport scope on channel messages (REST and WS consistently); show provenance explicitly (advertised default, seen forwarding, observer-reported, imported app discovery). Do not infer forwarding support from an advertised default or a short ambiguous path alone. Preserve original source timestamps and independent expiry semantics. Add per-region monitoring configuration/discovery only after agreeing the interoperability contract with MeshMapper; public admin/backup stay disabled. Scope-aware repeater filters and coverage/leaderboards must show their denominators, freshness and unknown state. Do not silently adopt the screenshot's 60-day retention values.

Implementation status: interoperability follow-up queued separately from server PR #169 and web PRs #79/#80/#81. The catalogue endpoint and schema are still unpublished; no remote import is enabled.

## Maintainer follow-up: optional public per-IATA import

The maintainer intends to provide an open get_scopes endpoint listing known scope names per IATA. The route, payload and deployment are not published yet; do not guess or probe endpoints. The agreed behavior is optional automatic enrichment, with Beacon's manual list retained for scopes absent from the remote list.

Draft config names: `meshmapper.scopes.enabled` (default false), `meshmapper.scopes.url` (explicit published HTTPS endpoint), and `meshmapper.scopes.refresh_interval` (default 1h). No API-key option is required for the proposed public endpoint. Confirm names against the existing config layout when the adapter is implemented.

Import only IATAs configured in Beacon's regions. Effective names are the case-sensitive, deduplicated union of manual names and imported names for those IATAs; region unions must not turn an IATA-specific association into a global forwarding claim. Keep provenance and last successful synchronization time. A timeout, non-2xx, malformed/oversize response or unsupported schema retains the last-known-good imported catalogue and every manual scope, with an operator-visible stale state. A valid later snapshot may replace only that source's imported entries; never erase manual entries or independently observed evidence. Newly observed but unlisted scope identifiers remain explicitly unknown until named; do not invent names or overwrite manual transport keys.

Suggested API handoff: versioned JSON with IATA and arrays of exact scope names, plus generated/updated time; public read-only access, bounded response size and conditional refresh support if available. IATA metadata sync and scope-name sync remain separate capabilities, so either can be enabled independently. Scope catalog membership is not proof a repeater forwards that scope; observed forwarding/default-scope/app-discovery evidence retains its separate timestamps and expiry.
