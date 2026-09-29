# Review corrections and retained-history periods — 29 September 2026

The Pi preview runs server `a35cba1d2c5cd1dccfa4a99b41717747ebd2f2fc` and web `e1133ab5c3364349af900fd4f2093384fbf34f56`, with all prior candidates and the new server #184 / web #95 included. Accepted bases remain server `db30c9b5` and web `17f48fb9`. Both stack Check commands pass for all seventeen exact published application heads; web CodeQL remains skipped. No upstream merge, stable tag or production cutover was performed.

## Maintainer review disposition

| PR | Implemented response |
|---|---|
| Server #166 | Keeps upstream repeat delivery, resolves current advert identity after side effects, removes the redundant observation stub override. Existing inserted/renamed/repeat regressions pass. The optional additional UpsertNode-ID optimization is deferred; repeat events still need current stored identity. |
| Server #167 | Restores both hourly Signal/Paths indexes; folds unknown observer activity into migration 039 and removes the need for a second observer-view rebuild. Archive counts have NOT NULL/default 0, cleanup runners serialize before shared upserts, and hourly IATA summaries explicitly cover 30 UTC days. |
| Server #169 | Removes unmerged 040, preserves the current partial bucket on live requests, aligns fixed-end cache keys and moves the summary query into queries.sql. Freshness fields are explicitly measured at generatedAt even with until; recordedPackets follows the activity window. Doc comments are corrected. |
| Server #172 | Narrows the concurrent evidence index and query with literal hop_count >= 2, repairs unrelated encoding, and tests index contents and custom/generic plans. Prefix-width drift is tracked separately in #183. |
| Server #174 | Manual matches retain first-match priority; ambiguity applies among imported names. Snapshot reads allocate no catalogue copy, invalid saved catalogues do not stop manual startup, and parent cancellation is normal shutdown. Queries/import grouping are tidied. Documentation explains that historical imported identities remain visible after disabling matching. |
| Server #176 | Operator documentation moves out of generated Swagger output, insertion comments are corrected, Message replaces the redundant NewMessage flag, and WebSocket scopeStatus has the enum tag. Contracts are regenerated on the combined stack. |

The coordinated refresh needed two reviewed merges: preserving the new observer explanation beside route documentation, and keeping both observer-summary and catalogue queries in queries.sql. Generated SQLc/Swagger output was regenerated. Existing feature boundaries and all web parents were preserved; web #95 is a new child of #92.

## User-approved history choices

- Observer monitoring and route evidence offer 24h/3d. Explicit raw route/comparison periods cannot exceed 72 hours. Old rolling observer/route 7d/30d links normalize to 3d; copied observer links use that effective range. Explicit invalid timestamps are not silently changed.
- Summary-backed Analytics offers 24h/3d/30d, without seven-day buttons. Traffic, payload, top-observer/advertiser/talker, Signal and Paths summaries survive raw expiry via the durable hourly archive in server #167, combined with live rows by materialized views. A materialized view alone would lose that data when refreshed after deletion.
- Scopes/population/clock/graph views keep their existing non-windowed semantics. Packet detail and exact overlap still depend on retained raw records. Older summaries accumulate after archiving starts; already-purged data cannot be recovered.
- The latest activity bucket may be partial. Revised range/help text ships in English and French. The underlying policy remains 72h raw packets / 30d summaries / 720h telemetry.

## Validation

The complete native Go/PostgreSQL suite passes, including archive failure/retry/concurrency, unknown payloads, index contents and recovery, cache windows, immutable scope snapshots, catalogue restart/cancellation, channel duplicate behavior and timestamp format/skew cases. Fresh migrations include the corrected 039 and omit 040; the existing preview preserves its earlier 040 journal entry and receives a separate operator repair.

The restored preview repair retained 245,934 packets, 919,654 observations, 4,263 messages, 1,956 nodes and 19,861 routes, with identical archive fingerprints. All three affected indexes and 16 count constraints validated. Restoring the old broader route index also passed on that copy. The live repair removed no data; ingestion advanced during its 10.95-second execution. Only the Beacon app restarted for deployment; 23 other containers were unchanged. Frontend publication changed no containers.

An isolated real-PostgreSQL replay with 504 scope candidates and a blocked later route-maintenance batch preserved 100 packets, 800 observations, 100 decrypted messages, 800 normal events, 2,400 opt-in events and 3,200 acknowledgements from 3,200 inputs, with zero fixture drops/invalid inputs in 11.481 seconds. This does not prove universal production losslessness or explain the old 1,810-counter gap.

During a 60.61-second live sample both feeds advanced with zero restarts, parser fallbacks, queue overflows, SQL errors or reconnects. There were 59 clock-skew clamps and 14 malformed-IATA warnings. These remaining input problems are not described as clean logs or proven packet loss.

Windows and native Pi web build/lint and all 940 tests pass. Desktop and French 390px phone checks load real Pi data, show the intended period controls and fit without horizontal overflow. Background-browser clipboard reads were unavailable; canonical effective-range generation is covered by regressions. Physical iPhone Safari remains a separate owner check. All 18 public assets and both source archives match the [changelog/source offer](https://canadaverse.org/beacon-dev/source.html).

## Review and release gates

All seventeen application candidates are out of draft. Server #167/#169/#174 had requested changes and require renewed maintainer review; passing checks do not dismiss those reviews. Server #184 closes #181 and web #95 closes #94 on acceptance. Existing focused closure references remain. Broad server #60/#72/#99/#116 and web #12 stay open. Route prefix-width drift #183 is the next focused issue; optional boundaries and wider parity follow issue work.

External server #182 (private CPU profiling) and web #93 (node-to-map navigation) remain separate unmerged work and are not included in this tested composition. Maintainers decide their integration and the release breakpoint. Both application repos still disable merge commits and the contributor has READ access; enabling that option requires a maintainer. Production-volume evidence, a month of accumulated summary history, physical Safari and owner acceptance remain separate gates; this is a review candidate, not a full parity or production release claim.

| Repository / PR | Published head | Parent |
|---|---|---|
| [server #166](https://github.com/MeshCore-Beacon/beacon-server/pull/166) | `319df7da5246a71f9693f923d2124bf831eabb82` | `db30c9b573357990c41166292e7cf42785c92cc4` |
| [server #167](https://github.com/MeshCore-Beacon/beacon-server/pull/167) | `2ab36356fa023abb247db45c8a33de4410507f64` | `db30c9b573357990c41166292e7cf42785c92cc4` |
| [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) | `8df398ab3da6d65ccb8db31efcbdc599976b582a` | `2ab36356fa023abb247db45c8a33de4410507f64` |
| [server #172](https://github.com/MeshCore-Beacon/beacon-server/pull/172) | `21ea989162659e6efc6dd7cd3a904a2eef655401` | `8df398ab3da6d65ccb8db31efcbdc599976b582a` |
| [server #174](https://github.com/MeshCore-Beacon/beacon-server/pull/174) | `e27fcb3783a2ae2c7abccb22edaff0195caea348` | `21ea989162659e6efc6dd7cd3a904a2eef655401` |
| [server #176](https://github.com/MeshCore-Beacon/beacon-server/pull/176) | `42d50bc692c53a593a1cd65945154e842a72c369` | `e27fcb3783a2ae2c7abccb22edaff0195caea348` |
| [server #184](https://github.com/MeshCore-Beacon/beacon-server/pull/184) | `c39df3043931dbe37d51a73d15f050a1c61d1a3b` | `db30c9b573357990c41166292e7cf42785c92cc4` |
| [web #75](https://github.com/MeshCore-Beacon/beacon-web/pull/75) | `e65e8e42ec7bcd75029ebc636645eedc2b889cbf` | `17f48fb932facbdcc45068afd2db6036ac2ec94d` |
| [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) | `4f3819b805ff8293939d1e6fb3918f05cafaadd5` | `e65e8e42ec7bcd75029ebc636645eedc2b889cbf` |
| [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) | `04ca3da919d9b0430f364a1a93bf36cf56e9770a` | `4f3819b805ff8293939d1e6fb3918f05cafaadd5` |
| [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) | `2f76286ec89c81db0345937b8c1712f363bd2e43` | `04ca3da919d9b0430f364a1a93bf36cf56e9770a` |
| [web #83](https://github.com/MeshCore-Beacon/beacon-web/pull/83) | `0787e5b5fdb1d8d47aefcbb20e816ba280a2ebe2` | `2f76286ec89c81db0345937b8c1712f363bd2e43` |
| [web #85](https://github.com/MeshCore-Beacon/beacon-web/pull/85) | `b21b8704c7403d7f963dc445de7137b9857e194e` | `0787e5b5fdb1d8d47aefcbb20e816ba280a2ebe2` |
| [web #87](https://github.com/MeshCore-Beacon/beacon-web/pull/87) | `be5434a3d4784e26434b5395693896dc7139fd4d` | `b21b8704c7403d7f963dc445de7137b9857e194e` |
| [web #89](https://github.com/MeshCore-Beacon/beacon-web/pull/89) | `037858b4646349c4599d9067fb8f42ad9d1a34a3` | `be5434a3d4784e26434b5395693896dc7139fd4d` |
| [web #92](https://github.com/MeshCore-Beacon/beacon-web/pull/92) | `6b6884951a3dac01b592dfec83f0191879c5696c` | `037858b4646349c4599d9067fb8f42ad9d1a34a3` |
| [web #95](https://github.com/MeshCore-Beacon/beacon-web/pull/95) | `e1133ab5c3364349af900fd4f2093384fbf34f56` | `6b6884951a3dac01b592dfec83f0191879c5696c` |

## Recovery

The previous pair is server `2ed2e031` / web `6b688495`. The verified checkpoint and corresponding source/binaries remain, with a checksum-verified private copy off the Pi. Backend rollback restores the broader route index for the old query planner and the previous app/frontend metadata while preserving new rows and the compatible archive constraints. Frontend-only rollback restores `6b688495` while retaining backend `a35cba1d`. Exact guarded operations are kept with the deployment's local evidence; do not apply an earlier phase's rollback command directly to this candidate.
