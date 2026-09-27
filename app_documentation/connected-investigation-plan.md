# Connected investigation rollout

## Packet reception investigation — 27 September

[Web PR #83](https://github.com/MeshCore-Beacon/beacon-web/pull/83), `1d5d65e2807c2cb53a998743212d9a5b64ba80c4`, follows #81 and closes focused issue #82 when accepted. It adds grouped retained packet reports, selected-report links, observer inspection/dashboard access and a selected-path map. The initial list stays compact and keeps the selected group open. Equal prefixes are not treated as confirmed identical physical routes; empty/missing paths and TRACE intended routes have explicit labels.

Map projection omits ambiguous/unlocated identities and breaks lines at gaps. Live animations across uncertain chains are suppressed, so fewer speculative lines appear. Unavailable selected paths no longer silently show All paths. A shared-path loading race is fixed by checking the requested packet hash. Packet labels use the existing Noto Sans stack; external basemap emoji-glyph/sprite fallback warnings can still occur.

The Pi now runs web `1d5d65e` with unchanged server `88c2c10c`. Native build/lint and all **906 tests** pass; focused Windows checks and desktop/390px phone/English/French/keyboard/Back/shared-link checks pass. Public assets and source match, both MQTT feeds are connected, and the frontend publication restarted no services. Earlier review candidates remain included. The [changelog/source](https://canadaverse.org/beacon-dev/source.html) identifies the running build. Maintainers still own merges, stable releases and production cutover.

**Next:** review feedback/issues first, then define a bounded known-route-to-retained-packet/report API with exact-byte versus possible-identity semantics and pagination. Non-packet overlay return navigation remains a separate follow-up. MeshMapper scope import remains a draft pending an agreed public endpoint/schema. Broader server #60/#72/#99/#116 and web #12 remain open; this is a first connected-investigation slice, not full parity.

## Evidence boundaries and follow-ups

The current packet detail is already deduplicated by packet/observer and can contain reports from multiple received regions. Grouping uses complete path bytes plus hash width; missing/malformed evidence is not folded into zero-hop paths. It is not a reconstruction of all RF receptions or an end-to-end delivery proof. The primary packet URL carries `observation=<id>`; copied path links carry the observer path key or `trace`. Old links remain usable, and unavailable selections are explicit.

The next backend contract should provide a bounded, paginated link from a known route to retained packet/report evidence. A match based only on endpoints or short prefixes must not be called an exact physical route. Follow that with node/route/trace presentation and richer return navigation across overlay contexts. Existing observer monitoring, retention and endpoint candidates stay in the review composition.

Validation uses existing client/map components and no new dependency, server endpoint or migration. Physical Safari and production-volume capacity remain separate gates. The initial long report list was tightened after real browser inspection; both the preliminary and final native suites passed, but only the final source is published.
