# MeshCore Tower Map Page Architecture

This folder tracks the staged map-page implementation plan for MeshCore Tower.
The target is MC-CartoLive feature parity where it fits Tower, but with Tower's
own backend contracts, privacy boundaries, IATA scoping, and path-confidence
rules.

The first implementation slice is intentionally small:

- MapLibre GL JS renders the browser map.
- OpenFreeMap provides the default basemap style and tiles.
- `tower-server` owns all mesh state through Tower-native API contracts.
- Live traffic overlays stay behind a master Live toggle and default off.
- Routes remain empty until ordered per-hop path confidence is complete.

## Documents

- `cartolive-parity-inventory.md` lists CartoLive behaviors and their Tower status.
- `tower-map-architecture.md` describes the Tower map shape and boundaries.
- `staged-roadmap.md` breaks parity into safe implementation stages.
- `api-contract-deltas.md` records map-specific backend contract additions.
- `live-layer-policy.md` captures the Live toggle and animation safety rules.
