# Atlas Unicode names: maintainer handoff

17 November 2026. Canadaverse now runs the qualified Unicode-name correction. Exact source,
artifacts and eight isolated public browser contexts pass the data-preservation checks below.
The separate French phone tab-clipping limitation remains explicitly tracked.

This follow-up addresses the separate Unicode-name limitation recorded in the
[previous cache, region and Atlas report](https://canadaverse.org/beacon-dev/performance-round4-20261117.md).
That historical report is unchanged. The fixes belong in two focused draft PRs to org `dev`,
with this documentation update separate. Maintainers retain upstream merge and release control.

## Contract and change

The existing server limit is **160 Unicode code points**, enforced by
[the server validator](https://github.com/n30nex/beacon-server-contributions/blob/b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590/internal/api/atlas.go#L195).
JavaScript and Dart string lengths
count UTF-16 code units instead: a valid name containing 160 supplementary characters occupied
320 code units and was shortened to 80 characters by the clients. The mixed boundary of 159
ASCII characters followed by one supplementary character could be cut between its surrogate halves.

Each patch changes the shared Atlas name normalizer to take 160 complete code points. The
same path is used by node and observer names, local restore, append, import/export and account
document conversion. Identity keys, pin order, tile/view choices, account revisions, configured
pin limits and document budgets remain unchanged. This is not grapheme-cluster counting:
combining sequences retain their constituent code points and normalization form. Truncating a
valid overlong name must not introduce a lone surrogate. This does not define a new malformed-input
repair policy; the existing document validation checks remain in place.

The fixes preserve names still present in saved, exported or server documents. They do not
reconstruct suffixes that an older client already overwrote with a truncated value, and perform
no data migration or historical-name recovery.

| Review unit | Draft | Release class |
| --- | --- | --- |
| Web name normalization | [Web #237](https://github.com/MeshCore-Beacon/beacon-web/pull/237) | Minor, unreleased configurable Atlas feature |
| Native name normalization | [App #50](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/50) | Minor, unreleased configurable Atlas feature |
| Contract wording and handoff | This handoff, separately proposed to dev | Minor documentation |

[Web issue #234](https://github.com/MeshCore-Beacon/beacon-web/issues/234) remains the canonical
cross-client contract discussion; [app issue #49](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues/49)
tracks native implementation. Both remain open until upstream accepts their fixes. A qualified
preview or fork promotion does not close an upstream issue or establish release acceptance.
New code drafts use `bug`, `p2-medium` and `release:minor`; documentation uses the corresponding
documentation type. The final open-item classification check covers all 12 Beacon repositories
and preserves existing milestones. Release labels assign no version or date.

## Qualification

Public acceptance passes **eight isolated browser contexts** on the exact deployed web build:
four English/French desktop/touch contexts cover node and observer restore, reload, export/import,
the 159-plus-one boundary and complete 161-to-160 truncation; four maximum-collection contexts
cover 100 node cards and 100 observer cards on desktop English and phone-sized French.
The original Unicode bug is reproduced separately on the prior qualified build.

These checks use synthetic saved identities and intercepted node reads, with mocked WebSockets.
Expected fixture 404s and the existing Cloudflare analytics CSP notice are recorded separately;
there are no unexpected application errors. No account write or RF operation occurs. This is
targeted Unicode/data acceptance, not a new all-page or live-animation qualification. Two French
phone contexts expose the existing inner-control clipping discussed below, despite no page-width
overflow.

Web draft #237 is `4ac3a9479049712cc747bc75f07d85cf76c54ed3`, based on dev
`f5feaaf1f2caeb5bc223fc6ff6f9e164c2c90538`. Its composition is
`274cef3e09c0787838546bc4985dfbee220f76f5`, retaining the previous qualified preview.
[Source CI](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44099701061) passes
**2,201 tests / 209 files**; [composed CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/44099970272)
passes **2,307 tests / 219 files**, including the Linux deployment-shell suite. Build and lint
pass; two existing lint warnings remain. Independent review repeats 75 focused tests.
Windows shell checks are not reported as fully passing: three HTML-inlining cases failed in
that environment, while the required Linux CI passed. No source change was made to mask them.
The [exact preview bundle build](https://github.com/n30nex/beacon-web-contributions/actions/runs/44099969846)
also passes. Its 82 manifest entries and exact source archive are verified. Distribution SHA-256:
`2ecf81555bd090e92049fa7e25cf0df70bf5c316a385a7de58844ef3054510f9`;
source SHA-256: `765ae6e953f8c7da315b40b6e3a3568cce0f20c0edc436b07e3c4aac458f69ac`.
All 82 public assets and the public source archive match the qualified artifact, and the eight
public Unicode/data contexts pass with the separately recorded layout limitation.

Native draft #50 is `2c845c4e87de15ebb3260b437af411b1072869e8`, based on dev
`aeb9cd0328e16100dc0ce4d36f0852ee726501b2`. Its composition is
`f88f0dc3ff0742f94f31b54d8fe82acf202ec84d`, retaining the previous fork and changing only
the shared name normalizer and its new regression file. Eight Unicode cases fail before the fix;
eight compatibility cases already pass. Source CI passes **888 tests**, and composed CI passes
**933 tests**, each with 16 optional screenshot skips. Independent review passes 74 tests plus
two maximum-collection fixtures (100 node cards and 100 observer cards).

The native [source CI](https://github.com/MeshCore-Beacon/beacon-flutter-app/actions/runs/44099293391),
[composed CI](https://github.com/n30nex/beacon-flutter-app/actions/runs/44099599452) and
[APK build](https://github.com/n30nex/beacon-flutter-app/actions/runs/44099600959) pass at those
exact heads. The APK is `meshcorebeacon.app` 2.3.0, versionCode 2, SHA-256
`00ede8c72bb7ecfd41de98802024b8fff8d65c6d43163bdd2633693d1d4e9823`.
Its source manifest, checksum and signature are verified. Its debug certificate differs from
the previous artifact: no in-place upgrade or signing compatibility is promised. No device
installation or signing-secret change was performed.
Fork `dev` was fast-forwarded to the qualified composition and
[fork #8](https://github.com/n30nex/beacon-flutter-app/pull/8) merged; the automatic post-push
CI and APK builds also pass. Org #50 remains a draft. The previous fork source
`7609d7985cd8602053cb13c445ce45e63eb32bed` remains available for source recovery; this is not
a device rollback instruction.

Matching regression fixtures cover 160 supplementary code points, the mixed 159-plus-one boundary,
161-to-160 truncation, BMP names, combining sequences, node/observer names and account conversion.
Source regressions cover append, including preservation of an existing name when a card is added.
The maximum-collection fixtures cover full persistence, file round trips and account-document conversions.

The existing composed-preview budgets are sufficient. A standard two-space, ASCII-escaped export
with 100 cards, all optional node settings, longest valid tile IDs and 160 supplementary code
points per name is **241,310 ASCII characters/UTF-8 bytes**, within the existing **256,000**
client parser/file bounds. The corresponding escaped account PUT is **230,056 bytes**, within
the existing Atlas-only **256 KiB (262,144-byte)** HTTP limit. No budget increase is part of these
Unicode patches. This is a defined maximum-settings fixture, not a promise to accept arbitrary
extra whitespace or unknown fields. The earlier budget fixes remain separate drafts; current org
dev still requires them for the maximum-collection scenario.

The backend remains `b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590`; its server validation already uses
code-point counting. No backend deployment, schema/config/retention change, RF operation or secret
change is part of this follow-up. Optional account/polling/alert features remain off on Canadaverse.
Account synchronization paths are fixture-tested, not exercised against real preview accounts.

## Deployment, recovery and remaining limits

The Canadaverse web cutover is verified at checkpoint `atlas-unicode-web-20261117T142933Z`.
Public asset/source checks pass on web `274cef3e09c0787838546bc4985dfbee220f76f5`.
The backend revision, published server metadata, feature flags and server fork remain unchanged;
both MQTT brokers are connected.

From the existing Pi preview root, this round's frontend-only recovery is:

```sh
sudo python3 evidence/atlas-unicode-20261117/web-runtime/deploy-web.py rollback
```

It restores web `231fec5397faf7e399f982c52033d74593e31b46` while keeping backend
`b54d1bf3afdacfecd42d5d9ebf7fdaae95d44590` and accumulated data. No live rollback rehearsal
was performed. Do not substitute an older full-stack recovery procedure.

Deployment is restricted to Canadaverse preview. No org merge or dev/dev1/live deployment occurred.
Browser touch emulation is not physical Android/iOS/Safari acceptance;
an APK build is not a device-install, background lifecycle, battery or RF test. Signing and
in-place upgrade compatibility must be reported from the actual new artifact.

No new CPU, GPU, battery or throughput improvement is claimed. Earlier audited performance
and resource-lifetime fixes stay in the compositions; this change preserves valid labels.

Public testing also identified a separate existing layout problem, now tracked in
[web #238](https://github.com/MeshCore-Beacon/beacon-web/issues/238): the fourth French view
label, **Télémétrie**, can be clipped in a 390-pixel card. It reproduces with short ASCII names
on the previous qualified web build as well. Page-level overflow checks do not detect the
clipped child control. No layout change is bundled into the Unicode drafts, and this handoff
does not claim that every inner control fits. The follow-up should preserve every view and its
accessible name while checking child bounds, reachability and view persistence.
