# Atlas view control layout follow-up

17 November 2026. The focused layout fix is deployed and qualified on the Canadaverse preview.
One small code draft targets org dev. Backend, app and the already qualified APK are unchanged;
no org merge, dev/dev1/live deployment, physical-device action or RF operation occurred.

The scope is [web issue #238](https://github.com/MeshCore-Beacon/beacon-web/issues/238): keep
all four Atlas view controls within narrow cards, preserve their full accessible labels and
retain selection/persistence behavior. The parallel backend/native queue review identified
existing coverage and remaining qualification gates, without proposing duplicate implementation.

## Verified starting point

The read-only baseline keeps repository identity separate from runtime identity:

| Target | Verified source |
| --- | --- |
| Canadaverse backend and fork | `b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590` |
| Canadaverse web and fork | `274cef3e09c0787838546bc4985dfbee220f76f5` |
| Qualified app fork | `f88f0dc3ff0742f94f31b54d8fe82acf202ec84d` |
| Upstream docs dev | `a98c62ea7ad2aaf0a675a99a117b950c8f4ee231` |
| Preview docs fork | `7375dc345b08b4a726a77c19953a4b5e5c310f80` |

Upstream server/web/app dev heads remain `cf14a67c04d5`, `f5feaaf1f2ca` and `aeb9cd0328e1`.
Public build metadata and API identity agree. The app and its already qualified APK are
preserved; this round does not rebuild, reinstall or re-sign the app. The
[previous Unicode handoff](https://canadaverse.org/beacon-dev/atlas-unicode-20261117.md)
remains a historical record.

## Failure and focused correction

Before the fix, on a 390-pixel French viewport, the fourth view control extended beyond both
its card and the viewport. The reproduced Telemetry button ran from x=306.25 to x=395; its card
ended at x=374 and the viewport at x=390. An ancestor clipped the control, so document scroll
width alone reported no overflow. Short ASCII names reproduced the issue on the earlier qualified source as well;
the Unicode-name correction did not introduce it.

[Web draft #239](https://github.com/MeshCore-Beacon/beacon-web/pull/239), source
`0d7ba4268f785829dc3a5bb922d6ef4f534f44c0`, changes two lines in
`src/features/stats/Segmented.tsx`. Stretched buttons can shrink, and a bounded span paints
ellipsis labels where needed. Full accessible names, pressed states, icons and callbacks
remain intact. The non-stretched control keeps its previous markup; Atlas is the current
stretched caller. No dependency, state, API, feature flag or persistence contract changes.
Issue #238 remains open for upstream acceptance; preview deployment is not an org merge.

The fresh baseline violates child containment in 10 of 12 cases. Candidate and public checks
measure each button and label against its card and viewport, so clipped children cannot pass
merely because document scroll width remains unchanged.

## Backend and native queue disposition

The read-only queue review found that all 15 open server bug issues have an existing fix or
an explicit qualification gate, and all 11 open native bug issues already have a PR. Existing
performance work is also covered by server #333 and app #35/#38. This is a disposition of the
current queue, not a claim that the entire codebase is defect-free or a new capacity benchmark.
No backend/native code, build, deployment or RF change was made in this pass.

The remaining work includes:

- [App #15](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/15) has an
  `action_required` workflow gate. Maintainer approval/review is needed; that state is neither
  a failed nor a passing test run. No competing PR or workflow-approval action was made here.
- [Server #224](https://github.com/MeshCore-Beacon/beacon-server/issues/224) needs current
  release-host maintenance soak evidence. An old failure does not establish a current regression.
- [Server #270](https://github.com/MeshCore-Beacon/beacon-server/issues/270) needs a delayed-replay
  timestamp/deduplication/receipt contract. [App #34](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/34)
  still needs default TRACE filtering semantics, while [app #33](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/33)
  needs the operator's signing and upgrade policy. Those are separate release/design gates.

## Exact source and artifact qualification

The final preview web source is `71eac3390c3dbe5959176b34cdbaaf6f1ef1b39b`, composed in
[fork PR #41](https://github.com/n30nex/beacon-web-contributions/pull/41). Its only new code
change is the independently reviewed two-line layout correction; prior audited fixes remain.
Fork PR #41 is merged at that source, while org PR #239 remains a draft.

| Qualification | Result |
| --- | --- |
| [Org CI](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44111398467) | Build/lint and 2,192 tests in 208 files pass at the exact #239 head |
| [Composed CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/44111707438) | Build/lint and 2,307 tests in 219 files pass at the exact preview head |
| Existing focused interactions | 67 component/card tests pass |
| [Actions artifact](https://github.com/n30nex/beacon-web-contributions/actions/runs/44111703419) | All 82 manifest files verified; source archive matches `git archive` |
| Final public identity | All 82 assets and source archive match the deployed revision; backend identity and feature state are preserved |

Distribution SHA-256: `7540f61722e719deb871bc9956745b64f7bf47390ea3b2238146fb8b2eecfa98`.
Source SHA-256: `97d9bbb62350f3487780bd189526db0fac34d9bce01d7be3258c002ed271444d`.

The initial Windows lint process ended with a native process exception and is excluded from
passing evidence. A local no-JIT rerun passes with two existing warnings and no errors; the
full Linux build/lint/tests pass normally. No source workaround or dependency was added.
There is no new backend/app suite, CPU, frame-rate, battery or production-capacity claim.

## Candidate and public browser acceptance

Both the exact Actions candidate and the final public preview pass the complete 12-case
matrix: English/French, widths 320/360/390, and loaded/unavailable saved nodes with all four
view choices. Candidate asset serving permits no fallback to an older public bundle.

Each run confirms containment and full accessible names, with 48 touch view selections,
48 controls reached using Tab, 12 Enter activations and 12 preferred-view saves using Space
followed by reload. Temporary choices do not overwrite the saved preference; preference saves
retain all other pin settings. Unavailable-node title and existing unavailable-view behavior
remain intact. Initial four-view screenshots are kept separately from post-preference images,
so the test cannot hide the original condition by selecting a different setup first.

These are isolated Chromium mobile-emulation contexts. Fixture node/observer and public-key
fallback reads are intercepted, WebSockets are mocked, and non-GET requests are blocked.
Polling/telemetry flags are enabled only inside browser fixtures to exercise the loaded
four-view state. Accounts remain off. Server configuration, live polling and RF are unchanged;
this is not physical-device, live telemetry or real-live-feed qualification.

## Deployment and recovery

Only the Canadaverse frontend changed. Public build/source checks confirm web
`71eac3390c3dbe5959176b34cdbaaf6f1ef1b39b` with backend
`b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590`. Configuration/secrets, feature flags, containers,
history, retention and radio services are preserved, and MQTT connections remain healthy.
Native polling/accounts/alerts stay disabled under existing policy; telemetry display flags
are preserved. The app remains `f88f0dc3ff0742f94f31b54d8fe82acf202ec84d`, with no rebuild,
new signer or device installation.

From the existing Pi preview root, the guarded frontend-only recovery is:

```sh
sudo python3 evidence/atlas-layout-20261117/web-runtime/deploy-web.py rollback
```

Checkpoint `atlas-layout-web-20261117T152100Z` restores web
`274cef3e09c0787838546bc4985dfbee220f76f5` while retaining the backend and data. No live
rollback rehearsal was performed. Do not substitute an older round's rollback without
checking its source/checkpoint lineage.

## Maintainer follow-up

Review the layout fix as a small separate draft to dev, in the minor lane with the unreleased
four-view Atlas feature. Keep historical reports intact. Existing milestones and release
numbering remain with maintainers; no release version or date is assigned here.

All open items across the 12 tracked repositories are checked for release/type/priority
classification after final PR and fork publication. The final count belongs to the dated
evidence receipt, not a permanent roadmap total. Keep source, runtime and artifact acceptance
separate; existing PR coverage is not upstream release acceptance.
