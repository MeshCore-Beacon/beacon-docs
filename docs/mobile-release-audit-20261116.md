# Beacon mobile and release audit — 16 November 2026

## Source and delivery boundaries

Canonical mobile upstream is `MeshCore-Beacon/beacon-flutter-app`, dev
`22cbceca816a9217dcb81e667aa24bff340030a8`, main
`d077a561d33dd2b4437aab09689c56b3646be32c`. The qualified preview fork started at
`54c13652bcbc3e87fb82251d01dc69da6182fbb4`. The separate private
`beacon-flutter-app-archive` is not GitHub-archived, but it is not the canonical app;
its four dependency PRs remain a legacy/backlog lane.

This review inspected the app's instance normalization, public and account HTTP
clients, live transport/lifecycle, paging, map loading/animation/telemetry,
directories, Atlas storage/sync, account/telemetry-request/alert flows, package
configuration and Android/release build paths. It also inventoried open issues,
PRs, labels, milestones, branches and release metadata across seven org repos and
five related forks/intake repositories. No device was installed, no RF command
was sent, and no signing credential was created or changed.

## Confirmed fixes

[Issue #25](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/25) and
[draft dev PR #26](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/26)
address abandoned WebSocket handshakes. `lib/core/live.dart` used a 20-second
`Future.timeout` around `WebSocket.connect`, but a timeout stops awaiting the
future rather than cancelling its underlying work. `stop()` only closed a socket
that had already upgraded. A pending upgrade could therefore survive stop,
background/server changes or timeout.

Each attempt now owns its HTTP handshake client. Stop/dispose or timeout closes
that client; a late upgrade belonging to an obsolete generation is also closed.
An upgraded WebSocket is detached from its HTTP client and remains usable. The
20-second deadline, ticket header, Dart User-Agent and reconnect/backoff contracts
are unchanged. The source path exists on released main, so this is patch-class work.

The real-loopback stop regression failed on unmodified dev, and then passed after
the fix. Eleven transport/ticket/User-Agent tests pass, including a real unanswered
20-second upgrade timeout. Analyzer and formatter pass. Existing loopback tests
explicitly opt into real HTTP because the widget test binding otherwise supplies
a fake 400 response; this is test setup, not a production-network override.

The final org/fork heads, full CI and Android artifact receipt are recorded in
`flutter-qualified.json`. Initial CI caught a
test-only `final` versus `const` lint; it was corrected without changing runtime
logic. No failed or superseded run is presented as a green final candidate.

Primary API references checked:

- [HttpClient.close](https://api.dart.dev/stable/latest/dart-io/HttpClient/close.html): force closes active HTTP work.
- [WebSocket.connect](https://api.dart.dev/stable/latest/dart-io/WebSocket/connect.html): accepts a caller-owned HTTP client.
- The installed Dart SDK's `_http/websocket_impl.dart` detaches the successful
  upgraded socket before completing the connection future. Existing transport
  regressions prove that the new cleanup does not close that usable socket.

### Trace quality warnings and original wire evidence

[Issue #27](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/27) / [draft PR #28](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/28)
add the optional server-provided suspect/ambiguous assessment to the native trace
directory, per-packet trace detail and selected-observation analyzer. The warning
retains raw evidence and explicitly avoids asserting that a real route or an RF
collision is established. Older-server responses without metadata and supported
assessments gain no authenticity badge. Five widget tests cover all three views,
legacy behavior and selected-observation precedence. English, French and Swedish
keys have passing key/placeholder coverage (13 warning/localization tests).
Full CI caught missing Swedish keys on the initial candidate; those were fixed
rather than weakening the locale contract. Default filtering remains a separate
pagination/count requirement in issue #27, not an implemented feature.

[Issue #29](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/29) / [draft PR #30](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/30)
correct raw/copyable frames and byte highlighting to prefer original `wirePathBytes`
over display `pathBytes`. TRACE display hashes can differ from original SNR bytes;
using display hashes corrupts the shown raw frame and payload offsets. Two tests
fail against dev before the fix; 16 wire-path/payload-view tests then pass, including
explicit empty original paths and older-server fallback. Analyzer is clean.

The whole optional quality/wire contract in server #307, web #199 and mobile
#28/#30 is in the **minor** lane. An inference-only backport of the released
server bug could be split into a separate patch; the entire paired contract is
not being silently designated a patch backport. No schema or RF behavior changes
are required by the client fixes.

## Existing fixes retained, not duplicated

- [#22](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/22): HTTP exchange
  cancellation and response-body limits. The canonical dev still has timeout-only
  paths; the fork includes this draft. It spans the existing public client and
  **new account/auth files absent from main**, so the whole PR belongs to the next
  minor feature lane. A public-HTTP-only patch backport is a separate maintainer
  decision, not a reason to ship the entire new account stack in a patch.
- [#23](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/23): skip an
  obsolete screen's read before starting it. The affected public API path exists
  on main and is patch-class.
- [#24](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/24): use receipt
  IDs for channel ordering rather than an untrusted sender clock. This is also
  patch-class and remains in the fork.
- [#15](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/15) already
  addresses portrait/large-text region selection. Preserve the contribution and
  finish its maintainer CI/device gate rather than duplicate it.
- [#20](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/20) is the existing
  `fl_chart` patch update; it is separate from this transport correction.

## Mobile capability and performance findings

1. **The app already has native parity foundations.** Nine main views, live events,
   server/region switching, paged directories, packet/path investigation, channel
   reading, routes/traces, Atlas imports/exports and native account/telemetry/alert
   clients are present. Map live flow is bounded to 120 concurrent entries and
   updates at 50 ms intervals, clearing work on background/navigation. Map pages
   share a budget, detect repeated/broken cursors and expose an incomplete-map
   error rather than silently truncating the catalogue.
2. **Expensive live-path resolution is currently connection-wide.** [Follow-up #32](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/32).
   `lib/core/live.dart` requests `resolvePath: true` on every connection, regardless
   of the active screen. A future focused performance change could request this
   only for consumers that need it. First inventory packet-row/path consumers and
   measure backend query/CPU cost; do not reduce detail on a screen that needs it
   merely to achieve an attractive number.
3. **Animation uses wall-clock time.** [Follow-up #31](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/31). `map_screen.dart` timestamps flow starts and
   ticks with `DateTime.now()`, unlike the web's elapsed-time animation. A backwards
   clock correction could prolong an animation and its timer. A monotonic elapsed
   clock is a sensible follow-up with controlled clock/lifecycle tests. This is a
   source-derived hazard, not a freshly reproduced physical-device incident.
4. **Native telemetry is the primary integration lane.** The cleaned app does not
   contain the old companion BLE/Wi-Fi collection client. Reintroducing it requires
   the same native coordinator/lease/credential/report-acceptance contract, not a
   second scheduler. [Issue #10](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/10)
   retains that deferred design. API flags/configuration are separate from the
   app's version number and from proof of live RF acceptance.
5. **Debug APKs are not an upgrade contract.** [Policy issue #33](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33). `android.yml` builds a debug APK
   using the pubspec build number (`2.2.0+2` at this snapshot), without a provisioned
   persistent signing key in that workflow. `Build.sh` instead makes signed APK,
   AAB and IPA releases using one epoch build number. The Gradle package ID is the
   same `meshcorebeacon.app`. Therefore CI success does not establish update
   compatibility with a differently signed or higher-version installed build.
   Agree a preview identity/signing/version-code policy before distributing an
   upgrade path; do not fix this by uninstalling users' data or enabling downgrade
   flags silently.
6. **Gaps worth addressing after contracts are settled:** shared public-node QR
   identity/contact export, consistent web/mobile export formats, evidence-qualified
   link/airtime/coverage analytics, and bounded historical replay. Push delivery,
   account enrollment and background behavior need physical/operational checks;
   source presence and widget tests do not establish those outcomes.

## Release policy and schedule findings

The authoritative [release guide](https://github.com/MeshCore-Beacon/beacon-docs/blob/dev/docs/releases.md)
requires server and web to share `major.minor` while permitting independent patch
numbers. `/api/v1` is the API contract namespace, not the product release number.
The documented maintainer flow uses signed release commits, a dev-to-main merge,
manual annotated tags and a subsequent dev fast-forward. This audit does not cut
or publish releases.

The latest published server, web and canonical mobile release is **v2.2.0**
(11 November 2026). There is **no authoritative dated or numbered next-minor
schedule** in the current release guide or milestones. Server still has open
milestones `Public Release`, `v1.2.0` and `Post 2.0`; other repositories have none.
These older milestones were preserved, not silently rewritten into invented
v2.3/v3.0 commitments.

Release labels describe shipping class, not a promise or approval:

| Label | Meaning |
| --- | --- |
| `release:patch` | Fix/hardening of an already released path without pulling a new feature line |
| `release:minor` | Backward-compatible additions, including correctness fixes within an unreleased feature lane |
| `release:major` | Breaking contract/destructive required migration that needs an explicit major plan |
| `release:backlog` | Unresolved design, cross-release planning, or inactive/legacy lane |

Correctness category and shipping class are independent: server polling fix #313
stays a **bug**, but is **minor-class** because `internal/polling` is absent from
main. The same reasoning applies to other polling-only fixes. API filter #314 and
the native handshake fix #26 affect released paths and are patch-class. Do not
classify a title beginning “Release” automatically as minor: use its actual version
transition and feature availability.

## Labeling execution and reconciliation

The first pass classified **60 open issues/PRs**, preserving every existing label
and milestone and adding a type/priority only when missing. Four consistent release
labels are now defined on all **12 audited repositories**, even queues with no
open work. No closed history was reclassified. Existing type/priority names were
reused; no milestone dates or Git release tags were created.

Receipts:

- `mobile-release-inventory.json`: initial repo/head/release/milestone/label inventory.
- `release-label-changes-initial.json`: initial before/after changes.
- `release-label-changes.json`: release-label synchronization and new-item refresh.
- `release-lane-corrections.json`: explicit corrections for server #313 and Flutter #22.
- `release-label-final.json`: final open-item coverage, late additions and preservation checks.

The final pass includes audit issues and PRs that appeared after the
initial snapshot. Items that already have a complete classification are preserved;
unclassified additions are assigned explicitly, not guessed from title keywords.
Private source, signing secrets, provider keys and user/account contents are not
included in this report or public label receipts.

## Final mobile qualification and fork maintenance

The maintained fork `dev` is now **458bcf80e1054dd2f348db1e81fe36630cec479c**,
fast-forwarded from `54c13652bcbc` only after exact-source qualification.
[Fork PR #3](https://github.com/n30nex/beacon-flutter-app/pull/3) is incorporated.
The repository default branch is now `dev`; the historical
`codex/flutter-telemetry-sharing-20261020` branch remains intact. No org default
branch/protection or release tag changed. Org dev PRs #26, #28 and #30 remain
open drafts with passing final CI, independently reviewable.

- [Exact final CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/43830774216): **880 tests passed**, **16 optional screenshot previews skipped**; formatting and analysis pass.
- [Exact Android build](https://github.com/n30nex/beacon-flutter-app/actions/runs/43830768689): success; downloaded `commit.txt` and checksum match final source and APK bytes.
- APK SHA-256: `59be0b030bc0c9e2be63aa96e85302b7acfe2f4e4ffcfe6d77ad44aea2bf621b`.
- Package/version: `meshcorebeacon.app`, `2.2.0`, versionCode `2`.
- The verified signing certificate differs from the earlier `54c13652bcbc`
  artifact, so these debug artifacts do **not** provide an in-place upgrade path.
  This concrete distribution finding is recorded in issue #33. No device was
  installed, uninstalled or downgraded, and no signing key was changed.
- No new RF, BLE/Wi-Fi companion collection, production account, push/mail or
  physical background behavior acceptance is claimed. Default trace filtering
  is still the bounded follow-up in #27; warnings/raw-wire display are implemented.

The canceled/failed intermediate candidates are not the delivered source. The
final guard checks are ready with clean worktrees and exact-head CI. Artifacts
and machine-readable receipts stay in `evidence/parity-audit-20261116`.
