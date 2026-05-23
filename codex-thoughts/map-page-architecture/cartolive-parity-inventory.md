# MC-CartoLive Parity Inventory

This inventory treats MC-CartoLive as the behavior reference, not as an API or
code structure to copy directly. Tower must keep its own server contracts,
schema, privacy rules, and UI conventions.

## Stage 1: Map Foundation

- OpenFreeMap basemap rendered through MapLibre GL JS.
- Full-viewport operational map inside the existing Tower shell.
- Mappable nodes from Tower server only.
- Mappable observers from Tower server only.
- Initial fit to data once per selected region or IATA.
- No auto-zoom on new packet traffic.

## Stage 2: Static Topology

- Low-zoom node clustering.
- High-zoom node and observer points.
- Node and observer hover/click inspection.
- Role/type filters.
- Stale or offline visual states.
- Passive route lines only when Tower can prove every hop is high confidence.

## Stage 3: Operational Panels

- Busy Pathways summary.
- Reachable-node phonebook.
- Route highlighting from a selected node.
- Plot routes between node endpoints or map points.
- Compact panel restore behavior for mobile and dense desktop use.

## Stage 4: Live Layer

- Master Live toggle defaults off.
- Packet comets, route glows, observer auras, and message bubbles render only
  when Live is enabled.
- Payload and channel filters apply before animation.
- Events may be dropped or throttled under load.
- VCR playback, scrubbing, and replay are intentionally excluded from Tower.

## Not Directly Portable

- CartoLive's `/api/v1/public/state` contract.
- Public hash and path shortcuts that do not match Tower privacy policy.
- Any route rendering that relies on guessed, ambiguous, or unordered paths.
- VCR state and history playback UI.
