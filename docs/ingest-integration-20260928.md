# Ingest integration validation — 28 September 2026

The Pi preview runs server `2ed2e03117f6c88795d446456e6d74c20c485d28` (tree `435400335edda9b9c0d1dc5210f5043403390c19`) and web `6b6884951a3dac01b592dfec83f0191879c5696c`. Accepted bases are server `db30c9b573357990c41166292e7cf42785c92cc4` and web `17f48fb932facbdcc45068afd2db6036ac2ec94d`. All fifteen application candidates remain included and out of draft. Published-head checks and both full-stack Check commands pass; web CodeQL remains skipped. Maintainers retain application merges, stable releases and production cutover.

## Source integration

Accepted server #177–#180 and web #91 are integrated through one coordinated helper refresh. The only source conflict was independent server #166: payload side effects must precede live endpoint resolution for inserted observations, while upstream's optional new-path repeat events must retain current identity without reapplying old adverts. Existing first/renamed-advert regressions failed on the upstream ordering and pass with the fix. A new repeat regression verifies fresh identity, no repeated side effects and no endpoint lookups for suppressed duplicates.

| Repository / PR | Published head | Exact parent |
|---|---|---|
| [server #166](https://github.com/MeshCore-Beacon/beacon-server/pull/166) | `e1c4fa2f70ae6b5efc0054b91433460d07f06ce1` | `db30c9b573357990c41166292e7cf42785c92cc4` |
| [server #167](https://github.com/MeshCore-Beacon/beacon-server/pull/167) | `70c5c389f9886cb8d8c9d9d34462c805cad6fc6b` | `db30c9b573357990c41166292e7cf42785c92cc4` |
| [server #169](https://github.com/MeshCore-Beacon/beacon-server/pull/169) | `39c9d185087dcf6bc5aede8f8d1e86c61c1365c9` | `70c5c389f9886cb8d8c9d9d34462c805cad6fc6b` |
| [server #172](https://github.com/MeshCore-Beacon/beacon-server/pull/172) | `0fc1398eecaa24f1dbdd0fae28bc259f15a439f2` | `39c9d185087dcf6bc5aede8f8d1e86c61c1365c9` |
| [server #174](https://github.com/MeshCore-Beacon/beacon-server/pull/174) | `235e2e0fd672febf8e236d5b5859ef3d660028df` | `0fc1398eecaa24f1dbdd0fae28bc259f15a439f2` |
| [server #176](https://github.com/MeshCore-Beacon/beacon-server/pull/176) | `cf8cee332a6494a2ab603eab306883fc6ba17f8d` | `235e2e0fd672febf8e236d5b5859ef3d660028df` |
| [web #75](https://github.com/MeshCore-Beacon/beacon-web/pull/75) | `e65e8e42ec7bcd75029ebc636645eedc2b889cbf` | `17f48fb932facbdcc45068afd2db6036ac2ec94d` |
| [web #79](https://github.com/MeshCore-Beacon/beacon-web/pull/79) | `4f3819b805ff8293939d1e6fb3918f05cafaadd5` | `e65e8e42ec7bcd75029ebc636645eedc2b889cbf` |
| [web #80](https://github.com/MeshCore-Beacon/beacon-web/pull/80) | `04ca3da919d9b0430f364a1a93bf36cf56e9770a` | `4f3819b805ff8293939d1e6fb3918f05cafaadd5` |
| [web #81](https://github.com/MeshCore-Beacon/beacon-web/pull/81) | `2f76286ec89c81db0345937b8c1712f363bd2e43` | `04ca3da919d9b0430f364a1a93bf36cf56e9770a` |
| [web #83](https://github.com/MeshCore-Beacon/beacon-web/pull/83) | `0787e5b5fdb1d8d47aefcbb20e816ba280a2ebe2` | `2f76286ec89c81db0345937b8c1712f363bd2e43` |
| [web #85](https://github.com/MeshCore-Beacon/beacon-web/pull/85) | `b21b8704c7403d7f963dc445de7137b9857e194e` | `0787e5b5fdb1d8d47aefcbb20e816ba280a2ebe2` |
| [web #87](https://github.com/MeshCore-Beacon/beacon-web/pull/87) | `be5434a3d4784e26434b5395693896dc7139fd4d` | `b21b8704c7403d7f963dc445de7137b9857e194e` |
| [web #89](https://github.com/MeshCore-Beacon/beacon-web/pull/89) | `037858b4646349c4599d9067fb8f42ad9d1a34a3` | `be5434a3d4784e26434b5395693896dc7139fd4d` |
| [web #92](https://github.com/MeshCore-Beacon/beacon-web/pull/92) | `6b6884951a3dac01b592dfec83f0191879c5696c` | `037858b4646349c4599d9067fb8f42ad9d1a34a3` |

## Validation and limits

- Local formatting/build/vet/tests and exact-head GitHub CI pass for all server candidates; local web build/lint/tests and exact-head build checks pass for all nine web candidates.
- The composed native Pi server build, full PostgreSQL suite and new queue/order/memory/drain/cancellation/clock-skew/route-lock tests pass. Linux CI supplies race checks; Pi ThreadSanitizer cannot run with this host's VMA layout.
- A native fixture used real PostgreSQL storage, the actual callback/ingest queue, 504 scope candidates, encryption/decryption, and normal plus opt-in live consumers. A later route-maintenance batch was deliberately blocked while an earlier completed batch continued ingesting. Its 3,200 inputs produced exactly 100 packets, 800 stored observations, 100 decrypted messages, 800 normal events, 2,400 opt-in events and 3,200 acknowledgements, with zero drops/invalid inputs in 12.217 seconds. The fixture used an isolated test schema and published no RF or broker traffic. It does not prove universal production losslessness or explain the historical 1,810-counter discrepancy.
- Native web build/lint and all 935 tests pass. All 18 rebuilt asset files are byte-identical to the previously geometry-tested build; exact corresponding source is newly offered. Public scoped packets, decoded Public history and message-to-packet inspection pass. English desktop and French 390px phone smoke checks pass without horizontal overflow or browser console errors. Existing untranslated controls remain under web #12.
- Both real MQTT feeds advanced across a 62.76-second observation window, with zero restarts and no queue-overflow/database errors or disconnects. Input warnings remain: 24 malformed-region messages, 51 timestamp clamps and 38 timestamp parsing fallbacks in that window. The numeric-offset timestamp parser gap is tracked as [server #181](https://github.com/MeshCore-Beacon/beacon-server/issues/181); do not call these logs clean.

## Deployment and recovery

Only the Beacon app restarted; the other 22 containers were unchanged. Frontend publication changed no container identity. Configuration digest remains `c09c3aea14eef795baf84d0462dd53c59de5f6e432a6023f93592f5adf6cc277`, runtime mode 0644, schema042, 72h packets / 30d summaries / 720h telemetry, standard Public key, 504 candidates and the YOW importer. Public admin/backup/foreign detection remain disabled. The country-wide candidate list is still a snapshot, not an automatic discovery service.

A fresh 58,002,666-byte database dump restored successfully and has a private checksum-verified off-Pi copy. SHA-256: `b6149d551db14a7bc1e847fd9c1bf19aab77e065e6d25680703082155f89612b`. Its disposable verification database was removed after the successful restore; the dump and original databases remain. Immediate same-schema rollback preserves new rows and restores server `7c9599b1` / web `dfeb2777`, using backup `ingest-cutover-20260928T222830Z` and Pi `evidence/ingest-integration-20260928/deploy-server.py rollback`. Frontend-only recovery uses backup `web-20260928T224458Z` and the deployment helper in that evidence directory, paired with server `2ed2e031`. Older schema041 recovery remains separately paired; do not apply older rollback commands directly to this build.

The [public source/changelog](https://canadaverse.org/beacon-dev/source.html) identifies the exact served revisions. Server binary SHA-256: `c3150945e53b49d7549a1936720f971e4c8c4ee9c2e26739184fd37f5748ee6e`; server source: `efe28b8cab9d87be7e2bd13e697bab060325e2840d75f22f60199bb61fa94824`; web corresponding source: `ccfa5750b606ca6c9506af1eb8fc838656efebd8f9e672333ec29e33a8f64f8f`.

## Next work

Review feedback and [server #181](https://github.com/MeshCore-Beacon/beacon-server/issues/181) take priority. Add parser regression coverage and accept supported RFC3339 numeric-offset timestamps without weakening invalid/future/stale guards. Broad server #60/#72/#99/#116 and web #12 remain open. Optional MeshMapper boundaries follow issue work.

Both application repositories still have merge commits disabled and the contributor has READ access. A maintainer must enable that option; no repository setting was changed. Merge commits preserve parent ancestry, but source conflicts and validation remain. Keep this queue in dependency order, use the existing helper for current composition/history repair, and start independent work from fresh dev after the queue is accepted.
