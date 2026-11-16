# Beacon backend re-audit — 16 November 2026

## Source and runtime identity

Upstream server dev remains `87ea88337ad25ea70b7fac927dabe835596cf445`; main is
`265a835e36931a2c39b9b08e7a78837b9cf0e343`; dev1 is `202acc6cc8f6`.
The initially inspected preview backend is `6292a743aaeb`, which already carries
the prior focused audit fixes #297–#312. Those are not duplicated here.

Fresh public `/api/v1/info` checks: production and dev return 200/API 2.2.0;
dev1 returns 502. Production does not expose an exact source SHA and was not
inspected over SSH/SQL. No production state was changed.

The authenticated, bounded **read-only** dev-host snapshot now finds server image
`2819d60ca25e` and web image `653ef5ca122c` running without restarts. These differ
from both the earlier audit's runtime images and the latest Git dev heads.
The dev database has 83 migrations, approximately 14.71 GB, zero invalid/not-ready
indexes and zero recorded deadlocks. Two dirty analytics hours are the current
and preceding live tail. Dev1's app/web/database/Redis remain stopped; app/db
exit 137 is not by itself an OOM diagnosis.

The Pi preview snapshot has approximately 5.96 GB of core data, zero invalid or
not-ready indexes and zero recorded deadlocks. Sampled app memory is 48.08 MiB /
384 MiB; PostgreSQL 160.1 MiB / 512 MiB; Redis 4.719 MiB / 96 MiB. About 13.47 GB
disk remains free. These are point observations, not peak usage or capacity proof.
The two recent dirty hours do not demonstrate a stuck historical backfill.

Dev retains a different traffic window and admitted regions from preview, so
database size and raw counts are not direct speed comparisons. No load generator,
RF poll, synthetic MQTT report, enrollment or notification was sent.

## Confirmed new fixes

| Finding | Evidence | Focused proposal | Release placement |
| --- | --- | --- | --- |
| Optional telemetry integer retains a preceding value after a repeated null or int64-overflow field | `internal/polling/wire.go:145`; public ParseReadings/ParseClaim regression fails for nullable battery/counters/slots, passes with one-line reset; explicit zero retained | [server #313](https://github.com/MeshCore-Beacon/beacon-server/pull/313), `79e1cb6` | Bug in unreleased native telemetry: ride that next minor, not an isolated main backport |
| Malformed route/trace numeric filter silently becomes absent filter/first cursor page | `internal/api/handlers/routes.go:59`, `traces.go:56`; ten malformed/overflow cases reach the reader before fix, zero after 400 rejection | [server #314](https://github.com/MeshCore-Beacon/beacon-server/pull/314), `956cf28` | Existing-functionality patch candidate; valid and absent values unchanged |
| Finite float64 polling SNR can overflow the stored float32 type | `internal/polling/wire.go` finite helper, `db/polling.go:207`, `internal/api/telemetry.go:76`; e.g. 1e100 converts to Infinity and can poison JSON telemetry output | [server #322](https://github.com/MeshCore-Beacon/beacon-server/pull/322), `de6994d`; public parser red→green with positive/negative overflow and valid zero controls | Native telemetry's next minor; no schema or physical RF behavior change |

The new work does not change polling intervals, observer election, credential
audiences, schema, retention, or data-history policy. Native optional features
remain off on the preview. Parser fixture passes are not physical polling proof.

## End-to-end reinspection coverage

- **Ingress and identity:** broker/topic identity, duplicate observations, queued
  work, explicit field presence, neighbor scope presence, TRACE evidence and route
  promotion. Existing #301/#302/#303/#307 remain the relevant focused corrections.
- **Reads and caches:** list limits, cursor tie handling, malformed numeric input,
  regional filtering and cache coalescing. New #314 corrects the silent-widening
  input problem; existing #298/#304/#309/#312 retain their separate scope.
- **Storage and maintenance:** migration/branch identity, sequence types, index
  readiness, bounded read-model backfills, route reconfirmation, current rollup
  tails and backup boundaries. Current runtime health is consistent with the prior
  audit; cumulative temp-file counters alone do not identify a new slow query.
- **Native polling:** claims/readings, optional numeric decoding, rate limits,
  trust flags, policy, owners, requested-node credentials and evidence ranking.
  The raw-to-storage float32 boundary needs the new guard described above.
- **Accounts/alerts:** bounded request decoding, user scoping, disabled-route
  behavior, rule/request errors and existing integration tests. No new account,
  password or delivery action was performed in this audit.
- **Operations:** exact source vs deployed image distinction, public health,
  read-only dev inspection, stopped dev1, unchanged preview feature flags and
  preserved private credentials. No private environments or raw production logs
  are included in the public handoff.

The current source snapshot is the same dev baseline as the previous audit;
existing source/CI evidence remains useful, but current runtime facts were refreshed.
This is not a proof that no additional bug exists in every possible execution.

## Intentional contracts and documentation drift

`min_plugin_version` is intentionally sent as an empty string; native firmware
gating is exposed through `version_ok`. The API contract explicitly says so
(`beacon-docs/docs/api-contract.md:1625–1626`). It is not an omitted assignment bug.

The current `polling.request_observers` default is **all**, with an explicit
approved-only setting available. One source comment in `internal/config/polling.go`
still calls approved the default; the resolved code and configuration guide say
all. Correct that comment during documentation cleanup; do not silently change
the maintainer's chosen runtime default in an unrelated patch.

MQTT acknowledgement is not SQL persistence acceptance. Offline replay remains
an explicit design gate under #270; timestamp clamping must not be presented as
a replay contract. Short prefixes are still evidence requiring disambiguation,
not globally unique node identities.

## Practical backend enhancements toward parity

1. **Richer native sensor channels (minor feature):** `DecodeLPP` currently extracts
   only channel-1 voltage and temperature. Raw LPP is already retained in
   `repeater_readings.lpp` with a 160-byte bound, but the public `NodeReading`/
   `NodeTelemetryPoint` contract does not expose humidity, pressure or independent
   environmental channels. Add a bounded typed channel/unit series contract before
   UI tiles. Preserve raw evidence and never collapse channel 2 into channel 1.
2. **Honest coverage and freshness across analytics (minor):** reuse rollup/raw-tail
   provenance and distinguish missing/rebuilding/expired windows from measured
   zeros. Start with the existing API coverage metadata, rather than introducing
   another global raw COUNT or client-side route crawler.
3. **Observer overlap and path evidence views (minor):** reuse windowed observer
   activity, exact route cursors and validated paths. Label observed distances and
   deduplication units; longest plotted lines are not proof of a direct RF link.
4. **Operator query diagnostics (operational):** retain bounded, authenticated
   diagnostics and per-query plan policy. Collect representative cold/warm query
   latency and I/O on a controlled fixture before changing global PostgreSQL
   memory, parallelism or indexes. `pg_stat_statements` is not preloaded on the
   preview; enabling it is an operator/restart decision, not an audit side effect.
5. **One telemetry coordinator:** develop any future phone/companion transport
   against the native claim/lease/report contract. Do not resurrect the retired
   independent intake/scheduler merely to match a competitor's feature checkbox.
6. **Deployment observability:** source SHA and compatible API version must remain
   separate. Keep #310 in the release queue, exact artifacts/source offers and
   recoverable application-only changes. A healthy public endpoint does not prove
   the newest Git dev is deployed.

## Qualification and handoff

Focused package tests, build/vet and red-to-green evidence are recorded locally.
The exact final Actions builds and deployment are identified in the receipt below.
The earlier two-fix candidate `ec2c1f8` passed CI but was not deployed; its proof is
retained separately. Private runtime JSON should not be published wholesale;
the sanitized findings and delivery receipt provide the public evidence summary.

Private evidence: `backend-runtime-current.json`, `dev-runtime-current.json`,
`public-runtime-current.json`, `polling-presence-red.log`,
`polling-presence-green.log`, `strict-filters-red.log`, and
`strict-filters-green.log` under `evidence/parity-audit-20261116`.

## Qualified backend delivery receipt

The backend-only Canadaverse cutover completed at checkpoint
**`parity-server-20261116T081228Z`**. Deployed backend:
**`4f4f833f7e50d3776041ccd27234f7645632f2d3`**. The frontend at this backend
cutover was **`4ee1fc304411`** and its files and build fields were preserved;
the system audit's subsequent frontend receipt identifies any later web revision.

- [Final full CI](https://github.com/n30nex/beacon-server-contributions/actions/runs/43826594411)
  passed, including PostgreSQL integration/plan, backup/recovery, build/vet,
  Swagger and vulnerability checks.
- [Exact ARM64 artifact](https://github.com/n30nex/beacon-server-contributions/actions/runs/43826594379)
  passed. Revision/tree/source archive/binary hashes were verified; the executable
  reports Go 1.26.11, GOARCH arm64 and a clean VCS revision matching the candidate.
- Org PRs #313, #314 and #322 remain independent drafts with passing current-head
  checks, closing issues #324, #325 and #326 respectively. Release classes are
  minor, patch and minor because the polling module is not in current main.
- Fork [server #26](https://github.com/n30nex/beacon-server-contributions/pull/26)
  is incorporated by fast-forward into `n30nex-test`; no org dev/main merge occurred.
- Public `/info` and build metadata identify the new backend; the corresponding
  source archive hash matches. Both brokers connected, five invalid numeric
  filter checks return 400, five ordinary read checks return 200, and the retired
  independent intake route remains 404.
- The prior backend stopped with exit code 0. The 86-entry migration ledger,
  configuration/secret hashes, radio-service state and unrelated containers were
  preserved. No schema, retention, observer-enrollment, RF or account-policy change
  was made. Normal ingestion can continue changing data; this is not a claim of
  universal MQTT losslessness during process replacement.

The old backend container, binary and startup script are retained. Recovery from
the existing Pi preview root is:

```sh
sudo python3 evidence/parity-audit-20261116/backend/deploy-server.py rollback
```

This restores backend `6292a743aaeb`, keeps the current frontend fields/files,
and does not downgrade the database. It refuses an unrelated newer backend.
The system audit documents the ordering with any subsequent frontend rollback
guard. A live rollback rehearsal was not performed; exact recovery copies and
no-schema-change boundaries were verified. Private receipts are under
`evidence/parity-audit-20261116/backend/` and should not be published wholesale.
