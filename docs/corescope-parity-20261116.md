# CoreScope / Beacon parity inventory — 16 November 2026

## Scope and evidence

This is a read-only source audit, not a fresh performance benchmark or physical-device acceptance result. CoreScope's working checkout was not changed. Its only observed dirty entry was the existing `.codex-remote-attachments/` directory. Source was read with immutable `git show` / `git grep` references, not inferred from whichever worktree happened to be checked out. Tokensave tools/database were unavailable.

The remote snapshot was checked at approximately 07:17 UTC. Later Beacon changes
prepared during this audit are separate proposals, not silently relabeled as
features already present in the baseline.

| Target | Verified head | Meaning |
| --- | --- | --- |
| `Kpa-clawbot/CoreScope` master | `d80ce90976d5ca7e31c270badda58187100a8af8` | Canonical upstream comparison |
| `n30nex/CoreScope` master | `43d83918c689837388a7d9fa6bf0e4382ec23f6b` | Canadaverse fork comparison; distinct capabilities/history |
| Existing `F:/Corescope` checkout | `6ae7971da0f55ba7da4158442711ad483b1507ea` | Stale working checkout; not the current upstream source |
| Beacon web dev | `7ed6a6264a1f79927c8eb21550be84bb18609575` | Current dev baseline checked against remote |
| Beacon server dev | `87ea88337ad25ea70b7fac927dabe835596cf445` | Current dev baseline checked against remote |
| Beacon qualified preview web | `4ee1fc304411a879626b3878d9ab2182264f36df` | Dev plus independently proposed audit/browser fixes |
| Beacon qualified preview server | `6292a743aaeb088132cc86320dc7f92343cb1e7e` | Dev plus independently proposed audit fixes |

The CoreScope fork versus current upstream diff spans 919 files. It is not a safe feature-port list: it combines upstream drift, custom features and a different storage implementation. Upstream's current `cmd/server/main.go` opens SQLite and polls it for live data; our fork's same file adds a `--backend` choice and its config documents SQLite/PostgreSQL selection. Do not describe upstream CoreScope as already running the fork's PostgreSQL work. Conversely, the upstream README's small in-memory benchmark is not a measurement of the fork, today's Beacon, or production at another retention/traffic scale.

“100% parity” needs a versioned list of user capabilities and acceptance tests. Page count, screenshots, endpoint count and percentage-of-lines ported are not valid denominators. Separate implemented-source coverage, configured-on-deployment availability, end-to-end acceptance, and deliberate non-goals.

## Capability matrix

`Gap` means no equivalent was found in the inspected Beacon dev UI/API contract. `Partial` means some required behavior exists, but the complete workflow differs. A disabled native feature is not an absent implementation.

| Capability | Current CoreScope upstream evidence | Beacon dev/preview disposition | Smallest useful next step |
| --- | --- | --- | --- |
| MQTT ingest and decoded packet feed | `cmd/ingestor`, `cmd/server/routes.go:324–331`, `public/packets.js` | Present: Go ingest, `/api/v1/packets`, live WS, virtual feed | Keep equivalent packet fixtures and counts, not UI pixel parity |
| Multi-broker/source filtering | Config/source routes plus observer metadata | Present: native broker configuration, IATA/region filters | Expose bounded broker freshness/gap indicators from existing status |
| Packet byte investigation and observations | Packet detail, `/api/packets/observations` | Present: PacketInvestigation/structure/ObservationTable | Preserve exact wire bytes and observation provenance |
| General raw packet decode tool | `/api/decode` POST | Gap: stored-packet investigation exists; equivalent public raw decode workflow not found | Separate bounded read-only decode proposal with size/type validation; no RF transmission |
| Boolean/expression packet filter | `public/packet-filter.js:1–47` lexer/operators | Partial: payload/route/observer/scope and hash/path filters; no general expression grammar | Add selected missing filters first; design a shared validated grammar before a full parser |
| Live geographic packet animation | `public/live.js`, route renderer | Present in native Map; preview enforces bounded work | Preserve unknown-hop rejection and elapsed-time motion; measure representative scenes |
| VCR historical replay/scrubbing/speed | `public/live.js:147+`, `/api/packets/timestamps` | Gap: native play/stop exists, historical VCR equivalent not found | Cursor-bound replay API and bounded client buffer before timeline UI |
| Node directory and neighbors | `/api/nodes/*`, `public/nodes.js` | Present: node filters/sorting, neighbor evidence, detail panels | Keep loaded-view completeness explicit and missingness visible |
| Nodes export to companion contacts | `public/nodes-export.js:1–91`; `nodes.js:764/794/1671` | Baseline gap; focused contact-file draft PR #219 supplies a bounded increment | Loaded rows only; full public keys, supported roles, valid coordinates, no private keys or fabricated route |
| CSV analysis export | CoreScope's node export is JSON, not CSV | Baseline gap; focused draft PR #210 supplies a separate analysis export | Formula-safe CSV of loaded/filtered rows; do not call this companion-export parity |
| Node/contact QR sharing | Node QR tests and node detail UI | Gap in inspected Beacon node UI | First agree signed advert vs public identity/link semantics; never synthesize a signed `meshcore://` advert |
| Channel QR/key sharing | `public/channel-qr.js` | Gap in inspected Beacon channel UI | Separate opt-in key-sharing contract; keys must not leak through ordinary copied links |
| Channel message viewing/decryption | `public/channels.js`, `channel-decrypt.js` | Present for backend-known channels; browser BYOK differs | Compare named/default/hashtag/private-key workflows separately |
| Browser-provided channel keys | `public/channel-decrypt.js`, key UI | Partial/gap: no matching user BYOK workflow found | Explicit client-only secret storage policy and hash-collision handling before implementation |
| Hashtag proposals/accounts workflow | `public/channel-proposals.js`, gated auth routes | Partial: Beacon has accounts, not equivalent proposal workflow | Track proposals as a distinct feature; reuse native identity/authorization |
| Observer health, detail and comparison | `public/observers.js`, `observer-detail.js`, `compare.js` | Present: observer directory/detail/stats and native comparison | Define equal time windows and received vs distinct counts |
| Pinned repeater dashboards | Analytics My Repeaters tab | Present/partial: native Atlas includes node/observer/telemetry views | Atlas is the reuse point; no second dashboard/storage system |
| Accounts, session/device management | Gated auth routes and account/admin UI | Present in native Beacon source; off on preview | Root-host/subpath and delivery setup are operational gates, not missing-code labels |
| Alerts/notifications | `public/notifications.js`, user service | Present in native Beacon source; off on preview | Qualify real email/push with privacy, dedupe and expiry; source tests alone are not delivery |
| Native telemetry/polling | CoreScope observer/reading/user integrations | Beacon native coordinator, trusted reading APIs and requests exist; off on preview | Prefer one native coordinator; do not restore independent collector as an unnoticed dependency |
| RF/signal/payload/path distributions | CoreScope Analytics RF/Topology/Hash Stats | Present/partial: Beacon Signal/Paths/Mesh/Traffic | Compare definitions and denominator coverage rather than matching chart count |
| Hash collision matrix/prefix selection tool | `analytics.js:1732+`, Prefix Tool tab | Gap/partial: path hash stats and ambiguity handling exist; visual planning tool not found | Read-only collision inventory first; recommendation remains advisory, not proof of RF collisions |
| Longest links/distance analytics | `/api/analytics/distance`, lazy build/readiness handling | Gap in inspected Beacon stats routes/UI | Bounded confirmed-hop distances with coordinate age/source and anomaly handling |
| Relay airtime share/retransmissions | `/api/analytics/relay-airtime-share`, `/retransmissions` | Partial: native signal/observer activity exists; corresponding relay-share view not found | State airtime assumptions, dedupe observation repeats, separate estimated airtime from occupancy |
| Route/subpath patterns | `/analytics/subpaths`, bulk/detail APIs | Partial: known Routes and exact route evidence are present | Reuse cursor-bound evidence; add an explicitly bounded subpath aggregation if justified |
| Neighbor graph | CoreScope Analytics Neighbor Graph | Present: native Beacon NeighbourGraphTab | Do not restore experimental 3D Topology merely to match a graph checkbox |
| Scope totals | `/api/scope-stats`, latest upstream splits unscoped by route | Present/partial: native Beacon Scopes stats | Compare compatible route families and dedupe grains; named/default/wildcard remain distinct |
| Configured-versus-forwarded scope audit | `cmd/server/scope_audit.go`, `/api/scope-audit`, `public/scope-audit.js` | Gap beyond basic scope totals/provider metadata; old preview extension retired | New evidence schema/proposal: configured, advert default, heard and uniquely repeated are separate facts |
| Node reach/geographic coverage | `/api/nodes/{pubkey}/reach`, `node-reach.js` | Gap beyond map/neighbors | Observed coverage first, with freshness/window/location quality; no inferred radio radius presented as measurement |
| Mobile RX coverage and leaderboard | Optional `/api/rx-coverage`, node RX coverage, `/rx-leaderboard` | Gap; native repeater telemetry is not mobile RF-coverage data | Explicit user opt-in, coarse geography/privacy, dedupe, throttling and signed/bounded intake contract |
| Passive RF noise samples | Optional `/api/rf-noise` | Partial: observer telemetry/noise exists, mobile sample workflow differs | Keep producer trust/source and channel configuration in the measurement schema |
| Global search shortcut | `public/index.html:170`, shared search UI | Gap: individual page searches exist | Bounded Ctrl+K palette reusing node/observer/packet searches; no full-network download |
| Theme editor/export/branding | `customize.js`, `customize-v2.js`, theme config | Partial: native theme selection and operator allowlists exist | Start with safe preset selection/export; avoid arbitrary CSS/script inputs |
| Audio/sonification lab | `public/audio-lab.js:561`, `/api/audio-lab/buckets` | Gap, optional product enhancement | User-triggered/muted-by-default, bounded audio work, reduced-motion/sensory controls |
| Performance/operator diagnostics UI | `/api/perf*`, MQTT status panel | Partial: Beacon native admin/metrics/DB diagnostics and planguard exist | One authenticated health view from existing metrics, no raw SQL/log/secret leakage |
| Backup/recovery tooling | Guarded `/api/backup` and manage tooling | Present/partial: native command/download and tested backup workflow; import UX separate | Do not confuse successful export with restore acceptance |
| Portable API contract | CoreScope protobuf/API docs | Present: Beacon OpenAPI, typed clients and `/info` compatibility/features | Add exact build identity/version compatibility to all operator receipts |
| Localization/mobile usability | CoreScope responsive/touch work; inspected UI is largely English | Beacon explicit English/French/Swedish catalogs and qualified responsive UI | Preserve as a Beacon strength; include translations in new features |

## Our fork is a separate comparison target

At `43d83918`, the Canadaverse fork includes `public/cross-border.js`,
`cross-border-dashboard.js`, `cross-border-flow.js`, PostgreSQL bootstrap/config and
PostgreSQL-specific tests, alongside scope audit/RX coverage/audio. These are not
all current upstream CoreScope features. New upstream commits since that fork
also fix evicted-store references, scope counts, map theming, route UI, clocks,
observer charts and reach links. A port from the fork can carry stale upstream
bugs unless the target feature is re-reviewed against current upstream.

Do not copy the fork wholesale or replace Beacon's PostgreSQL/read-model/native
coordinator foundation with CoreScope's storage paths. Port user outcomes and
evidence contracts in bounded pieces. CoreScope's LICENSE is GPL-3.0 while its
package metadata still says ISC; avoid treating the npm metadata as a permission
to copy arbitrary implementation code. Contact-file support here is independently
implemented from the field schema, not a code transplant.

## Prioritized roadmap and release classification

No numeric version or due date is assigned here: use the maintainer's current
major/minor schedule and the `release:minor` / bug-fix labels consistently.

### Safe next minor features

1. **Loaded Nodes CSV** — bounded, no new API, no extra requests, formula-safe cells.
   Explicitly report that only loaded filtered rows are exported. See
   [draft PR #210](https://github.com/MeshCore-Beacon/beacon-web/pull/210).
   It is an analysis enhancement, not companion-import equivalence.
2. **Contacts JSON export** — independent serializer and action; skip invalid
   identities/locations and duplicate full keys; do not synthesize learned routes,
   private credentials or signed adverts. List hearing time is not advert time.
   A consumer import test remains necessary before claiming device compatibility.
   Prepared as [issue #218](https://github.com/MeshCore-Beacon/beacon-web/issues/218)
   and [draft PR #219](https://github.com/MeshCore-Beacon/beacon-web/pull/219), commit
   `324123dee83da17c7050742d0bf9ffe80219c3f6`. Forty-two focused tests, build/lint and
   isolated desktop/390px touch browser downloads passed. Combined-preview
   qualification is recorded separately in the system audit delivery receipt.
3. **Read-only global search palette** — shared existing endpoint adapters,
   cancellable requests, request limits, keyboard access and empty/error states.
4. **Public node/share links and QR** — begin with Beacon URLs/full public-key
   identity, not a signed MeshCore business card without raw advert evidence.
5. **Loaded-view exports for observer comparisons/analytics** — reuse established
   window/completeness metadata; avoid creating unbounded bulk export APIs.

### Minor features needing backend contracts first

6. Distance/relay share analytics: finite coordinate pairs, confidence, age and
   explicit observation/packet/airtime denominator. Use rollups and indexes, bounded
   windows and plan/latency fixtures; never N+1 per-repeater queries.
7. Prefix collision inventory: expose candidates and observed path widths,
   distinguish prefix ambiguity from measured collisions, add regional constraints.
8. Replay: page by exact receipt/time cursor and dedupe id; bound memory and
   prefetched history; honor retention gaps and distinguish reconstruction from RF truth.
9. Scope audit: preserve missing versus explicitly empty reports; compare declared
   lists to uniquely attributed forwarding only; wildcard/default coexistence matters.
10. Coverage: privacy and consent precede producer collection; separate observed
    points, modeled estimates, dwell time, receiver capability and gaps.

### Separate major/architecture proposals only when required

11. Durable ingest replay/receipt contract, external federation or new collector
    trust domains. Do not infer application acceptance from MQTT acknowledgement.
12. Breaking API/auth/schema contracts or a large stored-data re-grain. Version
    and migration rehearsal are required, not silently folded into a UI feature.

### Exceed CoreScope on trustworthy evidence

- Make freshness, coverage, truncation and raw-versus-rolled windows visible next
  to metrics; a missing measurement is not zero and a partial export is not a census.
- Give every displayed route a bounded evidence drawer with exact hash widths,
  candidates, time window and provenance. Provide uncertainty rather than attractive
  but invented cross-country animations.
- Offer reproducible performance fixtures: mixed-region cold/warm reads, cache
  outage, reconnect/lag, history pagination and large but bounded map scenes.
- Use one telemetry owner/lease/coordinator contract across firmware and any future
  mobile bridge. Preserve sensor channels, nullable values, trusted producer identity,
  consent, polling budget and report acknowledgement.
- Keep UI rendering work independent of display refresh, stop hidden/disposed work,
  and qualify accessibility/localization on actual browser output as well as unit tests.

## Acceptance ledger

Each capability issue should state: source baseline, current Beacon behavior,
minimum increment, API/schema changes, dependencies, performance budget, privacy/
trust boundaries, acceptance fixtures, browser/mobile checks, release class and
operator gate. Close parity only after the whole user workflow passes; a UI button
or a compiled endpoint alone is not completion. Compare benchmark numbers only
with equivalent retained data, hardware, ingestion rate and measurement method.

## Primary source links

- [CoreScope upstream tree](https://github.com/Kpa-clawbot/CoreScope/tree/d80ce90976d5ca7e31c270badda58187100a8af8)
- [CoreScope routes](https://github.com/Kpa-clawbot/CoreScope/blob/d80ce90976d5ca7e31c270badda58187100a8af8/cmd/server/routes.go)
- [CoreScope actual analytics tabs](https://github.com/Kpa-clawbot/CoreScope/blob/d80ce90976d5ca7e31c270badda58187100a8af8/public/analytics.js#L154)
- [CoreScope contact-file schema](https://github.com/Kpa-clawbot/CoreScope/blob/d80ce90976d5ca7e31c270badda58187100a8af8/public/nodes-export.js)
- [CoreScope scope evidence rules](https://github.com/Kpa-clawbot/CoreScope/blob/d80ce90976d5ca7e31c270badda58187100a8af8/cmd/server/scope_audit.go)
- [CoreScope live/VCR implementation](https://github.com/Kpa-clawbot/CoreScope/blob/d80ce90976d5ca7e31c270badda58187100a8af8/public/live.js)
- [Canadaverse CoreScope fork](https://github.com/n30nex/CoreScope/tree/43d83918c689837388a7d9fa6bf0e4382ec23f6b)
- [Beacon web dev feature tree](https://github.com/MeshCore-Beacon/beacon-web/tree/7ed6a6264a1f79927c8eb21550be84bb18609575/src/features)
- [Beacon API router](https://github.com/MeshCore-Beacon/beacon-server/blob/87ea88337ad25ea70b7fac927dabe835596cf445/internal/api/router/router.go)
- [Beacon stats contract](https://github.com/MeshCore-Beacon/beacon-server/blob/87ea88337ad25ea70b7fac927dabe835596cf445/internal/api/handlers/stats.go)
- [Canonical MeshCore companion wire protocol](https://github.com/meshcore-dev/MeshCore/wiki/Companion-Radio-Protocol) — distinguishes contact metadata from raw signed business-card export/import.

The report is source-backed. It does not assert that every CoreScope instance has
every optional feature enabled, that every legacy fork feature is current, or that
this review proves production performance or physical companion import behavior.
