# Beacon system re-audit and CoreScope parity handoff

Audit date: 16 November 2026. This extends the prior end-to-end and browser audits
with fresh repository/runtime checks, a versioned CoreScope comparison, focused
fixes and additive feature proposals. It does not assert that every possible
defect is known or that parity is already 100%.

- [Source-backed CoreScope/Beacon capability matrix](corescope-parity-20261116.md)
- [Backend re-audit and measured runtime findings](backend-reaudit-20261116.md)
- [Mobile and release-policy audit](mobile-release-audit-20261116.md)
- [Release classes, proposal order and parity backlog](parity-release-plan-20261116.md)
- [Earlier full audit and handoff](https://canadaverse.org/beacon-dev/audit-handoff-20261116.md)
- [Completed browser qualification](https://canadaverse.org/beacon-dev/browser-qualification-20261116.md)

## Baselines and environment differences

| Target | Source/runtime observed at audit start | What this establishes |
| --- | --- | --- |
| Beacon server dev / main | `87ea88337ad2` / `265a835e3693` | Review baselines; not proof of deployed image |
| Beacon web dev / main | `7ed6a6264a1f` / `7c1680238b9c` | Native web baseline and release comparison |
| Beacon Flutter dev / main | `22cbceca816a` / `d077a561d33d` | Canonical app; old private archive is not the integration target |
| Preview server / web | `6292a743aaeb` / `4ee1fc304411` | Qualified running pair before this audit's new changes |
| Dev runtime | server `2819d60ca25e`, web `653ef5ca122c` | Fresh read-only image inspection; behind latest Git dev |
| Dev1 runtime | stopped stack; public 502 | Not restarted/deployed by this work; exit 137 alone is not proof of OOM |
| Production public API | 200, compatibility version 2.2.0 | No exact binary SHA exposed; production internals not SSH/SQL-audited |
| CoreScope upstream / fork | `d80ce90976d5` / `43d83918c689` | Separate feature/storage baselines; neither inferred from the stale local checkout |

The inventory covers the seven Beacon org repositories (server, web, docs,
canonical Flutter, Flutter archive, agent scaffold, scratch) and five related
fork/intake repositories. The agent scaffold is not a missing deployed service;
the independent collector remains retired. The new request authorizes reviewed
parity enhancements, not automatic restoration of old experimental stacks.

Native accounts, telemetry requests, polling and alerts exist on dev. They are
disabled on the Canadaverse subpath preview pending operator setup. Dev enables
some of these features. A disabled deployment option is not an absent feature,
and a successful build is not RF/mail/push delivery proof.

## Fresh backend findings

The preview database was about 5.96 GB with 415 indexes, none invalid/not ready,
and zero recorded deadlocks. Its completed rollups reached 05:00 UTC; the two
dirty hours were the 06:00/07:00 live tail. The dev database was about 14.71 GB
with 83 migrations and no invalid indexes or recorded deadlocks. Different
retention/admitted regions prevent direct database-size or packet-count speed
comparisons. These are bounded snapshots, not peak load measurements.

The prior high-volume IDs are bigint: preview packet observations were around
69.5 million, route sequence around 31.6 million. Remaining integer reference
sequences were far from their limit at this snapshot (channels around 1.38 million,
regions 30, transport scopes around 18 thousand). Continue monitoring rather than
claiming a universal sequence-lifetime guarantee.

New confirmed corrections are isolated in server #313/#314/#322. They address
optional integer presence, malformed numeric filters that otherwise widen reads,
and the finite64-to-float32 overflow boundary. Existing cache, streaming, backfill,
TRACE and activity fixes retain their previous focused PRs. No new migration,
retention change or credential audience expansion is part of these corrections.

## Frontend and parity increments

Core packet/map/node/observer/route investigation, Atlas, basic analytics and
native telemetry/account support are already present in Beacon. CoreScope adds
distinct workflows—not just more tabs—including VCR replay, raw decoding,
expression filters, contact/QR sharing, distance/relay share, prefix tools,
configured-vs-forwarded scope audits, RX coverage, customization and optional audio.
The matrix defines those gaps and their evidence/acceptance requirements.

Two immediate proposals avoid a backend expansion: loaded-row CSV (#210) and
eligible contact-file JSON (#219). Both are user-triggered, perform no extra reads,
and state their partial loaded-view scope. CSV neutralizes spreadsheet formulas;
contact JSON exports only whitelisted public fields, validates full keys/location/
role and leaves unknown advert times and learned routes unset. It is not a signed
MeshCore advert or a universal import guarantee.

The pagination-cancellation investigation (#220) is deliberately not called a bug:
TanStack allows unused reads to finish and populate cache when no AbortSignal is
consumed. A measured request/lifecycle contract must precede a global change.
Observer-directory and Atlas searches already pass signals; the shared Nodes/
Map/Routes paging path is the targeted investigation area.

## Mobile transport and release hygiene

Flutter #26 fixes an actual unanswered WebSocket-upgrade lifetime: timeout ended
only the wait, not the owned handshake. Each attempt gets an owned client; stop/
timeout closes it and obsolete successful upgrades are disposed. Eleven real
transport/ticket/User-Agent tests and analyzer checks passed, including the real
20-second unanswered-upgrade case. The wire contract, signing, RF behavior and
device installation are unchanged. APK qualification and physical device tests
remain distinct.

Flutter #28 adds the backend's TRACE uncertainty reasons to the directory,
packet detail and selected-observation views while preserving legacy-server
behavior and raw records. It does not implement default filtering. Flutter #30
uses the original TRACE wire bytes and correct raw-byte highlight offsets;
reconstructed values are not substituted for received evidence. Both depend on
the new server #307 quality/wire contract and belong to the minor release lane.

Release labels now describe shipping class independently of issue type/severity.
The release guide requires server/web major-minor alignment, not an invented next
version/date. Native polling fixes ship with that unreleased minor feature. The
entire mixed public-HTTP/account Flutter #22 likewise belongs with its minor
feature unless a released-main-only backport is split out.

## Validation limits and delivery receipt

Focused source tests, red-to-green regressions, builds, real transport fixtures,
loaded-export browser checks and read-only runtime checks are recorded in this
audit. The delivery receipt identifies final source heads, exact Actions
artifacts, current CI, public API/assets and recovery checkpoints separately from
prepared candidates. No synthetic RF, account enrollment, mail/push delivery or
production load test is claimed.

The rollout remains Canadaverse preview only. Dev/dev1/production and private
credentials/data are preserved. Physical Safari/iOS/Android, companion import,
background OS operation and operational native polling setup remain explicit
release gates. The baseline table above is intentionally historical; later
cutovers are listed below as they complete their qualification.

### Backend deployment receipt

Canadaverse now runs server `4f4f833f7e50d3776041ccd27234f7645632f2d3`,
qualified from the exact successful [CI run](https://github.com/n30nex/beacon-server-contributions/actions/runs/43826594411)
and [ARM64 artifact build](https://github.com/n30nex/beacon-server-contributions/actions/runs/43826594379).
Its public `/info` build revision and source archive match the candidate. Both
brokers are connected. Five malformed-filter requests returned 400 and five
ordinary public reads passed.

The backend-only cutover checkpoint is `parity-server-20261116T081228Z`. The prior
server stopped cleanly with exit code 0. Schema, frontend files/metadata, private
configuration, native feature flags, unrelated containers and radio-service state
were preserved. The retired intake remains absent. This receipt describes the
backend cutover with the previous web build still present; the final web/browser
and mobile receipts follow separately.

### Web and public browser qualification

The final public pair is web `b2af1b05c5555665e4657f879d5bcbb408bf3a70` and
server `4f4f833f7e50d3776041ccd27234f7645632f2d3`. Web
[CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/43830041518)
passed **2,243 tests across 211 files**, and the exact
[artifact build](https://github.com/n30nex/beacon-web-contributions/actions/runs/43830033677)
passed. All **85 public assets** and the offered source archive match that build.

The final public build passed all nine pages in English/French at 1440×900
desktop and 390×844 touch emulation: **36 page checks**, with no uncaught errors,
API failures or document overflow. Both CSV and contact downloads passed on
desktop and French mobile; neither triggered additional node reads. The CSV
notice explicitly identifies the loaded, filtered view. Browser contexts were
isolated; no physical Safari, Android/iOS or companion importer acceptance is
implied by these checks.

The frontend-only checkpoint is `browser-web-20261116T082320Z`. Backend,
containers, private configuration, credentials, retention and radio services
were unchanged during this web cutover. Both brokers and the existing feature
configuration remained healthy after publication.

### Mobile artifact and repository qualification

The maintained Flutter fork `dev` is
`458bcf80e1054dd2f348db1e81fe36630cec479c`. Its exact
[CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/43830774216)
passed **880 tests**, with **16 optional screenshot previews skipped**. The
[Android build](https://github.com/n30nex/beacon-flutter-app/actions/runs/43830768689)
passed; the downloaded commit marker and checksum match the final APK:
`59be0b030bc0c9e2be63aa96e85302b7acfe2f4e4ffcfe6d77ad44aea2bf621b`.

Fork PR #3 is incorporated, and that fork now defaults to `dev`; the historical
collector branch remains intact. Org Flutter #26/#28/#30 stay independent drafts
with passing final checks. The debug APK keeps package `meshcorebeacon.app` and
versionCode 2 but has a different certificate from the prior artifact. It is
**not a qualified in-place upgrade**; issue #33 tracks distribution policy.
No phone was installed, uninstalled or downgraded.

### Classification and recovery

At **08:28:59 UTC**, the reconciled open queue contains **97 issues/PRs across
12 repositories**: **45 patch**, **31 minor**, **21 backlog**, **0 major**.
Every open item has a type, priority and release class; existing milestones were
preserved. Later fork-integration closures can change the open count without
changing this dated audit snapshot.

Recovery commands run from the existing Pi preview root. For a frontend-only
rollback, use:

```sh
sudo python3 evidence/parity-audit-20261116/web-runtime/deploy-web.py rollback
```

This returns web to `4ee1fc304411` while retaining server `4f4f833f7e50`.
To restore both applications, run that frontend rollback **first**, then:

```sh
sudo python3 evidence/parity-audit-20261116/backend/deploy-server.py rollback
```

The second step returns server to `6292a743aaeb` without downgrading the database.
The web recovery guard expects the new backend, so reversing this order fails
the guard. No live rollback rehearsal was run. Recovery copies, exact artifacts
and the unchanged schema/configuration boundary were checked. Do not substitute
an older full-stack rollback or apply these guarded scripts after unrelated
deployment changes without checking their expected revisions.
