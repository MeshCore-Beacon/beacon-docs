# Contributor workflow

Use this workflow to keep small Beacon changes reviewable while reducing manual branch maintenance. The optional contributor helper is [tools/beacon_stack.py](tools/beacon_stack.py); a CI workflow is included for its [offline regression tests](tools/test_beacon_stack.py). Beacon does not run this script during ingestion or at runtime. Maintainers can review and merge through GitHub without installing it.

## Merge commits and when the helper is useful

The current stacks include commits from still-unmerged parent PRs. Squash merging replaces a parent's commits with a new commit; GitHub's rebase-and-merge also creates new SHAs. Children still contain the old parents. The helper records each feature's exact delta so it can repair that history once for the whole queue. It also composes the preview with independent fixes and verifies source and CI identities.

For dependent PRs, **merge commits are the recommended way to retain ancestry**. Merge the parent first, then inspect the child's updated diff and checks. The parent's original commits are now in `dev`, so that history alone no longer requires rewriting the child. Squashing an independent PR without pending descendants remains an option. GitHub documents these [merge methods and the long-running-branch tradeoff](https://docs.github.com/en/pull-requests/reference/pull-request-merges).

This reduces routine stack maintenance; it does not remove source conflicts, API dependencies or required validation. A rule requiring branches to be current can still require an update, and a linear-history rule would prohibit merge commits. Enabling the repository option does not repair ancestors that were already squashed/rebased. Merge in dependency order and inspect each remaining PR; do not merge a child early merely because it includes its parent.

At the 28 September check, both application repos allowed squash/rebase merging and disabled merge commits. Changing that repository setting is a maintainer decision. The visible `dev` rulesets did not list linear-history or up-to-date status-check requirements, but the legacy branch-protection endpoints returned 404; that response is not proof that no other policy applies.

The helper remains useful for the existing queue's integration with new `dev` changes, squash/rebase recovery, conflict isolation, exact combined-preview validation and leased fork updates. It is not an extra GitHub merge gate. Its current `Check`/`Publish` modes deliberately require a refreshed `dev` base; enabling merge commits does not silently change that implementation or make an old preview current. Use ordinary GitHub merging when its checks and dependencies permit it, and use the helper when preparing a current composed candidate. There is no need to run Sync merely to let a maintainer click Merge.

The normal long-term path is a short queue: finish the current review sequence, then start each independent change from fresh `dev`. Keep only real dependencies stacked. Retain the exact built source and existing rollback; a documentation or history-only change with the same source tree needs no application rebuild.

The My Atlas phase is one feature PR, web #97 after #95. It reused the published tip without rebasing earlier parents; source, checks and recovery are recorded in [the My Atlas handoff](app_documentation/my-atlas-20260929.md).

## Working loop

1. Refresh issues, review feedback and the [roadmap](ROADMAP.md). Choose one logical API, page or correction.
2. Start an isolated feature worktree. After the old queue has merged, Start uses freshly fetched `dev` and performs no rebase or build. If a pending stack exists, Start uses its published tip and reports the dependency; use Check to verify that queue's current validation state.
3. Follow each repository's contribution rules. Prefer existing components and feature-owned files; keep shared startup/router/navigation changes in a declared order.
4. Build and test the change, open its PR against `dev`, then record its exact parent, head, fork branch and worktree in the manifest. Link the parent-to-head comparison in the PR body.
5. Keep current Beacon contribution PRs out of draft as requested by the contributor, with dependencies visible. Request MrAlders0n's review; if account permissions prevent formal assignment, use an explicit review-request comment instead.
6. Keep cross-repository rollout order explicit: deploy a required server API before its web consumer. Development previews may compose declared review candidates; maintainers decide acceptance and production release. Ready for review does not imply ready to merge.
7. After merges, inspect status and the remaining dependencies. For a refreshed composed preview or history repair, run Sync and Check once for the queue. GitHub review/merge does not require this script. Rebuild/redeploy only if the composed source changes, preserving the actual running revision and corresponding-source offer.

A source conflict still needs review. The helper automates routine history movement; it does not promise that overlapping edits can never conflict, merge upstream PRs, deploy services, or create scheduled jobs.

## Current integration example

The September 29 review pass preserves the accepted dev bases and updates each affected server PR through the existing helper. Two authored merges kept both the new observer documentation and route section, and both query groups in queries.sql. SQLc/Swagger outputs were regenerated. Server #166/#184 remain independent; the ordered chain is #167 -> #169 -> #172 -> #174 -> #176. Web #95 is a new child of #92; none of the nine existing web parents needed rebasing.

Both full-stack Check commands pass for all seventeen actual application heads. The Pi runs server a35cba1d / web e1133ab5 with validated database repair/rollback and 940 web tests. See [current heads and evidence](app_documentation/review-release-20260929.md). All candidates are out of draft; requested-change reviews still need maintainer re-review.

Merge commits remain disabled and contributor permission remains READ. A maintainer must enable that repository option. No helper algorithm or repository policy changed in this phase. Continue from fresh dev after acceptance and stack only real dependencies.

## Setup

Requires Python 3.10+, Git and an authenticated GitHub CLI. Server validation needs Go and Swag; web validation needs Node/npm. Use the repository's pinned dependency/toolchain requirements.

Clone the application repositories with `origin` pointing at MeshCore-Beacon and a contribution remote pointing at your fork. The helper checks both identities before work. Keep local manifests, logs and isolated worktrees in a workspace outside the docs checkout, for example:

```text
workspace/
  beacon-server/
  beacon-web/
  planning/
    review-stack.json
    review-stack-web.json
  evidence/
  worktrees/
```

Copy [the server template](tools/review-stack.example.json) and [web template](tools/review-stack-web.example.json) into `planning/`, replacing the account/fork names. Paths may be absolute or relative to `--workspace`. Start with an empty `entries` list when no contribution queue exists.

```bash
python tools/beacon_stack.py status --workspace /path/to/workspace
python tools/beacon_stack.py start --workspace /path/to/workspace --branch codex/next-change
python tools/beacon_stack.py sync --workspace /path/to/workspace
python tools/beacon_stack.py check --workspace /path/to/workspace
```

Add `--project web` for the web queue. `--manifest` and `--state` select explicit files/directories when needed. Start writes its exact parent/worktree to `evidence/review-stack/started.json` (or the web equivalent); it does not automatically create a PR or invent a manifest entry.

An entry records the feature's delta boundary, not a guessed merge base:

```json
{
  "pr": 123,
  "branch": "codex/my-feature",
  "base": "EXACT_PARENT_COMMIT",
  "head": "CURRENT_LOCAL_COMMIT",
  "remote_head": "CURRENT_PUBLISHED_COMMIT",
  "worktree": "worktrees/my-feature"
}
```

`remote_head` is the lease protecting someone else's newer work. Never overwrite it to suppress a mismatch. Review external changes before updating the manifest.

If a maintainer lands several stacked PRs in one squash and closes the included parent, the helper deliberately stops. Verify the closed head is an ancestor of the accepted child, compare that child's tree with the upstream squash, and retain the maintainer's disposition link. Then remove only the verified included entry from the active manifest and run Sync. Do not reopen it or override a closed-state check without that evidence. Web #52 included by #53 is the first recorded example.

## What Sync actually does

- Reads current `dev` and PR state, drops merged parents and rejects unexpectedly changed or unmerged-closed PRs.
- Replays only each pending feature's declared delta in an isolated worktree. Existing dirty work is preserved.
- Regenerates generated-only server Swagger conflicts. Authored source conflicts stop with the worktree intact; it never blindly chooses a source-code side.
- Reuses local validation only for the same entire Git tree, tool versions, platform and effective build settings. Changed inputs run the repository checks. Real PostgreSQL, browser and native/device evidence remain separate requirements.
- Rechecks upstream and PR state immediately before publishing, including after a long validation run. If a merge happened meanwhile, it stops and retains reusable receipts.
- Publishes changed fork branches atomically with explicit leases, verifies remote heads and reports current CI separately.

`refresh` prepares without pushing; `publish` publishes a prepared result after fresh checks. `sync` combines both. `check` requires current published heads and passing required checks for the ordered queue **and every active independent preview PR**; only explicitly configured skipped jobs are allowed. A passing build is required for each. The helper rechecks source/merge state after reading CI and stops if it observes a changed head or merge state.

Local validation reuse does not suppress GitHub's checks on a changed head. The first refresh after an independent change joins several candidates can require new combination checks; later identical-tree refreshes reuse those receipts.

## Preview records and independent work

Set `preview.server_tree` to the verified composed Git tree only after native/public validation. This field is also used in the web manifest for compatibility. A different commit with an identical tree does not require rebuilding or relabeling an existing artifact. Keep the real built revision/source archive.

Independent pending work can be listed in `preview_overlays` as `{"pr": 123, "head": "EXACT_COMMIT"}`. Use full 40-character commit IDs and list each PR only once, outside the ordered queue. Status lists the active overlays; Check includes their CI results, marked `preview_overlay: true`. Merged overlays drop automatically; changed, unmerged-closed, wrong-fork or wrong-target overlays stop the workflow. Keep overlapping changes in the main ordered queue.

Refresh records the exact independent inputs in its prepared plan and verifies them after local validation. Publish rechecks them immediately before pushing. If an overlay moved, merged or was added/removed after preparation, refresh again; unchanged source still reuses validation. Prepared files made by older helper versions without an overlay snapshot must be refreshed when active overlays exist. This does not require rebasing unrelated PRs or rebuilding an identical preview.

Legacy bare commit overlays can still be composed, but Status marks them unverified and Check refuses to report a complete green result without a PR/head record. Standalone tools that are not part of the app preview, such as the backup-verifier CLI, retain their separate manifests/checks.

After all queued changes merge, Sync leaves an empty queue. Start then creates the next branch directly from current `dev`. This is the normal path for a new phase, without carrying historical feature commits forward.

## Optional site guard

The helper always requires clean, isolated feature branches, matching remotes and unchanged publication inputs. Operators with an additional repository guard can set `guard_script` in the local manifest, supply `--guard-script /path/to/guard.ps1`, or set `BEACON_GUARD_SCRIPT`. A manifest guard takes precedence; a configured missing or failing guard stops work. The hook receives Preflight/Finish, repository and receipt arguments through PowerShell.

The Canadaverse workspace keeps its required site guard in the local wrapper. Public examples contain no private host, key, credential or workstation path.

## Validate the helper

```bash
python -m unittest discover -s tools -p test_beacon_stack.py -v
```

Tests cover squash/drop-parent behavior, a fresh phase after all merges, cache reuse, environment changes, independent overlay CI/state/identity checks, missing or pending checks, skipped-job policy, publication races, dirty/default-branch rejection, source conflicts and upstream movement during validation. They use disposable local Git repositories and no GitHub or Pi credentials.

## Document encoding

Markdown is UTF-8. Read and write it with an explicit UTF-8 encoding in scripts, especially when moving between Windows tools. Check both the diff and rendered text before publication. Keep numeric ranges as en dashes and dependency arrows as arrows; do not round-trip the document through a legacy Windows code page.

## 1.3.2 release cut

Keep the active web manifest through #99 and keep Atlas #97 in a separate post-release manifest. Refresh the entire declared dependency sequence after review edits; publish with the recorded remote heads, then check the actual published revisions. The Atlas manifest can include the verified release parents to reuse identical-tree receipts, but must not change the active preview composition. Build and publish the release web archive without Atlas, preserve the prior archive/assets and browser-local saved cards, and keep Atlas based on the release tip for the owner's next phase.

The bounded border snapshot tool is independent of the stack helper and never deploys or changes configuration. The contributor CI runs all `test_*.py` files, including the stack safety checks and exact-member/null/invalid-polygon coverage (26 tests at this checkpoint).

The rebuild comparison now uses `preview.web_tree` for web source and `preview.server_tree` for server source, retaining the older field as a fallback. This prevents a web history-only refresh from comparing against the backend tree and asking for an unnecessary Pi rebuild. The actual deployed revision and source archive stay unchanged when the source tree matches. The release web refresh was verified to report no rebuild.
