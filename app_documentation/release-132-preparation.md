# Beacon 1.3.2 preparation

30 September 2026. Maintainers choose acceptance, the release commit, tags and the production switch. **1.3.2 is the web version**; the server currently has a v1.6.0 release and needs its own version decision. The dev interface reports 1.3.1, while the latest published web GitHub release remains v1.3.0.

The release composition stops at [web #99](https://github.com/MeshCore-Beacon/beacon-web/pull/99). [My Atlas #97](https://github.com/MeshCore-Beacon/beacon-web/pull/97) is held for after 1.3.2, as one feature PR based on the release work. Removing Atlas from this preview does not clear saved browser cards.

## Candidate and recovery

Server candidate `397d76b33488da0c5913356578aa708a44d0e18a` includes the refreshed #167 → #169 → #172 → #174 → #176 sequence, plus independent #166 and #184. All seven server PRs are now accepted in `dev` at `89a376c2`. Its `a7bfdb19` tree exactly matches the running `397d76b3` source, so acceptance required no rebuild or restart. Web `eb241ca7` is the current release candidate on accepted web dev `17f48fb9`; it contains all eleven release web PRs through #99. [Exact heads and validation metadata](release-132-heads.json).

The [development Pi](https://canadaverse.org/beacon-dev/) serves server `397d76b3` / web `eb241ca7`, with Atlas excluded. Its [corresponding source/changelog](https://canadaverse.org/beacon-dev/source.html) identifies the review deployment. The owner-managed [dev.meshcore.ca](https://dev.meshcore.ca/) remains a separate deployment. Browser inspection shows web 1.3.1 and its older observer detail pane; its exact running server commit is not exposed by the public API.

Windows and native Pi web build/lint and all **955 tests** pass. All eleven current release web heads pass build CI; web CodeQL is skipped by its existing workflow. All **21 public assets** and both source archives match the build, both MQTT inputs are connected, and static frontend publication left all **24 containers unchanged**. Desktop, 390px French phone, keyboard, comparison, shared path links, exact phone-list scroll restoration and dark/light border rendering pass browser checks. A deliberately paused map-module request confirmed that Close/Escape still work during loading.

The post-release Atlas head is `66ae0cc2`, directly after `eb241ca7`. Windows/Pi build/lint, all **975 tests**, current-head build CI and English/French browser checks pass. The marked storage paragraph is removed; Observers precedes My Atlas in navigation. Existing cards survive reload and Atlas-to-observer Back preserves state. This candidate was built separately and is not deployed.

The server/config rollback checkpoint is `release132-cutover-20260930T021238Z`. Its guarded `evidence/release-132-20260929/deploy-server.py rollback` restores server `a35cba1d`, the prior configuration/runner and affected IATA metadata, retaining new traffic rows. The verified dump was restored into an isolated database and checksum-verified off the Pi. Both phase-owned test databases were then retired after checking for active sessions; the working dump and recovery files remain. The frontend-only checkpoint `web-20260930T110037Z` restores `4fd4b0de` with server `397d76b3` using `evidence/release-132-20260929/deploy-beacon-web.py rollback --evidence-dir release-132-20260929`. The current server rollback explicitly accepts either the release frontend or that previous frontend and restores the paired older build. Never relabel an existing binary with a rebased commit.

## User-visible cleanup

The observer list stays on the left on desktop. On phones, Back opens the retained list. The duplicate dashboard picker, traffic badge, explanatory paragraphs and exact-values disclosure are removed. Status uses a coloured icon with an accessible name. The six metrics and activity charts remain first, with 24h/3d choices and comparison available in context.

Channels no longer has the scope explanation disclosure. The Analytics retention banner is removed and the Mesh scope list starts collapsed. Desktop navigation starts with Observers; Atlas will follow it after release. English and French changes ship together.

The missing map layer was a configuration issue: the Pi had no polygons for the affected IATAs. A bounded, reviewed snapshot now fills 26 missing boundaries through the existing border setting. Existing manual borders are preserved. Web caching now retries a missing border and notices a changed shape. See [boundary installation and recovery](meshmapper-border-snapshots.md). The public dev site still returned 204 for YKF/YOW in this audit and needs the same operator configuration step.

Review corrections also preserve cached charts during transient errors, anchor comparison at the time it is opened/refreshed, avoid polling fixed comparison windows, close competing observer/packet dialogs, preserve selected-report links, clear stale route links on navigation, validate future route windows, and keep the newest channel history page when loading older history.

## Every repository and open item

All four organisation repositories were inspected: server, web, docs and mobile. Mobile has no open issues/PRs or recent CI in the inspected metadata; its private contents are not reproduced here. Docs #5 carries the shared release record, operator guides and contributor tooling. The final audit has five open server issues plus profiling PR #182, thirteen web issues and thirteen web PRs, docs PR #5, and no open mobile items. Broader issues remain open; accepted server issues were closed separately. No unrelated mobile release is implied by the web version.

| Repository | Review candidates and linked issues | Disposition |
|---|---|---|
| Server | #166 → #164; #167 → #165; #169 → #168; #172 → #171; #174 → #173; #176 → #175; #184 → #181 | Accepted; focused issues #164/#165/#168/#171/#173/#175/#181 are closed. |
| Web | #75 → #74; #79 → #76; #80 → #77; #81 → #78; #83 → #82; #85 → #84; #87 → #86; #89 → #88; #92 → #90; #95 → #94; #99 → #98 | Release sequence, in this order. Review each focused parent-to-head diff. |
| Web | #97 → #96 | Post-1.3.2 feature; exclude from release artifacts. |
| Server | #183, saved-route prefix metadata after hash-width changes | Maintainer marked non-blocking. Separate correction; do not widen prefix matching to hide the inconsistency. |
| Server | #60 admin; #72 local/remote backup; #99 packet summaries; #116 MQTT timeout investigation | Partially addressed, still open. No blanket closure. Public admin/backup stay disabled. |
| Web | #12 remaining internationalisation | Still open beyond the translated work in this candidate. |
| Server | External #182, bounded CPU profiling | Source-reviewed and upstream CI green at `639148c6`; not in this deployment. Owner integration and a private-host profiling pilot remain separate. |
| Web | External #93, node View on map | Not in this deployment. At `c0dbb101`, no published check results and the author reported pre-existing test failures. It overlaps the changed navigation, and its new button label is English-only. Integration with the current panel stack, French text and exact-head tests are required before inclusion. |
| Docs | #5 | Shared roadmap, workflow, recovery and operator documentation. |

The contributor account has read access to the upstream application repositories. Merge commits are disabled there. Maintainers can enable merge commits to accept this sequence without recreating each parent; the contributor helper never merges upstream PRs. An out-of-draft PR or a green build does not replace maintainer acceptance. Web re-review remains a release gate. The server batch is accepted and accepted-head CI, coverage, CodeQL and image publication pass. Accept docs #5 so the operator-guide links in the now-merged server #172/#174 resolve on docs main.

## Performance evidence and limits

A controlled frontend build moved the packet-path canvas behind on-demand loading while keeping its dialog controls available. Initial static JavaScript fell from 1,628,804 to 598,019 bytes; gzip estimates fell from 448,100 to 172,032 bytes (about 62%). These totals follow the build manifest's static imports and exclude later on-demand chunks. This measures the initial payload, not a production latency or server-CPU improvement.

Native Pi Go tests used PostgreSQL. The 3,200-input/504-scope replay passed with 100 stored packets, 800 observations, 100 decrypted messages, 800 normal and 2,400 opt-in events, 3,200 acknowledgements and zero fixture drops. This is a bounded replay, not universal losslessness.

A 40-second read-only sample on 30 September, with an observer dashboard active, found both brokers connected on both sites and newest-packet timestamps advancing. Pi app CPU samples ranged 0.04–2.61% and memory 37.69–38.66 MiB; PostgreSQL CPU 0–2.15%, memory about 399–401 MiB. Sixteen public API reads took 0.105–0.200 seconds. The sampled Beacon log contained no queue-full/overflow, dropping, SQL-error, parser-fallback, reconnect or panic mentions. These are short point samples, not capacity or production CPU guarantees.

The operator's MeshMapper CPU screenshot cannot be attributed to a single Beacon code path from this Pi sample. If #182 is accepted, run its bounded private profiling on the affected host, compare input/event rate, queue drops, database refresh/cleanup time, process CPU/RSS and request latency over matched busy periods, then decide whether further optimisation is needed. Profiles must stay private; no profiling HTTP endpoint is required. Keep rollback ready before promotion.

Frontend costs remain explicit: one retained origin view preserves the requested Back/filter/scroll behaviour, but stays mounted and can keep its subscriptions. Removing the unrequested extra observer list avoids another duplicate surface. Channel history retains loaded pages so scrolling does not evict the live page; very long visits can accumulate memory. These are targeted follow-ups if measured usage warrants them, not claims of a fully idle background view or bounded total session memory.

Raw packets stay 72h, hourly summaries 30d and telemetry 720h. Summary history older than already-expired raw data cannot be reconstructed. Historical counter differences with CoreScope remain unexplained until inputs, observer identity, exact windows and duplicate policies are aligned. Physical iPhone Safari and sustained production-volume testing remain owner release checks.
