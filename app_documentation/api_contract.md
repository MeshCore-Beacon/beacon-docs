# MeshCore Tower: API Contract

The Go server exposes one HTTP base, one REST API namespace under `/api/v1/`, and one WebSocket endpoint at `/ws`. React (web) and Flutter (mobile) consume identical endpoints. All JSON is camelCase. Times are Unix epoch milliseconds as integers (e.g. `1747668456000`), bytes are hex strings, UUIDs are stringified.

**Why epoch ms:** smaller on the wire, no timezone or parser ambiguity, no string parsing in hot paths (chart axes, sorts, comparisons), and matches the units MeshCore uses internally (uint32 Unix seconds in adverts and traces). JS `new Date(ms)` and Dart `DateTime.fromMillisecondsSinceEpoch(ms)` consume it natively.

Query params follow the same convention: `since` and `until` are epoch ms integers. `range` is a human-friendly duration string (`24h`, `7d`, `30d`) for stats endpoints where the exact boundary doesn't matter.

---

## Auth

No authentication in v1. All endpoints are publicly readable. Operational configuration is managed via the config file described in the [High Level Design](high_level_design.md#operations-and-configuration).

## Versioning

Path is the contract: `/api/v1/`. Breaking changes get `/api/v2/`. Backward-compatible additions just expand the existing payloads. WebSocket messages include a `type` discriminator and a top-level `v: 1` field so we can evolve in place.

---

## REST endpoints

### Live Packets

```
GET /api/v1/packets?iata=YOW&payloadType=4&routeType=1&since=<ts>&until=<ts>&limit=50&cursor=<opaque>
```

Returns the most recent packets matching filters, newest first, with cursor-based pagination. Each row is a packet summary with the latest observation rolled in:

```json
{
  "packets": [
    {
      "packetHash": "9e9b7d6a91cab445",
      "payloadType": 4,
      "payloadTypeName": "ADVERT",
      "routeType": 1,
      "routeTypeName": "FLOOD",
      "firstHeardAt": 1747665456000,
      "lastHeardAt": 1747665462000,
      "observationCount": 15,
      "latestObserver": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "displayName": "FlightlessDt",
        "iata": "KEH"
      },
      "summary": "Advert \"WW7STR/PugetMesh Cougar\""
    },
    {
      "packetHash": "3c4f8a12b7e60d91",
      "payloadType": 5,
      "payloadTypeName": "GROUP_TEXT",
      "routeType": 1,
      "routeTypeName": "FLOOD",
      "firstHeardAt": 1747665440000,
      "lastHeardAt": 1747665455000,
      "observationCount": 8,
      "latestObserver": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "displayName": "Hull_Hospital",
        "iata": "YOW"
      },
      "summary": "Group text on #ottawa"
    }
  ],
  "nextCursor": "eyJsYXN0IjoiM2M0ZjhhMTJiN2U2MGQ5MSJ9"
}
```

### Packet detail

```
GET /api/v1/packets/{packetHash}
```

Full packet with all decoded fields plus all observations, with each observation's resolved path inline.

#### Common fields (all payload types)

Every packet detail response includes these top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `packetHash` | string | Content-based dedup hash (hex) |
| `headerByte` | string | Raw header byte (hex, e.g. "14"). Bit-packed as VVPPPPRR: bits 0-1 = routeType, bits 2-5 = payloadType, bits 6-7 = payloadVersion |
| `payloadType` | number | 0x00-0x0F per MeshCore protocol |
| `payloadTypeName` | string | Human-readable name (ADVERT, TRACE, GROUP_TEXT, etc.) |
| `payloadVersion` | number | 0-3 from bits 6-7 of header |
| `routeType` | number | 0-3 from bits 0-1 of header |
| `routeTypeName` | string | TRANSPORT_FLOOD, FLOOD, DIRECT, or TRANSPORT_DIRECT |
| `totalBytes` | number | Total packet size in bytes |
| `transportCodes` | object or null | Present only for TRANSPORT_FLOOD / TRANSPORT_DIRECT |
| `transportCodes.regionCode` | number | uint16 LE, MeshCore radio region code |
| `transportCodes.subRegionCode` | number | uint16 LE, return/home region code |
| `originPubkey` | string or null | Sender public key hex, if extractable from payload (e.g. adverts) |
| `rawPayload` | string | Full payload as hex |
| `parsedPayload` | object | Decoded payload, structure depends on payloadType (see below) |
| `decrypted` | boolean | Whether encrypted content was successfully decrypted |
| `channelHash` | string or null | 1-byte channel ID hex, if group/channel packet |
| `firstHeardAt` | number | Epoch ms, first observation |
| `lastHeardAt` | number | Epoch ms, most recent observation |
| `observationCount` | number | Total observations across all observers |
| `observations` | array | Per-observer hearings (see observation fields below) |

#### Observation fields

Each entry in the `observations` array:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Observation ID (for afterId pagination) |
| `observerId` | string | Observer UUID |
| `observerName` | string | Observer display name |
| `iata` | string | IATA code where this observer heard the packet |
| `heardAt` | number | Epoch ms |
| `pathLengthByte` | number | Raw path_length byte (encodes hash_size + hop_count) |
| `hashSize` | number | 1, 2, 3, or 4 bytes per hop hash |
| `hopCount` | number | 0-63 |
| `pathBytes` | string | Raw path bytes hex (hashSize * hopCount bytes) |
| `rssi` | number | Received signal strength (dBm) |
| `snr` | number | Signal-to-noise ratio (dB) |
| `propagationTimeMs` | number | Time from origin to observer (ms) |
| `radio` | object | Radio parameters |
| `radio.freqMhz` | number | Frequency in MHz |
| `radio.spreadFactor` | number | LoRa spread factor |
| `radio.bandwidthKhz` | number | Bandwidth in kHz |
| `radio.codingRate` | number | Coding rate |
| `sourceBroker` | string | "mqtt1" or "mqtt2" |
| `rawPacket` | string | Complete wire-format hex as received by this observer (header + optional transport codes + path_length_byte + path_bytes + payload). Differs per observation because path bytes accumulate as the packet hops. |
| `resolvedPath` | array | Per-hop resolution results (see path resolution in high level design) |

#### parsedPayload by payload type

The `parsedPayload` object is fully typed per payload type. Every payload includes a `type` field matching the packet's `payloadTypeName`.

##### Advert (0x04)

```json
{
  "type": "ADVERT",
  "publicKey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
  "timestamp": 1747665450,
  "signature": "a1b2c3d4e5f6...64 bytes hex",
  "signatureValid": true,
  "flags": 144,
  "deviceRole": 2,
  "deviceRoleName": "REPEATER",
  "hasLocation": true,
  "hasName": true,
  "hasFeature1": false,
  "hasFeature2": false,
  "latitude": 48.4284,
  "longitude": -123.3656,
  "name": "WW7STR/PugetMesh Cougar"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `publicKey` | string | 32-byte Ed25519 public key (hex) |
| `timestamp` | number | uint32 unix timestamp from advert |
| `signature` | string | 64-byte Ed25519 signature (hex) |
| `signatureValid` | boolean | Whether the signature verified against publicKey |
| `flags` | number | Raw flags byte |
| `deviceRole` | number | 0=Unknown, 1=ChatNode/Companion, 2=Repeater, 3=RoomServer, 4=Sensor |
| `deviceRoleName` | string | Human-readable role name |
| `hasLocation` | boolean | Bit 4 of flags |
| `hasName` | boolean | Bit 7 of flags |
| `hasFeature1` | boolean | Bit 5 of flags |
| `hasFeature2` | boolean | Bit 6 of flags |
| `latitude` | number or null | Degrees, present if hasLocation is true |
| `longitude` | number or null | Degrees, present if hasLocation is true |
| `name` | string or null | Node name, present if hasName is true |

##### Trace (0x09)

```json
{
  "type": "TRACE",
  "traceTag": "a3f1b2c4",
  "authCode": 2948173621,
  "flags": 2,
  "pathHashSize": 4,
  "pathHashes": ["ae9b1c2d", "bf3c4e5f"],
  "snrValues": [10.75, 7.25, -2.5]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `traceTag` | string | 4-byte unique trace identifier (hex) |
| `authCode` | number | uint32 authentication code |
| `flags` | number | 1-byte control flags |
| `pathHashSize` | number | Bytes per hash: 1, 2, 4, or 8 (derived from lower 2 bits of flags) |
| `pathHashes` | string[] | Per-hop hashes from the trace payload, each pathHashSize bytes (hex) |
| `snrValues` | number[] or null | SNR in dB per hop (signed int8 / 4.0), derived from packet path field. Null if no path data. |

##### GroupText (0x05)

```json
{
  "type": "GROUP_TEXT",
  "channelHash": "f3",
  "cipherMac": "a1b2",
  "ciphertext": "9c8d7e6f5a4b3c2d...",
  "ciphertextLength": 42,
  "decrypted": {
    "timestamp": 1747665450,
    "flags": 0,
    "sender": "Chris",
    "message": "anyone hear that trace?"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `channelHash` | string | 1-byte channel hash (hex), first byte of SHA256 of channel shared key |
| `cipherMac` | string | 2-byte MAC (hex) for HMAC-SHA256 verification |
| `ciphertext` | string | Encrypted content (hex) |
| `ciphertextLength` | number | Ciphertext length in bytes |
| `decrypted` | object or null | Null if key not available or decryption failed |
| `decrypted.timestamp` | number | uint32 unix timestamp |
| `decrypted.flags` | number | 1-byte flags |
| `decrypted.sender` | string | Sender name parsed from message body |
| `decrypted.message` | string | Message text content |

##### TextMessage (0x02)

```json
{
  "type": "TEXT_MESSAGE",
  "destinationHash": "ae",
  "sourceHash": "bf",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b9c0d1e2f...",
  "ciphertextLength": 38,
  "decrypted": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `destinationHash` | string | 1-byte destination node hash (hex) |
| `sourceHash` | string | 1-byte source node hash (hex) |
| `cipherMac` | string | 2-byte MAC (hex) |
| `ciphertext` | string | Encrypted content (hex) |
| `ciphertextLength` | number | Ciphertext length in bytes |
| `decrypted` | object or null | Null if decryption not possible |
| `decrypted.timestamp` | number | uint32 unix timestamp |
| `decrypted.flags` | number | Flags byte |
| `decrypted.attempt` | number | Attempt counter |
| `decrypted.message` | string | Message text content |

##### Request (0x00)

```json
{
  "type": "REQUEST",
  "destinationHash": "ae",
  "sourceHash": "bf",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b...",
  "decrypted": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `destinationHash` | string | 1-byte destination node hash (hex) |
| `sourceHash` | string | 1-byte source node hash (hex) |
| `cipherMac` | string | 2-byte MAC (hex) |
| `ciphertext` | string | Encrypted content (hex) |
| `decrypted` | object or null | Null if decryption not possible |
| `decrypted.timestamp` | number | uint32 unix timestamp |
| `decrypted.requestType` | number | 1=GetStats, 2=Keepalive, 3=GetTelemetryData, 4=GetMinMaxAvgData, 5=GetAccessList |
| `decrypted.requestTypeName` | string | Human-readable request type |
| `decrypted.requestData` | string | Request-specific data (hex) |

##### Response (0x01)

```json
{
  "type": "RESPONSE",
  "destinationHash": "ae",
  "sourceHash": "bf",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b9c0d...",
  "ciphertextLength": 28,
  "decrypted": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `destinationHash` | string | 1-byte destination node hash (hex) |
| `sourceHash` | string | 1-byte source node hash (hex) |
| `cipherMac` | string | 2-byte MAC (hex) |
| `ciphertext` | string | Encrypted content (hex) |
| `ciphertextLength` | number | Ciphertext length in bytes |
| `decrypted` | object or null | Null if decryption not possible |
| `decrypted.tag` | number | Response tag |
| `decrypted.content` | string | Response content |

##### AnonRequest (0x07)

```json
{
  "type": "ANON_REQUEST",
  "destinationHash": "ae",
  "senderPublicKey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b9c0d1e2f...",
  "ciphertextLength": 24,
  "decrypted": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `destinationHash` | string | 1-byte destination node hash (hex) |
| `senderPublicKey` | string | 32-byte Ed25519 sender public key (hex) |
| `cipherMac` | string | 2-byte MAC (hex) |
| `ciphertext` | string | Encrypted content (hex) |
| `ciphertextLength` | number | Ciphertext length in bytes |
| `decrypted` | object or null | Null if decryption not possible |
| `decrypted.timestamp` | number | uint32 unix timestamp |
| `decrypted.syncTimestamp` | number or null | Room server sync-since timestamp |
| `decrypted.password` | string or null | Password for repeater/room |

##### Ack (0x03)

```json
{
  "type": "ACK",
  "checksum": "a1b2c3d4"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `checksum` | string | 4-byte CRC checksum (hex) of message timestamp + text + sender pubkey |

##### Path (0x08) -- Returned Path

A PATH packet is a "returned path" message. When Node A sends a flooded packet to Node B, each repeater along the way appends its hash to the packet-level path field. When Node B receives it, the accumulated path describes the route from A to B. Node B then sends a PATH packet back to Node A containing that discovered route, typically with an ACK or Response piggybacked as an "extra" payload. The return trip is sent DIRECT using the reversed path.

PATH shares the same encrypted envelope as Request, Response, and TextMessage: the first 2 bytes are destination/source hashes, followed by a 2-byte MAC and ciphertext. The decrypted inner payload contains the returned path hashes plus a bundled extra payload.

For a passive observer (Tower), the encrypted content cannot be decrypted without the shared secret between the two nodes. The outer envelope (destination hash, source hash, MAC) is always visible.

```json
{
  "type": "PATH",
  "destinationHash": "ae",
  "sourceHash": "bf",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b9c0d1e2f...",
  "ciphertextLength": 28,
  "decrypted": null
}
```

When decryption is possible (e.g. if Tower has the shared secret):

```json
{
  "type": "PATH",
  "destinationHash": "ae",
  "sourceHash": "bf",
  "cipherMac": "c3d4",
  "ciphertext": "5e6f7a8b9c0d1e2f...",
  "ciphertextLength": 28,
  "decrypted": {
    "pathLength": 3,
    "pathHashSize": 2,
    "pathHashes": ["ae9b", "bf3c", "d4e5"],
    "extraType": 3,
    "extraTypeName": "ACK",
    "extraData": "a1b2c3d4"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `destinationHash` | string | 1-byte destination node hash (hex), first byte of destination public key |
| `sourceHash` | string | 1-byte source node hash (hex), first byte of source public key |
| `cipherMac` | string | 2-byte MAC (hex) for encrypted data verification |
| `ciphertext` | string | Encrypted content (hex) |
| `ciphertextLength` | number | Ciphertext length in bytes |
| `decrypted` | object or null | Null if shared secret not available or decryption failed |
| `decrypted.pathLength` | number | Hop count (0-63), from bits 5:0 of the inner path_len byte |
| `decrypted.pathHashSize` | number | Bytes per hash: 1, 2, or 3, from (bits 7:6 + 1) of path_len byte |
| `decrypted.pathHashes` | string[] | Per-hop node hashes (hex), each pathHashSize bytes long |
| `decrypted.extraType` | number | Bundled payload type (lower 4 bits of extra_type byte, e.g. 0x03 = ACK, 0x01 = Response) |
| `decrypted.extraTypeName` | string | Human-readable bundled payload type name |
| `decrypted.extraData` | string | Bundled payload content (hex), e.g. a 4-byte ACK checksum or response data |

##### Control (0x0B)

Control packets have a `subType` that determines the remaining fields.

**DISCOVER_REQ (subType 0x80):**

```json
{
  "type": "CONTROL",
  "subType": 128,
  "subTypeName": "DISCOVER_REQ",
  "rawFlags": 128,
  "prefixOnly": false,
  "typeFilter": 6,
  "typeFilterNames": ["REPEATER", "ROOM_SERVER"],
  "tag": 2948173621,
  "since": 1747500000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `subType` | number | 0x80 |
| `subTypeName` | string | "DISCOVER_REQ" |
| `rawFlags` | number | Full first byte |
| `prefixOnly` | boolean | Lowest bit, whether to return only key prefixes |
| `typeFilter` | number | Bitmask for node types (bit per ADV_TYPE) |
| `typeFilterNames` | string[] | Human-readable filtered types |
| `tag` | number | uint32, randomly generated by sender for response matching |
| `since` | number or null | uint32 epoch timestamp filter, null if not present |

**DISCOVER_RESP (subType 0x90):**

```json
{
  "type": "CONTROL",
  "subType": 144,
  "subTypeName": "DISCOVER_RESP",
  "rawFlags": 146,
  "nodeType": 2,
  "nodeTypeName": "REPEATER",
  "snr": 10.75,
  "tag": 2948173621,
  "publicKey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
  "publicKeyLength": 32
}
```

| Field | Type | Description |
|-------|------|-------------|
| `subType` | number | 0x90 |
| `subTypeName` | string | "DISCOVER_RESP" |
| `rawFlags` | number | Full first byte |
| `nodeType` | number | Lower 4 bits (matches ADV_TYPE / deviceRole) |
| `nodeTypeName` | string | Human-readable node type |
| `snr` | number | Inbound SNR in dB (signed int8 / 4.0) |
| `tag` | number | uint32, reflected from DISCOVER_REQ |
| `publicKey` | string | 8 or 32 bytes hex depending on prefixOnly flag from the request |
| `publicKeyLength` | number | 8 (prefix) or 32 (full) |

##### GroupData (0x06), Multipart (0x0A), RawCustom (0x0F)

These payload types have no structured decoder yet. `parsedPayload` returns only the raw bytes:

```json
{
  "type": "GROUP_DATA",
  "raw": "a1b2c3d4e5f6..."
}
```

#### Full example: Advert packet with 2 observations

```json
{
  "packetHash": "9e9b7d6a91cab445",
  "headerByte": "11",
  "payloadType": 4,
  "payloadTypeName": "ADVERT",
  "payloadVersion": 0,
  "routeType": 1,
  "routeTypeName": "FLOOD",
  "totalBytes": 112,
  "transportCodes": null,
  "originPubkey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
  "rawPayload": "7e7662676f7f...",
  "parsedPayload": {
    "type": "ADVERT",
    "publicKey": "7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
    "timestamp": 1747665450,
    "signature": "a1b2c3d4e5f67890abcdef1234567890a1b2c3d4e5f67890abcdef1234567890a1b2c3d4e5f67890abcdef1234567890a1b2c3d4e5f67890abcdef1234567890",
    "signatureValid": true,
    "flags": 144,
    "deviceRole": 2,
    "deviceRoleName": "REPEATER",
    "hasLocation": true,
    "hasName": true,
    "hasFeature1": false,
    "hasFeature2": false,
    "latitude": 48.4284,
    "longitude": -123.3656,
    "name": "WW7STR/PugetMesh Cougar"
  },
  "decrypted": false,
  "channelHash": null,
  "firstHeardAt": 1747665456000,
  "lastHeardAt": 1747665464000,
  "observationCount": 15,
  "observations": [
    {
      "id": 12345,
      "observerId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "observerName": "FlightlessDt",
      "iata": "KEH",
      "heardAt": 1747665462000,
      "pathLengthByte": 65,
      "hashSize": 2,
      "hopCount": 1,
      "pathBytes": "ae9b",
      "rssi": -98,
      "snr": 10.75,
      "propagationTimeMs": 1936,
      "radio": { "freqMhz": 910.525, "spreadFactor": 7, "bandwidthKhz": 62.5, "codingRate": 5 },
      "sourceBroker": "mqtt1",
      "rawPacket": "1141ae9b7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f...",
      "resolvedPath": [
        { "confidence": "high", "node": { "id": "d4e5f6a7-b8c9-0123-def0-123456789abc", "name": "YOW_Kanata", "publicKey": "ae9b...", "latitude": 45.3, "longitude": -75.9 } }
      ]
    },
    {
      "id": 12346,
      "observerId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "observerName": "Hull_Hospital",
      "iata": "YOW",
      "heardAt": 1747665464000,
      "pathLengthByte": 130,
      "hashSize": 2,
      "hopCount": 2,
      "pathBytes": "ae9bbf3c",
      "rssi": -105,
      "snr": 7.2,
      "propagationTimeMs": 4122,
      "radio": { "freqMhz": 910.525, "spreadFactor": 7, "bandwidthKhz": 62.5, "codingRate": 5 },
      "sourceBroker": "mqtt2",
      "rawPacket": "1182ae9bbf3c7e7662676f7f08501a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f...",
      "resolvedPath": [
        { "confidence": "high", "node": { "id": "d4e5f6a7-b8c9-0123-def0-123456789abc", "name": "YOW_Kanata", "publicKey": "ae9b...", "latitude": 45.3, "longitude": -75.9 } },
        { "confidence": "ambiguous", "candidates": [{ "id": "e5f6a7b8-c9d0-1234-ef01-23456789abcd", "name": "YOW_Gatineau", "publicKey": "bf3c..." }, { "id": "f6a7b8c9-d0e1-2345-f012-3456789abcde", "name": "YOW_Hull_West", "publicKey": "bf3c..." }], "idBytes": "bf3c" }
      ]
    }
  ]
}
```

#### Full example: Trace packet with 2 observations

```json
{
  "packetHash": "b4c5d6e7f8a90b12",
  "headerByte": "25",
  "payloadType": 9,
  "payloadTypeName": "TRACE",
  "payloadVersion": 0,
  "routeType": 1,
  "routeTypeName": "FLOOD",
  "totalBytes": 24,
  "transportCodes": null,
  "originPubkey": null,
  "rawPayload": "a3f1b2c4d5e6f7a8...",
  "parsedPayload": {
    "type": "TRACE",
    "traceTag": "a3f1b2c4",
    "authCode": 2948173621,
    "flags": 2,
    "pathHashSize": 4,
    "pathHashes": ["ae9b1c2d", "bf3c4e5f"],
    "snrValues": [10.75, 7.25]
  },
  "decrypted": false,
  "channelHash": null,
  "firstHeardAt": 1747665470000,
  "lastHeardAt": 1747665478000,
  "observationCount": 4,
  "observations": [
    {
      "id": 12350,
      "observerId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "observerName": "FlightlessDt",
      "iata": "KEH",
      "heardAt": 1747665470000,
      "pathLengthByte": 194,
      "hashSize": 4,
      "hopCount": 2,
      "pathBytes": "ae9b1c2dbf3c4e5f",
      "rssi": -92,
      "snr": 12.5,
      "propagationTimeMs": 820,
      "radio": { "freqMhz": 910.525, "spreadFactor": 7, "bandwidthKhz": 62.5, "codingRate": 5 },
      "sourceBroker": "mqtt1",
      "rawPacket": "25c2ae9b1c2dbf3c4e5fa3f1b2c4d5e6f7a802ae9b1c2dbf3c4e5f...",
      "resolvedPath": [
        { "confidence": "high", "node": { "id": "d4e5f6a7-b8c9-0123-def0-123456789abc", "name": "YOW_Kanata", "publicKey": "ae9b1c2d...", "latitude": 45.3, "longitude": -75.9 } },
        { "confidence": "high", "node": { "id": "c3d4e5f6-a7b8-9012-cdef-0123456789ab", "name": "YOW_Barrhaven", "publicKey": "bf3c4e5f...", "latitude": 45.28, "longitude": -75.76 } }
      ]
    },
    {
      "id": 12351,
      "observerId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "observerName": "Hull_Hospital",
      "iata": "YOW",
      "heardAt": 1747665478000,
      "pathLengthByte": 195,
      "hashSize": 4,
      "hopCount": 3,
      "pathBytes": "ae9b1c2dbf3c4e5f72d8a314",
      "rssi": -108,
      "snr": 5.5,
      "propagationTimeMs": 6200,
      "radio": { "freqMhz": 910.525, "spreadFactor": 7, "bandwidthKhz": 62.5, "codingRate": 5 },
      "sourceBroker": "mqtt2",
      "rawPacket": "25c3ae9b1c2dbf3c4e5f72d8a314a3f1b2c4d5e6f7a802ae9b1c2dbf3c4e5f...",
      "resolvedPath": [
        { "confidence": "high", "node": { "id": "d4e5f6a7-b8c9-0123-def0-123456789abc", "name": "YOW_Kanata", "publicKey": "ae9b1c2d...", "latitude": 45.3, "longitude": -75.9 } },
        { "confidence": "high", "node": { "id": "c3d4e5f6-a7b8-9012-cdef-0123456789ab", "name": "YOW_Barrhaven", "publicKey": "bf3c4e5f...", "latitude": 45.28, "longitude": -75.76 } },
        { "confidence": "none", "idBytes": "72d8a314" }
      ]
    }
  ]
}
```

### Search

```
GET /api/v1/packets/search?q=<query>&field=<field>&iata=<iata>&limit=50
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | yes | Search query |
| `field` | `hash` \| `path` \| `payload` | yes | Which field to search |
| `iata` | string | no | Region filter (omit for all) |
| `limit` | number | no | Max results (default 50) |

Response uses the same `PacketSummary[]` shape as the existing packet list, plus a total count:

```json
{
  "packets": [
    {
      "packetHash": "9e9b7d6a91cab445",
      "payloadType": 4,
      "payloadTypeName": "ADVERT",
      "routeType": 1,
      "routeTypeName": "FLOOD",
      "firstHeardAt": 1747665456000,
      "lastHeardAt": 1747665462000,
      "observationCount": 15,
      "latestObserver": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "displayName": "FlightlessDt",
        "iata": "KEH"
      },
      "summary": "Advert \"WW7STR/PugetMesh Cougar\""
    },
    {
      "packetHash": "7a2e9b0c44df1583",
      "payloadType": 4,
      "payloadTypeName": "ADVERT",
      "routeType": 1,
      "routeTypeName": "FLOOD",
      "firstHeardAt": 1747664200000,
      "lastHeardAt": 1747664218000,
      "observationCount": 6,
      "latestObserver": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "displayName": "Hull_Hospital",
        "iata": "YOW"
      },
      "summary": "Advert \"VE3XYZ/Ottawa Repeater\""
    }
  ],
  "total": 42
}
```

Search behavior by field:
- `field=hash` -- substring match on packet_hash (case-insensitive)
- `field=path` -- match against resolved path node names across all observations for a packet
- `field=payload` -- match against raw_payload hex string (case-insensitive)

### Nodes

```
GET    /api/v1/nodes?type=2&iata=YOW&firmwareTier=1.14.0&limit=50&cursor=<opaque>
GET    /api/v1/nodes/{nodeId}
GET    /api/v1/nodes/{nodeId}/observations?since=<ts>&limit=50&cursor=<opaque>
```

The node detail includes `iatasHeardIn`, `supportsMultibytePaths`, `supportsMultibyteTraces`, `minFirmwareVersion`, and the latest advert payload.

### Observers

```
GET    /api/v1/observers?iata=YOW&type=meshcoretomqtt&broker=mqtt1&status=online
GET    /api/v1/observers/{observerId}
GET    /api/v1/observers/{observerId}/telemetry?range=24h
GET    /api/v1/observers/{observerId}/adverts?limit=50&cursor=<opaque>
```

Telemetry response is a time-bucketed array suitable for direct chart consumption:

```json
{
  "range": "24h",
  "interval": "5m",
  "points": [
    {
      "t": 1747612800000,
      "batteryMv": 4180,
      "airtimeTxPct": 0.37,
      "airtimeRxPct": 1.05,
      "noiseFloorDb": -103.2,
      "uptimeSeconds": 86400,
      "queueLength": 0,
      "receiveErrors": 3
    },
    {
      "t": 1747613100000,
      "batteryMv": 4175,
      "airtimeTxPct": 0.42,
      "airtimeRxPct": 1.12,
      "noiseFloorDb": -102.8,
      "uptimeSeconds": 86700,
      "queueLength": 1,
      "receiveErrors": 3
    }
  ]
}
```

### Channels

```
GET    /api/v1/channels?iata=YOW&limit=50
GET    /api/v1/channels/{channelHash}
GET    /api/v1/channels/{channelHash}/messages?since=<ts>&limit=50&cursor=<opaque>
```

The list accepts a single `iata=` or comma-separated `iatas=YOW,YYZ` (case-insensitive)
and returns channels heard in those IATAs within the packet retention window.

Channel keys are configured via the server config file.

### IATAs and regions

```
GET    /api/v1/iatas
GET    /api/v1/iatas/{iata}
GET    /api/v1/regions
GET    /api/v1/regions/{regionId}
```

Region creation, IATA assignment, and grouping are managed via the server config file.

### Stats

```
GET /api/v1/stats/overview?iata=YOW
GET /api/v1/stats/observations?iata=YOW&range=24h&interval=1h
GET /api/v1/stats/payloadBreakdown?iata=YOW&range=24h
GET /api/v1/stats/topNodes?iata=YOW&range=24h&limit=10
GET /api/v1/stats/topObservers?iata=YOW&range=24h&limit=10
```

All stats endpoints accept either `iata` (one or comma-separated) or `regionId` (expands to all IATAs in that super-region).

### Errors

All errors use a consistent shape:

```json
{ "error": { "code": "not_found", "message": "Packet not found" } }
```

Codes: `bad_request`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal`.

---

## WebSocket

Single endpoint at `/ws`. Bidirectional JSON messages. Subscription-based: the client tells the server what it wants, the server pushes matching events.

### Connection

```
GET /ws
```

On connect the server sends a `hello`:

```json
{ "v": 1, "type": "hello", "serverTime": 1747665456000, "connectionId": "uuid" }
```

### Client → Server messages

All client messages have a `type` and an optional `id` for request/ack correlation.

**`subscribe`**: add filters to this connection. Multiple subscriptions on one connection are unioned (OR semantics): an event matches if it matches any active subscription.

```json
{
  "v": 1,
  "type": "subscribe",
  "id": "sub-1",
  "scope": {
    "iatas": ["YOW"],
    "regionIds": [],
    "payloadTypes": [4, 5],
    "routeTypes": [],
    "channelHashes": [],
    "observerIds": [],
    "events": ["packetObservation", "observerStatus"]
  }
}
```

All scope fields are optional. Omitted = no filter on that dimension. Empty array = match nothing for that dimension. Server replies with `subscribed`:

```json
{ "v": 1, "type": "subscribed", "id": "sub-1", "subscriptionId": "uuid" }
```

**`unsubscribe`**:

```json
{ "v": 1, "type": "unsubscribe", "id": "unsub-1", "subscriptionId": "uuid" }
```

**`ping`**:

```json
{ "v": 1, "type": "ping", "id": "p-1" }
```

Server replies with `pong { id: "p-1" }`. Client should ping every 30s; server closes idle connections after 90s.

### Server → Client events

All server events have `v`, `type`, and `event` body. They carry no `id` since they're unsolicited (replies to client requests echo the original `id`).

**`packetObservation`**: emitted when a new observation hits the DB. This is the primary live event.

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
      "isFirstObservation": false,
      "totalObservationCount": 16,
      "summary": "Advert \"WW7STR/PugetMesh Cougar\""
    },
    "observation": {
      "id": 12346,
      "observerId": "uuid",
      "observerName": "NodeRunner",
      "iata": "SEA",
      "heardAt": 1747665462000,
      "pathLengthByte": 130,
      "hashSize": 2,
      "hopCount": 2,
      "pathBytes": "ae9bbf3c",
      "rssi": -105,
      "snr": 7.2,
      "propagationTimeMs": 4122,
      "sourceBroker": "mqtt2",
      "resolvedPath": []
    }
  }
}
```

`isFirstObservation: true` means this is the first time this packet has been seen, so the UI should add a new row. `false` means UI should update the existing packet row's observation count and timestamp, and if the packet is currently expanded, append the new observation card.

**`observerStatus`**: emitted when an observer's `/status` message updates them. Used for the Observer Status grid (online/offline transitions, battery curves, etc.).

```json
{
  "v": 1,
  "type": "event",
  "event": "observerStatus",
  "data": {
    "observerId": "uuid",
    "displayName": "Hull_Hospital",
    "iata": "YOW",
    "online": true,
    "batteryMv": 4180,
    "uptimeSeconds": 86400,
    "lastStatusAt": 1747665462000,
    "fields": ["batteryMv", "uptimeSeconds", "lastStatusAt"]
  }
}
```

`fields` lists which keys actually changed in this update, so the client can do partial UI refreshes without diffing.

**`nodeUpdate`**: emitted when a node's capability flags flip, when a new IATA is added to its `node_iatas`, or when an advert refreshes its location/name.

```json
{
  "v": 1,
  "type": "event",
  "event": "nodeUpdate",
  "data": {
    "nodeId": "uuid",
    "publicKey": "...",
    "name": "YOW_Kanata",
    "supportsMultibytePaths": true,
    "supportsMultibyteTraces": true,
    "minFirmwareVersion": "1.14.0+",
    "iatasHeardIn": ["YOW", "YUL"],
    "reason": "capabilityUpgraded"
  }
}
```

`reason` is one of: `advertRefresh`, `capabilityUpgraded`, `newIataHeard`.

**`channelMessage`**: emitted when a group text packet is decrypted into a chat message. Only sent to subscribers including that `channelHash` in their scope.

```json
{
  "v": 1,
  "type": "event",
  "event": "channelMessage",
  "data": {
    "channelHash": "f3",
    "channelName": "#ottawa",
    "senderName": "Chris",
    "content": "anyone hear that trace?",
    "sentAt": 1747665462000,
    "packetHash": "..."
  }
}
```

**`error`**: server-side errors that aren't replies to a specific request.

```json
{ "v": 1, "type": "error", "code": "rate_limited", "message": "Subscription scope too broad" }
```

---

## Backpressure and reconnection

The server's write buffer per connection is bounded (default 256 events). If the client can't keep up, the server drops the oldest queued events and sends a `lagged` notice:

```json
{ "v": 1, "type": "lagged", "droppedCount": 47, "since": 1747665440000, "lastObservationId": 12340 }
```

Clients should react by re-fetching the relevant REST page using `afterId` to fill the gap deterministically, then resume normal streaming.

Reconnection is the client's responsibility. On any disconnect, the client should:
1. Reconnect with backoff (1s, 2s, 5s, 10s, 30s cap)
2. Re-issue all subscriptions
3. Hit the relevant REST endpoint with `afterId=<last observation id seen>` to backfill anything missed
4. Resume streaming

There's no replay buffer for missed events; REST is the source of truth for history. This keeps the server stateless per-connection (no per-client cursors held in memory waiting for slow consumers), and reconnection is cheap. Using `afterId` rather than timestamps avoids clock-skew edge cases between server and client.

REST endpoints support `afterId` as a query param on listing endpoints:

```
GET /api/v1/packets?iata=YOW&afterId=12345&limit=100
GET /api/v1/observers/{id}/telemetry?afterId=987&limit=100
```

---

## Mobile-specific concerns

Flutter on iOS background suspension and Android battery saver will kill the WebSocket. Pattern for the mobile app:

1. On foreground: open WS, subscribe.
2. On background: close WS gracefully (don't fight the OS).
3. On return to foreground: reopen, re-subscribe, and fire a REST refresh on whatever screen is active to backfill anything missed.

The protocol doesn't need to know about backgrounding; the client just treats reconnection as the recovery mechanism.

---

## Open questions

- **packetObservation payload size.** Currently fat: includes the full resolved path with node coordinates. Could be 1-2 KB per event in heavy traffic. Slim alternative would be `{packetHash, observationId, iata, heardAt}` only, with clients fetching details via REST when needed. Tradeoff is bandwidth vs round-trip count.

(See [Questions and Answers](high_level_design.md#questions-and-answers) in the high level design for resolved items: SSE fallback, rate limiting strategy, mobile push notifications, broker bundling, pprof protection, observationId backfill.)
