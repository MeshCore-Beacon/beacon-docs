# Focused dev review map — November audit

Every bug fix below is an independent PR to `dev`. The current preview is a separately qualified fork composition. No combined bug-fix stack is proposed to the org.

| Component | Focus | PR |
| --- | --- | --- |
| server | Return a structured error when JSON encoding fails | [#297](https://github.com/MeshCore-Beacon/beacon-server/pull/297) |
| server | Coalesce cache-outage reads and recheck late misses | [#298](https://github.com/MeshCore-Beacon/beacon-server/pull/298) |
| server | Bound WebSocket control work and fail closed on missing regions | [#299](https://github.com/MeshCore-Beacon/beacon-server/pull/299) |
| server | Notify clients when the global live queue drops events | [#300](https://github.com/MeshCore-Beacon/beacon-server/pull/300) |
| server | Reject oversized MQTT envelopes before queue admission | [#301](https://github.com/MeshCore-Beacon/beacon-server/pull/301) |
| server | Preserve known scopes when a neighbor report omits its list | [#302](https://github.com/MeshCore-Beacon/beacon-server/pull/302) |
| server | Keep missing and invalid signal measurements out of averages | [#303](https://github.com/MeshCore-Beacon/beacon-server/pull/303) |
| server | Pin route evidence cursors to the observed hash representation | [#304](https://github.com/MeshCore-Beacon/beacon-server/pull/304) |
| server | Count the inserted advert in clock-history retention | [#305](https://github.com/MeshCore-Beacon/beacon-server/pull/305) |
| docs | Bound Docker logs in every deployment template | [#63](https://github.com/MeshCore-Beacon/beacon-docs/pull/63) |
| docs | Correct TRACE widths and performance claims in the design guide | [#64](https://github.com/MeshCore-Beacon/beacon-docs/pull/64) |
| server | Bound boot backfill writes without losing progress | [#306](https://github.com/MeshCore-Beacon/beacon-server/pull/306) |
| server | Validate TRACE evidence before resolving or promoting hops | [#307](https://github.com/MeshCore-Beacon/beacon-server/pull/307) |
| server | Include late hearings of older packets in node activity | [#308](https://github.com/MeshCore-Beacon/beacon-server/pull/308) |
| server | Keep rebuilding activity history from looking like zero traffic | [#309](https://github.com/MeshCore-Beacon/beacon-server/pull/309) |
| server | Expose optional artifact identity separately from API version | [#310](https://github.com/MeshCore-Beacon/beacon-server/pull/310) |
| web | Bound live-map worker updates on high-refresh displays | [#197](https://github.com/MeshCore-Beacon/beacon-web/pull/197) |
| web | Coalesce chart resizes and cancel pending work on disposal | [#198](https://github.com/MeshCore-Beacon/beacon-web/pull/198) |
| web | Show TRACE quality and original wire SNR evidence | [#199](https://github.com/MeshCore-Beacon/beacon-web/pull/199) |
| web | Keep copied route links tied to their evidence window | [#200](https://github.com/MeshCore-Beacon/beacon-web/pull/200) |
| flutter | Bound mobile HTTP request lifetimes and account responses | [#22](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/22) |
| flutter | Skip mobile reads after their screen has been superseded | [#23](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/23) |
| web | Keep future-dated channel messages from pinning the conversation | [#201](https://github.com/MeshCore-Beacon/beacon-web/pull/201) |
| flutter | Keep future-dated channel messages from pinning the conversation | [#24](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/24) |
| server | Trim trailing whitespace in legacy SQL fixtures | [#311](https://github.com/MeshCore-Beacon/beacon-server/pull/311) |
| server | Reject node activity windows shorter than its hourly resolution | [#312](https://github.com/MeshCore-Beacon/beacon-server/pull/312) |
| web | Allow unavailable signal fields in live event types | [#202](https://github.com/MeshCore-Beacon/beacon-web/pull/202) |
| web | Drain virtual-scroll timers before test environment teardown | [#203](https://github.com/MeshCore-Beacon/beacon-web/pull/203) |
| web | Atlas rename compatibility, refreshed for native telemetry pins | [#195](https://github.com/MeshCore-Beacon/beacon-web/pull/195) |
| docs | Full audit, roadmap and delivery receipt | [#62](https://github.com/MeshCore-Beacon/beacon-docs/pull/62) |

## Review order

1. JSON response correctness, cache outage handling, input/stream bounds and signal presence.
2. Backfill, activity/clock correctness, TRACE integrity and route evidence, with their matching client changes.
3. Map/chart work bounds, mobile HTTP lifetime, channel ordering, test isolation and deployment documentation.

Regenerate affected SQL/Swagger files and rerun current CI when overlapping fixes are merged. GitHub mergeability and source ancestry are checked separately from green checks. Draft status does not imply operator acceptance.

## Superseded and deferred

Closed with replacement comments: server #296/#266/#268/#292/#293; web #196/#182/#184/#192/#193; Flutter #21/#11; docs #43/#44. Their branches are retained.

Topology remains a future feature under web #163. Scope/profile extensions and any future companion collection bridge need clean proposals against accepted dev. They are not hidden prerequisites of these bug fixes. The old independent collector and duplicate dev1 PR path are retired from this baseline.

## Other open contributions

Flutter #15 addresses the portrait/large-text region selector. Its check state and maintainer workflow approval must be resolved before acceptance; no approval is inferred from source review. Flutter #20 is the existing fl_chart patch update, with CI and Android checks on its recorded head. Avoid opening duplicate dependency or portrait fixes.

## Issue disposition and next action

| Repository / issue | Current disposition | Concrete next action |
| --- | --- | --- |
| server #254 / #258 / #252 | Focused fixes #297 / #298 / #306 | Review independently; keep error/outage/timeout regressions |
| server #223 | TRACE fix #307, web #199 | Review wire-width/consumed-hop rules together; preserve raw history |
| server #231 | Web #201 and Flutter #24 | Accept receipt ordering; do not delete future-dated evidence |
| server #224 | Old timeout coupling changed upstream | Soak paced reconfirm progress and separate neighbour task on intended release host |
| server #270 | Replay policy unresolved | Specify age/rate/idempotency/acceptance contract before enabling producer replay |
| server #72 | Backup capability partly implemented; restore UI is not | Design authenticated import/off-site retention; prove recovery separately |
| server #60 | Older proposal overlaps new native accounts | Reconcile with current auth model; allowlisted operator controls only |
| server #265 | Updated audit tracker | Use independent fixes; no combined Topology dependency |
| web #96 / #161 / #162 | Closed: Atlas, sparse samples and pointer cleanup are in dev | Preserve their current regressions; #195 remains a separate compatibility fix |
| web #170 | Existing overscroll report not freshly reproduced | Recheck channel sidebar at phone height/large text with long lists; no speculative patch |
| web #150 | Configurable map defaults enhancement | Agree operator defaults versus per-viewer preferences; retain explicit URL overrides |
| web #163 | Deferred Topology proposal | Follow the bounded snapshot/renderer acceptance plan in the roadmap |
| web #181 | Updated native Atlas/web tracker | Review #195 and #197–#203 |
| docs #13 | Focused log-bound fix #63 | Verify all deployment templates; existing containers need planned recreation |
| docs #45 | Updated central queue | Keep one independent dev PR per fix and dated delivery receipts |
| Flutter #4 / PR #15 | Existing portrait/large-text contribution retained | Maintainer enables checks, refreshes against dev, then physical acceptance |
| Flutter #10 | Deferred native-coordinator bridge | Agree credential/lease/report contract before companion RF work |
| Flutter PR #20 | Existing dependency patch, CI/Android green on recorded head | Refresh/check against accepted dev; no duplicate dependency proposal |
| Legacy app archive's four bot PRs | Not the canonical app; repo is not GitHub-archived | Owner decides archive/maintenance policy; no automatic merge or archive |
| beacon-agent / beacon-scratch | Scaffold / notes, not runtime implementations | Keep one canonical polling contract; do not build a second unneeded service |
| Private independent intake | Stopped on preview, history preserved | Keep recovery/export access; future migration must retain provenance/channels |

Issues listed as future design, existing unreproduced reports or operator gates are
not silently called fixed. The broad superseded PRs were closed, not merged.

## Verification status

All 30 org drafts target dev and were mergeable at the final check. Current-head code checks passed. Exact runtime/artifact/backup proof and visual limitations are in the [delivery receipt](audit-20261116.md#delivery-receipt--qualified-preview). No org merge or dev/dev1/live deployment was performed.
