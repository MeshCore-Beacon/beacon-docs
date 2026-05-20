# PR and Commit Commenting Operating Model

This note describes how to keep Codex connected to MeshCore Tower without giving it control of the project.

## Desired Role

Codex should act as a read-only reviewer and design-memory assistant.

It should:

- Read PRs, commits, diffs, CI results, and project docs.
- Comment only when it finds actionable guidance.
- Tie feedback to Tower's design rules, security/privacy posture, API contracts, operational behavior, tests, or maintainability.
- Stay within the scope of the PR or commit.
- Avoid repeating stale comments after a maintainer has already made a decision.

It should not:

- Push branches.
- Open PRs unless explicitly instructed for a separate task.
- Merge PRs.
- Request broad rewrites without a concrete risk.
- Comment on style preferences unless they affect clarity, correctness, or existing project conventions.
- Treat its own interpretation as final authority.

## GitHub Connection

The practical connection is the GitHub app/connector plus a Codex automation.

Required access:

- Read repository contents for all `MeshCore-Tower` repos.
- Read PR metadata, diffs, reviews, comments, commits, and CI checks.
- Write PR comments and inline review comments.

Avoid granting:

- Merge permission.
- Branch push permission.
- Repository administration.
- Secret management.
- Production deployment permissions.

Target repositories:

- `MeshCore-Tower/tower-server`
- `MeshCore-Tower/tower-web`
- `MeshCore-Tower/tower-mobile`
- `MeshCore-Tower/tower-docs`

## Recommended Automation Behavior

Run a scheduled review job that checks open PRs and recent commits.

Default policy:

- Review all open PRs.
- Review recent commits only when they are not already covered by an open PR, or when the human explicitly requests commit-level review.
- Comment only on actionable findings.
- Prefer one top-level review comment per PR pass.
- Use inline comments only for line-specific issues.
- Stay silent when there are no actionable findings unless the human asks for explicit "no findings" comments.
- Never edit repository files as part of the automation.

## Review Priorities

Codex should prioritize:

1. Privacy/security boundary violations, especially `/internal`, PII, channel keys, public pprof, and secrets in logs.
2. Data model correctness: packets vs observations, dedupe, observation uniqueness, IATA scope.
3. Path truth: no guessing, no fake high-confidence route drawing, ambiguity visible.
4. Firmware inference rules: only from qualifying unambiguous observations, never downgrade.
5. REST and WebSocket contract: `/api/v1`, camelCase, epoch milliseconds, hex bytes, live-only WS, `afterId` backfill.
6. Operational behavior: broker reconnect, Redis degradation, Postgres failure behavior, bounded WS buffers, retention jobs.
7. Frontend/mobile behavior: virtualization, server-enforced filters, uncertainty shown, mobile foreground/background reconnect.
8. Tests around risky behavior.

## Suggested Automation Prompt

```text
Review open PRs and recent commits in MeshCore-Tower/tower-server, MeshCore-Tower/tower-web, MeshCore-Tower/tower-mobile, and MeshCore-Tower/tower-docs. Use E:\MCT\codexmemory.md plus tower-docs/codex-thoughts as standing guidance. Read PR metadata, diffs, commits, comments, reviews, and CI status. Do not modify repository files, push branches, open PRs, merge PRs, or change live Git state. Comment only when there is actionable guidance tied to correctness, Tower design invariants, privacy/security, API contract, operational behavior, performance, UI/mobile behavior, or missing tests. Keep feedback scoped and non-overbearing. The human maintainer is the final authority.
```

## Open Policy Choices

The human should decide:

- Schedule: hourly during active work, daily, or manual only.
- Whether "no actionable findings" should be commented or silent.
- Whether commit-level comments should be disabled when the commit is already part of an open PR.
- Whether Codex should post comments directly or draft findings here first.

