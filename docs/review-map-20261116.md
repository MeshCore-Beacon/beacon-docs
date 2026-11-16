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

## Verification status

Final head/check, preview deployment and recovery evidence is linked from the delivery receipt. Initial snapshots and historical green runs are not substituted for final-candidate checks.
