# Beacon review map after Atlas landed on dev

Updated 5 November 2026. **Use `dev` as the single integration target.** Dev1 is
an operator-controlled test environment, not a second PR for the same branch.
Historical branch names containing `dev1` do not change the target shown here.

My Atlas is already on web dev at `38017d8`, following `e8434bd`. The maintainer
closed web #97, #151, #164 and #167 after incorporating that work. The current
core web candidate preserves those Atlas files byte for byte; its remaining
feature is Topology with the shared reliability and trace-quality UI changes.

## Review these eleven PRs

| Order or feature | Server | Web | Other | Status and dependency |
| --- | --- | --- | --- | --- |
| 1. Core performance and Topology | [#266](https://github.com/MeshCore-Beacon/beacon-server/pull/266) | [#182](https://github.com/MeshCore-Beacon/beacon-web/pull/182) | [Docs #43](https://github.com/MeshCore-Beacon/beacon-docs/pull/43) | Primary next review. Atlas itself is already on dev. |
| 2. MQTT scope investigation | [#292](https://github.com/MeshCore-Beacon/beacon-server/pull/292) | [#192](https://github.com/MeshCore-Beacon/beacon-web/pull/192) | Covered by this roadmap | Follow-on after core; includes the earlier #290/#190 scope foundations. Contains no collected-sensor telemetry. |
| 3. MeshMapper profile extensions | [#293](https://github.com/MeshCore-Beacon/beacon-server/pull/293) | [#193](https://github.com/MeshCore-Beacon/beacon-web/pull/193) | Covered by this roadmap | Follow-on after the scope pair in the current source stack. Existing MeshMapper integration is already upstream. |
| Optional Flutter telemetry | [#268](https://github.com/MeshCore-Beacon/beacon-server/pull/268) | [#184](https://github.com/MeshCore-Beacon/beacon-web/pull/184) | [Flutter #11](https://github.com/MeshCore-Beacon/beacon-flutter-app/pull/11), [docs #44](https://github.com/MeshCore-Beacon/beacon-docs/pull/44) | Separate from the scope stack; depends on core. Device/RF/background acceptance remains open. |

These remain drafts. They identify the intended review candidates and their
dependencies, not permission to merge or deploy them. Core code can be reviewed
now; optional telemetry is not a release prerequisite for Topology.

## Read only the incremental changes

All canonical PRs target dev. Before a prerequisite is accepted, GitHub's normal
diff includes that prerequisite. Use these comparisons to review each addition:

| Addition | Server comparison | Web comparison |
| --- | --- | --- |
| Optional collected telemetry after core | [Core to telemetry](https://github.com/MeshCore-Beacon/beacon-server/compare/codex/release-core-20261021...codex/release-telemetry-20261021) | [Core to telemetry](https://github.com/MeshCore-Beacon/beacon-web/compare/codex/release-core-20261021...codex/release-telemetry-20261021) |
| Scope foundations and investigation after core | [Core to scopes](https://github.com/MeshCore-Beacon/beacon-server/compare/codex/release-core-20261021...codex/scope-pages-dev1-20261031) | [Core to scopes](https://github.com/MeshCore-Beacon/beacon-web/compare/codex/release-core-20261021...codex/scope-pages-dev1-20261031) |
| MeshMapper extensions after scopes | [Scopes to profiles](https://github.com/MeshCore-Beacon/beacon-server/compare/codex/scope-pages-dev1-20261031...codex/meshmapper-profiles-dev1-20261031) | [Scopes to profiles](https://github.com/MeshCore-Beacon/beacon-web/compare/codex/scope-pages-dev1-20261031...codex/meshmapper-profiles-dev1-20261031) |

Web #193 is not the entry point for reviewing the whole stack. Its incremental
change extends the existing MeshMapper panel with provider links, attribution,
radio presets/status and uploaded-neighbour observations. The paired server
change adds regional import narrowing and credential/coverage-bound cache
invalidation. Existing hardware/site data and the authenticated MeshMapper
connection are not being proposed as new integration.

The scope pair is MQTT evidence and views. The telemetry pair is companion
polling and sensor history. Neither optional feature contains the other one;
scope membership does not authorize polling or prove packet delivery.

## Superseded review entries

The replacements below are the canonical review targets. Closing an older PR
does not delete its branch, abandon its feature or assert that it was merged.
Source heads and original PR metadata are preserved in the cleanup evidence.

| Repository | Older PRs | Replacement or disposition |
| --- | --- | --- |
| Server | #225, #230, #242, #253, #255, #256, #259 | Commits are included in #266. The focused fixes remain individually inspectable in that history. |
| Server | #267 | Exact same branch as #266, with the redundant dev1 target. |
| Server | #263, #269 | #268 is the sole optional intake target. |
| Server | #290 | Exact ancestor of #292; review the combined scope feature there. |
| Server | #210 | Early preview staging, superseded by the current core and feature lanes. |
| Server | #192 | The moving `n30nex-test` preview umbrella is not a merge candidate. Review #266, #268, #292 and #293 separately. |
| Web | #165, #169, #179, #183 | #182 is the sole remaining Topology/core target. |
| Web | #180, #185 | #184 is the sole optional sensor-telemetry UI target. |
| Web | #190 | Exact ancestor of #192; review the combined scope feature there. |
| Web | #148 | Early mixed preview staging. Its full NodePage and preview-only extras stay in the preview fork; current org feature proposals use the shared inspector. |
| Docs | #7 | Mixed preview documentation targeting main; #43/#44 are the curated dev proposals. Historical/preview-only docs remain in the fork. |

The three focused backend fixes (#253, #255 and #259) are retained verbatim in
#266's ancestry. Keeping both their standalone PRs and the containing core PR
open made the intended integration ambiguous. Their branches are retained;
the single chosen review entry is #266.

## Runtime and acceptance boundary

This cleanup changes review organization and refreshes the remaining web proposal
on the accepted Atlas source through a history-preserving merge. It does not
deploy dev, dev1, live or the Canadaverse preview. The preview remains the broader
experimental source pair identified in its published build metadata.

Flutter is the intended telemetry polling client. Keep the legacy Pi poller and
RemoteTerm disabled while retaining the shared Flutter intake. No fresh RF,
phone/tablet or background collection test is implied by this cleanup.

The [project roadmap](project-roadmap.md), [current compatibility record](upstream-refresh-20261105.md)
and [tracking issue #45](https://github.com/MeshCore-Beacon/beacon-docs/issues/45)
provide supporting context. Dated audit tables remain historical; this review
map is the current PR disposition.
