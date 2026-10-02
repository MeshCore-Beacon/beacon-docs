# Beacon: API Contract

The Go server exposes one REST API namespace under `/api/v1/` and one WebSocket endpoint at `/ws`. React (web) and Flutter (mobile) consume identical endpoints. All JSON is camelCase. Times are Unix epoch milliseconds as integers (e.g. `1747668456000`), bytes are hex strings, UUIDs are stringified.

**Why epoch ms:** smaller on the wire, no timezone or parser ambiguity, no string parsing in hot paths (chart axes, sorts, comparisons), and matches the units MeshCore uses internally (uint32 Unix seconds in adverts and traces). JS `new Date(ms)` and Dart `DateTime.fromMillisecondsSinceEpoch(ms)` consume it natively.

Query params follow the same convention: `since` and `until` are epoch ms integers. `range` is a Go duration string (`24h`, `168h`, `720h`) on the endpoints that take one.

This document describes the contract and the parts that need explaining. Every request parameter and response schema is in the Swagger UI the server serves at `/swagger/index.html`.

---

## Auth

Everything under `/api/v1/` is public and read-only, except the `/api/v1/admin/` subtree.

Admin routes need the operator key, set as `auth.api_key` in `config.yaml` or `BEACON_API_KEY` in the environment (the variable wins when set, even if empty). A key shorter than 16 characters or with whitespace inside it stops startup.

```
Authorization: Bearer <key>
```

- No key configured: every admin route returns `503` with code `service_unavailable`.
- Missing or wrong key: `401` with code `unauthorized` and `WWW-Authenticate: Bearer`.
- Admin responses carry `Cache-Control: no-store`.

Send the key only over HTTPS.

## Rate limiting

On by default for `/api/v1/*` (not `/ws` or `/swagger`). Each client gets `ratelimit.requests_per_minute` (default 300) per minute, plus a one-second window capped at `ratelimit.burst` (defaults to the per-minute value). Clients are keyed by IP after the trusted-proxy step below; IPv6 clients share a budget per /64. Over the limit:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{"error":{"code":"rate_limited","message":"Request rate limit exceeded. Retry later."}}
```

`Retry-After` is 1 or 60 seconds depending on which window tripped. `ratelimit.enabled: false` turns both windows off. Counters live in the server process, so each Beacon instance counts separately.

**Client IP.** The server only accepts `X-Real-IP`, and only from a direct peer listed in `server.trusted_proxies`. `X-Forwarded-For` and `True-Client-IP` are always ignored and stripped. Behind a reverse proxy that isn't listed, every client shares the proxy's budget.

## Versioning

Path is the contract: `/api/v1/`. Breaking changes get `/api/v2/`. Backward-compatible additions just expand the existing payloads. WebSocket messages include a `type` discriminator and a top-level `v: 1` field so we can evolve in place.

## Errors

All errors use one shape:

```json
{ "error": { "code": "not_found", "message": "packet not found" } }
```

`code` is the HTTP status text in snake_case, so match on it or on the status. Codes in use: `bad_request`, `unauthorized`, `not_found`, `conflict`, `request_entity_too_large`, `unsupported_media_type`, `rate_limited`, `internal_server_error`, `service_unavailable`, `gateway_timeout`, `insufficient_storage`. The heavy stats endpoints (`series`, `signal`, `paths`, `observer-comparison`) return `503` when the query times out; try a shorter window.

A `404` means the requested thing doesn't exist. A database or other server-side failure is always a `500` (or `503` above), never a `404`, so clients can retry 5xx and treat 4xx as final. Empty lists are `200` with `[]`.

## Pagination

Most lists return a page:

```json
{ "items": [ ... ], "nextCursor": 1747665456000, "hasMore": true }
```

Pass `nextCursor` back as `cursor` for the next page; it is omitted on the last page. What the cursor holds depends on the list (a timestamp in epoch ms, or an ID), as noted per endpoint. `limit` has a per-endpoint default, must be positive, and is clamped to 200.

A few lists return a plain array instead: the backfill endpoints, `/routes*`, `/traces` and the stats endpoints.

## Common filters

Most list and stats endpoints take the same location filters:

| Param | Meaning |
|---|---|
| `iatas` | Comma-separated IATA codes, case-insensitive (`YOW,YYZ`) |
| `iata` | Single IATA, used only when `iatas` is absent |
| `region` / `regionId` | Region slug or ID; expands to its member IATAs and adds them to any `iatas`. An unknown region or malformed ID is a `400`; a failed lookup is a `500`. |
| `scope` | Transport scope name, URL-encoded (`%23bc` for `#bc`) |

---

## REST endpoints

### Packets

| Endpoint | Notes |
|---|---|
| `GET /packets` | Page of packet summaries, newest first. Default limit 50. |
| `GET /packets/{packetHash}` | Full packet with every observation. `404` if unknown. |
| `GET /packets/backfill?afterObservationId=<id>` | Packets with observations after that ID, oldest first, plain array. Default limit 100. For reconnect backfill. |

`/packets` params: `payloadType` or `payloadTypes` (comma-separated integers), `payloadTypeName` (`advert`, `group_text`, `trace`, ...; used when no number is given), `routeType` or `routeTypes`, the location filters, `scope` or `scopes` (comma-separated), `since`, `until`, `cursor`, `limit`. Filters OR within themselves and AND across each other. The cursor is epoch ms: global `lastHeardAt` order without an IATA filter, and the time heard at the requested sites when one is set, so a filtered list stays bounded to those IATAs.

`/packets/backfill` takes single `payloadType`/`payloadTypeName`, `routeType`, the location filters, `scope` and `limit`.

A packet summary:

```json
{
  "packetHash": "9e9b7d6a91cab445",
  "payloadType": 4,
  "payloadTypeName": "advert",
  "routeType": 1,
  "routeTypeName": "FLOOD",
  "scope": "#bc",
  "firstHeardAt": 1747665456000,
  "lastHeardAt": 1747665462000,
  "observationCount": 15,
  "latestObserver": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "displayName": "FlightlessDt",
    "iata": "KEH",
    "pathLength": { "raw": "41", "hashSize": 2, "hopCount": 1 },
    "pathBytes": "ae9b"
  },
  "summary": "WW7STR/PugetMesh Cougar"
}
```

`summary` is the advert name, `ACK <checksum>`, `TRACE <tag>` or `PING <tag>`, and is omitted for other types. `scope` is the matched transport scope, omitted when none. `latestObserver` can also carry `resolvedSource` / `resolvedDestination` (see below).

### Packet detail

```
GET /api/v1/packets/{packetHash}
```

| Field | Type | Description |
|-------|------|-------------|
| `packetHash` | string | Content hash (hex) |
| `header` | object | `raw` (hex byte), `routeType`, `routeTypeName`, `payloadType`, `payloadTypeName`, `payloadVersion` |
| `transportCodes` | object | `regionCode`, `subRegionCode`; only on TRANSPORT_FLOOD / TRANSPORT_DIRECT |
| `originPubkey` | string | Sender public key (hex), when the payload carries one (ADVERT, ANON_REQ) |
| `parsedPayload` | object | Decoded payload; shape depends on type, see below |
| `rawPayload` | string | Payload hex, without header and path |
| `decrypted` | boolean | True when a group text was decrypted |
| `channelHash` | string | Channel byte (hex), group packets only |
| `scope` | string | Matched transport scope |
| `firstHeardAt`, `lastHeardAt` | number | Epoch ms |
| `firstToLastMs` | number | Spread between first and last observation |
| `observationCount` | number | Observations across all observers |
| `resolvedRoute` | array | TRACE only: the probed route, resolved hop by hop |
| `observations` | array | One entry per observer hearing |

Each observation:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Observation ID (use with `/packets/backfill`) |
| `observerId`, `observerName` | string | Observer UUID and display name |
| `iata` | string | Where it was heard |
| `heardAt` | number | Epoch ms |
| `pathLength` | object | `raw` (hex byte), `hashSize` (1–3), `hopCount` |
| `pathBytes` | string | Accumulated path hashes (hex). For TRACE these are per-hop SNR bytes. |
| `rssi`, `snr` | number | dBm / dB, omitted when missing |
| `propagationTimeMs` | number | Milliseconds after the packet's first observation (0 for the first) |
| `radio` | object | `freqMhz`, `spreadFactor`, `bandwidthKhz`, `codingRate`, copied from the observer |
| `sourceBroker` | string | Name of the MQTT broker it arrived through |
| `resolvedPath` | array | Per-hop resolution |
| `resolvedSource`, `resolvedDestination` | object | The packet's endpoints, for types that carry them (ADVERT by full key; REQUEST, RESPONSE, TEXT_MESSAGE, PATH and ANON_REQ by 1-byte hash) |

A resolved hop is `{ "confidence": "high" | "ambiguous" | "none", "snr": 7.25, "nodes": [ ... ] }`, with one node for `high`, several for `ambiguous` and none for `none`. Each node is `{ id, name, publicKey, latitude, longitude }` (`publicKey` is the prefix that matched). Resolution is empty on a fresh database until adverts have taught the server which nodes exist.

#### parsedPayload by type

Every shape has `type` and `raw` (payload hex). `type` uses the upper-case names below, which differ from the lower-case `payloadTypeName` in the header.

| `type` | Fields |
|---|---|
| `ADVERT` | `publicKey`, `timestamp` (uint32 seconds), `signature`, `appData` |
| `REQUEST`, `RESPONSE`, `TEXT_MESSAGE`, `PATH` | `destinationHash`, `sourceHash` (1 byte hex), `cipherMac`, `ciphertext`, `ciphertextLength`, `decrypted` |
| `GROUP_TEXT`, `GROUP_DATA` | `channelHash`, `cipherMac`, `ciphertext`, `ciphertextLength`, `decrypted` |
| `ANON_REQUEST` | `destination` (byte as a number), `ephemeralPubKey` (sender key, hex) |
| `TRACE` / `PING` | `traceTag` (hex), `authCode`, `flags`, `pathHashes` (hex per hop), `snrValues` (dB per hop). `PING` is a trace with one hop. |
| `ACK` | `checksum` (4 bytes hex) |
| `MULTIPART` | `remaining`, `wrappedType`, `wrappedPayload` |
| `DISCOVER_REQ` | `prefixOnly`, `typeFilter` (bitmask), `tag` (hex), `since` (seconds, omitted when unset) |
| `DISCOVER_RESP` | `nodeType`, `nodeTypeName`, `requestSnr` (the responder's reading of the request), `tag`, `pubKey`, `pubKeyPrefixOnly` |
| `CONTROL` | `flags`, `data`; other CONTROL sub-types |
| `RAW` | Anything without a decoder (e.g. RAW_CUSTOM) |

`decrypted` in `parsedPayload` is always `null` today. Decrypted channel text is served by the messages endpoints; direct messages are not decrypted.

An ADVERT payload:

```json
{
  "type": "ADVERT",
  "raw": "7e7662676f7f...",
  "publicKey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
  "timestamp": 1747665450,
  "signature": "a1b2c3d4...",
  "appData": {
    "raw": "92...",
    "flags": {
      "raw": "92",
      "deviceRole": 2,
      "deviceRoleName": "REPEATER",
      "hasLocation": true,
      "hasName": true,
      "hasFeature1": false,
      "hasFeature2": false
    },
    "latitude": 48.4284,
    "longitude": -123.3656,
    "feature1": null,
    "feature2": null,
    "name": "WW7STR/PugetMesh Cougar"
  }
}
```

Adverts with a bad signature are not decoded and have no `parsedPayload`.

### Nodes

| Endpoint | Notes |
|---|---|
| `GET /nodes` | Page of node summaries. Cursor is `lastSeen` epoch ms. Default limit 50. |
| `GET /nodes/{nodeId}` | Node detail: capability flags, `minFirmwareVersion`, `iatas` (`[{iata, lastHeard}]`), `neighbors`, clock drift for repeaters and room servers. |
| `GET /nodes/{nodeId}/observations` | Page of observations of packets the node originated. Cursor is the observation ID. |
| `GET /nodes/{nodeId}/neighbors` | Plain array of neighbours. |

`/nodes` params: `type` (1 companion, 2 repeater, 3 room server, 4 sensor) or `typeName`, the location filters, `name` (partial, case-insensitive), `scope`, `pubkey` (exact hex), `pubkeyPrefix`, `supportsMultibytePaths`, `supportsMultibyteTraces`, `neighbors` (adds `neighborIds`), `cursor`, `limit`. Summaries include `stale` (not seen within `nodes.stale_threshold`) and, when `nodes.mark_foreign` is on, `possiblyForeign`.

### Observers

| Endpoint | Notes |
|---|---|
| `GET /observers` | Page of observers. Params: location filters, `type` (e.g. `meshcoretomqtt`), `broker`, `status` (`online`/`offline`), `name`, `scope`, `cursor` (`lastSeen` epoch ms), `limit`. |
| `GET /observers/{observerId}` | Observer detail. |
| `GET /observers/{observerId}/telemetry?range=24h&interval=1h` | Telemetry history. `interval` is `1h` (default), `6h` or `24h`. `afterId` returns only newer points. |
| `GET /observers/{observerId}/activity?range=24h&interval=15m` | What the observer heard, bucketed. |
| `GET /observers/{observerId}/adverts` | Page of adverts the observer heard. Cursor is the observation ID. |

Telemetry response is a time-bucketed array suitable for direct chart consumption. `airtimeTxSecs` and
`airtimeRxSecs` are seconds of radio time as reported by the observer: cumulative since boot on
`interval=1h` points, and the per-bucket delta on `6h`/`24h`. Divide by the bucket length for a percentage.
Fields the observer did not report are omitted.

```json
{
  "range": "24h",
  "interval": "1h",
  "points": [
    {
      "t": 1747612800000,
      "batteryMv": 4180,
      "airtimeTxSecs": 13.4,
      "airtimeRxSecs": 37.8,
      "noiseFloorDb": -103.2,
      "uptimeSeconds": 86400,
      "queueLength": 0,
      "receiveErrors": 3
    }
  ]
}
```

Activity reports what an observer actually heard, bucketed over a trailing window. `range` is a Go
duration up to `720h` (default `24h`); `interval` is one of `5m`, `15m`, `1h`, `6h`, `24h`
(default `15m`). `range / interval` may not exceed 1000 buckets, sub-hour intervals (`5m`, `15m`)
additionally cap `range` at `48h`, and an unknown observer is a `404`. An optional `until` (epoch ms,
at most 30 days old) ends the window earlier.
Buckets are aligned to the clock in UTC (a `15m` bucket always starts at :00, :15, :30 or :45) and the
window start is rounded up to the next bucket boundary, so bucket starts are stable across requests.
Only non-empty buckets are returned — gaps in `points` mean the observer heard nothing in that bucket,
and the client is expected to render them as zero, except for uncovered hours (below).

Hourly intervals (`1h`, `6h`, `24h`) read the analytics rollups up to the newest complete rollup hour,
and raw observations after it, at most 24 hours back. Those responses add `rolledUntil` (end of the
newest complete rollup hour, epoch ms; omitted before the first rollup) and `rawFrom` (start of the raw
tail, epoch ms). Rollup buckets cover times before `rolledUntil` and raw buckets from `rawFrom` on.
When `rawFrom` is later than `rolledUntil` (or `rolledUntil` is missing), the rollup is more than 24
hours behind and `[rolledUntil, rawFrom)` is unknown, not quiet; show it as a gap.

`radio` echoes the observer's current radio parameters plus the preamble length the airtime maths
assumes; it is `null` when those parameters are unknown, in which case `airtimeMs` is `null` on every
bucket too (airtime cannot be costed without them). `snrAvg`, `snrMin` and `rssiAvg` are `null` for
buckets whose observations carried no usable signal readings. The `payloadTypes` counts cover the same
window and their total matches the sum of `observations` across `points`. On sub-hour intervals only,
observations with an undetermined payload type are counted in `observations` but omitted from the
breakdown; none exist within the retention window in practice.

`airtimeMs` sums only the observations that could be costed. The migration that introduced airtime
backfills the trailing 7 days, so for the first 30 days after deploy buckets older than 7 days may be
only partially costed, and observations recorded without radio parameters are never costed.

Intervals of `1h` and up are read from the hourly analytics rollups. Each UTC hour is rolled about
95 minutes after it closes, so the newest hour or two are not yet included at those intervals. Sub-hour
intervals read live observation rows and are always current. The response also reports `windowStart`,
`windowEnd`, `generatedAt`, `source` (`raw` or `hourly`) and a `summary` of recorded packets and the
last complete hour.

```json
{
  "range": "24h",
  "interval": "15m",
  "radio": {
    "freqMhz": 869.525,
    "sf": 11,
    "bwKhz": 250,
    "cr": 5,
    "preambleSymbols": 16
  },
  "payloadTypes": [
    { "payloadType": 4, "payloadTypeName": "advert", "count": 128 },
    { "payloadType": 5, "payloadTypeName": "group_text", "count": 41 }
  ],
  "points": [
    {
      "t": 1747612800000,
      "observations": 12,
      "airtimeMs": 3120.5,
      "snrAvg": 6.2,
      "snrMin": -4.5,
      "rssiAvg": -92.3
    }
  ]
}
```

### Channels and messages

| Endpoint | Notes |
|---|---|
| `GET /channels` | Channels, most recently seen first. |
| `GET /channels/{channelID}` | Channel detail by integer ID. |
| `GET /channels/{channelID}/messages` | Page of that channel's messages, newest first. |
| `GET /messages` | Page of messages across channels, newest first. |
| `GET /messages/backfill?afterId=<id>` | Messages after that ID, oldest first, plain array. Default limit 100. |

`/channels` params: `hash` (channel byte hex), `iata`/`iatas`, `keyKnown` (`true` for channels Beacon can decrypt, `false` for hash-only), `cursor`, `pageCursor`, `limit` (default 50). An IATA filter lists channels MeshMapper lists there, configured channels scoped to a region containing it, and Beacon-wide configured channels. The page adds `nextPageCursor`, an opaque string that keeps timestamp ties and precision; prefer it over the numeric `cursor` (the two can't be combined). A channel's `messageCount` is a lifetime total; packet retention does not reduce it.

Message lists take `since`, the location filters, `scope`, `cursor` (message ID) and `limit` (default 50). `/messages` also takes `channelID` or `channelHash`. A message:

```json
{
  "id": 88213,
  "packetHash": "3c4f8a12b7e60d91",
  "channelHash": "f3",
  "senderName": "Chris",
  "content": "anyone hear that trace?",
  "sentAt": 1747665450000,
  "observationCount": 8,
  "scope": null,
  "scopeStatus": "unscoped"
}
```

`sentAt` comes from the sender's clock. `scopeStatus` is `matched`, `unscoped`, `unknown` or `unavailable`.

Channel keys come from the server config file and, optionally, MeshMapper.

### IATAs, regions and scopes

| Endpoint | Notes |
|---|---|
| `GET /iatas` | All IATAs, including ones created from traffic. `[]` when there are none. |
| `GET /iatas/{iata}` | One IATA. `404` if unknown or not three letters. |
| `GET /iatas/{iata}/border` | GeoJSON Feature (Polygon or MultiPolygon, with `bbox`); `204` when the IATA has no border, `404` if the IATA is unknown. |
| `GET /regions` | Regions in display order. `[]` when none are configured. |
| `GET /regions/{regionId}` | One region with its IATAs. `400` for a non-numeric ID, `404` if unknown. |
| `GET /scopes` | Array of scope names. Location filters narrow it to manual scopes configured for a matching region and imported scopes whose MeshMapper catalogue includes a matching IATA. |
| `GET /scopes/{name}` | Scope detail (`%23bc` for `#bc`). |
| `GET /brokers` | `[{ "name", "connected" }]` per MQTT broker. |

Regions, IATA names and scopes are managed in the server config file (or imported from MeshMapper), not through the API.

### Routes

Known routes are fully resolved multi-hop paths distilled from packet history.

| Endpoint | Notes |
|---|---|
| `GET /routes` | Plain array, newest `lastSeen` first. Params: `iata`, `hopCount`, `cursor` (last item's `lastSeen`, epoch ms), `cursorId` (last item's `id`), `limit` (default 50). |
| `GET /routes/search?iata=&from=&to=` | Routes in one IATA between two node hash prefixes (hex). All required. |
| `GET /routes/cross?fromIata=&fromHash=&toIata=&toHash=` | Routes that cross IATA boundaries. All required. |
| `GET /routes/{iata}/{pathKey}/observations` | Retained reports that match a saved route exactly. `pathKey` comes from a route response. Window: `range` (default `24h`, max `720h`) or `since`+`until` (max 30 days); `pageCursor` for the next page; `limit` default 50. |

To page `/routes`, send the last item's `lastSeen` as `cursor` and its `id` as `cursorId`. Routes share a millisecond often (one batch of upserts), and `cursorId` returns the ones that didn't fit on the previous page. `cursor` alone still works but can skip those ties. `cursorId` must be a positive integer and requires `cursor`; otherwise `400`.

### Stats

```
GET /api/v1/stats/overview?iatas=YOW
GET /api/v1/stats/series?iatas=YOW&since=<ms>&until=<ms>
GET /api/v1/stats/observations?iatas=YOW&since=<ms>
GET /api/v1/stats/payload-breakdown?iatas=YOW&since=<ms>
GET /api/v1/stats/top-nodes?iatas=YOW&since=<ms>&limit=10
GET /api/v1/stats/top-observers?iatas=YOW&since=<ms>&limit=10
GET /api/v1/stats/top-advertisers?iatas=YOW&since=<ms>&limit=10
GET /api/v1/stats/top-talkers?iatas=YOW&since=<ms>&limit=10
GET /api/v1/stats/scopes?iatas=YOW&since=<ms>
GET /api/v1/stats/signal?iatas=YOW&since=<ms>&until=<ms>
GET /api/v1/stats/paths?iatas=YOW&since=<ms>&until=<ms>
GET /api/v1/stats/observer-comparison?observerA=<uuid>&observerB=<uuid>&since=<ms>&until=<ms>
GET /api/v1/stats/clock-drift?iatas=YOW&limit=10
GET /api/v1/stats/radio-presets?iatas=YOW&preset=910.525,62.5,7
GET /api/v1/stats/node-types?iatas=YOW
```

All stats endpoints accept `iatas` (comma-separated), `region` (slug) or `regionId`; a region expands to
its member IATAs. `since` and `until` are epoch milliseconds. `limit` defaults to 10 and is capped at 200.

Historical stats are read from hourly rollup tables, not raw observations. One background task rolls
each UTC hour about 95 minutes after it closes, so the newest hour or two are never included. Windows
snap down to UTC hours, and responses report the effective window. Any window can reach back
`analytics.rollup_retention` (90 days by default), independently of packet retention; `/stats/signal`
and `/stats/paths` keep their 30-day cap. Server-side details are in beacon-server's
[`docs/historical-stats.md`](https://github.com/MeshCore-Beacon/beacon-server/blob/main/docs/historical-stats.md).

Packets, adverts and messages count once per hour they were heard, however many of the requested IATAs
heard them, so a packet heard across an hour boundary counts twice (about 1%). Multi-IATA and region
filters give exact distinct counts.

Default windows: `overview` covers the 24 most recent rolled hours; `observations` and `scopes`/`top-nodes`
default to the last 7 days; `payload-breakdown`, `top-observers`, `top-advertisers` and `top-talkers`
default to the last 24 hours.

#### `GET /stats/series`

Hourly network activity for sparklines and KPI cards. `since` (inclusive) and `until` (exclusive) are
required, rounded down to UTC hours; the window may be at most the rollup retention, and `since` is
clamped to the oldest hour the rollups still hold. An empty region returns zeros, not all IATAs.

```json
{
  "since": 1747526400000,
  "until": 1747612800000,
  "revision": 4182,
  "earliestComplete": 1739750400000,
  "completeHours": 22,
  "hours": [
    {
      "hour": 1747526400000,
      "status": "complete",
      "values": {
        "observations": 1840, "uniquePackets": 412, "activeObservers": 23, "activeIatas": 4,
        "scopedPackets": 37, "activeScopes": 3, "maxPathEntries": 9,
        "snrSum": 1520.5, "snrSamples": 1802, "rssiSum": -168211, "rssiSamples": 1802
      }
    },
    { "hour": 1747609200000, "status": "missing", "values": null }
  ],
  "summary": { "observations": 40211, "uniquePackets": 9120, "...": "same fields as values" }
}
```

- `status` is `complete`, `missing` (not rolled yet) or `partial` (raw rows were deleted before the
  hour could be rolled; it never fills). `values` is `null` unless the hour is complete. Draw gaps, not
  zeros.
- `summary` covers complete hours only. Counts sum across hours; `activeObservers`, `activeIatas` and
  `activeScopes` are distinct across the whole window, so the hours do not sum to them. Averages are
  `snrSum / snrSamples` and `rssiSum / rssiSamples` (guard against 0 samples).
- `revision` changes whenever any rolled hour changes. `earliestComplete` is the first complete hour
  held, or `null`.

#### Response notes

- `overview` returns `since`/`until` for the 24 rolled hours it summarises.
- `observations` items are `{ "hour", "iata", "observationCount" }`. Distinct packet and observer counts
  do not sum across IATAs; read them from `/stats/series`.
- `top-nodes` ranks nodes by advert hearings. `TopNode` and `TopAdvertiser` carry `publicKey` (hex,
  always set) and a nullable `nodeId` (null once the node row has been deleted); key rows by `publicKey`.
- `scopes` counts packets heard since `since`. Observer and node counts are current memberships:
  observers filter by the IATA they last reported from. `hourly` splits the packet count by UTC hour.
- `signal` gives SNR/RSSI distributions and hourly trends; `paths` gives path-entry and hash-width
  distributions. Both require `since` and `until` (at most 30 days) and read hourly snapshots refreshed
  every `background.view_refresh`, so the current hour is excluded.
- `observer-comparison` counts distinct flood packets heard by A only, B only and both, over a required
  `since`/`until`. The observers must be different; an unknown one is a `404`.
- `clock-drift` lists repeaters and room servers whose last advert clock is off by more than
  `nodes.clock_drift_threshold`, worst first. It is current state, not windowed.

### Traces

```
GET /api/v1/traces?type=TRACE&scope=<name>&since=<ms>&until=<ms>
GET /api/v1/traces/{tag}
```

`/traces` reads a per-tag summary kept at ingest and also accepts `iatas`, `region` and `regionId`.
Filters apply to whole tags: `type` is `TRACE` if any packet in the tag is multi-hop and `PING`
otherwise, `scope` matches the first scope seen, and `since`/`until` match the tag's first hearing.
Counts and times always describe the whole tag.

It returns a plain array, most recently heard first, default limit 50. To page, pass the last item's
`lastHeardAt` as `cursor` and its trace tag (hex) as `cursorTag`; the tag breaks ties between traces
last heard in the same millisecond. `/traces/{tag}` is a `404` for an unknown tag.

### Admin

All under `/api/v1/admin/`, bearer key required (see [Auth](#auth)).

| Endpoint | Notes |
|---|---|
| `GET /admin/config` | Running CORS settings, whether auth is configured, and the broker count. No secrets. |
| `PUT /admin/config` | Replaces `cors.allowed_origins` until the next restart. JSON body up to 16 KiB. |
| `GET /admin/accounts`, `POST /admin/accounts` | List or create operator account records (name only; not logins). |
| `GET /admin/accounts/{id}`, `DELETE /admin/accounts/{id}` | Fetch or deactivate one. |
| `GET /admin/backup` | Streams a private `.tar.gz` of the database and saved config. Off unless `backup.enabled: true`; needs `pg_dump` in the server's runtime. One export at a time (`409`), `504` on timeout, `507` over the size limit. Contains secrets. |

Backup details are in beacon-server's
[`docs/backup-export.md`](https://github.com/MeshCore-Beacon/beacon-server/blob/main/docs/backup-export.md).

---

## WebSocket

Single endpoint at `/ws`. Bidirectional JSON messages. Subscription-based: the client tells the server what it wants, the server pushes matching events.

### Connection

```
GET /ws
```

The upgrade is checked before anything else:

- **Connect rate.** Each client IP gets `websocket.max_connects_per_minute` attempts per minute (default 10, IPv6 per /64), failed handshakes included. Over that, the server answers `429` with `Retry-After: 60` and no upgrade.
- **Origin.** A browser `Origin` must match the request's host, or one of `websocket.allowed_origins`. Anything else gets `403`. Set `allowed_origins` when the web app is served from a different host than the API.
- **Concurrent connections.** At most `websocket.max_connections_per_ip` (default 5) open sockets per IP. Past that, the socket is accepted and immediately closed with code `1013` (try again later), reason `connection limit reached`, so the browser can back off.

On connect the server sends a `hello`:

```json
{ "v": 1, "type": "hello", "serverTime": 1747665456000, "connectionId": "uuid" }
```

### Client → Server messages

All client messages have a `type` and an optional `id`, which replies echo.

**`subscribe`**: add a filter to this connection. Subscriptions are unioned: an event is sent if it matches any of them. A connection with no subscriptions gets no events.

```json
{
  "v": 1,
  "type": "subscribe",
  "id": "sub-1",
  "scope": {
    "iatas": ["YOW"],
    "regionIds": ["3"],
    "regionSlugs": ["eastern-canada"],
    "payloadTypes": [4, 5],
    "channelHashes": ["f3"],
    "events": ["packetObservation", "observerStatus"]
  }
}
```

- `iatas`, plus the member IATAs of any `regionIds` (numeric IDs as strings) and `regionSlugs`. Unknown regions are skipped.
- `payloadTypes`: numeric payload types.
- `channelHashes`: only filters `channelMessage` events.
- `events`: any of `packetObservation`, `observerStatus`, `nodeUpdate`, `channelMessage`.

Every field is optional, and an omitted field or an empty array means no filter on that dimension. `routeTypes` filters `packetObservation` events; `observerIds` filters `packetObservation` and `observerStatus`; `channelHashes` only filters `channelMessage`. The server replies with `subscribed`:

```json
{ "v": 1, "type": "subscribed", "id": "sub-1", "subscriptionId": "uuid" }
```

**`unsubscribe`**, replied to with `unsubscribed` (same fields):

```json
{ "v": 1, "type": "unsubscribe", "id": "unsub-1", "subscriptionId": "uuid" }
```

**`ping`**:

```json
{ "v": 1, "type": "ping", "id": "p-1" }
```

Server replies with `{ "v": 1, "type": "pong", "id": "p-1" }`. The server closes a connection that sends nothing for 90s, so ping every 30s.

**`configure`**: connection-wide options, separate from subscriptions. Every `configure` sets all flags to exactly the values sent, so an omitted flag turns off. All default to false.

```json
{ "v": 1, "type": "configure", "id": "cfg-1", "resolvePath": true, "includeObserverKey": false, "includeRepeats": false }
```

- `resolvePath`: `packetObservation` events carry per-hop `observation.resolvedPath`.
- `includeObserverKey`: `packetObservation` events carry `observation.observerPublicKey`.
- `includeRepeats`: also stream later hearings of a packet by an observer that already reported it, when they arrive over a new path. See below.

Server replies with `configured`, echoing all three flags:

```json
{ "v": 1, "type": "configured", "id": "cfg-1", "resolvePath": true, "includeObserverKey": false, "includeRepeats": false }
```

Malformed or unknown messages are logged and ignored; there is no error reply.

### Server → Client events

Events share one envelope and carry no `id`:

```json
{ "v": 1, "type": "event", "event": "<name>", "data": { ... } }
```

**`packetObservation`**: a new observation was stored. This is the primary live event.

```json
{
  "v": 1,
  "type": "event",
  "event": "packetObservation",
  "data": {
    "packetHash": "9e9b7d6a91cab445",
    "packet": {
      "payloadType": 4,
      "payloadTypeName": "ADVERT",
      "routeType": 1,
      "routeTypeName": "FLOOD",
      "isFirstObservation": false,
      "observationCount": 16,
      "scope": "#bc",
      "summary": "WW7STR/PugetMesh Cougar"
    },
    "observation": {
      "observerId": "uuid",
      "observerName": "NodeRunner",
      "iata": "SEA",
      "heardAt": 1747665462000,
      "rssi": -105,
      "snr": 7.2,
      "sourceBroker": "mqtt2",
      "pathBytes": "ae9bbf3c",
      "pathLength": { "raw": "42", "hashSize": 2, "hopCount": 2 },
      "propagationTimeMs": 0,
      "resolvedPath": null,
      "resolvedSource": { "confidence": "high", "nodes": [ { "id": "uuid", "name": "WW7STR/PugetMesh Cougar", "publicKey": "7e76..." } ] }
    }
  }
}
```

- `isFirstObservation: true` means the packet is new, so add a row. `false` means update the existing row's count and time, and append the observation if the packet is expanded.
- `payloadTypeName` here is the protocol name (`ADVERT`, `GRP_TXT`, `TXT_MSG`, ...), not the lower-case REST name.
- `scope` and `summary` are omitted when there is none. `resolvedSource` / `resolvedDestination` are omitted for types without endpoints.
- `resolvedPath` is `null` unless the connection set `resolvePath`. `observerPublicKey` appears only with `includeObserverKey`.
- `propagationTimeMs` is always 0 on live events. The event has no observation ID.

Connections with `includeRepeats` also get repeats, which have `packet.isRepeat: true`. A repeat is a later hearing of the packet by an observer that already reported it, arriving over a different path, for example after a repeater further out rebroadcast it. Repeats are never stored, so they don't appear in REST reads. They carry `observationCount: 0` and `isFirstObservation: false`, so don't treat them as count updates. Exact copies (the same path again, or the same hearing via another broker) are not sent. When the server is busy, repeats are dropped before any other event. Without `includeRepeats` the key is absent.

**`observerStatus`**: an observer's `/status` message was processed.

```json
{
  "v": 1,
  "type": "event",
  "event": "observerStatus",
  "data": {
    "observerId": "uuid",
    "displayName": "Hull_Hospital",
    "observerType": "meshcoretomqtt",
    "iata": "YOW",
    "online": true,
    "radio": "910.525,62.5,7",
    "scopes": ["#bc"],
    "batteryMv": 4180,
    "uptimeSeconds": 86400,
    "lastStatusAt": 1747665462000
  }
}
```

`online` is always `true` (the event means a status just arrived). `radio` is `freqMhz,bwKhz,sf`. `observerType`, `iata`, `radio` and `batteryMv` are omitted when unknown. The event is a full snapshot, not a diff.

**`nodeUpdate`**: a new advert from a node was stored.

```json
{
  "v": 1,
  "type": "event",
  "event": "nodeUpdate",
  "data": {
    "nodeId": "uuid",
    "publicKey": "7e7662676f7f...",
    "name": "YOW_Kanata",
    "nodeType": 2,
    "nodeTypeName": "repeater",
    "iata": "YOW",
    "lat": 45.3,
    "lng": -75.9,
    "isObserver": false,
    "iatas": [{ "iata": "YOW", "lastHeard": 1747665462000 }],
    "defaultScope": "#bc",
    "radio": "910.525,62.5,7",
    "possiblyForeign": false
  }
}
```

`lat`/`lng` omitted means the advert had no position (keep the one you have); `null` means the advert cleared it. `iatas` holds only the IATA that heard this advert, so merge it into what you have. `possiblyForeign` is only sent when `nodes.mark_foreign` is on. `defaultScope` and `radio` are omitted when unknown.

**`channelMessage`**: a group text was decrypted into a new message. The `data` is the same shape as a REST message (see [Channels and messages](#channels-and-messages)) plus `channelId`, without `observationCount`.

### Backpressure and reconnection

Each connection has a 256-event send buffer. When it is full, the server drops the oldest queued event, discards the new one, and queues a `lagged` notice:

```json
{ "v": 1, "type": "lagged", "droppedCount": 1, "since": 1747665440000 }
```

Each notice reports one drop; `since` is when the notice was sent. Several can arrive in a burst. Clients should treat a `lagged` notice as a gap and refresh the affected view over REST.

Reconnection is the client's responsibility. On any disconnect, the client should:
1. Reconnect with backoff (1s, 2s, 5s, 10s, 30s cap)
2. Re-issue all subscriptions and `configure`
3. Backfill over REST
4. Resume streaming

There's no replay buffer for missed events; REST is the source of truth for history. For backfill by ID:

```
GET /api/v1/packets/backfill?afterObservationId=12345&iatas=YOW&limit=100
GET /api/v1/messages/backfill?afterId=88213&limit=100
```

`channelMessage` events carry the message `id`, so `afterId` is the last one seen. `packetObservation` events carry no observation ID; packet summaries (including `/packets/backfill` results) don't either. Observation IDs come from packet detail, `/nodes/{id}/observations` and `/observers/{id}/adverts`, so in practice the simplest recovery is to re-fetch the first page of `/packets`.

---

## Mobile-specific concerns

Flutter on iOS background suspension and Android battery saver will kill the WebSocket. Pattern for the mobile app:

1. On foreground: open WS, subscribe.
2. On background: close WS gracefully (don't fight the OS).
3. On return to foreground: reopen, re-subscribe, and fire a REST refresh on whatever screen is active to backfill anything missed.

The protocol doesn't need to know about backgrounding; the client just treats reconnection as the recovery mechanism.

---

## Open questions

- **packetObservation payload size.** With `resolvePath` on, events carry the full resolved path with node coordinates, which can be 1-2 KB each in heavy traffic. Clients that only need counts should leave it off and fetch detail over REST.

(See [Questions and Answers](high_level_design.md#questions-and-answers) in the high level design for resolved items.)
