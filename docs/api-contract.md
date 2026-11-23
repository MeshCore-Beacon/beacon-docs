# Beacon: API Contract

The Go server exposes one REST API namespace under `/api/v1/` and one WebSocket endpoint at `/ws`. React (web) and Flutter (mobile) consume identical endpoints. All JSON is camelCase. Times are Unix epoch milliseconds as integers (e.g. `1747668456000`), bytes are hex strings, UUIDs are stringified. The one exception is [Firmware polling](#firmware-polling): four routes outside `/api/v1` that use snake_case and RFC 3339 times.

**Why epoch ms:** smaller on the wire, no timezone or parser ambiguity, no string parsing in hot paths (chart axes, sorts, comparisons), and matches the units MeshCore uses internally (uint32 Unix seconds in adverts and traces). JS `new Date(ms)` and Dart `DateTime.fromMillisecondsSinceEpoch(ms)` consume it natively.

Query params follow the same convention: `since` and `until` are epoch ms integers. `range` is a Go duration string (`24h`, `168h`, `720h`) on the endpoints that take one.

This document describes the contract and the parts that need explaining. Every request parameter and response schema is in the Swagger UI the server serves at `/swagger/index.html`.

---

## Auth

Everything under `/api/v1/` is public and read-only, except the `/api/v1/admin/` subtree and, when [user accounts](accounts.md) are on, the `/api/v1/auth` and `/api/v1/me` routes (see [User accounts](#user-accounts)).

Admin routes need the operator key, set as `auth.api_key` in `config.yaml` or `BEACON_API_KEY` in the environment (the variable wins when set, even if empty). A key shorter than 16 characters or with whitespace inside it stops startup.

```
Authorization: Bearer <key>
```

- No key configured: every admin route returns `503` with code `service_unavailable`.
- Missing or wrong key: `401` with code `unauthorized` and `WWW-Authenticate: Bearer`.
- Admin responses carry `Cache-Control: no-store`.

Send the key only over HTTPS.

## Rate limiting

On by default for `/api/v1/*` (not `/ws` or `/swagger`). Each client gets `ratelimit.requests_per_minute` (default 600) per minute, plus a one-second window capped at `ratelimit.burst` (defaults to the per-minute value). Clients are keyed by IP after the trusted-proxy step below; IPv6 clients share a budget per /64. Over the limit:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{"error":{"code":"rate_limited","message":"Request rate limit exceeded. Retry later."}}
```

`Retry-After` is 1 or 60 seconds depending on which window tripped. `ratelimit.enabled: false` turns both windows off. Counters live in the server process, so each Beacon instance counts separately.

**Client IP.** The server only accepts `X-Real-IP`, and only from a direct peer listed in `server.trusted_proxies`. `X-Forwarded-For` and `True-Client-IP` are always ignored and stripped. Behind a reverse proxy that isn't listed, every client shares the proxy's budget.

## Cost guards

Every public `/api/v1` request also passes through cost guards (not `/ws`, not `/api/v1/admin/*`). By default they only count what they would refuse, and no response changes. A guard refuses only for a family the operator has listed in `guards.enforce` (see [Configuration](configuration.md#database-pools-and-cost-guards)). Clients should still handle the three refusals:

| Status | `code` | `Retry-After` | When |
|---|---|---|---|
| `429` | `rate_limited` | `1` | More than 4 database-backed requests at once from one client, and no slot freed within 5 s. Cache hits don't count. |
| `503` | `service_unavailable` | `2` | No database connection within 5 s. |
| `503` | `deadline_exceeded` | `5` | The request's database time passed its class limit: entity 5 s, list 10 s, aggregation 30 s, counted from its first statement. |

```
HTTP/1.1 503 Service Unavailable
Retry-After: 5

{"error":{"code":"deadline_exceeded","message":"The request ran past its database time limit. Retry later."}}
```

The body is the usual error envelope. Wait at least `Retry-After` seconds before retrying; a `deadline_exceeded` request will likely run as long again, so narrow it (a shorter window, a region) rather than repeat it. Clients are keyed by IP after the trusted-proxy step above.

Separately from the guards, and on every server, a page whose database statement runs past its pool's statement limit (35 s) answers `503` with code `deadline_exceeded` and `Retry-After: 10`. This covers every `/api/v1` endpoint that reads the database; account, backup and plan-check admin routes keep their own errors. The heavy stats endpoints (`series`, `signal`, `paths`, `observer-comparison`) and route searches (`/routes/search`, `/routes/cross`) answer the same `503` when their own request time limit runs out, with a message that names the query. Any other failed read is a `500` without `Retry-After`.

Each request falls in one family and one class:

| Path | Condition | Family | Class |
|---|---|---|---|
| `/packets`, `/packets/backfill` | `since` or `until` set (`/packets` only) | `packets_window` | aggregation |
| `/packets`, `/packets/backfill` | region set | `packets_region` | list |
| `/packets`, `/packets/backfill` | otherwise (including `hashPrefix`) | `packets_global` | list |
| `/packets/{hash}` | | `packet_detail` | entity |
| `/routes` | | `routes` | list |
| `/routes/cross`, `/routes/search` | | `routes` | aggregation |
| `/routes/{iata}/{pathKey}/observations` | | `routes` | entity |
| `/channels/{id}/messages`, `/messages`, `/messages/backfill` | | `channel_messages` | list |
| `/stats/*` | | `stats` | aggregation |
| `/channels`, `/nodes`, `/observers`, `/traces`, `/nodes/{id}/observations`, `/observers/{id}/adverts` | | `other` | list |
| `/observers/directory` | region set | `other` | list |
| `/observers/directory` | otherwise | `other` | aggregation |
| `/observers/{id}/activity`, `/nodes/{id}/activity` | | `other` | aggregation |
| `/observers/{id}`, `/observers/{id}/telemetry`, `/nodes/{id}`, `/nodes/{id}/neighbors`, `/channels/{id}`, `/traces/{tag}` | | `other` | entity |
| everything else (`/iatas*`, `/regions*`, `/scopes*`, `/info`, `/ws-ticket`, `/brokers`, unknown paths) | | `other` | entity |

"Region set" means a non-empty `iata`, `iatas`, `region` or `regionId`.

## Pages that wait for server data

Some pages are served only from data the server prepares in the background. While it is not ready they answer `503` with code `service_unavailable` and `Retry-After: 30`, whatever `guards.enforce` says:

| Pages | Ready when |
|---|---|
| `/packets` with `iata`, `iatas`, `region` or `regionId`, without `hashPrefix` (region pages) | the server trusts its `packet_sites` read model |
| `/channels/{id}/messages` with `iatas`, or with `scope` and no `since`; `/messages` with `iatas` (with or without `since` or `scope`), or with `scope`, no `since` and no `iatas` | the server trusts its `channel_message_iatas` read model |
| `/observers/{observerId}/adverts` | every observation carries its payload type |

That happens during the first fill after an upgrade, during a repair, after a failed verification, until the observation payload-type backfill is done, and for as long as the operator turns a read model off (see [Operations](operations.md#pages-that-wait-for-a-read-model)). `/messages` with `iatas` and `since` or `scope` is in the table since 2.1: development builds of 2.1 served it from the observations whatever the read model's state, and answered `503` with `Retry-After: 5` when that pool was busy; that `503` is gone.

```
HTTP/1.1 503 Service Unavailable
Retry-After: 30

{"error":{"code":"service_unavailable","message":"This page is not available yet. Retry later."}}
```

Retry after `Retry-After`. A first fill can take minutes, so a client that gives up after a few retries should let the user retry later.

## Versioning

Path is the contract: `/api/v1/`. Breaking changes get `/api/v2/`. Backward-compatible additions just expand the existing payloads. WebSocket messages include a `type` discriminator and a top-level `v: 1` field so we can evolve in place.

## Errors

All errors use one shape:

```json
{ "error": { "code": "not_found", "message": "packet not found" } }
```

`code` is the HTTP status text in snake_case, so match on it or on the status. The account routes add their own codes, listed under [User accounts](#user-accounts). Codes in use: `bad_request`, `unauthorized`, `not_found`, `conflict`, `request_entity_too_large`, `unsupported_media_type`, `rate_limited`, `internal_server_error`, `service_unavailable`, `gateway_timeout`, `insufficient_storage`, and `deadline_exceeded` (a `503` from the [cost guards](#cost-guards)). A `503` `service_unavailable` with `Retry-After` can also mean a page is [waiting for server data](#pages-that-wait-for-server-data). A `503` `deadline_exceeded` with `Retry-After` from any endpoint means its query ran out of time; retry later or ask for a shorter window. A response the server cannot encode is a `500` `internal_server_error`, never an empty `200`.

A `404` means the requested thing doesn't exist. A database or other server-side failure is always a `500` (or `503` above), never a `404`, so clients can retry 5xx and treat 4xx as final. Empty lists are `200` with `[]`.

## Pagination

Most lists return a page:

```json
{ "items": [ ... ], "nextCursor": 1747665456000, "hasMore": true }
```

Pass `nextCursor` back as `cursor` for the next page; it is omitted on the last page. What the cursor holds depends on the list (a timestamp in epoch ms, or an ID), as noted per endpoint. `limit` has a per-endpoint default, must be positive, and is clamped to 200 (2000 for `GET /nodes`).

ID cursors are 64-bit integers: the observation ID `cursor` of `/observers/{id}/adverts` and `/nodes/{id}/observations`, telemetry `afterId`, the message ID `cursor` of `/messages`, and the backfill `afterObservationId` and `afterId` ([Backpressure and reconnection](#backpressure-and-reconnection)). The same goes for the IDs they come from. Store and send them as full integers; never narrow them to 32 bits, since a busy server passes 2^31. As JSON numbers they stay exact up to 2^53, so a JavaScript `number` or a Dart `int` holds them.

A few lists return a plain array instead: the backfill endpoints, `/routes*`, `/traces` and the stats endpoints.

### Exact page cursors

A numeric `cursor` holds a millisecond, so rows that share the last row's millisecond can fall
between two pages. `/packets`, `/nodes`, `/observers` and `/channels` also return
`nextPageCursor` on a page with `hasMore`: an opaque string of at most 160 characters (512 on a
sorted `/nodes` list) that marks the exact last row. Send it back as `pageCursor`. A walk by `pageCursor` returns every row once,
including those ties. Don't parse or build it; today it reads `v1:<epoch µs>:<packet hash hex>`
on `/packets` and `v1:<epoch µs>:<id>` on `/nodes` and `/observers`.

| Endpoint | `pageCursor` | `nextPageCursor` |
|---|---|---|
| `/packets` without `iata`, `iatas`, `region`, `regionId` or `hashPrefix` | Wins over `cursor` when both are sent. | When `hasMore` |
| `/packets` with `iata`, `iatas`, `region` or `regionId` (a region page), without `hashPrefix` | Wins over `cursor` when both are sent. | When `hasMore`, except on a page requested by a millisecond `cursor` alone that a sparse filter sent to the server's fallback statement |
| `/packets` with `hashPrefix` | Checked, then ignored; `cursor` pages. | Not returned |
| `/nodes`, `/observers` | Wins over `cursor` when both are sent. | When `hasMore` |
| `/channels` | Can't be combined with a positive `cursor` (`400`). | When `hasMore` |

- `nextCursor` stays on every page with `hasMore` and keeps its meaning: rows strictly older than
  that millisecond. Paging by `cursor` alone gives the same pages as before and still skips
  rows tied on the boundary millisecond.
- On `/packets`, `/nodes` and `/observers`, send both: `cursor` set to `nextCursor` and
  `pageCursor` set to `nextPageCursor` when the page has both, `cursor` alone otherwise. A server
  older than 2.1.0 ignores `pageCursor` and still moves forward by `cursor`. Treat
  `nextPageCursor` as optional on every list. `/channels` takes only one of the two.
- Region pages of `/packets` are served only while the server trusts its `packet_sites` read
  model, which it checks again after every start and drops on any doubt; otherwise they answer
  `503` (see [Pages that wait for server data](#pages-that-wait-for-server-data)). Keep sending
  both cursors whenever a page has both.
- A malformed `pageCursor` is a `400` with message `invalid pageCursor` on those three
  endpoints, on every path, including the `/packets` paths that ignore it. Start again from
  the first page without it. An empty `pageCursor` counts as absent.

## Common filters

Most list and stats endpoints take the same location filters:

| Param | Meaning |
|---|---|
| `iatas` | Comma-separated IATA codes, case-insensitive (`YOW,YYZ`) |
| `iata` | Single IATA, used only when `iatas` is absent |
| `region` / `regionId` | Region slug or ID; expands to its member IATAs and adds them to any `iatas`. An unknown region or malformed ID is a `400`; a failed lookup is a `500`. A region with no member IATAs matches nothing, so a list filtered by it alone comes back empty. |
| `scope` | Transport scope name, URL-encoded (`%23bc` for `#bc`) |

Comma-separated list params (`iatas`, `scopes`, `payloadTypes`, `routeTypes`) take at most 1000 values; more is a `400`.

---

## REST endpoints

### Packets

| Endpoint | Notes |
|---|---|
| `GET /packets` | Page of packet summaries, newest first. Default limit 50. |
| `GET /packets/{packetHash}` | Full packet with every observation. `404` if unknown. |
| `GET /packets/backfill?afterObservationId=<id>` | Packets with observations after that ID, oldest first, plain array. Default limit 100. For reconnect backfill. |

`/packets` params: `payloadType` or `payloadTypes` (comma-separated integers), `payloadTypeName` (`advert`, `group_text`, `trace`, ...; used when no number is given), `routeType` or `routeTypes`, the location filters, `scope` or `scopes` (comma-separated), `since`, `until`, `hashPrefix` (4 to 16 hex characters of the packet hash), `cursor`, `pageCursor`, `limit`. Filters OR within themselves and AND across each other. The cursor is epoch ms: global `lastHeardAt` order without an IATA filter, and the time heard at the requested sites when one is set, so a filtered list stays bounded to those IATAs. With `hashPrefix` the order and cursor use global `lastHeardAt` even when an IATA filter is set.

With an IATA or region filter and no `hashPrefix` (a region page), the list is ordered by the time the packet was last heard at the requested sites, newest first. While the server trusts its site read model (see [Operations](operations.md#read-models-packets-by-site)), `pageCursor` applies and those pages are the same as before with three differences:

- Packets heard at the same site time are ordered by `packetHash`, descending.
- A `pageCursor` page returns the rows in the cursor's millisecond that a millisecond `cursor` skips, as on `/packets` without a region (see [Exact page cursors](#exact-page-cursors)).
- Where many observers heard a site's packets, the previous statement could end a page short, end a walk early or move `nextCursor` past rows it never returned; the new page returns those rows.

While it does not, region pages answer `503` with `Retry-After: 30`; see [Pages that wait for server data](#pages-that-wait-for-server-data).

Without an IATA or region filter or `hashPrefix`, the list is ordered by `lastHeardAt`, newest first, and packets heard in the same instant by `packetHash`, descending. `pageCursor` applies there (see [Exact page cursors](#exact-page-cursors)). Repeated values in the type and scope lists count once, and type values outside the header's range (payload type 0 to 15, route type 0 to 3) are dropped; a type list left with no valid value returns an empty page, not a `400`. When several observations of a packet share the newest time, `latestObserver` comes from the one with the highest observation ID, so the choice is stable.

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

#### Packet summaries

Packet lists, regional lists, reconnect backfill and live `packetObservation` events carry the
optional `summary` string. It comes from the packet's own stored metadata, never from a node's
current name or a fresh decode.

| Payload | Summary | Source |
|---|---|---|
| ADVERT | Advertised name | Saved `appData.name` / verified decoded advert |
| ACK | `ACK 01020304` | Four-byte acknowledgement checksum |
| TRACE | `TRACE efbeadde` | Trace tag |
| TRACE classified as PING | `PING efbeadde` | Trace tag |

- References are eight lowercase hex characters in the same byte order as packet detail's
  `checksum` / `traceTag`. Zero is valid. Extended ACK retry bytes do not change the checksum.
- They are short references, not unique packet IDs or proof of delivery. No message body, trace
  auth code or inferred sender or recipient is included.
- The text is projected from saved JSON in the existing list queries: no extra column, backfill
  or per-packet lookup. A stored value of the wrong type or not exactly eight hex characters
  omits the field.
- Other payload types have no summary yet. A missing summary does not mean the packet is
  invalid.

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
| `pathBytes` | string | Accumulated path hashes (hex). For a TRACE, the live event and packet lists carry the on-air path field, one SNR byte per hop reached. Packet detail carries the hop hashes the TRACE payload lists instead, and `pathLength.hashSize` and `hopCount` describe those. |
| `wirePathBytes` | string | Packet detail observations only, optional. The path field exactly as it was on air (hex), sent for a TRACE whose `pathBytes` were replaced by its hop hashes; empty when no hop had been reached. To rebuild the frame use header + `pathLength.raw` + `wirePathBytes` if present, else `pathBytes`, + payload. Absent before 2.3.0. |
| `rssi`, `snr` | number | dBm / dB, each omitted when the observer did not report a usable value. A usable RSSI is -164 to -1 dBm and a usable SNR is -32 to 32 dB. An SNR of 0 is a real reading when it comes with a usable RSSI; 0 with no RSSI is how observers write "unknown" and is omitted. A missing value is never sent as 0 and never counted in an average. |
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
| `GET /nodes` | Page of node summaries, newest `lastSeen` first, ties by `id` descending, or in a `sort` order (see below). Cursor is `lastSeen` epoch ms; `pageCursor` is exact. Default limit 50, at most 2000 (older servers clamp to 200, so ask for 2000 and keep paging): clients that load a whole region, like the map, use big pages. |
| `GET /nodes/{nodeId}` | Node detail: capability flags, `minFirmwareVersion`, `iatas` (`[{iata, lastHeard}]`), `neighbors`, clock drift for repeaters and room servers, and `meshmapper` when imported (see [MeshMapper repeater details](#meshmapper-repeater-details)). |
| `GET /nodes/{nodeId}/observations` | Page of observations of packets the node originated, ordered by the packet's first heard time, newest first, then by packet, then by observation ID descending. Observation IDs do not descend across the whole list, and an old packet heard again recently keeps its original place. Cursor is the last item's observation ID; a cursor whose observation no longer exists returns an empty page with `hasMore` false, not an error. |
| `GET /nodes/{nodeId}/activity?range=24h` | Hourly totals of those observations, with signal averages. See [Node activity](#node-activity). |
| `GET /nodes/{nodeId}/neighbors` | Plain array of neighbours: `{ id, name, publicKey, nodeType, nodeTypeName, lat, lng, iata, observationCount, firstSeen, lastSeen, snr }`. |
| `GET /nodes/{nodeId}/telemetry?range=168h&interval=6h` | Repeater readings of a polled node, bucketed for charts. See [Node telemetry](#node-telemetry). |
| `GET /nodes/telemetry/latest` | The newest battery and temperature of every polled node, for map labels. See [Latest node telemetry](#latest-node-telemetry). |
| `GET /nodes/{nodeId}/polling` | Which observer polls the node and when it last got a trusted reading. See [Node polling](#node-polling). |

`/nodes` params: `type` (1 companion, 2 repeater, 3 room server, 4 sensor) or `typeName`, the location filters, `name` (partial, case-insensitive), `scope`, `pubkey` (exact hex), `pubkeyPrefix`, `supportsMultibytePaths`, `supportsMultibyteTraces`, `neighbors` (adds `neighborIds`), `sort`, `order`, `cursor`, `pageCursor`, `limit`. Summaries include `lastSeen` (when the node was last heard, epoch ms; list rows carry it from 2.1.1, node detail always has), `stale` (not seen within `nodes.stale_threshold`), `defaultScope` (the transport scope last matched from the node's adverts, omitted when none; list rows carry it from 2.1.0, node detail always has) and, when `nodes.mark_foreign` is on, `possiblyForeign`. To list one scope's nodes, send `scope` rather than filtering rows: a server before 2.1.0 leaves `defaultScope` off list rows.

Sorted node lists (2.1.0): `sort` is `lastSeen` (the default), `name`, `type` or `neighbors`, and `order` is `asc` (the default) or `desc`. `lastSeen` defaults to `desc`, the newest-first list; from 2.1.1 it also takes `asc`, oldest heard first, which is a sorted list like the others (a server before 2.1.1 answers it with a `400`). Every page says which order it is in with `sort` and `order` (`lastSeen` and `desc` by default). The orders match what the web's node table shows:

- `name`: natural order, as `Intl.Collator` with `numeric: true` sorts (symbols and emoji before digits, digits before letters, `Node 9` before `Node 10`, lowercase before uppercase). Nodes without a name come last in both directions.
- `type`: companion, repeater, room server, sensor, then any other type.
- `neighbors`: `knownNeighborCount`.
- `lastSeen` with `asc`: oldest heard first.

Ties go newest `lastSeen` first, then by `id`. Filters work the same as without `sort`. Page a sorted list (any order but the default newest first) with `pageCursor` only: a numeric `cursor`, or a `pageCursor` from another sort or order, is a `400`. A sorted page has no `nextCursor`. An unknown `sort` or `order` is a `400`. A server older than 2.1.0 ignores both and returns pages in `lastSeen` order with no `sort` field; a client that sees no `sort` must sort for itself.

#### Node activity

`GET /nodes/{nodeId}/activity` reports how often a node's packets were heard, in one-hour buckets
over a trailing window that ends now. `range` is a Go duration (default `24h`); it must be at least
`1h` and at most `720h`. A bad `range` or node ID is a `400` and an unknown node is a `404`. There is no
`interval`: buckets are always one hour, aligned to the clock in UTC. The response is cached for 60
seconds.

```json
{
  "windowStart": 1747530000000,
  "windowEnd": 1747612980000,
  "generatedAt": 1747612980000,
  "rolledUntil": 1747609200000,
  "rawFrom": 1747609200000,
  "range": "24h",
  "summary": { "observations": 412, "snrAvg": 5.8, "rssiAvg": -94.1, "hopAvg": 2.3 },
  "points": [
    { "t": 1747605600000, "observations": 18, "snrAvg": 6.2, "rssiAvg": -92.3, "hopAvg": 2.1 }
  ],
  "latest": { "packetHash": "a1b2c3d4e5f60718", "heardAt": 1747612500000 }
}
```

- `windowEnd` is the time of the request, so the last hour is still filling. `windowStart` is
  `windowEnd` minus `range`, rounded up to the hour. `range` echoes the request.
- `points` are in ascending order and hold only the hours that have records; `t` is the start of
  the hour. A missing hour means nothing was recorded, except for uncovered hours (below).
- `summary` covers the whole window. Its averages are the sum over the samples, not a mean of the
  hourly averages.
- An observation whose RSSI and SNR are both zero or missing counts in `observations` but is not a
  signal sample. An average is `null` when its hour, or the window, has no samples for it.
- `latest` is the node's packet that was first heard most recently, whether or not it falls in the
  window, and `heardAt` is the later of that packet's first and last heard times. It is `null`
  when the node has no stored packet.
- Complete hours come from the hourly rollup. Hours after the newest rolled one are read from raw
  observations, at most the last 24 hours. `rolledUntil` and `rawFrom` mean the same as on
  [observer activity](#observers): `rolledUntil` is omitted before the first rollup, and when
  `rawFrom` is later than `rolledUntil` (or `rolledUntil` is missing), the hours between are
  uncovered, not quiet.

#### Node telemetry

```
GET /api/v1/nodes/{nodeId}/telemetry?range=168h&interval=6h&include=untrusted
```

The readings that observers took from a repeater or room server when [repeater polling](repeater-polling.md) is on, folded into UTC buckets. Every parameter is optional.

| Param | Values | Default |
|---|---|---|
| `range` | `24h`, `72h`, `168h`, `720h` | `168h` |
| `interval` | `1h`, `6h`, `24h` | `1h` for `24h` and `72h`, `6h` for `168h`, `24h` for `720h` |
| `include` | `untrusted` | none |

Any other value of `range`, `interval` or `include`, or a `nodeId` that is not a UUID, is a `400`. An unknown node is a `404`. A node with no readings is a `200` with `polled` false and `points` empty. With polling off on the server the route still checks the node, so an unknown node is a `404`, and otherwise answers as for a node with no readings: `{"range":"168h","interval":"6h","polled":false,"untrustedReadings":0,"points":[]}`, with `range` and `interval` as asked or defaulted. A client can ask without checking `features` first.

```json
{
  "range": "168h",
  "interval": "6h",
  "polled": true,
  "untrustedReadings": 0,
  "points": [
    {
      "t": 1794700800000, "readings": 3,
      "batteryMv": 4226, "temperatureC": 16.5, "noiseFloorDb": -97, "lastRssiDb": -20, "lastSnrDb": 12.0,
      "uptimeSeconds": 79884, "queueLength": 0,
      "airtimeTxSecs": 1.5, "airtimeRxSecs": 220.0, "packetsReceived": 410, "packetsSent": 6, "receiveErrors": 12,
      "counterSpanSecs": 21600
    }
  ]
}
```

| Field | Notes |
|---|---|
| `range`, `interval` | The values used, defaults filled in. |
| `polled` | True when Beacon has ever stored a reading for this node, trusted or not. It does not depend on `range` or `include`. |
| `untrustedReadings` | Readings inside `range` that were left out because `include=untrusted` was not sent. Always 0 when it was sent. |
| `points` | Ascending by `t`. A bucket with no readings is not sent, so a gap between points is a gap in polling. |
| `t` | Bucket start, epoch ms, aligned to UTC. |
| `readings` | How many readings fell in the bucket. |
| `batteryMv` | Battery, millivolts. Average, rounded to a whole number. |
| `temperatureC` | Degrees Celsius. Average, rounded to a tenth. |
| `noiseFloorDb` | Noise floor, dBm. Average, rounded to a whole number. |
| `lastRssiDb` | RSSI of the last packet the repeater heard, dBm. Average, rounded to a whole number. |
| `lastSnrDb` | SNR of that packet, dB. Average, rounded to a tenth. |
| `queueLength` | Packets waiting to be sent. Average, rounded to a whole number. |
| `uptimeSeconds` | Seconds since the repeater started. The largest value in the bucket, not an average. |
| `airtimeTxSecs`, `airtimeRxSecs` | Seconds of radio time spent sending and receiving. Increase within the bucket, covering `counterSpanSecs`. |
| `packetsReceived`, `packetsSent`, `receiveErrors` | Packet counts. Increase within the bucket, covering `counterSpanSecs`. |
| `counterSpanSecs` | Seconds of elapsed time that the five counter increases in this point cover. Left out when zero. See below. |

Every field after `readings` is left out when no reading in the bucket carried it. Repeaters do not all report every field.

The five counters (`airtimeTxSecs`, `airtimeRxSecs`, `packetsReceived`, `packetsSent`, `receiveErrors`) are running totals on the repeater. Beacon turns them into increases one pair at a time. A status reading is a reading whose stored `method` is `status`, whether or not it carries any counter: a status reply too short to carry counters is still a status reading. A pair is two consecutive status readings. A status reading without counters therefore takes part in a pair and breaks it (the pair adds nothing), and the next pair starts from that reading, not from the last one that had counters. Telemetry readings (`method` `telemetry`) are never part of a pair. The increases of a pair are credited to the bucket of the later reading. A pair gives the same answer whatever `range` was asked for, so the first pair of a range uses the newest status reading (by `method`) before the range as its earlier half.

A pair either contributes all of its counters or none of them. It contributes when all of these hold:

- The later reading is after the earlier one and no more than 48 hours later. A longer gap cannot be placed in a bucket.
- At least one counter is present in both readings.
- No counter is negative, in either reading. A negative value cannot be a running total, so the whole pair is refused.
- The counters do not disagree. Either none went down, or the repeater rebooted and none went up. A reboot is seen when both readings carry uptime and the later uptime is lower than the earlier, or is shorter than the time between the two readings.
- The span is at least one second.
- No increase is faster than its cap: 1 second per second for `airtimeTxSecs` and `airtimeRxSecs`, 10 per second for `receiveErrors`, 50 per second for `packetsReceived` and `packetsSent`.

The increase of a counter is the later total minus the earlier total. When the pair spans a reboot and every counter went down, the counters restarted from zero, so the increase is the later total, and the span is the later uptime if that is shorter than the time between the readings. A counter that is present in only one of the two readings is skipped for that pair. A pair that does not contribute adds nothing, so it never produces a zero.

Counters only arrive on status readings, which are hours apart (6 hours by default, up to 24). An increase can therefore cover more time than the bucket it lands in, so it is not a rate per bucket. `counterSpanSecs` says how much time the increases in a point cover. Divide an increase by it to get a rate. For example, `airtimeRxSecs / counterSpanSecs` is the share of time the repeater spent receiving. Do not divide by the bucket length.

`counterSpanSecs` is the sum of the spans of the pairs that contributed to the bucket, so all the counters in a point share one span. A counter field is left out of a point when any contributing pair in that bucket lacked it, because its increase would cover less time than the span and understate the rate. When no pair contributed, `counterSpanSecs` and all five counters are left out. That includes a bucket that holds only telemetry readings, the first status reading Beacon has for a node, and a bucket whose pairs were all dropped. A client should treat such a point as having no value for the counters, not as zero.

One case cannot be detected. A corrupt reading that is lower than the truth but passes the rate check can make the following pair read high.

A reading is trusted when, at the moment it was stored, its observer was assigned to that repeater and Beacon had itself heard the repeater directly through that observer. The decision is made once, when the reading is stored, and does not change later, so a chart does not shift when assignments change. Readings stored before this was recorded were judged against the assignments as they stood when the server was upgraded. Only trusted readings are in `points` by default, so an observer that merely claims a repeater cannot put numbers on its chart. `include=untrusted` adds the rest and `untrustedReadings` tells a client how many it left out.

#### Latest node telemetry

```
GET /api/v1/nodes/telemetry/latest?iata=YOW
```

The newest battery and temperature of every polled node, in one answer, so a map can label its pins. The location filters `iata`, `iatas`, `regionId` and `region` work as on the node list. There are no other parameters.

The answer has one item for each node that has a trusted reading in the last 7 days carrying a battery or temperature value. Untrusted readings are never used. A node with no such reading is not listed. With polling off on the server the answer is `{"generatedAt": ..., "items": []}`, so a client can ask without checking `features` first. With Redis configured the server caches the answer for about 60 seconds; without it every request is computed.

```json
{
  "generatedAt": 1794700800000,
  "items": [
    { "nodeId": "7c1f0e9a-3b52-4d8e-9a61-2f4b8c0d5e17", "sampledAt": 1794697200000, "batteryMv": 4080, "temperatureC": 1.5 }
  ]
}
```

| Field | Notes |
|---|---|
| `generatedAt` | When the server built the answer, epoch ms. |
| `items` | One item per node. `[]` when there are none, never `null`. |
| `nodeId` | The node's ID, as on the node list. |
| `batteryMv` | Battery, millivolts. The newest trusted battery value in the last 7 days. Left out when there is none. |
| `temperatureC` | Degrees Celsius. The newest trusted temperature value in the last 7 days. Left out when there is none. |
| `sampledAt` | Epoch ms. The newer of the two readings that gave `batteryMv` and `temperatureC`. |

`batteryMv` and `temperatureC` are picked one by one, so they can come from different readings. Temperatures are always Celsius, whatever `display.temperatureUnit` in [Server info](#server-info) says. That key only tells a client which unit to show.

#### Node polling

```
GET /api/v1/nodes/{nodeId}/polling
```

Who polls this node right now. A `400` for a `nodeId` that is not a UUID and a `404` for an unknown node. With polling off it still checks the node (an unknown node is a `404`) and then answers `{"polled":false,"latestReadingAt":null,"poller":null,"standbys":[]}`, the same as for a node nobody polls.

```json
{
  "polled": true,
  "latestReadingAt": 1794702630000,
  "poller": { "observerId": "8f0c6a52-0d56-4a47-9c36-3e8f1c2f4b11", "name": "HOWL V4.2" },
  "standbys": [ { "observerId": "5b1d0f1e-7c3a-4d0e-8a56-9f2b6c1d7a20", "name": "Ridge West", "rank": 1 } ]
}
```

| Field | Notes |
|---|---|
| `polled` | True when Beacon has ever stored a reading for this node, trusted or not. Same meaning as in the telemetry answer. |
| `latestReadingAt` | Time of the newest trusted reading, epoch ms. `null` when there is none, even if untrusted readings exist. |
| `poller` | The observer ranked first: `observerId` and `name`. `null` when nobody is assigned. |
| `standbys` | The other assigned observers, in rank order, each with `observerId`, `name` and `rank` (1, 2, ...). An empty array when there are none. The poller has no `rank` field. |

`name` is the observer's display name, or the first 8 hex characters of its public key when it has none.

#### MeshMapper repeater details

With `meshmapper.repeaters.enabled`, node detail carries `meshmapper` when MeshMapper's repeater
list has the node's full public key. It is omitted otherwise. Times are epoch ms; `fetchedAt` is
when Beacon last fetched the list. Text is admin-entered on MeshMapper, so escape it.

```json
"meshmapper": {
  "iata": "YOW",
  "fetchedAt": 1791234600000,
  "site": {
    "power": "1W", "hardware": "RAK4631", "antenna": "5.8 dBi fibreglass",
    "heightM": 12, "heightAslM": 341.6, "powerSource": "solar",
    "notes": "On the fire tower, east face"
  },
  "carpeater": false,
  "admins": ["MrAlders0n"],
  "scopes": [
    { "scope": "yow", "observedAt": 1791200000000, "observedPackets": 37, "proof": "multibyte", "reportedAt": 1791100000000 }
  ],
  "scopesCheckedAt": 1791100000000,
  "defaultScope": { "name": "yow", "state": "named", "updatedAt": 1791230000000, "source": "advert" }
}
```

- `site` is always an object; each field is omitted when unset. `powerSource` is `mains`,
  `solar`, `battery` or `poe`. `heightAslM` can lag a new `heightM` by a few minutes.
- `carpeater` marks a repeater riding in a car: its position moves.
- `scopes` lists scopes MeshMapper confirmed it carrying. `proof` is `multibyte` or `floor`;
  `observedAt`/`observedPackets` (seen forwarding), `reportedAt` (an observer asked it) and
  `uploadedAt` (a wardriver's app asked it) are omitted for sources that never confirmed it.
  `scopesCheckedAt` present with empty `scopes` means it answered with none.
- `defaultScope.state` is `named`, `unknown` (it sets one MeshMapper can't name yet) or
  `none`; `name` is only sent when `named`; `source` is `advert` or `reported`. This is
  MeshMapper's view; the top-level `defaultScope` is what Beacon matched from adverts.

#### Foreign repeater indication

With `nodes.mark_foreign: true`, repeater nodes carry `possiblyForeign`. It is `true` when the
repeater's reported position is outside the union of all configured `iatas.<code>.borderFile`
polygons, with `meshmapper.zones` borders replacing them where MeshMapper has one. IATAs without
a border add no area, and airport coordinates are not used. Enabling it with no border source, a
missing file or invalid geometry stops startup. Border changes need a restart.

- Points on an edge (including hole edges) are inside; hole interiors are outside.
- Other roles and missing or invalid positions get no value. A 0/0 advert clears the stored
  position.
- It is a hint from the reported position, not proof of origin. Ingest, heard-in IATAs and route
  matching are unaffected.
- Computed at read time, so existing nodes need no backfill. The field is omitted when the
  feature is off (the default).
- In `nodeUpdate`, it is a boolean when the advert carries a position, `null` when the position
  is 0/0 or invalid or the node stops being a repeater, and omitted to keep the previous value.
  `lat`/`lng` follow the same rule.

GeoJSON uses longitude, latitude order. Split borders that cross the antimeridian into
MultiPolygons per [RFC 7946 section 3.1.9](https://www.rfc-editor.org/rfc/rfc7946#section-3.1.9);
edges spanning more than 180 degrees are rejected.

### Observers

| Endpoint | Notes |
|---|---|
| `GET /observers` | Page of observers, most recently seen first, ties by `id` descending. Params: location filters, `type` (e.g. `meshcoretomqtt`), `broker`, `status` (`online`/`offline`), `name`, `scope`, `cursor` (last-seen epoch ms), `pageCursor`, `limit`. |
| `GET /observers/directory` | Traffic/name pagination, row counts and type facets. See [observer directory contract](observer-directory.md) for rollout status and exact semantics. |
| `GET /observers/{observerId}` | Observer detail. |
| `GET /observers/{observerId}/telemetry?range=24h&interval=1h` | Telemetry history. `interval` is `1h` (default), `6h` or `24h`. `afterId` returns only newer points. |
| `GET /observers/{observerId}/activity?range=24h&interval=15m` | What the observer heard, bucketed. |
| `GET /observers/{observerId}/adverts` | Page of adverts the observer heard. Cursor is the observation ID. |

`/observers` pages by each observer's last-seen time, which the summary does not include. Since
2.1.0 `nextCursor` is that time for the last row and is present whenever `hasMore` is true.
Before, it came from the last status message and was missing when the last row had none, so a
walk by `cursor` skipped most observers. Paging by `cursor` alone can still skip observers that
share a millisecond (presence updates often stamp many at once); `pageCursor` reaches all of them.

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
Only non-empty buckets are returned. Gaps in `points` mean the observer heard nothing in that bucket,
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

Sub-hour intervals read live observation rows and are always current. The response also reports
`windowStart`, `windowEnd`, `generatedAt`, `source` (`raw` or `hourly`) and a `summary` of recorded
packets and the last complete hour:

- `summary.recordedPackets` counts stored observations in the window; repeated broker deliveries of
  the same packet count once. Unknown payload types show as `-1`.
- Freshness fields (`lastCompleteHour` with its start and end, `latestRecordedAt`) are measured at
  `generatedAt`, even for historical `until` requests.
- `until` lines up two observers' charts.
- Missing records do not prove downtime. The observer's `observationCount` is a legacy cumulative
  presence counter (including status and neighbour events), not a packet total.

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
| `GET /regions` | Regions in display order, each with the same fields as `GET /regions/{regionId}` (`iatas` always present, `[]` for a region with none), so one call resolves every region. `[]` when none are configured. Older servers list only `id`, `slug` and `name`: when `iatas` is missing, fetch each region. |
| `GET /regions/{regionId}` | One region with its IATAs. `400` for a non-numeric ID, `404` if unknown. |
| `GET /scopes` | Array of scope names. Location filters narrow it to manual scopes configured for a matching region and imported scopes whose MeshMapper catalogue includes a matching IATA. |
| `GET /scopes/{name}` | Scope detail (`%23bc` for `#bc`). |
| `GET /brokers` | `[{ "name", "connected" }]` per MQTT broker. |

Regions, IATA names and scopes are managed in the server config file (or imported from MeshMapper), not through the API.

### Routes

Known routes are fully resolved multi-hop paths distilled from packet history.

| Endpoint | Notes |
|---|---|
| `GET /routes` | Plain array, newest `lastSeen` first. Params: `iatas` (comma list, at most 100), `iata`, `hopCount`, `cursor` (last item's `lastSeen`, epoch ms), `cursorId` (last item's `id`), `limit` (default 50, larger values clamp to 200). A `hopCount` or `cursor` that is not a number is a `400`. With neither `iatas` nor `iata`, every IATA. |
| `GET /routes/search?from=&to=[&iatas=]` | Routes within one IATA between two node hash prefixes. `from`, `to` required (hex, 1–4 bytes; widths may differ). `iatas` optional: comma list, at most 100, omitted = every IATA; the single `iata` is still accepted. At most 500 results, shortest first. `hops` is trimmed to source…destination and `hopCount` = `hops.length`. |
| `GET /routes/cross?fromHash=&toHash=[&iatas=]` | Routes that cross from one IATA into another. `fromHash`, `toHash` required. `iatas` optional: 2–100 codes, omitted = every IATA. The legacy `fromIata`+`toIata` pair is still accepted, but not together with `iatas`. At most 500 results, sorted by `totalHops`, then `crossHop.lastSeen` newest first. |
| `GET /routes/{iata}/{pathKey}/observations` | Retained reports that match a saved route exactly. `pathKey` comes from a route response. Window: `range` (default `24h`, max `720h`) or `since`+`until` (max 30 days); `pageCursor` for the next page; `limit` default 50. The cursor keeps the hash size and path bytes the first page matched, so later pages follow the same path even if the route's stored prefixes change. A lookup past the statement limit answers `503` + `Retry-After` ([Cost guards](#cost-guards)). |

To page `/routes`, send the last item's `lastSeen` as `cursor` and its `id` as `cursorId`. Routes share a millisecond often (one batch of upserts), and `cursorId` returns the ones that didn't fit on the previous page. `cursor` alone still works but can skip those ties. `cursorId` must be a positive integer and requires `cursor`; otherwise `400`.

`iatas` returns the routes of every listed IATA, in the same order and with the same cursors as one IATA's list, so a region pages like a single IATA. Codes are trimmed, uppercased and deduplicated; one that isn't three characters, more than 100 codes, or a list with no codes (`iatas=,`) is a `400`. `iatas` takes precedence over `iata`. An empty `iatas=` counts as absent.

The single `iata` is matched exactly as sent, so lowercase matches nothing. An `iata` that ends in a blank (`YYZ` followed by a space) matches no region and returns `200 []`.

`iatas` is new in 2.1.0: older servers, and 2.1.0 development builds from before it, ignore it and answer with every IATA's routes. A client that asks for a region checks each route's `iata`; when one is outside the list, it pages without `iatas` and filters, as before.

`/routes` and `/routes/search` return a plain array of routes:

```json
{
  "id": 412,
  "pathKey": "5d1c0e7a9b2f4c8d6e3a1b0f9c8d7e6a",
  "iata": "YOW",
  "hopCount": 3,
  "hops": [ { "nodeId": "uuid", "hashBytes": "ae", "node": { "id": "uuid", "name": "YOW_Kanata", "...": "" } } ],
  "firstSeen": 1747526400000,
  "lastSeen": 1747665456000,
  "observationCount": 57
}
```

`/routes/cross` returns `[{ sourceSegment, crossHop, targetSegment, totalHops }]`, where the segments are hop arrays as above and `crossHop` is `{ fromNode, toNode, fromIata, toIata, lastSeen }`. `sourceSegment` runs from the source node to the boundary node and `targetSegment` from its neighbor across the boundary to the destination node; `fromNode`/`toNode` are that boundary pair (the last and first hops of the segments). `totalHops` is the two segment lengths combined.

Both searches return `400` for bad input, and also `hash matches too many areas; use a longer hash or fewer iatas` when a short hash resolves in too many IATAs; show that message to the user. A search that hits the 15s timeout returns `503`.

The observations endpoint returns `{ items, hasMore, nextPageCursor, route, windowStart, windowEnd, generatedAt, matchType, matchAvailable, hashSize, pathBytes }`. Each item is `{ id, packetHash, observerId, observerName, heardAt, payloadType, payloadTypeName, rssi, snr }`. It matches on the route's full path bytes, hash size and hop count within its IATA; `limit` is capped at 200. Evidence expires with raw packets, so a route can outlive every observation that produced it.

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
  observers filter by the IATA they last reported from. `hourly` is `[{ hour, packets, observers, nodes }]`,
  oldest first with empty hours omitted: the scope's packets that hour, plus the distinct observers that
  heard them and nodes whose adverts were heard in the scope.
- `signal` gives SNR/RSSI histograms and averages; `paths` gives hash-width and path-length
  distributions. Both have an `hourly` array, require `since` and `until` (at most 30 days) and read the
  hourly rollups, so empty or not-yet-rolled hours are missing. Each `paths` hour carries `maxEntries`,
  the longest path heard that hour (0 if only empty paths were heard).
- `observer-comparison` counts distinct flood packets heard by A only, B only and both, over a required
  `since`/`until`. The observers must be different; an unknown one is a `404`. Response:
  `{ observerA, observerB, since, until, totalPackets, onlyA, onlyB, both }`.
- `clock-drift` lists repeaters and room servers whose last advert clock is off by more than
  `nodes.clock_drift_threshold`, worst first. It is current state, not windowed.
  `clockDriftSeconds` (here and on node detail) is the advert's clock minus the server's, in seconds.
  A device clock decades off gives values from about -1.8 × 10⁹ to +2.5 × 10⁹ (the negative bound
  grows over time); every value fits a JSON number exactly.
- `radio-presets` is `[{ preset, iata, sourceType, count }]`, where `preset` is `freqMhz,bwKhz,sf` and
  `sourceType` is `observer` or `node`; it is rebuilt every `background.view_refresh` (default `1h`).
  `node-types` is `[{ nodeType, nodeTypeName, count }]` over all known nodes.

### Traces

```
GET /api/v1/traces?type=TRACE&scope=<name>&since=<ms>&until=<ms>
GET /api/v1/traces/{tag}
```

`/traces` reads a per-tag summary kept at ingest and also accepts `iatas`, `region` and `regionId`.
A `since`, `until` or `cursor` that is not epoch ms is a `400`.
Filters apply to whole tags: `type` is `TRACE` if any packet in the tag is multi-hop and `PING`
otherwise, `scope` matches the first scope seen, and `since`/`until` match the tag's first hearing.
Counts and times always describe the whole tag.

It returns a plain array, most recently heard first, default limit 50. To page, pass the last item's
`lastHeardAt` as `cursor` and its trace tag (hex) as `cursorTag`; the tag breaks ties between traces
last heard in the same millisecond. `/traces/{tag}` is a `404` for an unknown tag.

A list item:

```json
{
  "traceTag": "a3f1b2c4",
  "firstHeardAt": 1747665450000,
  "lastHeardAt": 1747665462000,
  "packetCount": 3,
  "iataCount": 2,
  "traceType": "TRACE",
  "pathHashes": ["ae", "9b", "f3"],
  "snrValues": [7.25, 4.5, -1.0]
}
```

`pathHashes` and `snrValues` come from the most complete observation. The detail is
`{ traceTag, packets }`, one entry per packet: `{ packetHash, routeType, routeTypeName, scope, firstHeardAt,
lastHeardAt, rawPath, resolvedRoute }`. `rawPath` is `[{ hash, snr }]` as received; `resolvedRoute` uses the
resolved hop shape from packet detail.

### Server info

```
GET /api/v1/info
```

Public, no key. Counts against the normal rate limit and is sent with `Cache-Control: no-cache`.

```json
{
  "minAppVersion": "0.1.1", "minWebVersion": "2.0.3", "serverVersion": "2.0.4",
  "features": { "polling": true, "accounts": "off", "registration": false, "telemetryRequests": false, "alerts": false, "alertChannels": { "email": false, "push": false }, "atlasTelemetry": true, "atlas7d": true, "mapTelemetry": true, "appDeviceLabel": true },
  "display": { "temperatureUnit": "c", "distanceUnit": "metric" },
  "limits": { "atlas": 20 }
}
```

`minAppVersion` and `minWebVersion` are the oldest BEACON Mobile and Beacon Web releases allowed
to use this server, as strict `X.Y.Z` strings, or `null` when there is no requirement. Each is the
higher of the server's built-in floor and the operator's `mobile.min_app_version` /
`web.min_web_version`. With `websocket.require_origin` on, `minAppVersion` is at least `2.1.1`, the
first release that sends a [WebSocket ticket](#websocket-ticket). `serverVersion` is the server's API version (`X.Y.Z`, no `v`), the same value
Swagger shows. Servers older than this endpoint return `404`. See
[Mobile-specific concerns](#mobile-specific-concerns) for how the app uses it.

`features` tells a client which optional parts of the API this server offers, so it can hide what is off.

| Flag | Meaning |
|---|---|
| `polling` | True when [repeater polling](repeater-polling.md) is enabled on this server. Clients show the reading charts only when it is true. |
| `accounts` | A string: `"off"`, `"local"` or `"portal"`. `"local"` and `"portal"` mean [user accounts](#user-accounts) are on; `"portal"` is sign-in through the MeshMapper portal. |
| `registration` | True when new sign-ups are open. Only meaningful when `accounts` is `"local"`; always `false` for `"portal"`. |
| `portalUrl` | The portal's base address. Present only when `accounts` is `"portal"`. |
| `telemetryRequests` | True when [telemetry requests](#telemetry-requests) are on: polling and accounts are on, `BEACON_SECRET_KEY` is set and `polling.requests_per_user` is not 0. |
| `alerts` | True when [alerts](#alerts) are on: accounts are on and at least one channel is on. |
| `alertChannels` | `{"email": bool, "push": bool}`: the channels this server sends alerts by. Always present. |
| `push` | `{"server": "https://push.meshcorebeacon.ca", "pushId": "inst_…"}`: the push server the app gets a device handle from, and this server's Push ID there. Present only while `alertChannels.push` is true. See [Push delivery](#push-delivery). |
| `atlasTelemetry` | True when the server accepts the `telemetry` Atlas view and `telemetryTiles` on node pins, and the `72h` [node telemetry](#node-telemetry) range. Always true on servers that have it. |
| `atlas7d` | True when the server accepts the `7d` range on [`/me/atlas`](#atlas-sync). Always true on servers that have it. |
| `mapTelemetry` | True when the server has [latest node telemetry](#latest-node-telemetry). Always true on servers that have it. It stays true when polling is off. A client shows its map telemetry toggle only when both `mapTelemetry` and `polling` are true. |
| `appDeviceLabel` | True when `POST /auth/app/token` takes a `deviceLabel`. Always true on servers that have it. The app sends one only when this is true: an older server refuses the unknown field. |

`display` holds the instance's display units, set by the operator in [`display`](configuration.md#display-units):

| Field | Values | Meaning |
|---|---|---|
| `temperatureUnit` | `c` or `f` | The unit clients show temperatures in, and the unit [alert](alerts.md) text and temperature limits use. |
| `distanceUnit` | `metric` or `imperial` | The unit clients show distances in. |

`limits` holds the instance caps:

| Field | Meaning |
|---|---|
| `atlas` | The most cards one Atlas holds, set by [`atlas.limit`](configuration.md#atlas-size) (1 to 100, default 20). It applies to an Atlas kept in the browser or app and to one synced through [`/me/atlas`](#atlas-sync), whose `limit` is the same number. |

The API itself stays in Celsius and metric whatever `display` says. Alert temperature limits are still stored and sent as tenths of a degree C. Clients convert for display.

A client must treat a missing `features`, as sent by an older server, as all off, a missing `registration` as `false`, and a missing `portalUrl` or `push` as none, a missing `alertChannels` as both off, a missing `atlasTelemetry` as `false`, a missing `atlas7d` as `false` (do not offer `7d` or send it; a saved `7d` Atlas shows and sends `3d`), a missing `mapTelemetry` as `false` (hide the toggle), a missing `appDeviceLabel` as `false`, a missing `display` as `c` and `metric`, and a missing `limits.atlas` as 12, the cap before it was configurable. A client that does not know an `accounts` value other than `"off"` and `"local"` should treat it as `"off"`.

Beacon Web calls `/info` on load and again when the tab regains focus (at most once a minute). When
its own version is lower than `minWebVersion` it shows a full-screen "reload" screen instead of the
app. A `404`, a `null` or malformed value, and network errors never block.

### WebSocket ticket

```
GET /api/v1/ws-ticket
```

Public, no key. Counts against the normal rate limit and is sent with `Cache-Control: no-store`.

```json
{ "ticket": "AAABmZ1s4CgLBvU1n1yN3v8hQm9YtVq2", "expiresAt": 1793470167000 }
```

For clients that send no `Origin` header, such as BEACON Mobile. The client sends `ticket` in the
`X-Beacon-Ticket` header of its next `/ws` upgrade. A ticket works until `expiresAt` (60 seconds),
only from the address that asked for it (IPv6: the same /64), and only on the server process that
issued it, so a restart retires every outstanding ticket. Fetch a fresh one before each connect.
Only servers with `websocket.require_origin` on check it; browsers never need one. Servers older
than this endpoint return `404`.

### Admin

All under `/api/v1/admin/`, bearer key required (see [Auth](#auth)).

| Endpoint | Notes |
|---|---|
| `GET /admin/config` | Running CORS settings with defaults applied, `auth.configured`, `ingest.broker_count` (configured broker workers, not connection status), `mobile.min_app_version` and `web.min_web_version` (read-only effective floors; `""` when there is none), and `guards` (below). No credentials, broker addresses, channel material or database connection settings. |
| `PUT /admin/config` | Replaces `cors.allowed_origins`, `guards.enforce` or both until the next restart. JSON body up to 16 KiB. |
| `GET /admin/db/statements` | `pg_stat_statements` for this database, summed by statement name. `503` when the extension is missing or not preloaded. |
| `GET /admin/db/planguard` | The last report of the daily plan check. `?fresh=true` runs it now, at most one run per 5 minutes. `404` while `planguard.daily_check` is off or before the first run; `500` when no run has succeeded. Details below. |
| `GET /admin/users`, `PUT /admin/users/{id}`, `DELETE /admin/users/{id}` | Manage [user accounts](#operator-user-routes). `503` while accounts are off or the server is read-only. |
| `GET /admin/accounts`, `POST /admin/accounts` | List or create operator account records (name only; not logins). |
| `GET /admin/accounts/{id}`, `DELETE /admin/accounts/{id}` | Fetch or deactivate one. |
| `GET /admin/polling` | Repeater polling settings: `paused`, `pausedUntil` (epoch ms or `null`), `configPaused`, `excludedNodes` (64 hex each), `configExcludedNodes`, `authority` and `observers`, each `{publicKey, blocked, approved, note}`. `paused` is the stored pause and reads `false` once `pausedUntil` has passed; `configPaused` is `polling.paused` from config, which pauses every observer whatever the stored state says. `configExcludedNodes` is `polling.excluded_nodes`; the policy excludes the union of both lists. `authority` is `polling.authority`, `evidence` or `approved`. `noPasswordBlocked` is a list of repeater keys (64 hex) that gave admin access to a blank login, and `adminStops` lists `{targetPublicKey, observerPublicKey, reportedAt}`. `503` unless `polling.enabled` is true and the server is not read-only. |
| `GET /admin/polling/targets` | Who polls what. `{targets: [...]}`, at most 500 repeaters with a live claim or an assignment, newest claim first. Each is `{publicKey, latestTrustedReading, latestReading, candidates}`; the two times are epoch ms or `null`, `latestTrustedReading` follows the same rule as `latest_ts` in [Owners](#owners) and `latestReading` counts every observer. Each candidate is `{observerPublicKey, rank, evidenceSnr, evidenceCount, keyMode, state, misses, lastOk, approved}`: `rank` is `0` for the poller, `1` and up for standbys and `null` when unassigned; `evidenceSnr` and `evidenceCount` come from the last election; `keyMode`, `state`, `misses` and `lastOk` come from the observer's live claim and are empty, `0` or `null` when it has none; `lastOk` is epoch ms or `null`; `approved` is the operator's flag for the observer. Each target also has `requested` (a telemetry request is in use for it) and `requests` (how many requests name it). Same `503` rule as above. |
| `PUT /admin/polling/targets/{target}` | `{"noPasswordBlocked": false}` lifts the block on passwordless [telemetry requests](#telemetry-requests) for one repeater (64 hex characters in the path). Only `false` is accepted (`400` otherwise). Returns the body, or `404` for a repeater Beacon has no record of. Body up to 4 KiB. |
| `DELETE /admin/polling/admin-stops/{target}/{observer}` | Clears one admin stop so the observer can be offered the requested repeater again. `204`, or `404`. Both keys are 64 hex characters. |
| `PUT /admin/polling/state` | Replaces `{paused, pausedUntil, excludedNodes}`. `pausedUntil` is epoch ms in the future or `null`; excluded keys are 64 hex characters (repeats count once), and together with `configExcludedNodes` they may name at most 16 distinct repeaters. Otherwise `400` with a message giving the counts, and nothing changes. Body up to 4 KiB, `application/json`, unknown fields rejected. Returns the full state. |
| `PUT /admin/polling/observers/{publicKey}` | Replaces one observer's `{blocked, approved, note}` (note up to 200 characters). The key is 64 hex characters in either case. Returns the observer. |
| `GET /admin/backup` | Streams a private `.tar.gz` of the database and saved config. Off unless `backup.enabled: true`; needs `pg_dump` in the server's runtime. One export at a time (`409`), `504` on timeout, `507` over the size limit. Contains secrets. |

`PUT /admin/config` accepts `{"cors":{"allowed_origins":[...]}}`, `{"guards":{"enforce":[...]}}`
or both, and applies them immediately. Both are validated before either is applied, so a rejected
update changes nothing. It is runtime-only: nothing is written to disk, and a restart reloads the
file. The response carries `config`, `persisted: false` and `requires_restart: false`. Send 1 to
32 ASCII http(s) origins of at most 512 bytes each, with an optional single hostname wildcard; a
lone `*` allows all. Empty or null lists, paths, queries, credentials, control characters and
unknown fields are rejected. Concurrent updates apply one at a time; requests already in flight
may see the old settings.

`guards` in the config reports the [cost guards](#cost-guards):

```json
{ "enforce": ["other", "routes"], "observe_only": false, "budget": "shadow", "api_plan_layout": "custom_all" }
```

`enforce` lists the families that refuse; every other family only counts. `observe_only` is true
under `database.api_plan_layout: single`, where every family observes whatever `enforce` says.
`budget` is always `shadow`. In a `PUT`, `guards.enforce` is a list of family names (`routes`,
`channel_messages`, `packets_global`, `packets_region`, `packets_window`, `packet_detail`,
`stats`, `other`), deduplicated and returned in that order. `[]` makes every family observe; an
unknown name is a `400`. The change applies to requests that start afterwards.

`GET /admin/db/statements` returns `{"items":[...]}`, highest total execution time first. Each
item has `name` (the statement name; statements without one are summed as `(unnamed)`), `calls`,
`exec_ms`, `plan_ms`, `shared_hit` and `shared_read` (buffer blocks), `rows` and `wal_bytes`.
Times are milliseconds rounded to microseconds. `plan_ms` stays 0 unless `pg_stat_statements.track_planning` is on.
Counters run from the last `pg_stat_statements` reset. Setup is in
[Operations](operations.md#statement-statistics).

`GET /admin/db/planguard` reports the daily plan check (see
[Configuration](configuration.md#daily-plan-check)). It is admin-only and changes nothing in the
public API. Like the other `/admin/db/` reports, its fields are snake_case, and `started_at` is
an RFC 3339 timestamp rather than epoch milliseconds:

```json
{
  "tier": "prod",
  "started_at": "2026-10-19T14:02:11.482Z",
  "duration_ms": 41873.2,
  "clean": true,
  "counts": { "ok": 120, "RETIRED_INDEX": 2, "SKIP": 640 },
  "failures": [],
  "runs": [
    {
      "entry": "routes.byiata.R01_SEA_first_l50",
      "stmt": "ListKnownRoutesByIATA",
      "mode": "custom",
      "verdict": "ok",
      "drivers": ["known_routes:Index Scan:idx_known_routes_iata_keyset"]
    }
  ]
}
```

- `clean` is true when no run is `FALSE_POSITIVE`, `MISSED` or `ERROR`.
- `counts` maps each verdict to its number of runs.
- `runs` has one item per corpus entry and plan mode (`custom` or `generic`): `entry`, `stmt`,
  `mode`, `verdict`, and when they apply `failures` (the plan rules the run broke), `drivers`
  (`relation:node:index` of each driving scan) and `skip` (why the run was not made).
- `failures` holds the failing runs in the same shape. It is `[]`, never null, when there are
  none.
- `verdict` is one of `ok`, `DETECTED`, `MISSED`, `FALSE_POSITIVE`, `RETIRED_INDEX`,
  `KNOWN_ISSUE`, `SKIP` or `ERROR`. What each means is in
  [Operations](operations.md#plan-checks-planguard).

Without `fresh`, it returns the last successful report, or `404` with
`planguard has not run yet` (the first run is about an hour after startup) or
`planguard daily check is disabled`. A read-only server cannot turn the check on, so it always
answers the latter.

`?fresh=true` runs the check now and waits for it, which can take minutes. A request during a run
joins that run. Within 5 minutes of the end of the last run it starts nothing and returns the last
successful report (`started_at` gives its age), or `500` when no run has succeeded yet. A run
that fails is a `500` too. A run started this way keeps going if the client gives up, for at most
15 minutes. A `fresh` value that is not a boolean is a `400`.

The check also feeds two metrics on the [metrics listener](operations.md#metrics):
`beacon_planguard_failures{entry,mode}` (1 for each failing run of the last check) and
`beacon_planguard_last_run_timestamp_seconds` (when the last successful check finished; 0 until
the first one, and absent while the check is off).

`POST /admin/accounts` takes `{"name": "..."}` in a body of at most 4 KiB. The name is trimmed,
case-sensitive, 1 to 128 characters with no control characters, and unique among active
accounts. `DELETE` deactivates: `204`, or `404` if missing, `409` if already inactive. The name
can then be reused. The list returns active and inactive accounts, newest first, unpaginated.

Browser admin clients need the matching methods in `cors.allowed_methods`. The default
`GET, HEAD, OPTIONS` is read-only. For an admin UI, use
`[GET, HEAD, OPTIONS, POST, PUT, DELETE]`, restrict `cors.allowed_origins` to that UI and allow
the `Authorization` and `Content-Type` headers, or preflight blocks requests that work from
curl. CORS controls browser access, not authentication.

Backup details are in [Backup and export](backup-export.md).

### User accounts

Off unless `accounts.mode` is `local` ([User accounts](accounts.md)) or `portal` ([portal sign-in](portal-sign-in.md)). With it off every route below,
under `/api/v1/auth` and `/api/v1/me`, answers `404` with code `accounts_disabled`, and no cookie is set.
These are separate from the operator records at `/admin/accounts`.

A session is the `beacon_session` cookie or `Authorization: Bearer <token>`. A request that sends a
bearer header never falls back to the cookie. The cookie is `HttpOnly`, `SameSite=Lax`, `Path=/`, and
`Secure` unless the `accounts.public_url` is `http://localhost...` or `http://127.0.0.1...`.

Rules for every route here:

- Bodies are one JSON object of at most 4 KiB with `Content-Type: application/json`, no unknown
  fields: `415`, `413` and `400` otherwise.
- Answers carry `Cache-Control: no-store`. On a read-only server every write answers `503` with code
  `read_only`.
- **Forgery check.** A `POST`, `PUT`, `PATCH` or `DELETE` authenticated by the cookie must send
  `X-Beacon-CSRF: 1`, and an `Origin` header, if there is one, must be the origin of `public_url` or
  one of `cors.allowed_origins` (`*` never counts), else `403 csrf_rejected`. Bearer requests and
  signed-out requests skip it.
- A web client on another origin needs `cors.allowed_methods`, `cors.allowed_headers` (with
  `X-Beacon-CSRF`) and `cors.allow_credentials`. See [User accounts](accounts.md#same-site-and-a-web-app-on-another-origin).

Shapes (times are epoch ms):

```json
{ "id": "uuid", "username": "ridgewalker", "displayName": "Ridge Walker", "email": "a@example.org",
  "emailVerified": true, "pendingEmail": null, "provider": "local", "createdAt": 1794700000000 }
```

```json
{ "id": "uuid", "kind": "web", "label": "Firefox on macOS", "current": true,
  "createdAt": 1794700000000, "lastUsedAt": 1794703600000, "expiresAt": 1797292000000 }
```

The first is a user, the second a session (`kind` is `web` or `app`). No response ever carries a
password hash. `provider` is `local` or `portal`; a portal user has an empty `email`.

| Route | Needs | Body | Success |
|---|---|---|---|
| `POST /auth/register` | nothing | `{username, email, password}` | `202 {"status":"check_email"}` |
| `POST /auth/verify` | nothing | `{token}` | `200 {"status":"verified"}` |
| `POST /auth/verify/resend` | nothing | `{email}` | `202 {"status":"check_email"}` |
| `POST /auth/login` | nothing | `{login, password}` | `200 {"user":{...}}`, sets the cookie |
| `POST /auth/logout` | session | none | `204`, clears the cookie |
| `POST /auth/reset/request` | nothing | `{email}` | `202 {"status":"check_email"}` |
| `POST /auth/reset/confirm` | nothing | `{token, password}` | `200 {"status":"password_set"}` |
| `POST /auth/app/code` | cookie session | `{codeChallenge, state, deviceLabel}` | `200 {"code","redirectUri"}` |
| `POST /auth/app/token` | nothing | `{code, codeVerifier, deviceLabel?}` | `200 {"token","expiresAt","user"}` |
| `GET /me` | session | | `200 {"user":{...}}` |
| `PATCH /me` | session | `{displayName}` | `200 {"user":{...}}` |
| `POST /me/password` | session | `{currentPassword, newPassword}` | `204`, ends every other session |
| `POST /me/email` | session | `{email, currentPassword}` | `202 {"status":"check_email"}` |
| `DELETE /me` | session | `{currentPassword}`, or `{confirmUsername}` for a portal user | `204`, clears the cookie |
| `GET /auth/portal/start?return=<path>` | nothing | | `302` to the portal; portal mode only |
| `GET /auth/portal/callback?code=&state=` | the `beacon_portal` cookie | | `302` into the web app with the session cookie set; portal mode only |
| `GET /me/sessions` | session | | `200 {"sessions":[...]}` |
| `DELETE /me/sessions/{id}` | session | | `204` |
| `DELETE /me/sessions` | session | | `204`, ends every session but the current one |

Notes:

- **Register, resend and reset request** never reveal whether an address is registered: the same
  status and body for a known and an unknown address. The mail is sent after the answer. A username that
  is already used, whether by a verified account or a pending sign-up, is `409 username_taken` whatever
  the address.
- **Pending sign-ups.** Each sign-up against an unverified address gets its own verify link carrying
  its own username and password. The link that is used decides which credentials the account gets, and
  it ends every earlier session of the user. Resend mails the link of the newest pending sign-up.
- **Verify** also finishes an email change: the stored email changes only when the link is used, and
  fails as `token_invalid` if another user owns the address by then. It does not sign anyone in.
- **Username** 3 to 30 of `A-Za-z0-9_.-`, unique ignoring case; `admin`, `root`, `beacon`, `system`,
  `support`, `moderator` and `operator` are reserved. **Email** one address of at most 254 bytes,
  stored lower case. **Display name** 1 to 40 characters after trimming. **Password** at least 12
  characters and at most 128 bytes. It is converted to Unicode NFC first, on every route that takes a
  password, and the 12 characters (runes, not UTF-16 units or bytes) and the 128 bytes (UTF-8) are
  counted after that. It is refused when it is one repeated character, contains the username or the
  email's local part (ignoring case), or is on the common-password list. The local-part check is
  skipped when the local part is shorter than 3 characters; that is deliberate, because a name such as
  `al` would refuse a large share of ordinary passwords. The messages are "Password must be at least
  12 characters." and "Password must be at most 128 bytes." A client should count characters, not
  bytes, for its own check of the minimum. Refusals are `422 weak_password` with the reason in
  `message`, or `422 invalid_input`.
- **Login** `login` is a username or an email. An unknown name and a wrong password both give
  `401 invalid_credentials`, so does a disabled user. `403 email_unverified` comes only after the
  password was right.
- **Throttle.** 10 wrong passwords within 15 minutes for one typed name or one account refuse further
  checks for 15 minutes: `429 too_many_attempts` with `Retry-After`. A password reset clears it.
- **Reset confirm** ends every session of the user. A password the policy refuses does not use up the
  link.
- **Links** in mail are `<public_url>/?view=verify#token=...` and `<public_url>/?view=reset#token=...`
  (an email-change link is a verify link). The token is in the URL fragment so that a browser never
  sends it to a server and no proxy or access log sees it. The web app also still accepts
  `?token=...`, for links mailed before the change. Verify and email-change links last 24 hours,
  reset links 1 hour. All are single use. While a user is disabled, a reset link or an
  email-change link for it fails as `token_invalid`; an email-change link whose address was taken
  meanwhile also fails as `token_invalid` and is not used up.
- **Sessions.** Web: 30 days, rolling. App: 180 days, rolling, hard end 365 days after creation, at
  most 10 per user (the oldest is ended). The rolling expiry is written at most once every 5 minutes.
  `DELETE /me/sessions/{id}` with an id that is not the user's changes nothing; a bad id is
  `422 invalid_input`; ending the current session also clears the cookie.
- **App sign-in.** The user must be signed in on the web. `/auth/app/code` takes the base64url
  SHA-256 of a random verifier as `codeChallenge` (S256 only), a `state` of at most 256 characters
  and a `deviceLabel`, and returns a one-time `code` and `redirectUri`, always `meshcorebeacon://auth`.
  The app sends `code` and `codeVerifier` to `/auth/app/token`, and its own `deviceLabel` (such as
  `Beacon app on iOS`) when `/info` has `features.appDeviceLabel`. That label names the session; when it
  is missing or blank the session keeps the label the browser sent with the code. The code lasts 5 minutes and is used
  up before the verifier is checked, so a wrong verifier needs a new code. The `token` goes in the
  `Authorization: Bearer` header. Beacon mails the user when an app signs in. Without the cookie,
  `/auth/app/code` is `401 not_signed_in`.
- **Delete** removes the user and everything it owns in one transaction. A portal user sends
  `confirmUsername` (their own username) instead of a password; a wrong one, or a `currentPassword`,
  is `422 invalid_input`.
- **Portal mode.** `start` stores a state for 10 minutes against the `beacon_portal` cookie and
  redirects to the portal; `callback` always redirects, to `<public_url><return>` with
  `beacon_session` set, or to `<public_url>/?view=signin&error=portal` on any failure including a
  cancel. Both answer `503 read_only` on a read-only server. In portal mode `register`, `verify`,
  `verify/resend`, `login`, `reset/request`, `reset/confirm`, `/me/password` and `/me/email` answer
  `404 portal_managed`. See [Sign-in through the MeshMapper portal](portal-sign-in.md).
- **Mail.** Beacon mails the account address when a password is changed (by reset or from the
  profile), mails the old address when an email change is applied, and when an app signs in.
- **Reset links** are bound to the address they were mailed to: after the address changes, an
  earlier reset link is `token_invalid`.
- **Resend** repeats the newest pending sign-up even if its link has expired.
- **Credential races.** Sign-in, password and email changes, reset, delete and the app code exchange
  are serialised per user. An app code minted before a reset or password change is `token_invalid`
  at exchange.

Rate limits per client address, on top of the normal REST limit: register 5 / 5 min, login 10 / 1 min, verify 30 /
1 min, resend and reset request 5 / 5 min, reset confirm 10 / 5 min, app token 10 / 1 min, every other
`/auth` and `/me` write 60 / 1 min together. The answer is `429 rate_limited` with `Retry-After`.

Error codes the account routes use:

| Status | Code | When |
|---|---|---|
| 404 | `accounts_disabled` | Accounts are off. |
| 401 | `not_signed_in` | No valid session. |
| 401 | `invalid_credentials` | Wrong name, email or password, or a wrong current password. |
| 403 | `email_unverified` | Right password, address not confirmed. |
| 403 | `registration_closed` | `accounts.registration` is `closed`. |
| 403 | `csrf_rejected` | The forgery check failed. |
| 400 | `token_invalid` | A link or code is wrong, used or expired. |
| 409 | `username_taken` | The username is in use. |
| 422 | `weak_password` | The password breaks the rules; `message` says why. |
| 422 | `invalid_input` | Another value is out of range. |
| 429 | `rate_limited` | A per-address limit; `Retry-After` in seconds. |
| 429 | `too_many_attempts` | The password throttle; `Retry-After` in seconds. |
| 503 | `read_only` | The server is read-only. |
| 503 | `service_unavailable` | Sent with `Retry-After: 5`, never a sign-out or a wrong password: keep the token and what was typed and retry. Two causes: the session could not be looked up, or, on a route that hashes or checks a password (sign-up, sign-in, reset confirm, password change, email change, account delete), the request waited more than 5 seconds for a turn (at most 4 password hashes run at once). The second has the message "The server is busy. Try again in a moment." |
| 404 | `portal_managed` | A local sign-up or password route in portal mode. |

#### Operator user routes

Bearer admin key, see [Auth](#auth). `503` while accounts are off or the server is read-only.

- `GET /admin/users?search=&cursor=&limit=` lists users newest first. `limit` is 1 to 200, default 50;
  `search` is part of a username or email, at most 100 characters. Returns `{items, nextCursor}`;
  `nextCursor` is missing on the last page. Each item is a user plus `disabled` and `lastLoginAt`
  (epoch ms or `null`).
- `PUT /admin/users/{id}` with `{"disabled": true}` ends every session of the user and refuses new
  sign-ins; `false` lifts it. Returns `{user}`. `404` for an unknown id.
- `DELETE /admin/users/{id}` removes the user and everything it owns in one transaction, taking the same locks as a telemetry request change: `204`, or `404`.

### Atlas sync

A signed-in user's [Atlas](atlas.md#sync-to-an-account), up to the server's
[`atlas.limit`](configuration.md#atlas-size) (1 to 100, default 20). Both routes need a
session (`401 not_signed_in`) and follow the [rules for account routes](#user-accounts) above. `PUT`
takes a body of at most 256 KiB, passes the forgery check and answers `503 read_only` on a read-only
server. Atlas sync is on whenever accounts are.

```
GET /api/v1/me/atlas
```

```json
{ "revision": 7, "range": "24h", "limit": 20,
  "pins": [
    { "kind": "node", "publicKey": "<64 hex>", "id": "uuid or null", "observerId": "uuid or null",
      "name": "Hilltop", "tiles": ["packets", "snr", "rssi", "noise"], "view": "telemetry",
      "telemetryTiles": ["battery", "noise", "uptime", "packets"] },
    { "kind": "observer", "observerPublicKey": "<64 hex>", "observerId": "uuid or null", "name": "Roof listener" }
  ] }
```

`range` is `24h`, `3d` or `7d`; `7d` only on a server that reports `features.atlas7d`. At `7d` a
client reads `168h` in hourly buckets: `/nodes/{id}/activity?range=168h`, and
`/observers/{id}/activity`, `/observers/{id}/telemetry` and `/nodes/{id}/telemetry` with
`range=168h&interval=1h`. A node pin has `publicKey` and `id`; an observer pin has
`observerPublicKey`. `observerId` is the observer record with that key, or `null`. `tiles` (exactly
four distinct metric ids, see [Atlas](atlas.md#choosing-the-observer-tiles)) and `view` (`heard`, `observer` or `telemetry`, node pins only) are left out when not set.
`telemetryTiles` (node pins only) is exactly four distinct ids from `battery`, `noise`, `uptime`,
`airtime`, `temperature`, `packets`, `signal` and `errors`; it holds the Telemetry view's tiles,
apart from `tiles`, which stay the Observer view's. It is left out when the default applies. A client
ignores a `view` or field it does not know. An observer pin whose key now has a node
record comes back as a node pin.

```
PUT /api/v1/me/atlas
{ "baseRevision": 7, "range": "24h",
  "pins": [ { "kind": "node", "publicKey": "<64 hex>", "name": "Hilltop", "tiles": [...], "view": "telemetry", "telemetryTiles": [...] },
            { "kind": "observer", "observerId": "uuid", "observerPublicKey": "<64 hex>", "name": "..." } ] }
```

Replaces every pin. A node pin needs `publicKey`. An observer pin needs `observerId` or
`observerPublicKey`, and if it sends both they must name the same observer. A `name` is at most 160
Unicode code points (not UTF-16 units). Answers `200` with the Atlas that this save committed, `revision` plus one. The body is read inside the same transaction, so a save from another device that lands right afterwards does not change what this answer says.

| Status | Code | When |
|---|---|---|
| 409 | `atlas_conflict` | `baseRevision` is not the stored revision. The body is the usual error plus the stored Atlas as `current`, at the top level: `{"error":{"code":"atlas_conflict","message":"..."},"current":{...}}`. |
| 422 | `invalid_input` | Bad range, more pins than `limit` (`atlas.limit`, default 20), a bad key, id, tiles, telemetryTiles or view, `telemetryTiles` on an observer pin, or the same radio pinned twice. `message` names the pin. |
| 400, 413, 415, 429 | | As for other account routes. |

Removing a radio from the Atlas deletes its alert rules in the same transaction.

### Telemetry requests

A user asks for a repeater or room server to be polled. See [Requested telemetry](telemetry-requests.md).
With requests off (`features.telemetryRequests` is false) every route here answers
`404 requests_disabled`. All need a session, are cookie writes that pass the forgery check, and
answer `503 read_only` on a read-only server.

```
GET /api/v1/me/telemetry-requests
```

```json
{ "limit": 6,
  "requests": [
    { "id": "uuid",
      "node": { "id": "uuid or null", "publicKey": "<64 hex>", "name": "Hilltop" },
      "status": "waiting", "statusReason": "No observer can reach this repeater yet.",
      "statusReasonCode": "no_observer", "hasPassword": true,
      "createdAt": 1794700000000, "updatedAt": 1794700000000,
      "poller": { "observerId": "uuid", "name": "North Ridge", "state": "not_direct", "stateAt": 1794703500000 },
      "latestReadingAt": 1794703600000 } ] }
```

Oldest first. `poller` and `latestReadingAt` are `null` when there is none; `latestReadingAt` is the
newest trusted reading. `statusReasonDays` (integer) is present only with the `offline` code. A
password is never returned, only `hasPassword`.

`poller.state` is what the poller's own latest live claim says about this repeater, so a user can see
why a poll is not working even while `status` is `active`. `poller.stateAt` is epoch ms when that claim
was received, or `null` when the observer has no live claim (the same cutoff the polling service uses
for a live claim). The same `poller` object is in the create and update answers.

| `poller.state` | Meaning for the user |
|---|---|
| `pending` | The observer has the repeater but has not tried it yet (also shown when its claim sent no state). |
| `ok` | The observer logged in and got a reading on its last try. |
| `no_reply` | The observer tried and the repeater did not answer. It tries again later. |
| `login_failed` | The repeater did not accept the guest password. |
| `admin_stop` | The repeater answered with admin access, so the observer stopped. |
| `not_direct` | The observer cannot hear the repeater directly (zero hops), so it cannot poll it. |
| `not_claimed` | The observer's live claim does not list this repeater, or it has no live claim, for example after a reboot. |
| other | Any other state the firmware sends, passed through in lower case and cut to 32 characters. |

`status` and `statusReasonCode` do not change because of `poller.state`.

`status` and `statusReasonCode`:

| `status` | `statusReasonCode` | Meaning |
|---|---|---|
| `active` | empty | An observer polls it, or the requests ride on a poll already set. |
| `waiting` | `no_observer` | No observer can reach the repeater yet (none approved in `approved` mode, none with evidence or request support). |
| `waiting` | `no_seat` | Every observer that can reach it is at its polling maximum. |
| `login_failed` | `login_failed` | The repeater did not accept the guest password. |
| `login_failed` | `blank_login_failed` | The repeater did not accept a blank or hello login. |
| `admin_stopped` | `admin_stopped` | The password gave admin access and Beacon deleted it. |
| `admin_stopped` | `blank_blocked` | The repeater gives admin access to a blank login; a guest password is needed. |
| `disabled` | `offline` | No observer heard the repeater for `statusReasonDays` days. Only a `waiting` or `active` request becomes `disabled`; `login_failed` and `admin_stopped` keep their status and code. |
| `disabled` | `observer` | The repeater is also an observer that sent status over MQTT in the last 7 days, so it reports its own telemetry and is not polled. A `waiting` or `active` request on it becomes `disabled`, and `enabled: true` is refused until the observer has sent no status for 7 days. |
| any | `other` | A reason the server has no code for. Show `statusReason`. |

`statusReason` is the English sentence for the same reason.

```
POST /api/v1/me/telemetry-requests
{ "nodeId": "uuid", "password": "optional" }
```

`password` is optional, 1 to 15 bytes with no zero byte, and must be a guest password, never an
admin password. Absent, `null` or empty means the blank or hello login. Body at most 4 KiB. Answers
`201` with the single request object.

```
PATCH /api/v1/me/telemetry-requests/{id}
{ "password": "new" }        or  { "password": null }   or  { "enabled": true }
```

At least one field. `enabled` can only be `true`, and restarts a `disabled` request. On a
`login_failed` or `admin_stopped` request it changes nothing: only a new password restarts those,
and they keep their status and reason code even while nobody hears the repeater. `null` removes the
password (a blank or hello login); on an `admin_stopped` request it is refused with
`422 password_invalid` and the request stays as it was, because that user must enter a guest
password. A `login_failed` request may still switch to the blank login. Answers `200` with the
request. Status can change in the same step as the edit that caused it (create, edit, enable,
cleanup), not only at the next election.

```
DELETE /api/v1/me/telemetry-requests/{id}
```

`204`; deletes the stored password too.

| Status | Code | When |
|---|---|---|
| 404 | `requests_disabled` | Requests are off. |
| 404 | `not_found` | Unknown node, or an unknown or foreign request id. |
| 409 | `already_requested` | The user already has a request for this repeater (wins over the limit). |
| 409 | `request_limit` | The user holds `limit` requests. |
| 409 | `no_password_blocked` | The repeater gives admin to a blank login, so a request needs a guest password. Also when removing the password on such a repeater. |
| 422 | `not_a_repeater` | The node is not a repeater or room server. |
| 422 | `observer_node` | The node is also an observer that sent status in the last 7 days, so it reports its own telemetry. Answered on create, and on `enabled: true`. |
| 422 | `password_invalid` | The password is not 1 to 15 bytes without a zero byte. |
| 422 | `invalid_input` | Another value is out of range, or `enabled` is `false`. |

### Alerts

Rules on radios in the user's Atlas. See [Alerts](alerts.md). With alerts off every route here
answers `404 alerts_disabled`. All need a session and follow the account route rules.

```
GET /api/v1/me/alerts
```

```json
{ "channels": {
    "email": { "available": true, "enabled": true, "reason": "" },
    "push": { "available": true, "enabled": true, "hasDevice": true } },
  "targets": [
    { "id": "uuid or null", "kind": "node", "publicKey": "<64 hex>", "name": "Hilltop", "polled": true,
      "available": ["gone_quiet", "back_online", "clock", "battery_low"],
      "unavailable": { "temperature": "This repeater does not report a temperature." },
      "unavailableCodes": { "temperature": "no_data" },
      "rules": [
        { "id": "uuid", "kind": "battery_low", "threshold": 3500, "thresholdHigh": null,
          "enabled": true, "state": "ok", "stateChangedAt": 1794700000000, "lastSentAt": null } ] } ] }
```

One target per Atlas pin, in Atlas order. `id` is the node's or observer's id as used by
`/nodes/{id}` and `/observers/{id}`, or `null` when the radio no longer exists. `polled` is true while
the radio has a current source of telemetry: for a repeater, an observer holds it as a polling
assignment now; for an observer, it sent status telemetry in the last 24 hours. Old readings do not
count, so a target that was polled can read `polled: false`, its telemetry kinds then move to
`unavailable` with `not_polled` (repeater) or `observer_no_data` (observer), and its telemetry rules
read `inactive`. It is what offers the telemetry kinds and, for a repeater, the 3 and 6 hour
`gone_quiet` thresholds. `available` is always an array and `unavailable` always an object of kind to
English reason. `unavailableCodes` is always an object with the same keys, kind to a stable code a
client can translate; fall back to the sentence for a code it does not know.

`channels` is how the user's alerts reach them. Each user chooses: email, push, both or neither.

| Field | Meaning |
|---|---|
| `email.available` | The server sends alert mail and the user has a verified address. |
| `email.enabled` | The user's switch. Defaults to `true`. |
| `email.reason` | Why email is not available: `server_off` (the server does not send alert mail), `portal_account` (portal users have no address) or `unverified_email`. Empty when available. |
| `push.available` | The server sends push notifications. |
| `push.enabled` | The user's switch. Defaults to `true`, and registering a device turns it on. |
| `push.hasDevice` | An app session of the user has registered a device. Push reaches the user only when this and `enabled` are both true. It is the only thing the API says about devices. |

A channel reaches the user only when it is both available and enabled. Clients show both switches
in the user's profile, with the reason when one is not available.

Reason codes (`unavailableCodes`, and `reasonCode` in the `kind_unavailable` error):

| Code | Meaning |
|---|---|
| `observer_no_data` | An observer does not report this value. |
| `repeaters_only` | Only repeaters report this value; the radio is not one. |
| `not_polled` | No observer holds this repeater as a polling assignment now; request telemetry for it first. |
| `no_data` | A polled repeater does not report this value. |
| `observer_no_clock` | Observers have no clock drift value. |
| `clock_repeaters_only` | Only repeaters and room servers report a clock. |
| `needs_gone_quiet` | `back_online` needs an enabled `gone_quiet` rule (error only). |
| `not_applicable` | The kind has nothing to do with this radio (error only). |

Kinds, thresholds and ranges (`threshold` is null where none is taken):

| `kind` | Unit | Accepted |
|---|---|---|
| `gone_quiet` | hours | 12, 24, 48; also 3 and 6 for observers and polled repeaters |
| `back_online` | none | null. Needs an enabled `gone_quiet` rule on the radio. |
| `clock` | seconds | 300, 3600, 86400 |
| `battery_low` | millivolts | 2500 to 5000 |
| `battery_falling` | millivolts per day | 100, 200, 300 |
| `rebooted` | none | null |
| `temperature` | tenths of a degree C | `threshold` is the low limit, `thresholdHigh` the high limit, -500 to 1500; at least one, low below high. With both set on a rule that is on, `thresholdHigh - threshold` must be at least 20 (2.0 C), else `422 invalid_threshold` ("The range must be at least 2 degrees wide."); turning a rule off is not held to it |
| `noise_high` | dBm | -130 to -50 |
| `observer_offline` | minutes | 30, 60, 180, 360 (observers only) |

`state` is `ok`, `firing`, `inactive` (the data is gone, or the radio is no longer polled) or `unknown` (not enough data yet).
`request_attention` is announced to users with telemetry requests but is not a stored rule and never
appears here.

```
PUT /api/v1/me/alerts/rules
{ "target": { "kind": "node", "publicKey": "<64 hex>" }, "kind": "battery_low",
  "threshold": 3500, "thresholdHigh": null, "enabled": true }
```

Creates or updates the rule for that radio and kind. `enabled` defaults to `true`. Answers `200`
with the rule. Changing a threshold or turning a rule on resets its state to `unknown`. A rule that
is being turned off is checked for shape only. Turning `back_online` on needs an enabled `gone_quiet`
rule on the radio (`422 kind_unavailable`, `needs_gone_quiet`). If that rule is later turned off or
deleted, the `back_online` rule reads `inactive` until one is enabled again.

```
DELETE /api/v1/me/alerts/rules/{id}
```

`204`.

```
PUT /api/v1/me/alerts/channels
{ "email": true, "push": false }
```

Turns the user's channels on or off. A field left out stays as it is; at least one is needed, else
`422 invalid_input`. Answers `200` with the `channels` object above. Any session may call it, web or
app. A switch can be on while its channel is unavailable: it takes effect once the channel is.

```
POST /api/v1/me/devices
{ "platform": "ios", "pushToken": "h_3k9x2m7q…", "payloadKey": "<base64 of 32 bytes>" }
DELETE /api/v1/me/devices
```

Register or remove the push device of the calling app session. `platform` is `ios` or `android`.
`pushToken` is the device handle the app got from the push server for this server (see
[Push delivery](#push-delivery)): it starts with `h_`, is ASCII with no spaces and at most 256
characters. `payloadKey` is the AES-256 key the app generated for this
device, standard base64 of exactly 32 bytes; the server encrypts every notice for the device with
it. Registering turns the user's push switch on. `POST` answers `204`, `DELETE` `204` even when there
was none. A handle another session or user held moves to this session. `POST` is limited to 10 per
user per 10 minutes, and answers `404 push_disabled` when the server does not send push. These routes
need an app session: a cookie session gets `403 app_session_required`. No route returns a handle or
a key.

| Status | Code | When |
|---|---|---|
| 404 | `alerts_disabled` | Alerts are off. |
| 409 | `not_on_atlas` | The radio is not pinned on the user's Atlas. |
| 422 | `kind_unavailable` | The radio cannot have this kind; `message` is the English reason and `error.reasonCode` its code (the only error with that extra field). |
| 422 | `invalid_threshold` | The threshold is out of range or the wrong shape for the kind. |
| 422 | `invalid_input` | A bad key or rule id; a bad platform, push token or payload key; or a channels body with neither field. |
| 404 | `push_disabled` | `POST /me/devices` on a server that does not send push. |
| 404 | `not_found` | Unknown or foreign rule id. |
| 403 | `app_session_required` | A device route called with a cookie session. |

#### Push delivery

Every Beacon server sends push through the MeshCore Beacon push server, `features.push.server`
(the official one is `https://push.meshcorebeacon.ca`). Its API is documented in the
[beacon-push README](https://github.com/MeshCore-Beacon/beacon-push/blob/dev/README.md). The app:

1. Reads `features.push` from `/info`. Without it the server does not send push.
2. Gets its device token (APNs on iOS, FCM on Android), then `POST <push.server>/v1/handles`
   `{"pushId": "<features.push.pushId>", "platform": "ios"|"android", "token": "...", "apnsEnvironment": "sandbox"|"production"}`
   (`apnsEnvironment` on iOS only), which answers
   `{"handle", "handleSecret"}`. The handle works for this server only. Keep both per server.
3. Generates a random 32-byte payload key for this server and keeps it in secure storage.
4. Calls `POST /api/v1/me/devices` with the handle as `pushToken` and the key as `payloadKey`.
5. When the platform gives a new token: `PUT <push.server>/v1/handles/{handle}`
   `{"handleSecret", "token", "apnsEnvironment"}` (`apnsEnvironment` on iOS only)
   for every server. The handle stays the same, so the Beacon server needs no call.
6. On sign-out or removing the server: `DELETE /api/v1/me/devices`, then
   `DELETE <push.server>/v1/handles/{handle}` `{"handleSecret"}`.

The push server sends iOS notices straight to Apple (APNs) and Android notices through Firebase
Cloud Messaging, so Google sees no iPhone traffic. The fields are the same on both platforms (FCM
data on Android, custom payload keys next to `aps` on iOS):

```json
{ "v": "1", "pushId": "inst_…", "serverName": "Ottawa Mesh", "messageId": "m_…", "ct": "<base64>" }
```

`serverName` is the name the server registered with the push server; the server cannot change it.
Android gets a data-only, high-priority message that the app decrypts and shows itself. iOS gets a
placeholder alert (title: the server name, body: "New alert") with `mutable-content: 1`, so a
Notification Service Extension decrypts the message and replaces the text.

`ct` is AES-256-GCM with the device's payload key: `nonce (12 bytes) || ciphertext || tag (16 bytes)`,
with associated data `"beacon-push/v1:" + pushId`. It opens to the notice, not to ready-made text:

```json
{ "v": 1, "kind": "battery_low", "name": "Ridge Rptr", "value": 3412, "detail": "",
  "targetKind": "node", "publicKey": "<64 hex>", "id": "<uuid or empty>", "tempUnit": "c" }
```

| Field | Meaning |
|---|---|
| `kind` | An alert kind from the table above, or `request_attention`. Ignore a notice of a kind you do not know. |
| `name` | The radio's name, already cleaned and cut to 40 characters (see [Names in alerts](alerts.md#names-in-alerts)). Cap it again before showing it. |
| `value` | The figure the sentence gives, in the kind's unit: hours for `gone_quiet`, millivolts for the battery kinds, tenths of a degree C for `temperature`, dBm for `noise_high`, seconds for `clock`, minutes for `observer_offline`. Always `null` for `back_online`, `rebooted` and `request_attention`, which give no figure. |
| `detail` | For `request_attention`: `login_failed`, `admin_stopped` or `disabled`. Otherwise empty. |
| `targetKind`, `publicKey`, `id` | The radio, to open it on tap: by `id` when present, else by key. |
| `tempUnit` | `c` or `f`, the instance's display unit for temperatures. |

The app builds the sentence itself from these fields, in the same words as alert mail, and always
shows which server sent it. A server therefore cannot put text of its own choosing under the app's
name.


## Firmware polling

Observer firmware with repeater polling calls four routes and publishes two kinds of MQTT
message. They follow the firmware's contract, not the rest of this one:

- JSON is **snake_case**, not camelCase.
- The HTTP routes are at the site root, **outside `/api/v1`**, with no authentication. The policy
  and owners routes have their own rate limit (240 requests a minute per client IP, separate from
  `/api/v1`); the two key routes have none.
- Times are RFC 3339 strings, not epoch milliseconds. Keys are hex.

How an operator turns this on is in [Repeater polling](repeater-polling.md). The bodies are not
in the Swagger UI.

### Routes

| Route | Answer |
|---|---|
| `GET /api/guest-polling/policy` | `200`, the policy. `503` when the polling state cannot be read. |
| `GET /api/guest-polling/owners` | `200`, `{"nodes": {...}, "policy": {...}}`. `503` when the polling state cannot be read, or when the answer lists a requested repeater and Beacon cannot record what it served (see below). |
| `POST /api/guest-keys` | `404`, always. The body is never read or logged. |
| `GET /api/shared-guest/key` | `404`, always. |

Beacon never accepts polling keys, so the two key routes always answer `404`. (Guest passwords for [telemetry requests](telemetry-requests.md) go the other way: Beacon sends them, sealed, in the owners answer.) They answer `404` even to a client
that has used up the policy and owners rate limit. The firmware
reads a `404` on the policy route as "upload keys instead", so the policy route never answers
`404`. With `polling.enabled: false` the policy and owners routes still answer `200`, with
`paused: true`, no hosts and no nodes. A read-only server answers the policy route normally, and the
owners route too unless the answer would carry a requested repeater: Beacon has to record which
password version each requested entry was served with, and a read-only instance cannot write it.
Whenever the owners answer cannot record that (a read-only instance, a store error) or cannot read
the password in use, it is `503` with `Retry-After: 60`, never a `200` that leaves the requested
entries out, because the device would read an omitted entry as withdrawn and drop it. Owners
answers with no requested repeater are unaffected.

A device that is full of requested repeaters and holds a younger one gets the older replacement in
the same answer: the seat a withdrawn target frees is offered to it at once. A repeater the
observer polls from its own configuration never uses a requested seat.

When Beacon cannot read the pause state, the caller's blocked flag or the caller's roles, both
routes answer `503` with the standard error body, an exact `Content-Length` and
`Retry-After: 60`. On any non-200 answer other than `404` the firmware keeps the policy it
already has, including a pause or a block, and keeps its last roles until they lapse. A made-up
`200` would un-pause and unblock everyone instead.

Both GET routes take these query parameters. Beacon only uses the ones listed. Each answer
has an exact `Content-Length`, is not compressed and carries `Cache-Control: no-store`. It is
under 6144 bytes for an observer that claims 8 or fewer repeaters, which is all the firmware
claims.

| Parameter | Meaning |
|---|---|
| `observer` | The observer's public key, 64 hex characters in either case. It is a claim, not proof. Anything else is treated as no observer. |
| `client` | The firmware family, such as `meshcore.observer_fw`. Up to 32 characters. |
| `client_version` | The firmware version. Up to 23 characters. |

### Policy

Every answer carries every field.

| Field | Type | Meaning |
|---|---|---|
| `reading_format` | string | Always `"telemetry"`. |
| `mqtt_hosts` | array of strings | `polling.mqtt_hosts`, lowercase. |
| `direct_s` | int | Poll window in seconds, 1800 to 86400. |
| `one_hop_s` | int | Twice `direct_s`, at most 86400. Sent for completeness. |
| `grace_s` | int | Wait per standby rank in seconds, 600 to 7200. |
| `max_requests` | int | 1 to 3. |
| `version` | string | A short hash of the settings. The firmware echoes it in claims. |
| `paused` | bool | Every observer should stop. |
| `paused_until` | string | RFC 3339 end of a timed pause, or `""`. |
| `observer_blocked` | bool | The caller is blocked. |
| `min_plugin_version` | string | Sent as `""`. |
| `version_ok` | bool | False when `client` is the observer firmware, `polling.min_client_version` is set, and `client_version` is below it, missing or not a version. |
| `excluded_nodes` | array of strings | Repeater keys never polled, up to 16. |
| `node_windows` | object | Sent as `{}`. |

### Owners

`nodes` has one entry for each repeater the caller has a live claim for, keyed by the repeater's
64 lowercase hex key. It is `{}` when the observer is unknown, blocked or has no live claim.

| Field | Type | Meaning |
|---|---|---|
| `role` | string | `polling` or `standby`, or `excluded` for an excluded repeater. Case-sensitive. |
| `mine` | bool | True for the poller. A repeater nobody has been elected for yet is `polling` and `mine` for every claimant; once one has a poller, a claimant the election has not placed (for example one not approved in `approved` mode) is the last standby. |
| `excluded` | bool | True when `role` is `excluded`. |
| `standby_rank` | int | 1 and up for a standby. The poller and excluded repeaters send 1. |
| `owner_hops` | int | `0`. |
| `requested` | bool | Present and `true` only for a repeater given to this observer by a [telemetry request](telemetry-requests.md). |
| `pw` | object | Only on a requested entry that has a guest password in use: `{"epk","ct","tag","ver"}`, lower hex, `ver` an integer. The password sealed to this observer's public key. Sent fresh on every answer; `ver` changes when the password in use changes. An entry whose password cannot be sealed is left out of the answer. |
| `latest_ts` | string or `null` | `sampled_at` of the newest trusted reading for the repeater. A reading is trusted when its observer is ranked for the repeater (poller or standby) and Beacon saw it hear the repeater's own adverts directly (zero hops) in the day before the last election. Other readings, including a poller's without that evidence, are stored but do not count here, so claiming a repeater alone does not hold anyone back. Advert evidence comes from the observer's own packet uplink, so it is not proof; with `polling.authority: approved` only approved observers are ranked. |

### Claim message

An observer publishes this to `meshcore/{IATA}/{OBSERVER PUBLIC KEY, UPPER HEX}/polling` at QoS 1,
not retained, and refreshes it about every 30 minutes. Each claim replaces the previous one.

```json
{"v": 2, "origin": "Name", "origin_id": "<UPPER hex>", "timestamp": "2026-11-13T22:13:20Z",
 "plugin": "meshcore.observer_fw/<fw>", "policy_version": "a1b2", "community": true,
 "accepts_requests": true, "request_slots": 3,
 "nodes": [{"node_id": "<lower hex>", "reply_hops": 0, "via": null, "key": "own", "snr": 6.5,
            "state": "ok", "misses": 2,
            "last_attempt": "2026-11-13T22:11:40Z", "last_ok": "2026-11-13T22:12:30Z"}]}
```

- `origin_id` must equal the topic's key. Otherwise the claim is dropped.
- `node_id` is the repeater's 64 character public key. `key` is `own`, `shared` or `password`.
- `state` is `pending`, `ok`, `no_reply`, `login_failed`, `admin_stop` or `not_direct`. A claim
  with an unknown state is still accepted.
- `misses` is the count of failed polls in a row. At 3 or more the observer ranks as failing,
  below healthy observers with the same kind of evidence. An observer with advert evidence ranks
  above one without, failing or not.
- `accepts_requests` says the observer takes requested repeaters, and `request_slots` is how many
  free seats it has (clamped to 8). A node entry with `"requested": true` is one the observer was
  given by a request. A report of `admin_stop` or `login_failed` for a requested repeater counts only
  from the observer that was assigned it. A `login_failed` report does not count while that observer
  has a trusted reading of the repeater stored after the current option became active and within the
  last 4 hours (the default; four times `polling.direct_window`, at most 48 hours). A claim and the state reports in it are stored in one
  transaction, so a report that fails to store rolls the claim back and the device's next claim
  repeats it.
- `accepts_requests`, `request_slots`, `requested`, `state`, `misses`, `last_attempt` and
  `last_ok` are absent from claims sent by clients without request support. Those still send
  `"v": 2`; there is no v1 claim.
- At most 32 repeaters per claim; a longer claim is dropped whole. The firmware sends up to 8.
- A claim is ignored when its `timestamp` is not newer than the stored one or is more than
  10 minutes ahead of Beacon's clock. It is live for 65 minutes after Beacon receives it.
- A claim that arrives less than 30 seconds after Beacon received the observer's last one is
  dropped. The check is made where the claim is stored, so two claims arriving together cannot
  both pass it. The firmware claims at most once a minute.
- `misses` and `request_slots` are clamped (0 to 255, 0 to 8). A number too large for a 64-bit
  integer counts as absent.

### Reading message

Published to `.../telemetry` (`"v": 2`) or `.../battery` (`"v": 1`), same topic prefix, QoS 1,
not retained. One reading per message in the v2 format, up to 1664 bytes. Beacon accepts up to 8
readings in one message and drops a message with more.

```json
{"v":2,"origin":"Name","origin_id":"<UPPER hex>","timestamp":"2026-11-13T22:13:23Z",
 "plugin":"meshcore.observer_fw/<fw>","readings":[{"node_id":"<lower hex>","battery_mv":4038,
 "source":"poll","reply_hops":0,"method":"status","sampled_at":"2026-11-13T22:13:20Z","snr":6.5,
 "stats":{"uptime_secs":788089,"noise_floor":-116,"last_rssi":-114,"last_snr":1.25,"tx_queue":0,
 "packets_recv":81234,"packets_sent":20276,"recv_flood":76198,"recv_direct":5012,
 "sent_flood":19211,"sent_direct":1065,"tx_air_secs":18301,"rx_air_secs":73835,
 "flood_dups":56298,"direct_dups":36,"recv_errors":28074,"err_events":2},
 "tag":1794484800,"packet_hash":"0123456789ABCDEF"}]}
```

- `method` is `status` (has `stats`) or `telemetry` (has `lpp`, raw CayenneLPP as lower hex up to
  160 bytes, and `battery_mv` and `temperature_c` when decoded). Any other value drops the message.
  Each `stats` key is present only if the repeater's reply was long enough to hold it.
- A `battery_mv` of 0 means no voltage and is stored as none.
- Beacon decodes the parts of `lpp` that parse and keeps the bytes.
- A reading is stored once per repeater, observer, `tag` and `method`. With no `tag`, `sampled_at`
  stands in for it. The same reading arriving twice is stored once.
- Beacon keeps at most one new reading per observer, repeater and `method` every 5 minutes of
  receive time; a second one inside that window is dropped. The firmware's shortest poll window is
  30 minutes.
- Beacon keeps at most 120 readings per observer in any hour of receive time, across all
  repeaters and methods, and drops the rest. The firmware stays under 100.
- Both reading limits hold when readings from one observer arrive at the same moment: Beacon
  checks and stores one observer's readings one at a time.
- A `stats` value or `battery_mv` that does not fit its column (32-bit for the small counters,
  64-bit for the large ones) is stored as absent, never wrapped.
- A reading is stored only when `origin_id` equals the topic key, the observer has a live claim
  listing `node_id`, the observer is not blocked, and `sampled_at` is not more than a minute in
  the future or more than 2 hours old. Other readings in the message are skipped one by one.
- `packet_hash` lets Beacon count how many other observers heard the repeater's reply. It is
  never required. It must be 16 hex characters (8 bytes); any other value is ignored and the
  reading is kept without it.

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
- **No Origin.** By default an upgrade without an `Origin` is accepted. With `websocket.require_origin` on, it needs a valid [ticket](#websocket-ticket) in `X-Beacon-Ticket`, or it gets `403` and no upgrade.
- **Concurrent connections.** At most `websocket.max_connections_per_ip` (default 5) open sockets per IP (IPv6 per /64). Past that, the socket is accepted and immediately closed with code `1013` (try again later), reason `connection limit reached`, so the browser can back off.

**Compression.** When a Chromium or Firefox browser, or BEACON Mobile (`dart:io`), offers `permessage-deflate`, the server accepts it with context takeover, unless the client asks for `no_context_takeover`, and compresses messages of 128 bytes or more. The live feed shrinks about 3× on the wire. Every other client gets uncompressed frames: iOS WebKit (every browser on iPhone and iPad) drops the connection on the first compressed message, and an iPad in desktop mode reports itself as Mac Safari, so Safari on any platform is not compressed. Message content is the same either way.

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

- `iatas`, plus the member IATAs of any `regionIds` (numeric IDs as strings) and `regionSlugs`. Unknown regions are skipped. If regions were given and they, together with `iatas`, yield no IATA, the subscription is still acknowledged with `subscribed` and receives no events.
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
- `observation.rssi` and `observation.snr` are each omitted when not measured, under the same rule as the REST observation fields. Servers before 2.3.0 sent 0.
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

Each connection has a 256-event send buffer. When it is full, the server evicts the oldest queued event to make room and then queues the new one; if that still fails, the new event is dropped too. A `lagged` notice follows with the count:

```json
{ "v": 1, "type": "lagged", "droppedCount": 1, "since": 1747665440000 }
```

`droppedCount` is 1 or 2 per buffer notice; `since` is when the notice was sent. Several can arrive in a burst.

Each connection also has a send budget: at most `websocket.max_send_bytes_per_second` of event JSON (default 1048576, 1 MiB/s, counted before compression), with a `websocket.send_burst_bytes` burst (default 8 MiB). Events past it are dropped, and a `lagged` notice, at most one every 30 seconds, carries how many; its `droppedCount` can be any size. The connection stays open.

When the server-wide live queue overflows, every connection with a subscription gets a `lagged` notice whose `droppedCount` is the number of events lost for all clients since the last such notice. These are sent at most once every 5 seconds.

Clients should treat any `lagged` notice as a gap and refresh the affected view over REST.

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

**WebSocket ticket.** Before each connect the app asks `GET /ws-ticket` and sends the ticket in
`X-Beacon-Ticket`. If that request fails (a `404` from an older server, a network error), it
connects without one, which works on any server that leaves `websocket.require_origin` off.

**Minimum app version.** The app calls `GET /info` on launch, on return to foreground and when
the user switches servers. When the app's own version is lower than `minAppVersion` (compared
numerically, part by part), it blocks that server behind an "update required" screen until the
app is updated. Other servers stay usable. `minAppVersion: null` means no requirement. A `404`
comes from a server that predates the endpoint and also means no requirement. Network errors,
timeouts and other failures do not block: the app keeps using the server and checks again next
time.

---

## Open questions

- **packetObservation payload size.** With `resolvePath` on, events carry the full resolved path with node coordinates, which can be 1-2 KB each in heavy traffic. Clients that only need counts should leave it off and fetch detail over REST.

(See [Questions and Answers](high-level-design.md#questions-and-answers) in the high level design for resolved items.)
