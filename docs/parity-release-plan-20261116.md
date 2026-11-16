# Beacon parity release plan — 16 November 2026

## Release policy, not an invented calendar

Follow [Releases and versioning](releases.md). Server and web share a major/minor
line; their patch numbers may differ. `/api/v1` is a separate compatibility
contract. Maintainers cut the signed release commits and the release/tag flow.
The latest published server/web/mobile release observed by the audit is v2.2.0.
No accepted next-minor number or due-date schedule was found. This plan therefore
uses shipping classes and readiness gates, not invented milestone dates.

| Label | Meaning | Gate |
| --- | --- | --- |
| `release:patch` | Correct existing released behavior without adding a new feature dependency | Recut/test against released main when a patch backport is intended |
| `release:minor` | Additive feature or a fix that must ship with an unreleased feature | Review its complete contract and operator setup; bump server/web together for release |
| `release:major` | A deliberate incompatible API/data/auth transition | Explicit migration/rollback/compatibility decision |
| `release:backlog` | Investigative or unaccepted design | Prove behavior, cost and scope before promising delivery |

Bug severity and shipping class are separate. Native polling does not exist in
the checked server main tree, so its parser fixes #313/#322 belong with the next
minor feature even though their type is `bug`. Server #314 fixes an existing API
and can be considered for a focused patch backport. Flutter #26 fixes an existing
LiveConnection path and is patch-class. Flutter #22 mixes public HTTP work with
unreleased account code; its whole proposal belongs in the minor lane unless a
separate public-HTTP-only backport is prepared.

## Current small proposals

| Component | Proposal | Class | Acceptance boundary |
| --- | --- | --- | --- |
| Server | [#313 nullable integer presence](https://github.com/MeshCore-Beacon/beacon-server/pull/313) | Minor shipping lane, bug type | Explicit null/overflow clears old values; real zero remains |
| Server | [#314 strict numeric filters](https://github.com/MeshCore-Beacon/beacon-server/pull/314) | Patch | Invalid input is 400 before any read; omitted/valid input unchanged |
| Server | [#322 float32 storage boundary](https://github.com/MeshCore-Beacon/beacon-server/pull/322) | Minor shipping lane, bug type | A finite float64 must not become stored Infinity |
| Web | [#210 loaded Nodes CSV](https://github.com/MeshCore-Beacon/beacon-web/pull/210) | Minor feature | Current loaded/filtered rows only, formula-safe cells, no hidden full crawl |
| Web | [#219 contact-file JSON](https://github.com/MeshCore-Beacon/beacon-web/pull/219) | Minor feature | Eligible full-key contacts, no private data/routes or invented advert times; physical importer still a gate |
| Flutter | [#26 handshake cancellation](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/26) | Patch | Stop/timeout closes the underlying attempt; late generations cannot replace the current socket |

These are independent dev drafts, not a combined org implementation PR. Existing
audit/browser fixes keep their original review entries rather than being duplicated.
An export button or a debug APK does not establish physical-device acceptance.

## Backlog with concrete issue owners

| Issue | Next slice | Shipping class |
| --- | --- | --- |
| [beacon-web #211](https://github.com/MeshCore-Beacon/beacon-web/issues/211) | Bounded keyboard search across nodes, observers and packets | `release:minor` |
| [beacon-web #212](https://github.com/MeshCore-Beacon/beacon-web/issues/212) | Share public node identity and Beacon links as QR | `release:minor` |
| [beacon-web #213](https://github.com/MeshCore-Beacon/beacon-web/issues/213) | Design client-only channel key and collision-aware decryption workflow | `release:backlog` |
| [beacon-web #214](https://github.com/MeshCore-Beacon/beacon-web/issues/214) | Design explicit opt-in channel QR sharing | `release:backlog` |
| [beacon-server #315](https://github.com/MeshCore-Beacon/beacon-server/issues/315) | Add a bounded read-only raw packet decode contract | `release:minor` |
| [beacon-server #316](https://github.com/MeshCore-Beacon/beacon-server/issues/316) | Define cursor-bound historical map replay before adding VCR UI | `release:backlog` |
| [beacon-server #317](https://github.com/MeshCore-Beacon/beacon-server/issues/317) | Add evidence-qualified distance and longest-link analytics | `release:minor` |
| [beacon-server #318](https://github.com/MeshCore-Beacon/beacon-server/issues/318) | Add relay airtime-share and repeat analytics with explicit denominators | `release:minor` |
| [beacon-server #319](https://github.com/MeshCore-Beacon/beacon-server/issues/319) | Expose a read-only regional prefix ambiguity inventory | `release:minor` |
| [beacon-server #320](https://github.com/MeshCore-Beacon/beacon-server/issues/320) | Define configured, heard and forwarded scope evidence separately | `release:backlog` |
| [beacon-server #321](https://github.com/MeshCore-Beacon/beacon-server/issues/321) | Design consent-based observed RX coverage and native producer intake | `release:backlog` |
| [beacon-web #215](https://github.com/MeshCore-Beacon/beacon-web/issues/215) | Build an operator health view from existing bounded diagnostics | `release:minor` |
| [beacon-web #216](https://github.com/MeshCore-Beacon/beacon-web/issues/216) | Prototype optional bounded packet sonification | `release:backlog` |
| [beacon-web #217](https://github.com/MeshCore-Beacon/beacon-web/issues/217) | Export and import validated theme presets | `release:minor` |
| [beacon-web #220](https://github.com/MeshCore-Beacon/beacon-web/issues/220) | Investigate cancellation of obsolete shared paged reads | `release:backlog` |
| [beacon-server #323](https://github.com/MeshCore-Beacon/beacon-server/issues/323) | Expose bounded native telemetry channels and environmental measurements | `release:minor` |

Sequence the inexpensive, existing-data improvements first: exports, bounded
search, public identity links and operator freshness/coverage visibility. Then
agree the bounded backend contracts for distances, relay share, raw decode and
prefix ambiguity. Replay, BYOK/channel sharing, configured-vs-observed scopes,
mobile RX coverage and audio need their own threat/privacy/performance designs.

Retired Topology and independent collector code are research/reference material,
not dependencies that these issues silently restore. A new Topology proposal
must have a bounded evidence snapshot, separate layout/effect work, adaptive
detail, reduced motion and measured low-end acceptance. A companion telemetry
bridge shares the native coordinator rather than reintroducing a second scheduler.

## How to exceed feature parity

- Show freshness, coverage, partial/truncated windows, and evidence confidence
  beside outputs. Exported rows are not a network census; ambiguous prefixes are
  not measured RF collisions; longest plotted distances are not confirmed direct links.
- Retain typed per-channel telemetry and nullability before adding rich tiles.
  Provider-entered metadata, MQTT observations and native polled readings are
  distinct evidence classes.
- Make route evidence reproducible with exact cursor/representation/window links.
  Preserve a user-facing reason when a route cannot safely be drawn.
- Use one set of fixtures across API, web and mobile for malformed packets,
  missing numbers, clock skew, cursor boundaries, cache outage and reconnect gaps.
- Budget requests, retained memory, animation submissions and background work.
  Compare performance only on like-for-like hardware, retention and traffic.

## Promotion gates

1. One focused issue/PR per logical change, with type, priority and release class.
2. Exact-head tests/build/lint plus relevant PostgreSQL/native transport/browser
   checks. Retest overlapping changes after each accepted merge.
3. Exact Actions artifact/source identity, private backup/recovery boundary and
   preview-only deployment. Keep prepared candidate and running revision separate.
4. Operator acceptance for native accounts/polling/alerts: root-host/subpath
   contract, private email/portal settings, explicit observer credential audience,
   lease/report behavior and physical firmware/mobile tests.
5. Maintainer release decision and version bumps. This task does not merge dev
   into main, create stable release tags, or deploy dev/dev1/production.

The label reconciliation is additive and preserves existing owner labels and
milestones. It classifies current open issues/PRs across all twelve Beacon org/fork
repositories; closed historical discussions are not rewritten as a new roadmap.
Final reconciliation counts and late-created items are recorded in the parent
delivery receipt rather than treated as a fixed count throughout ongoing work.
