# Staged Roadmap

The map should reach parity in small PRs because the server and frontend are
changing quickly and multiple people are working in the repos.

## Stage 1: Static Map Foundation

- Add `GET /api/v1/map/state`.
- Add MapLibre GL JS and OpenFreeMap to `tower-web`.
- Render nodes, observers, and empty routes from Tower state.
- Fit to visible data once when the selected IATA changes.
- Add compact layer toggles.
- Keep Live off by default.

## Stage 2: Confidence-Correct Routes

- Replace flattened path resolution with ordered per-hop results.
- Store or derive route-safe observations only from all-high paths.
- Add route edges to `/api/v1/map/state`.
- Render passive route lines with no click-stealing.
- Add route-focused tests for ambiguous and unresolved paths.

## Stage 3: Inspection And Topology Tools

- Add node/observer detail drawer.
- Add route and neighbor highlighting.
- Add searchable reachable-node phonebook.
- Add Busy Pathways from recent high-confidence route activity.
- Add route plotting by selected endpoints or map corners.

## Stage 4: Live Layer

- Add map-safe live event payloads if the existing WebSocket packet event stays
  too slim.
- Convert high-confidence live observations into packet comets and route glows.
- Convert observer-only observations into observer auras.
- Add payload/channel filters.
- Throttle and drop frames under load.

## Excluded

VCR playback, scrub bars, replay mode, and historical animation are not part of
Tower map parity.
