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

Release labels now describe shipping class independently of issue type/severity.
The release guide requires server/web major-minor alignment, not an invented next
version/date. Native polling fixes ship with that unreleased minor feature. The
entire mixed public-HTTP/account Flutter #22 likewise belongs with its minor
feature unless a released-main-only backport is split out.

## Validation limits and delivery receipt

Focused source tests, red-to-green regressions, builds, real transport fixtures,
loaded-export browser checks and read-only runtime checks are recorded in this
audit. The parent deployment receipt must identify final source heads, exact
Actions artifacts, current CI, public API/assets and recovery checkpoint before
calling any prepared candidate deployed. No synthetic RF, account enrollment,
mail/push delivery or production load test is claimed.

The rollout remains Canadaverse preview only. Dev/dev1/production and private
credentials/data are preserved. Physical Safari/iOS/Android, companion import,
background OS operation and operational native polling setup remain explicit
release gates. The final receipt is appended when the parent task's combined
qualification is complete; the baseline table above is intentionally historical.
