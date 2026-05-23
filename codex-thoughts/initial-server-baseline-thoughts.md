# Initial tower-server Baseline Thoughts

Reviewed baseline: `MeshCore-Tower/tower-server` at commit `57cfdbb` (`small readme update`)

This document captures Codex's first read of the refreshed backend repository. It is not a code review on a specific PR. It is a working baseline for future PR comments, implementation planning, and design-alignment checks.

## Current Shape

`tower-server` has moved beyond a placeholder repo. It now contains a real Go backend skeleton and several early implementation slices:

- Go service entrypoint in `cmd/tower/main.go`.
- Postgres schema in `db/migrations/001_schema.sql`.
- sqlc query source in `db/queries/queries.sql` with generated code in `db/sqlc`.
- A concrete store wrapper in `db/store.go`.
- MQTT ingest worker in `internal/ingest`.
- WebSocket hub and handler in `internal/hub` and `internal/ws`.
- REST router and handler stubs in `internal/api`.
- YAML config loading and seed logic in `internal/config`.
- Channel key lookup in `internal/keystore`.
- Docker Compose with app, Postgres, Redis, and Caddy services.

I ran `go test ./...` locally after the Go tool downloaded the declared `go1.26.1` toolchain. All packages compiled successfully. There are currently no test files.

## Strong Alignment With The Design

Several core design choices are already represented in the code:

- The service is a single Go process that wires ingest, persistence, REST, and WebSocket fanout.
- The schema preserves the packet vs observation split.
- The schema includes IATAs, regions, nodes, observers, node short IDs, channel messages, and materialized views.
- MQTT ingest uses `github.com/meshcore-go/meshcore-go` for packet decode and packet hash computation.
- Packet observations are inserted with conflict handling for duplicate deliveries.
- Status and packet topics are split in the ingest path.
- Role 2 privacy intent is visible: `/internal` is not handled in dispatch.
- IATA and region REST endpoints are implemented.
- Most v1 endpoint families are at least routed, which gives the project a visible API surface to fill in.
- WebSocket hello, subscribe, ping/pong, and event fanout are scaffolded.

The repo is broadly heading in the direction described by the high-level design and Golden Reference Kit.

## Important Gaps To Track

These are not criticisms of the initial work. They are the areas I should watch carefully in future PRs because they touch Tower's core promises.

### Path resolution is not yet design-complete

The design requires ordered per-hop resolution states:

- `high`
- `ambiguous`
- `none`

The current store method returns only a distinct list of node UUIDs for all path hashes in a packet. That loses hop order and ambiguity information. It also makes it hard to tell whether every hop resolved with high confidence.

Future path work should return one result per hop, preserving order and confidence state. The API/UI can then honestly show candidates or raw unresolved hash bytes.

### Capability inference needs stricter gates

The design says firmware capability inference should happen only when:

- The observation insert succeeded.
- `hash_size` is greater than 1.
- There are no duplicate hash prefixes inside the same path.
- Every hop resolves to exactly one node.

The current scaffolding runs capability detection from the resolved node ID list. Because the resolver does not yet return per-hop confidence, capability inference cannot yet enforce the "all hops high-confidence" rule.

This should be tightened before relying on `supports_multibyte_paths`, `supports_multibyte_traces`, or `min_firmware_version` in UI or operator decisions.

### Node short IDs appear defined but not populated

The schema and generated sqlc code include `node_short_ids` and `UpsertNodeShortID`. The current advert side effect appears to upsert the node and node-IATA association, but I did not see the short ID insert wired through the store interface.

Path resolution depends on these short IDs. A future PR should explicitly populate `node_short_ids` from advert public keys and include tests proving the prefixes are available for 1, 2, 3, and 4 byte lookup.

### WebSocket backpressure is scaffolded, not complete

The hub has bounded buffers, which is good. The design requires that slow clients receive a `lagged` event and then recover through REST with `afterId`.

Current behavior logs and drops a queued event when a client send buffer is full. I did not see a real `lagged` event emitted to the client, and REST backfill endpoints are still stubs.

This should remain a design gate for declaring WebSocket behavior complete.

### REST is only partially implemented

Implemented:

- `GET /api/v1/iatas`
- `GET /api/v1/iatas/{iata}`
- `GET /api/v1/regions`
- `GET /api/v1/regions/{regionId}`

Routed but returning `501`:

- packets
- nodes
- observers
- channels
- stats

This is a reasonable early state, but future frontend work should avoid depending on contract details that are not backed by server code yet.

### Telemetry history is in schema but not wired

`observer_telemetry` exists in the migration. Status ingest updates latest observer fields and emits an `observerStatus` event, but I did not see time-series telemetry insertion wired yet.

Observer detail charts will need this before they can match the design.

### Deployment files need a pass

Two immediate deployment mismatches stood out:

- `docker-compose.yml` mounts `./Caddyfile`, but I did not see a `Caddyfile` in the repo.
- `go.mod` declares Go `1.26.1`, while the Dockerfile uses `golang:1.23-alpine`.

Both are easy to fix, but they should be handled before using Compose as a release confidence check.

## Suggested Near-Term PR Sequence

For `tower-server`, I would keep the next PRs narrow and testable:

1. Health/readiness and deployment sanity
   - Add `/healthz` and `/readyz`.
   - Add or adjust Caddyfile reference.
   - Align Docker Go version with `go.mod`.
   - Smoke test Compose boot.

2. Path resolution foundation
   - Populate `node_short_ids` from adverts.
   - Return ordered hop results with `high`, `ambiguous`, and `none`.
   - Add unit tests for no match, ambiguous match, and high-confidence match.

3. Capability inference hardening
   - Skip hash size 1.
   - Detect duplicate hash prefixes within one path.
   - Only infer when every hop is high-confidence.
   - Test regular 2/3 byte and trace 2/4 byte cases.

4. REST packet backfill
   - Implement packet list/detail enough to support WebSocket recovery.
   - Add `afterId` behavior.
   - Match camelCase, epoch milliseconds, and hex byte strings.

5. WebSocket backpressure completion
   - Emit real `lagged` events.
   - Include the last observation ID needed for REST recovery.
   - Add slow-client tests.

## Test Baseline To Add

There are no tests yet, so the first tests should protect Tower's core invariants rather than broad coverage for its own sake:

- Topic parser accepts valid `meshcore/{IATA}/{pubkey}/packets` and rejects malformed topics.
- `/internal` messages are ignored.
- Duplicate packet observations are not inserted twice.
- Advert creates or updates node, node-IATA, and node short IDs.
- Path resolver returns ordered `none`, `ambiguous`, and `high` states.
- Capability inference never runs for ambiguous paths.
- Group text with unknown key stores channel activity without exposing key material.
- WebSocket slow client receives `lagged`.
- API responses use camelCase and epoch milliseconds.

## Review Posture For Future PRs

When reviewing `tower-server`, I should be strictest about:

- Privacy boundaries.
- Path truth and ambiguity.
- Packet vs observation data modeling.
- Firmware inference gates.
- WebSocket recovery semantics.
- Public API contract shape.
- Deployment claims matching actual files.

I should be more flexible about:

- Internal package layout while the service is young.
- Names that are local-only and not part of the API contract.
- Temporary 501 handlers when they are clearly marked and not claimed as implemented.

## Bottom Line

The backend is moving in the right direction and already encodes many of Tower's design decisions. The main risk is not overall architecture; it is prematurely treating scaffolded behavior as complete. The next backend PRs should turn the path-resolution, capability-inference, WebSocket recovery, and REST contract scaffolds into tested behavior.

