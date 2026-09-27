# Contributor workflow

Use this workflow to keep small Beacon changes reviewable while reducing manual branch maintenance. The executable helper is [tools/beacon_stack.py](tools/beacon_stack.py); a CI workflow is included for its [offline regression tests](tools/test_beacon_stack.py).

## Working loop

1. Refresh issues, review feedback and the [roadmap](ROADMAP.md). Choose one logical API, page or correction.
2. Start an isolated feature worktree. After the old queue has merged, Start uses freshly fetched `dev` and performs no rebase or build. If a pending stack exists, Start uses its published tip and reports the dependency; use Check to verify that queue's current validation state.
3. Follow each repository's contribution rules. Prefer existing components and feature-owned files; keep shared startup/router/navigation changes in a declared order.
4. Build and test the change, open its PR against `dev`, then record its exact parent, head, fork branch and worktree in the manifest. Link the parent-to-head comparison in the PR body.
5. Keep current Beacon contribution PRs out of draft as requested by the contributor, with dependencies visible. Request MrAlders0n's review; if account permissions prevent formal assignment, use an explicit review-request comment instead.
6. Keep cross-repository rollout order explicit: a new web page waits until its server endpoint is merged **and deployed**. Ready for review does not imply ready to merge.
7. After merges, run Sync and Check. Rebuild/redeploy the preview only if the composed source changes, preserving the actual running revision and corresponding-source offer.

A source conflict still needs review. The helper automates routine history movement; it does not promise that overlapping edits can never conflict, merge upstream PRs, deploy services, or create scheduled jobs.

## Current integration example

The 27 September refresh moved #166 independently and #167 -> #169 together onto accepted server #170. Route evidence #172 then follows #169; its web consumer #85 follows #83. The Pi composition includes every current candidate. Refresh/Publish/Check handles this ancestry once; source conflicts still require review. A history-only change with an identical tree still needs no Pi rebuild.

Current preview is server `99e623c5` / web `3b3abdcc`, validated natively and publicly. The route API must be deployed before its UI. Rollback retains the previous schema040 database plus previous web assets. Follow the [roadmap](ROADMAP.md) for current issues, evidence boundaries and the next navigation slice.

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
