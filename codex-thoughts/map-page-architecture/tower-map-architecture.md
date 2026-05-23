# Tower Map Architecture

The Tower map is a Tower-native feature. It should reuse CartoLive's proven
interaction model where appropriate, but all data must flow from `tower-server`
and all UI must follow the compact Tower shell.

## Rendering Stack

- Renderer: MapLibre GL JS.
- Basemap: OpenFreeMap style URL, defaulting to Liberty unless configured.
- Overlay data: GeoJSON sources owned by `src/features/map`.
- Live effects: a separate source/layer or canvas overlay, controlled by the
  Live toggle.

## Frontend Boundaries

The map feature should stay under `tower-web/src/features/map`:

- `api.ts`: fetches Tower map state.
- `types.ts`: map-specific frontend contract types.
- `geojson.ts`: pure source builders for nodes, observers, routes, and live
  overlays.
- `layers.ts`: MapLibre source and layer declarations.
- `live.ts`: safe conversion from Tower live events to map pulses.
- `MapView.tsx`: React lifecycle and controls.

The feature should not require packet-list internals. It may listen to the
shared WebSocket manager only when the Live toggle is on.

## Backend Boundaries

The map API should expose sanitized, mappable records only:

- Node UUIDs, labels, roles, coordinates, IATAs, last seen, and counts.
- Observer UUIDs, labels, type, IATA, coordinates, online state, and counts.
- Route edges only after ordered path confidence exists.
- Aggregate activity counts for panels and status.

The API must not expose full public keys, raw path bytes, packet hashes, owner
metadata, broker secrets, channel keys, or resolver debug internals.

## Route Rule

Map routes are allowed only when every hop resolves in order with confidence
`high`. Any `ambiguous` or `none` hop blocks route drawing for that observation.
The UI may show ambiguity in details later, but must not promote it into a map
edge.
