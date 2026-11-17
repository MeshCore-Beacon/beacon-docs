# Beacon cache, region and Atlas follow-up

17 November 2026. Canadaverse now runs the qualified upstream-dev composition plus the audited
fixes below. Final public browser, API, source/artifact and recovery-identity checks pass.
Ten focused code review units, including the refreshed footer PR and a test-only prerequisite,
remain separate draft PRs to org `dev`; the contract correction and this handoff are separate
documentation PRs. Maintainers retain org merges, release numbering and signed release
acceptance. No dev, dev1 or live host deployment occurred.

This follows the [third performance handoff](https://canadaverse.org/beacon-dev/performance-round3-20261116.md).
Current upstream dev introduces the configurable Atlas limit (1 to 100, default 20), six
optional telemetry requests per user and version 2.3.0. Those are inherited upstream changes,
not new polling policy chosen for Canadaverse. Native account/polling/alert options stay off
under the preview's existing configuration. Retired collector, Topology and scope experiments
are not restored.

The final source audit found no upstream drift: server dev `cf14a67c04d5`, web dev
`f5feaaf1f2ca`, app dev `aeb9cd0328e1` and docs dev `a98c62ea7ad2` are incorporated.
All ten code drafts are open, draft, mergeable, labelled, targeted to dev and green at their
recorded exact heads. A release-class label is not a release date or permission to deploy live.

## Review units

| Area | Draft | Change | Release class |
| --- | --- | --- | --- |
| Native reading cache keys | [Server #336](https://github.com/MeshCore-Beacon/beacon-server/pull/336) | Encode cache identity unambiguously for native latest readings. | Minor, unreleased native telemetry |
| Empty-region reads | [Server #337](https://github.com/MeshCore-Beacon/beacon-server/pull/337) | Keep explicitly empty regions empty across HTTP readers and cache warm orders, with real PostgreSQL coverage. | Patch; adapt native-reading portions for a main-only backport |
| Atlas storage tests | [Server #339](https://github.com/MeshCore-Beacon/beacon-server/pull/339) | Update the storage regression for the upstream configurable card cap. Test-only prerequisite, no production policy change. | Minor, new configurable Atlas contract |
| Atlas HTTP body budget | [Server #341](https://github.com/MeshCore-Beacon/beacon-server/pull/341) | Raise only the Atlas sync body budget to 256 KiB, with 100-card acceptance, 101-card rejection and oversized-body rejection tests. | Minor, new configurable Atlas contract |
| Node detail states | [Web #231](https://github.com/MeshCore-Beacon/beacon-web/pull/231) | Distinguish loading, missing records and retryable request failures. | Patch |
| Translated Atlas footer | [Web #204](https://github.com/MeshCore-Beacon/beacon-web/pull/204), refreshed | Refresh the existing clipping fix against upstream's new footer; its final files match the already qualified preview. | Patch |
| Browser Atlas persistence | [Web #233](https://github.com/MeshCore-Beacon/beacon-web/pull/233) | Preserve large valid Atlas collections through reload, append and export/import. | Minor, new configurable Atlas contract |
| Browser Atlas import readiness | [Web #236](https://github.com/MeshCore-Beacon/beacon-web/pull/236) | Hold import until initial server metadata settles, avoiding premature use of the old twelve-card fallback. | Minor, new configurable Atlas contract |
| Native cache generations | [App #46](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/46) | Retire obsolete readers without letting stale responses alter newer cache ownership, and keep valid shared reads during LRU eviction. | Patch |
| Native Atlas persistence | [App #48](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/48) | Use the existing bounded Atlas file parser budget for saved data, preserving 100 fully configured cards. | Minor, new configurable Atlas contract |
| Atlas contract wording | [Docs #69](https://github.com/MeshCore-Beacon/beacon-docs/pull/69) | Replace stale twelve-pin statements, preserve the old-server fallback of 12, and document the Atlas-only body budget. Depends on server #341. | Minor, new configurable Atlas contract |

Server #339 is a test-only prerequisite already included in #336, #337 and #341 so their full
required checks can run on current dev. Merge #339 first, then refresh the dependent PRs against
accepted dev so their review diffs contain only their focused changes. Docs #69 must not land its new HTTP
body-limit statement ahead of server #341.

## Evidence and limits

### Region and cache correctness

An explicitly empty region is not an unfiltered request. PostgreSQL regressions exercise
nodes/default/sorted/latest, observers, packets/default/hash/backfill, messages/backfill, traces
and node types. Blank, NULL and legacy three-character `---` values cannot match the separate
four-character empty marker. Explicit YKF unions and normal response envelopes, sort order,
generated timestamps and packet-read-model readiness behavior are retained. Tests warm global
and empty-region caches in both orders. Disposable fixtures do not insert fake rows or regions
into preview or org databases.

Native latest-reading cache keys previously joined filters as comma-separated text, allowing
global and explicit empty-code requests to alias in either cache warm order, and comma-bearing
values to alias multi-IATA filters. Sorted JSON arrays preserve element boundaries and keep
nil/empty global requests equivalent. A new cache namespace separates old entries, which expire
under their existing TTL; no Redis flush is needed. This is independently reviewable from the
empty-region marker correction.

The mobile client cache correction covers filtered lists, first-load requests, live patches, stale
no-store responses, LRU eviction, accounting and disposal. Original callers can finish with
their own snapshot, while a new reader cannot join an obsolete request. Ordinary body eviction
does not retire a still-valid shared request or lose its no-store ownership. No cache size,
refresh interval or RF polling policy is increased.

### Atlas capacity end to end

The old client parser rejected saved JSON over 32,000 characters even when every card was valid.
With upstream's 100-card maximum, reload and import could return an empty collection; adding a
card could also empty it. Both clients now reuse their existing bounded file parser budget.
Tests cover full optional card settings, 160-character names, worst-case JSON escaping, card
order, view and tile selections, append, import/export, server caps and oversized rejection.

The native parser retains its established character-count contract; the device picker retains
its separate UTF-8 byte limit. Neither is an unlimited reader. The server's independent HTTP
budget is now 256 KiB for Atlas only. Its authenticated-handler regression first returned 413
on unchanged dev, then accepted 100 fully configured pins with 160 supplementary Unicode
characters per name encoded as surrogate pairs. A 101st pin still returns 422; an oversized
body still returns 413 and rejected input is not saved. Authentication, CSRF, read-only gates,
rate limits and pin/name/tile validation remain unchanged. These checks use isolated fixtures,
not production accounts or RF collection.

The passing client maximum-name fixtures cover ASCII and JSON-escaped controls. A separate Unicode
length mismatch remains tracked in [web #234](https://github.com/MeshCore-Beacon/beacon-web/issues/234)
and [app #49](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/49): 160 supplementary
Unicode characters are truncated to 80 by a client UTF-16 name-length check. These parser-budget
fixes do not claim to correct that separate name-validation issue.

Public acceptance exposed a second, independent web import problem: the Import action was
available before the initial `/info` response, so a valid 20-card file could be saved as 12
cards and stay truncated when the actual limit of 20 arrived. [Issue #235](https://github.com/MeshCore-Beacon/beacon-web/issues/235)
and #236 retain that red reproduction. The fix reuses the existing shared initial-readiness
hook to disable the button/input and reject forced file events until metadata settles. An
initially offline query remains pending; old-server and settled-error fallback of 12 remains
explicit, including the skipped-entry notice. Three pending/offline regressions first failed;
two compatibility cases already passed. Independent review repeats all 64 focused tests.

The connected native app already awaits its shared `api.features()` future before parsing
an import. Two additional widget fixtures held that future, confirmed no save while pending,
then verified configured caps of 2 and 20. Its qualified source/artifact remains unchanged.
No-API or settled-failure fallback remains a compatibility boundary, not a newly fixed behavior.

### Current source qualification

| Target | Source | Status |
| --- | --- | --- |
| Preview server | `b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590` | Deployed and verified; full Go/PostgreSQL/plan/security/recovery CI, race checks, exact ARM64 artifact/source and real WebSocket profiles pass |
| Preview web | `231fec5397faf7e399f982c52033d74593e31b46` | 2,298 tests / 218 files; all 82 public assets and source archive verified; final public browser acceptance passes |
| App fork dev | `7609d7985cd8602053cb13c445ce45e63eb32bed` | 917 tests; 16 optional screenshots skipped; exact APK, checksum and signature verified; fork fast-forwarded |

The native composition includes dev `aeb9cd0328e16100dc0ce4d36f0852ee726501b2`, both focused
fixes and the previous audited fork. Independent cache review ran 72 tests; independent Atlas
review ran 66 parser/store tests. Final focused cache/Atlas tests pass 192 cases. Strict UTF-8
and JSON checks preserve current upstream labels plus prior audited TRACE warnings. Previously
qualified live/map/chart lifetime files remain unchanged.

The exact app build passes [full CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/44062383836),
[artifact build](https://github.com/n30nex/beacon-flutter-app/actions/runs/44062383378) and both
automatic dev-branch reruns. Its APK is `meshcorebeacon.app` version 2.3.0, versionCode 2,
SHA-256 `7fbb153ebd744dfe169f755c2b64fba5b3c6ea549c64b3ae8967fed5d979dd03`.
The debug certificate differs from the previous artifact; it is not an in-place upgrade
promise. No phone/tablet install, physical OS lifecycle, battery, CPU or RF acceptance is claimed.

The backend incorporates dev `cf14a67c04d5a6630d72a339561adea670ed95a5` and the prior audited
preview. Its [full CI](https://github.com/n30nex/beacon-server-contributions/actions/runs/44064916951)
and [ARM64 artifact build](https://github.com/n30nex/beacon-server-contributions/actions/runs/44064916778)
pass at the exact deployed source. The ARM64 binary SHA-256 is
`410ff80d229e983996b0cc55521493d8a82ee9f5f6b0ceb7f275c38d3648bc5e`.
The source archive, binary VCS metadata and manifest agree. Both MQTT brokers remain connected;
four native-ticket WebSocket profiles exercise plain, resolved, key-only and combined demand.
Only counts and protocol assertions are retained, not packet contents; no RF is transmitted.

The empty-region fixture initially failed its own setup by checking unrelated provider text
columns. That setup failure is excluded from behavior evidence. The repaired fixture fails
against unchanged current dev across all ten reader paths, then passes with the fix. Separate
Atlas storage tests still expected the old cap of 12; #339 corrects that test contract without
changing production behavior. Final checks use clean remote clones, excluding earlier local
worktrees with missing historical alternate objects. No old source or recovery data was deleted.

Web #204 was refreshed in place to `25d9eff14c653ea6cb063ac7f13bb11ba60bac7d`; it retains its
two-file scope and matches the qualified preview's footer files byte for byte. Its
[Linux CI](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44066817577) passes 2,192
tests in 208 files plus build/lint. The refreshed PR does not create a second preview artifact.
Web #233's Windows full suite recorded 2,187 passes and eight shell-dependent failures because
`sh` was unavailable (`ENOENT`). They are not reported as passing tests. Its exact-head
[Linux CI](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44064088464) passes all
2,195 tests. The first composed web head `eb6c86fcc58796ad4ad5404bf1e5e4e3729229da` passed
2,293 tests, then public testing found the separate import-readiness race above. The final head
adds only #236's two-file patch. Its [full CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/44070394612)
passes 2,298 tests in 218 files; #236's [org CI](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44069939603)
passes 2,197 tests in 208 files. Earlier browser-harness
fold selectors and Windows artifact-path attempts are retained as excluded harness failures,
not described as product regressions.

The final [web Actions artifact](https://github.com/n30nex/beacon-web-contributions/actions/runs/44070386179)
matches all 82 manifest entries, and the source archive matches `git archive` byte for byte.
Distribution SHA-256: `766c1625b991773c66a891e4bb176d99922d82c46f1975247a84cb5733cb4c9b`.
Source SHA-256: `86eba3afa0634ca0da79449283d431bc8d439b7dd64de66faa61bb67e2a0595a`.

## Final public browser acceptance

Chromium 143 qualification used isolated contexts on the actual deployed preview. All were
closed after testing. It covers all nine pages in English and French at desktop 1440 x 900
and touch emulation 390 x 844: **36 page checks**. No final application API, JavaScript or
WebSocket errors, unexpected console errors or horizontal page overflow were found.
This is desktop/browser emulation, not physical Android/iOS or Safari acceptance.

The focused checks also pass:

- **24 node-state cases** across English/French and desktop/mobile: a 500 is retryable, its
  retry restores real data, a 404 remains missing, pending sections say loading, failed
  sections say failed, and successful empty retries show empty states.
- **Two live-map contexts, eight checks each**: language changes preserve the canvas,
  actual live events animate, global region and style changes work, Stop/navigation end
  animated-source submissions, return has no stale flow, and reduced motion does not auto-start.
- **Two 100-card contexts** preserve 47,227-character saved collections and 63,302-byte exports
  through reload/import on desktop and mobile, without overflow or page errors. Synthetic
  node reads stay intercepted in the isolated browser; no fake nodes or RF are sent upstream.
- **The startup import regression** holds metadata, confirms disabled controls and no forced
  event save, then imports all 20 cards after the configured cap is supplied.
- **Two loaded-data export contexts**, desktop English and mobile French, retain the filtered rows in CSV/contact exports,
  without extra node requests, overflow or page errors. These are loaded-view exports, not
  a claim to fetch/export the complete catalogue.

The live-map samples retain the existing per-source 30 Hz submission bound and record zero
animated-source updates after Stop or navigation:

| Context | Sample seconds | Live events | Located packets | Updates per animated source |
| --- | ---: | ---: | ---: | ---: |
| Desktop | 10.013 | 163 | 52 | 270 |
| Touch emulation | 10.016 | 128 | 27 | 269 |

These are short windows with different real traffic, not before/after CPU, GPU, battery or
production-capacity benchmarks. Base event processing is not claimed to stop with the animation.

The first parallel browser run hit the existing WebSocket handshake rate limit. It is excluded
from final acceptance; storage/fault fixtures now mock their WebSockets and the final public
suite runs serially, while the page matrix and live maps retain real connections. Eight
Cloudflare edge-analytics requests remain blocked by the existing CSP. That expected third-party
notice is recorded separately; the security policy was not weakened to hide it. The first
public import failure was a genuine product bug and was fixed by #236, not reclassified as a
test-harness error.

## Deployment acceptance and recovery

The backend cutover is qualified at checkpoint `round4-server-20261117T104808Z`. Public API,
source archive, revision and feature-state checks pass, including five malformed-filter checks
and six ordinary reads. Schema, configuration/secrets, history,
unrelated containers and radio services are preserved. No database/cache flush or retention
change was performed. Normal ingestion continues; a healthy cutover does not prove universal
packet losslessness.

The final web cutover is verified at `performance-round4-import-web-20261117T110722Z`;
all 82 public assets and the source archive match. Public browser acceptance passes on that
exact final source. Server, web and app forks were fast-forwarded only after their gates passed;
fork server #30, web #39 and app #7 are merged. Org code PRs remain drafts.
Do not run an earlier round's recovery recipe against a later composed deployment without
checking its recorded source and checkpoint lineage.

From the existing Pi preview root, restore frontend layers first, in order, then the backend
only if it also needs to return to the previous qualified pair:

```sh
sudo python3 evidence/performance-round4-20261117/web-import-runtime/deploy-web.py rollback
sudo python3 evidence/performance-round4-20261117/web-runtime/deploy-web.py rollback
sudo python3 evidence/performance-round4-20261117/backend/deploy-server.py rollback
```

The first web checkpoint returns `231fec5397fa` to the initial round4 web `eb6c86fcc587`.
The initial web checkpoint `performance-round4-web-20261117T104910Z` returns that to
`bf872c6e1c7c`. The backend checkpoint above then returns `b54d1bf3afda` to `821a76dc90d0`.
The scripts guard exact identities and retain accumulated server history and schema. No
database downgrade, live-preview rollback rehearsal or device downgrade was performed.

## Maintainer roadmap

1. Review the small fixes independently. Refresh overlapping cache, hub, reader and Atlas
   changes after each accepted dev merge rather than merging an aggregate implementation PR.
2. Keep the Atlas client parser corrections, HTTP budget and contract documentation together
   for the configurable-cap feature's minor release. A passing parser test alone does not prove
   that the largest valid collection can pass every sync boundary.
3. Retain the existing optional telemetry enrollment and operator-policy gates. Upstream's
   six-request default is not permission to turn collection on in preview or transmit RF tests.
4. Resolve the [app identity/signing policy](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33)
   before promising preview upgrades or store distribution. Maintainers own signing secrets.
5. Continue measured performance work from the audit backlog: request lifetimes, duplicate
   reads, bounded caches and live-display costs. No new global capacity or battery claim is
   established by these targeted corrections. Existing preview-only parity additions remain
   explicitly staged; this report does not claim complete CoreScope parity.

All open items across 12 repositories have release/type/priority classification, verified again
after this round's final drafts and fork publication. Labels describe candidate release classes,
not assigned versions or dates; existing milestones are retained. The exact final inventory count
belongs to the dated evidence receipt rather than a permanently fixed roadmap total.
