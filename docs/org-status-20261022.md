# Beacon organisation status and roadmap reconciliation — 22 October 2026

Prepared by **[Torchlight]** for the [owner's request](https://discord.com/channels/1507764602253869197/1507788454774182030/1562765854255484929).
[Canonical roadmap](../ROADMAP.md) · [Feature decision register](post-20-feature-decisions-20261004.md) · [Project tracker](https://canadaverse.org/torchlight/)

## Scope and status language

The public GitHub organisation inventory exposes **four repositories**: beacon-server,
beacon-web, beacon-docs and beacon-flutter-app. All were checked; all are public,
unarchived and use `dev` as their default branch. The listing was checked through
its empty final page, not inferred from the older three-repository source catalogue.
This is a bounded status/acceptance reconciliation, not a line-by-line audit or an
exhaustive review of every issue. Private or unlisted repositories cannot be certified
from this public-channel pass. The separate intake/headless project is not silently
counted as an audited public organisation repository.

**🟢 EXISTS / MERGED / TAGGED** describes the specifically named evidence, not blanket
production stability. **🟡 DRAFT / IN PROGRESS / VERIFY** means work or acceptance
remains. **🔴 BLOCKED / DO NOT DUPLICATE** always includes the reason. Branch code,
a release tag, a reported deployment and independent runtime verification are distinct.

## Repository inventory

Checked 22 October 2026, approximately 09:54–10:01 UTC.

| Repository | Main | Dev | Other relevant baseline |
| --- | --- | --- | --- |
| [beacon-server](https://github.com/MeshCore-Beacon/beacon-server) | `202acc6cc8f616819a3577c57a7009ea1a48c0dd` | `080141145e964945d3f105be01903b082ebbfd8b` | Latest stable tag `v2.0.7` is main; current `dev1` also points to main. |
| [beacon-web](https://github.com/MeshCore-Beacon/beacon-web) | `19f604e91e630f601235bd9593b63498b160d514` | `811f8430ea7eea0a556068904e71a43e07ac93f7` | Latest stable tag `v2.0.5` is main; `dev1` is `add7acbaa1cc195bea253753d4108a49afca0ad5`. |
| [beacon-docs](https://github.com/MeshCore-Beacon/beacon-docs) | `27319994eae7c63271b868f774ee1fdd5e655f7a` | `3c2ffe2b4214619dd999800b03b808acea86e666` | Dev has the current 2.1 upgrade, read-model and paired-client guidance; core/telemetry guides remain separate drafts. |
| [beacon-flutter-app](https://github.com/MeshCore-Beacon/beacon-flutter-app) | `5a3de514244cacd98f5bbd5a8a656c0360c9ce0d` | `a8107047f52da43f8b30afb98655bc4452b7a74e` | Visible tags include `v2.0.0+1792022320` at `b258ef28a13703b2219e582295de4d088c983f22`; this is not proof of app-store distribution. |

The former mobile-repository HTTP-404 gap is **resolved for current public source
access**. Preserve the old dated observation; it was not proof that the project did
not exist. The public repository API reports creation on 10 October.

Server `v2.1.0-dev1.4` and web `v2.1.0-dev1.7` exist as prerelease tags, but neither
is the current `dev1` head. No stable server/web 2.1 tag appeared in the checked tag
lists. Do not use an old prerelease label or a high experimental version to mark the
accepted 2.1 roadmap complete. Likewise, different main/dev SHAs are not by themselves
a count of missing features.

## Core and optional review stacks

The current consolidation is more relevant than treating every earlier focused
branch as a separate next implementation. All PRs below remain open candidates;
core and optional server/web/docs targets are drafts. The Flutter PR explicitly
retains draft qualification status. Do not merge both a focused precursor and its
consolidated replacement without reconciliation, and do not infer that old PRs have
been closed merely because a new consolidation exists.

| Layer | Server | Web | Docs / mobile |
| --- | --- | --- | --- |
| **🟡 Core** | [#266 dev](https://github.com/MeshCore-Beacon/beacon-server/pull/266), [#267 dev1](https://github.com/MeshCore-Beacon/beacon-server/pull/267); `774b46c120755393ce95169a8efac0fb4390aa6a` | [#182 dev](https://github.com/MeshCore-Beacon/beacon-web/pull/182), [#183 dev1](https://github.com/MeshCore-Beacon/beacon-web/pull/183); `6cf9ebc4bec4c4cb45f931fedbc8c7def63e0b42` | [Docs #43](https://github.com/MeshCore-Beacon/beacon-docs/pull/43); `b221d58a31e4dd1fce4818d421eccd34da9bc8a2` |
| **🟡 Optional collected telemetry** | [#268 dev](https://github.com/MeshCore-Beacon/beacon-server/pull/268), [#269 dev1](https://github.com/MeshCore-Beacon/beacon-server/pull/269); `a44cd25d12e02b4f8d1d1227c24c9b48aa0de711` | [#184 dev](https://github.com/MeshCore-Beacon/beacon-web/pull/184), [#185 dev1](https://github.com/MeshCore-Beacon/beacon-web/pull/185); `1632b4a318055a6f13ced780ed37063ac11c8f55` | [Docs #44](https://github.com/MeshCore-Beacon/beacon-docs/pull/44); `0d70bf73729fe9e9438c0a8de683d8bb2e3eef5e` |
| **🟡 Optional mobile collection** | Uses the selected instance's optional intake contract, not a new core database. | Ordinary app/viewer use does not require collection. | [Flutter #11](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/11), dev-targeted; `1f704187a94ea5c84c458a5d63ab8c0a4fdef525`, version `2.1.0+3`. No app `dev1` branch was listed. |

### Server: implemented work is no longer merely a wishlist

Current dev and the core candidate include substantial 2.1 database/client work.
The consolidation combines upstream bigint/exact cursors, indexed read models and
workload pools with paced first fills, resumable bounded historical decryption,
cache-failure coalescing, missing-signal preservation, bounded WS control/writes and
global gap notices, Topology/TRACE contracts and artifact identity. Historical
messages must not become new live chat, and invalid RSSI/SNR must not become zero.

[PR #264](https://github.com/MeshCore-Beacon/beacon-server/pull/264) is merged into dev:
read-only scope catalogue restoration, retryable statement-timeout behavior and
read-model restore logging. The broader consolidation is still draft, not stable
release acceptance. Preserve the upstream **001–053 migration and rollback boundary**;
this is not an image-only update of an old database. Nonroot mount ownership,
connection budgets, restore rehearsals and production workload qualification remain gates.

### Web: basic/core views stay independent of collected telemetry

The core candidate contains basic node/observer Atlas and performance-enhanced
animated Topology. It preserves camera continuity, cursors and TRACE evidence, and
reuses active projected segment geometry while animation continues. Geometry reuse
and unit tests are not a universal FPS guarantee.

The optional layer adds full-key telemetry availability filtering, attributed
battery/environmental history, channel-2 and zero-value preservation, coverage/cap
labels, and visible retryable service errors. Basic Atlas and Topology must continue
to work without the optional gateway. Match server/web contracts and minimum versions;
upstream docs now explicitly require **Beacon Web 2.1 with Server 2.1**.

### Mobile: public native viewer plus a separate collection candidate

The [pinned dev README](https://github.com/MeshCore-Beacon/beacon-flutter-app/blob/a8107047f52da43f8b30afb98655bc4452b7a74e/README.md)
describes the native iOS/Android REST/WebSocket viewer and its foreground WebSocket
lifecycle. Do not equate that viewer with completed background collection.

PR #11 adds opt-in BLE or Wi-Fi/TCP companion collection, selected repeater contacts,
locally held credentials, signed instance-bound enrollment/reports, bounded polling
and saved upload retry. Android has an explicit background choice and foreground
service notification; **iOS remains foreground-only in this draft**. App/source build
availability does not prove store publication or new physical radio qualification.
The public qualification record reports analyzer/347 Flutter tests and five Android
service tests passed; none was rerun by this review. Fresh BLE/Wi-Fi, screen-off,
reconnect and real RF-to-intake-to-card testing remain open for that exact revision.

### Docs and component boundaries

Upstream docs dev records read-model readiness/503 behavior, pool/fill pacing, a
single 2.0.x-to-2.1 upgrade path, compatible rollback and measured upgrade examples.
Those examples are deployment-specific observations, not capacity promises.

The [pinned optional collection guide](https://github.com/MeshCore-Beacon/beacon-docs/blob/0d70bf73729fe9e9438c0a8de683d8bb2e3eef5e/docs/telemetry-collection.md)
separates mobile/headless polling clients, core API proxy, independent validating
intake/storage and web presentation. The app does not replace intake. The guide says
the org `beacon-agent` scaffold is not a deployable substitute for the current intake;
that repository is not exposed by this public inventory, so its source/completion
is not independently certified here. No private implementation was inspected.

The headless MQTT path requires idempotent HTTPS acceptance of the same signed
sample; broker PUBACK alone is not intake acceptance. Core views remain usable
without collection. Cross-instance RF leases and hardware/sensor attestation are not
claimed. Retain the adopted hourly/three-hop qualification gates; a known route length
still does not establish a firmware-enforced flood limit.

## Roadmap reconciliation and next gates

| Existing area | Current evidence | Tracker/roadmap treatment |
| --- | --- | --- |
| **2.1.0 / R05–R06 foundations** | Basic Atlas has historical dev1 delivery; core Atlas/Topology is now a consolidated candidate with reported preview checks. | 🟡 In progress, not complete. Keep agent responsibility, setup/receipt contract, paired migration and actual target acceptance visible. |
| **2.1.1 / R01–R03 correctness** | Global WS-gap/write bounds, cache/backfill/data-quality and TRACE work are implemented in the core draft; some upstream dev fixes already merged. | 🟡 Candidate review/qualification, not an untouched bug list. Do not blindly reimplement the old B1–B9 shortlist or label every case fixed. |
| **2.1.x / D05 collection** | Optional gateway/intake/web and Flutter collection code now exist as a dependent stack, with reported software/API tests. | 🟡 In progress rather than merely proposed; physical mobile/headless coexistence and intake acceptance gates remain. Do not mark the Windows/Linux tray UX or iOS background capability delivered. |
| **2.2 refinement / R07** | Attributed optional histories, sensor channels, gap/cap labels and renderer improvements exist in candidates/preview reports. | 🟡 Partial implementation; whole Atlas and production performance acceptance remain open. |
| **2.2.3 / FW01** | Firmware-direct collaboration remains an accepted future direction; mobile companion Wi-Fi/TCP is a different producer path. | 🟡 Conditional target remains. Do not count mobile Wi-Fi support as firmware-native push integration. |
| **2.3–2.5 investigation/routing/replay** | New indexed read models and route search are useful foundations, not proof of transit history, a weighted best-route planner or replay completion. | Keep larger goals separately prioritized and unclaimed. |

Recommended review sequence is **core → optional server/web/intake → mobile physical
qualification**, preserving the owner-adopted version plan. The old patch slots are
planning targets, not proof every feature is missing or tied to an already released
tag. This update does not retag upstream, create a new product scope or authorize
implementation/deployment of the remaining work.

## Preview evidence and explicit verification limit

The [public changelog](https://canadaverse.org/beacon-dev/source.html) and
[pinned qualification record](https://github.com/MeshCore-Beacon/beacon-docs/blob/b221d58a31e4dd1fce4818d421eccd34da9bc8a2/docs/release-qualification-20261021.md)
report a combined 21 October Canadaverse candidate at server
`fdae02d4b7c501264280995d145bfe529b9e0d2f` and web
`79edb9ce26a8eda0764b32de6545d1d486afa98b`, labelled **2.5.0-n30nex.1** while the
server API version is **2.1.0**. Current preview-fork heads match those revisions.
This high experimental label is not completion of this roadmap's 2.5 goals.

The record reports native PostgreSQL/race/vulnerability/image checks, 1,512 core web
and 1,555 combined web tests, API/browser checks, preserved retained history and
recovery rehearsals. These are attributed prior results, not tests rerun here.
Current `beacon_preview verify` stopped with **“Runtime image changed; owner
requalification required.”** The public changelog was readable, but fresh guarded
runtime verification did not pass. Do not bypass that guard or infer an application
outage from it. Production and current dev/dev1 deployments were not verified.

Remaining gates include:

- 🟡 **Cold 24-hour Topology cost:** the qualification note reports 5.24–5.80 s local
  cold samples and one 13.877 s public cold request, with much faster cache hits.
  These are individual shared-host samples, not p95, throughput or FPS promises.
  The explored path-dedup query was explicitly not shipped; don't record it as a fix.
- 🟡 **Mobile physical/background acceptance:** exact-build BLE/Wi-Fi connection,
  screen-off/unlock/reconnect, notification controls and actual RF-to-card receipt.
- 🟡 **Shared-radio coordination and recovery:** mobile/headless coexistence,
  complete maintenance-cycle/load soak, pool/role budgets, migration/restore/RPO/RTO
  and device-enforced route/flood constraints. No new polling is initiated by this review.
- 🔴 **Fresh guarded preview verification blocked** until the owner resolves the
  changed-runtime-image qualification. This is a verification blocker, not proof
  the application is broken.

The public tracker currently exposes only its loading shell to text extraction.
Ontology records can be updated and read back; that alone does not establish that
the rendered dashboard has refreshed. Keep that visibility limit explicit.

## Inventory provenance

- [Organisation listing](https://api.github.com/orgs/MeshCore-Beacon/repos?type=all&per_page=100&sort=full_name),
  [bounded continuation](https://api.github.com/orgs/MeshCore-Beacon/repos?type=all&per_page=2&sort=full_name&page=2)
  and [empty terminal page](https://api.github.com/orgs/MeshCore-Beacon/repos?type=all&per_page=2&sort=full_name&page=3).
- Current server/web/docs branch and tag reads through beacon_research; public
  [Flutter branches](https://api.github.com/repos/MeshCore-Beacon/beacon-flutter-app/branches?per_page=100)
  and [Flutter tags](https://api.github.com/repos/MeshCore-Beacon/beacon-flutter-app/tags?per_page=10).
- Current PR metadata/body reads and the pinned docs/README links above. Compact
  responses may omit older PRs; no total open-issue or review-completion count is claimed.

Only documentation and tracker/memory reconciliation are requested here. Upstream
merges, host changes, schema operations, credentials and radios remain outside this task.
