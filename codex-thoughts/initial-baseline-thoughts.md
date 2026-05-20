# Initial Baseline Thoughts and Suggestions

Date: 2026-05-20

This is Codex's first baseline read on MeshCore Tower after reviewing the high-level design, the Golden Reference Kit, and the current local repositories.

These notes are advisory. They are meant to help review and planning, not to replace human decisions.

## Current Baseline

The project has a strong design center:

- Tower is a real-time MeshCore packet analyzer and observer-of-observers.
- V1 is intentionally compact: one Go binary for MQTT ingest, decode, REST, and WebSocket fanout.
- Postgres is durable truth, Redis plus in-memory LRU are hot-read acceleration, and Caddy is the edge.
- WebSocket is live-only. REST is history and recovery.
- IATA is the primary geography anchor.
- Path ambiguity is not a UI inconvenience to hide; it is real mesh information to show honestly.
- Privacy boundaries are clear: Role 2 MQTT subscriber for v1, no `/internal`, no owner PII, no public pprof.

The local repos are currently starter shells:

- `tower-server`: backend/server stack placeholder.
- `tower-web`: web frontend placeholder.
- `tower-mobile`: mobile frontend placeholder.
- `tower-docs`: documentation placeholder plus this `codex-thoughts` folder.

That means the project is at a useful moment to lock down contracts and review habits before implementation inertia sets in.

## Main Suggestion

Make `tower-docs` the shared source of truth early.

The source design and Golden Reference Kit currently live outside the repos on the local machine. That is fine for handoff, but the team will work better if the important durable parts are promoted into `tower-docs`:

- Project charter.
- System architecture.
- Data model reference.
- Ingestion and path resolution rules.
- API and WebSocket contract.
- Security and privacy rules.
- Development flow and PR sequence.
- ADRs for major choices.

This keeps all agents and humans aligned without depending on files from one workstation.

## Cross-Repo Contract Risk

The Golden Reference Kit suggests a monorepo-shaped layout, while the GitHub organization currently has separate repos for server, web, mobile, and docs.

That split can work, but the contracts need to live somewhere central:

- OpenAPI seed and REST response schemas.
- WebSocket message schemas.
- Error shape.
- Time and byte encoding rules.
- Config schema.
- Shared terminology for packet, observation, observer, node, IATA, region, path confidence, and firmware tier.

Recommendation: keep canonical contracts in `tower-docs`, then let each repo consume or copy generated artifacts as needed. Avoid letting each repo invent its own version of the same contract.

## Suggested First Implementation Sequence

Use small PRs that match the Golden Reference Kit:

1. `tower-server`: skeleton, config loader, health endpoints, DB/Redis connections, Docker Compose, Caddy reference.
2. `tower-server`: MQTT client manager, topic parser, observer/IATA upserts, packet decode wrapper, packet/observation writes.
3. `tower-server`: advert handling, node short IDs, path resolver, ambiguity states, firmware inference.
4. `tower-server`: REST API and WebSocket hub with bounded buffers and `afterId` backfill.
5. `tower-web`: dashboard, live packets, expanded packet row, analyzer drawer, node map/list, observers, stats.
6. `tower-mobile`: API client, WebSocket lifecycle, foreground/background reconnect and REST backfill.
7. All repos: load tests, contract tests, redaction checks, docs, release checklist.

Server first is important because web and mobile should not guess at contracts that the backend has not proven.

## Design Rules to Defend in Review

These should be treated as high-signal review checks:

- No `/internal` subscription in v1.
- No owner PII in public API responses, logs, or UI.
- No channel key material returned by APIs or logged.
- Packets and observations remain separate concepts.
- Packet hash dedupe and observation uniqueness are both enforced.
- Path resolution is scoped by observer IATA or explicit super-region IATA set.
- Ambiguous paths are never drawn or described as high-confidence.
- Firmware inference only happens from qualifying, unambiguous observations and never downgrades.
- WebSocket remains live-only and does not grow per-client replay state.
- `lagged` events lead to REST backfill with `afterId`.
- Filters are server-enforced.
- UI remains responsive under large packet volumes through virtualization and bounded live updates.

## Repo-Specific Suggestions

### `tower-server`

Start with boring, observable infrastructure:

- Config/env loader before feature code.
- Health and readiness endpoints before MQTT ingest.
- Migration runner and schema tests before business logic.
- Topic parser tests before broker integration.
- Fake MQTT fixtures before live broker dependence.
- Logging redaction rules before secrets enter logs.

The packet pipeline is the highest-risk area. It should have tests for duplicate observations, malformed payloads, adverts, ambiguous paths, high-confidence paths, and firmware inference.

### `tower-web`

Do not build a marketing surface first. Build the operator experience:

- Live packets list.
- Expanded packet rows.
- Analyzer drawer.
- Nodes and observers.
- Stats.

The UI should be dense, calm, and operational. It should show uncertainty clearly instead of smoothing it over.

### `tower-mobile`

Mobile can follow once backend contracts stabilize.

The critical behavior is lifecycle correctness:

- Open WebSocket on foreground.
- Close gracefully on background.
- Reopen and re-subscribe on foreground return.
- REST backfill active screen data from last seen ID.

### `tower-docs`

This repo should hold:

- Stable design rules.
- API and WebSocket contracts.
- ADRs.
- Review checklists.
- Release readiness checklists.
- Cross-repo decisions.

If a design choice affects multiple repos, it should be documented here before or during implementation.

## Suggested Early ADRs

Create ADRs for:

- Separate repos vs monorepo-shaped implementation references.
- Role 2 only for v1 ingest.
- No `/internal` subscription in v1.
- REST history plus live-only WebSocket.
- IATA-scoped path resolution.
- Config-file admin surface for v1.
- Medium-sized `packetObservation` WebSocket events with lazy detail fetch.

## Suggested Review Automation Policy

Begin conservatively:

- Prefer PR-level review over commit-level review.
- Comment only when findings are actionable.
- Stay silent on no findings unless maintainers want confirmation comments.
- Do not use admin-scoped local GitHub CLI credentials for automation.
- Prefer the GitHub app/connector with read plus PR comment permission only.
- Use inline comments sparingly for line-specific issues.
- Use one top-level comment for design-alignment summaries or test gaps.

Commit-level comments should be reserved for commits that are not part of an open PR, or cases where a human explicitly asks for commit review.

## What Codex Should Watch For

The highest-value review findings will likely be:

- A PR accidentally introduces admin/write concerns into v1.
- Backend code treats packet content and observation metadata as one row or one concept.
- Path resolver picks a candidate when there is ambiguity.
- UI draws a path that is not fully high-confidence.
- WebSocket code accumulates per-client replay buffers.
- API returns timestamps as strings or bytes as raw arrays instead of the contract.
- Mobile reconnect skips REST backfill.
- Logs include broker passwords, channel keys, or owner data.
- Tests cover happy paths but skip ambiguity, duplicate broker delivery, and slow clients.

## Open Questions for Humans

- Should `tower-docs` import the full Golden Reference Kit docs now, or should it distill them into a smaller canonical docs set?
- Should `tower-server` own generated OpenAPI artifacts, or should `tower-docs` own the source contract and server consumes it?
- Should PR review automation post directly once the GitHub connector is authorized, or draft notes first for human approval?
- Should `tower-docs/codex-thoughts` stay as a permanent notebook, or should mature notes be promoted into normal docs and then removed from this folder?

