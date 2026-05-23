# API Contract Deltas

This file records map-specific API additions that extend the existing Tower API
without copying MC-CartoLive's public-state contract.

## `GET /api/v1/map/state`

Query parameters:

- `iata=YOW`: restrict map state to one IATA.
- `regionId=1`: expand the region to its member IATAs.
- Omitting both returns all mappable public state.

`iata` and `regionId` are mutually exclusive.

Response shape:

```json
{
  "serverTime": 1760000000000,
  "scope": { "iatas": ["YOW"], "regionId": 1 },
  "metadata": {
    "basemap": "openfreemap",
    "routesComplete": false,
    "routesStatus": "blocked_by_ordered_path_confidence",
    "liveDefaultEnabled": false
  },
  "nodes": [],
  "observers": [],
  "routes": [],
  "activitySummary": {
    "packets24h": 0,
    "observations24h": 0,
    "activeObservers24h": 0,
    "activeIatas24h": 0,
    "lastHeardAt": null
  }
}
```

## Route Contract Requirement

Routes must not be populated until path resolution returns one item per hop:

- hop order preserved from packet path bytes
- `confidence = high | ambiguous | none`
- candidates retained for ambiguous detail UI
- raw bytes and full public keys excluded from public map responses

Only all-high observations may produce map route edges.

## Live Contract Direction

The existing WebSocket remains the primary live channel. If the current
`packetObservation` event remains too slim for map animation, add a map-safe
event shape rather than exposing packet internals. REST remains authoritative;
WebSocket events update freshness and optional animation only.
