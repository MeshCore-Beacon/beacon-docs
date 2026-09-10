# MeshCore Tower: High Level Design

**Codename:** Tower

A real-time packet analyzer and observer-of-observers for the MeshCore network. Tower watches the mesh from above. It passively listens to MQTT brokers, decoding LoRa packets, mapping observer health and node firmware capabilities, and surfacing the network's pulse to web and mobile clients.

This is the single source of truth for the project; sub-documents (deployment, repo layout, frontend specs) reference back to this.

---

## Table of contents

1. System overview
2. Core design insights
3. MeshCore payload types
4. Database schema
5. Operations and configuration
6. Ingestion pipeline
7. Path resolution function
8. API contract
9. Feature to schema mapping
10. UI pattern: collapsed vs expanded packet rows
11. Future features
12. Questions and Answers

---

## System overview

### Stack

- **Backend:** Single Go binary, pgx + pgxpool + sqlc for Postgres, `github.com/meshcore-go/meshcore-go` for packet decoding, internal Go channels for live WebSocket fanout
- **Database:** Postgres with BRIN + composite indexes, materialized views for aggregations
- **Cache:** Redis for hot reads (recent packets, region stats, node metadata) plus in-memory LRU in Go in front
- **Web client:** React + Vite + TypeScript + Tailwind + TanStack Query/Virtual + shadcn/ui
- **Mobile client:** Flutter (native iOS + Android)
- **Edge:** Caddy for TLS and reverse proxy
- **Deployment:** Docker Compose with four services (app, postgres, redis, caddy)
- **Observability:** pprof endpoint on the Go binary
- **MQTT brokers:** mqtt1.meshcore.ca + mqtt2.meshcore.ca over WSS, Role 2 SUBSCRIBER account auth (see Broker authentication below)

### Flow

The single Go binary connects to both MeshCore MQTT brokers over WSS with SUBSCRIBER credentials. It decodes each incoming packet, dedupes via a content-based packet hash (plus UNIQUE constraint on observations across both brokers), writes to Postgres, updates Redis caches, and fans out to connected WebSocket clients via internal Go channels.

The same binary serves REST API endpoints for historical queries, hitting Redis first and falling back to Postgres on misses. Caddy terminates TLS and reverse-proxies HTTP and WebSocket traffic to the Go binary. Web and mobile clients connect through Caddy.

### Diagram

```
   ┌─────────────────────┐    ┌─────────────────────┐
   │  mqtt1.meshcore.ca  │    │  mqtt2.meshcore.ca  │
   │  MeshCore broker    │    │  MeshCore broker    │
   │  WSS                │    │  WSS                │
   └──────────┬──────────┘    └──────────┬──────────┘
              │                          │
              │      SUBSCRIBER auth     │
              └──────────┬───────────────┘
                         ▼
              ┌──────────────────────┐
   ┌──────────┤    Go server         ├──────────┐
   │          │  Ingest + API + WS   │          │
   │          │  (single binary)     │          │
   │          └──────────┬───────────┘          │
   ▼                     │                      ▼
┌──────────┐             │              ┌──────────────┐
│ Postgres │             │              │    Redis     │
│ Packets, │             │              │ Hot reads,   │
│ metadata │             │              │ recent data  │
└──────────┘             ▼              └──────────────┘
                  ┌──────────────┐
                  │    Caddy     │
                  │ TLS + proxy  │
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       ┌───────────────┐        ┌────────────┐
       │  Web client   │        │   Mobile   │
       │ React + Caddy │        │  Flutter   │
       └───────────────┘        └────────────┘
```

### Broker authentication

The MeshCore MQTT broker (`michaelhart/meshcore-mqtt-broker`) defines three subscriber roles in its `.env` config:

- **Role 1 (Admin):** full access including `/internal` topics (which contain PII) and `$SYS/*` system topics
- **Role 2 (Full access):** all public topics, no data filtering
- **Role 3 (Limited):** public topics only, with `snr`, `rssi`, `score`, `stats`, `model`, and `firmware_version` stripped from messages

We need Role 2 because the analyzer relies on SNR and RSSI per observation. Coordinate with the broker operator to provision a Role 2 SUBSCRIBER account for the ingest service; the username and password go in our `.env`.

### Why this is fast

One process, no inter-service network hops for live packets. Postgres queries hit Redis or in-memory cache most of the time. BRIN indexes keep time-range scans cheap at billions of rows. Caddy speaks HTTP/3 and brotli. React + virtualized lists keep the UI snappy regardless of how many packets are on screen. Flutter on mobile is native-compiled and runs at 60fps by default.

---

## Core design insights

### Packets vs observations

The MeshCore packet wire format is:

```
[header (1)][transport_codes (4, optional)][path_length (1)][path (0-64)][payload (0-184)]
```

Maximum total packet size is 255 bytes (LoRa MTU constraint).

**Header byte** is bit-packed as `VVPPPPRR`:
- Bits 0-1: Route type (4 values)
- Bits 2-5: Payload type (16 values, see payload type reference below)
- Bits 6-7: Payload version (4 values)

**Transport codes** (optional 4 bytes) follow the header only when route_type is `TRANSPORT_FLOOD` or `TRANSPORT_DIRECT`. They contain `[region_code (uint16 LE)][sub_region_code (uint16 LE)]` and let repeaters do geographic flood suppression. Note: this `region_code` is MeshCore's radio region, not our IATA-based logical region.

**Path length byte** encodes BOTH the hash size and the hop count:
- Top 2 bits: `hash_size - 1` (so values 0, 1, 2, 3 mean 1, 2, 3, or 4 bytes per hop hash)
- Bottom 6 bits: hop count (0-63)
- Effective path bytes = `hash_size * hop_count`

**Path bytes** are accumulated as the packet hops. Each forwarding repeater appends its truncated node hash. Regular (non-trace) packets use 1, 2, or 3 byte hashes. Trace packets (`0x09`) use 1, 2, or 4 byte hashes. Which sizes a given repeater is capable of emitting depends on its firmware version (see Node firmware capability detection below).

**Payload** is the actual content, type-specific.

A MeshCore packet can be any payload type: adverts, acknowledgments, requests, responses, traces, plain text messages, group text messages, and so on. Chat messages (plain text and group text) are just two of the payload types. Everything we ingest is a packet.

The MeshCore decoder computes a content-based hash from the payload. This hash is the same across all observers of a single packet, regardless of which path each saw. We dedupe and identify packets by this hash.

This means:
- `packets` table: one row per unique packet (keyed on packet_hash), holds the invariant content (route_type, payload, transport codes if present)
- `packet_observations` table: one row per (packet, observer) hearing, holds the per-observation path data, SNR, RSSI, radio params (path bytes accumulate as the packet hops, so they differ per observation)

### Path resolution scope

MeshCore path hashes are 1, 2, 3, or 4 byte truncations of a node's public key. The hash size used is signaled by the top 2 bits of the path_length byte. Regular packets use 1, 2, or 3 byte hashes; trace packets (`0x09`) use 1, 2, or 4 byte hashes.

- 1 byte: 256 possible IDs (collisions guaranteed globally)
- 2 bytes: 65,536 possible IDs (collisions at scale)
- 3 bytes: 16.7M possible IDs (still possible at high density)
- 4 bytes: 4.3 billion possible IDs (collisions rare)

We store a single 4-byte prefix per (node, IATA) in `node_short_ids`. Generated columns expose 1, 2, 3, and 4 byte prefixes with their own indexes for fast lookups regardless of which hash size a given packet uses.

All path resolution must be scoped to an IATA or a set of IATAs. Even at 4 bytes, a path entry can only be confidently resolved against nodes known in the observer's geographic area.

The scope rule is:
- Default narrow scope: just the observer's IATA. The repeaters that forwarded this packet are physically near the observer, so they almost certainly live in the same IATA.
- Broader scope when viewing through a super-region: all IATAs that belong to that super-region (via `region_iatas`).

In both cases, the actual lookup runs against `node_short_ids` filtered to `iata IN (...)`. The function takes the list of IATAs and the hash size, and returns one resolution per hop with a confidence level.

If a prefix is ambiguous within the chosen scope, the UI shows "unresolved" rather than guessing.

### Node discovery via adverts

MeshCore payload type `0x04` is a Node Advertisement. The decoded advert contains:
- Full 32-byte Ed25519 public key
- Device role (1 = companion, 2 = repeater, 3 = room server)
- Optional latitude/longitude (self-reported)
- Optional node name
- Timestamp + Ed25519 signature

When we ingest an advert, we upsert the `nodes` row by public key (updating name/role/location), then upsert the corresponding `node_iatas` and `node_short_ids` rows for the IATA the advert was heard in. This is the authoritative way to populate the node map.

### Cross-IATA node propagation

Long-range LoRa propagation means the same physical node can be heard from multiple IATAs. A node is not tagged with a single IATA. The `node_iatas` join table tracks which IATAs each node has been heard in, with first-heard / last-heard / observation-count per pair. `node_short_ids` carries the same prefix per IATA, so path resolution against any of the node's known IATAs lights up the same node.

### Observer types and detection

An "observer" in this system is any client that authenticates to the MeshCore MQTT broker with its own MeshCore keypair and publishes packets. Observers come in several distinct forms, each with their own quirks:

| Type code                 | Description                                                                    |
|---------------------------|--------------------------------------------------------------------------------|
| `meshcore-ha`             | Home Assistant plugin talking to a companion device                            |
| `meshcore-repeater-mqtt`  | Repeater running MQTT-enabled firmware (e.g. EastMesh `*_repeater_mqtt` builds)|
| `mctomqtt`                | Python script connected to a repeater via serial                               |
| `meshcore-terminal`       | Companion device addressed by a host program                                   |
| `pymc`                    | Raspberry Pi acting as a repeater, publishing via MQTT                         |
| `unknown`                 | Fallback when no identifying signal is present                                 |

Each client identifies itself differently. The detection sources, in priority order:
1. Explicit `client_type` or `software` field in the observer's `/status` payload
2. Recognizable signature in `/status` metadata structure (e.g. specific keys only one client emits)
3. JWT claims at authentication time (if the broker forwards them through)
4. Manual override via the config file

Observers publish to three subtopics under `meshcore/{IATA}/{pubkey}/`:
- `/packets`: the raw packet stream we use for everything else
- `/status`: periodic observer health (battery, uptime, queue depth, radio stats, software identity)
- `/internal`: PII (owner email/name from JWT). Admin-only on the broker. We use Role 2 so we do not subscribe to `/internal`.

The ingest service subscribes to `meshcore/#` and routes by subtopic. Packets go to the observation pipeline; status messages update the observer row.

### Node firmware capability detection

Two MeshCore firmware features that affect path encoding landed in known releases:

- **Multi-byte trace paths**: introduced in **1.11.0+**. Trace packets (payload type `0x09`) can use 1, 2, or 4 byte hashes. Old firmware can only emit 1-byte traces; new firmware lets the user choose 1, 2, or 4. So observing a node in a 2 or 4 byte trace conclusively proves the node is on 1.11.0+. Observing it in a 1-byte trace tells us nothing about firmware version.
- **Multi-byte packet paths**: introduced in **1.14.0+**. Regular (non-trace) packets can use 1, 2, or 3 byte hashes. Old firmware can only emit 1-byte regular paths; new firmware lets the user choose 1, 2, or 3. So observing a node in a 2 or 3 byte regular path conclusively proves 1.14.0+. Observing it in a 1-byte regular path tells us nothing.

We track these as two boolean flags on `nodes`:
- `supports_multibyte_paths` → directly observed in a 2 or 3 byte regular packet path
- `supports_multibyte_traces` → directly observed in a 2 or 4 byte trace path

A generated column `min_firmware_version` derives the strongest minimum version we can prove from observation:
- `supports_multibyte_paths = TRUE` → `'1.14.0+'`
- `supports_multibyte_traces = TRUE` (and not multibyte_paths) → `'1.11.0+'`
- Neither → `NULL` (could be old, could just be unobserved at multi-byte sizes)

We only flip a flag when we observe the node in an unambiguous multi-byte path of the relevant kind, and we never downgrade once set. A node currently showing `1.11.0+` could actually be on 1.14.0+ but just hasn't been observed forwarding a multi-byte regular packet yet; it'll get bumped automatically the next time we see it in one. A node showing NULL could be on old firmware, or could be on new firmware that has only ever forwarded 1-byte paths so far.

**Rules per incoming observation:**
- If `hash_size == 1`: do nothing (1-byte is valid on all firmware versions, proves nothing)
- If the path has duplicate hash prefixes within itself: skip entirely (collision suspicion or routing weirdness)
- Otherwise, for each hop that resolves to exactly one node in the observer's IATA:
  - If `payload_type != 0x09` (any non-trace packet) and `hash_size` is 2 or 3: set `supports_multibyte_paths = TRUE` for that node
  - If `payload_type == 0x09` (trace) and `hash_size` is 2 or 4: set `supports_multibyte_traces = TRUE` for that node

This lets the UI show which repeaters have proven minimum firmware versions and helps spot upgrade candidates (NULL firmware tier), while being honest that NULL is "unknown", not "definitely old".

### MeshCore decoder

We use **`github.com/meshcore-go/meshcore-go`** (MIT, pure Go, v1.0.6 as of May 2026) for all packet decoding. It implements the actual LoRa over-the-air protocol that we receive via MQTT, not the host-to-device companion protocol. Key features for our purposes:

- **`PacketFromBytes([]byte)`** parses the full wire format: header byte → optional transport codes (FLOOD/DIRECT) → path_length byte (hash_size + hop_count) → path bytes → payload
- **`PacketHash()`** computes the canonical content-based dedup hash: SHA256(payload_type + [path_length for traces] + payload) truncated to 8 bytes. Matches the firmware's `Packet::calculatePacketHash`. This is exactly the `packet_hash` column in our `packets` table.
- **`PathHashes()`** returns the per-hop hashes already split by hash_size, ready to feed into our path resolution function
- **Per-payload-type sub-packages** for all 13 payload types: `Advert`, `TextMessage`, `GroupText`, `Trace`, `Ack`, `MultiPart`, `Path`, `Control`, `Request`, `Response`, `AnonReq`, `GroupData`, `RawCustom`
- **`crypto.go`** provides everything needed for group chat decryption with our `channel_keys` table: `DeriveSharedSecret`, `EncryptThenMAC`, `MACThenDecrypt`, AES-128-ECB
- **`identity.go`** handles Ed25519 keys and signature verification on adverts
- **`region.go`** derives MeshCore radio region keys and transport codes
- Each source file has a `_test.go` counterpart; the library is well-tested

What our wrapper code still needs to do:
- Subscribe to MQTT and pass hex payloads through `PacketFromBytes`
- Map the decoded `*Packet` and per-payload structs into our DB rows (packets, packet_observations, nodes, channel_messages)
- Apply our capability detection logic from `PathHashes()` against the observer's IATA
- Maintain our channel_keys table and pass keys to `GroupText.Decrypt` when needed
- Compute and store the `packet_hash` returned by `PacketHash()`

What we don't need to use from the library:
- The `companion/` subpackages (USB/BLE/TCP host protocol for talking to a physical device); not relevant to our ingest path
- The `hardware/` subpackages (KISS modem framing); not relevant
- The `node/` runtime (routing, peer tracking, TX engine); that's for building a mesh node, not analyzing one

Reference: `github.com/michaelhart/meshcore-decoder` (TypeScript, used by letsmesh). If our pipeline produces different results from it for the same hex, we likely have a bug worth investigating.

---

## MeshCore payload types

| Hex    | Name                | Notes                                              |
|--------|---------------------|----------------------------------------------------|
| `0x00` | Request             | dest/source hashes + MAC                           |
| `0x01` | Response            | response to req/anon_req                           |
| `0x02` | Plain text message  | unencrypted                                        |
| `0x03` | Acknowledgment      |                                                    |
| `0x04` | Node advertisement  | **node discovery, has pubkey + role + location**   |
| `0x05` | Group text message  | **encrypted, decryptable with channel key**        |
| `0x06` | Group datagram      | encrypted                                          |
| `0x07` | Anonymous request   |                                                    |
| `0x08` | Returned path       | route discovery                                    |
| `0x09` | Trace               | path tracing with SNR per hop                      |
| `0x0A` | Multi-part packet   | sequence of packets exceeding MTU                  |
| `0x0F` | Custom packet       | raw, custom encryption                             |

---

## Database schema

```sql
-- ============================================================
-- IATA CODES (the primary geographic grouping)
-- ============================================================
-- Every observation, node, and path resolution is anchored to an IATA.
-- Super-regions (below) are virtual overlays that group IATAs together,
-- but the IATA is what owns the data.

CREATE TABLE iata_codes (
  iata          CHAR(3) PRIMARY KEY,
  display_name  TEXT,
  approx_lat    DOUBLE PRECISION,
  approx_lng    DOUBLE PRECISION,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- REGIONS (virtual super-region groupings of IATAs)
-- ============================================================
-- Operator-managed virtual containers that group one or more IATAs together
-- for display and filtering. Many-to-many: an IATA can belong to multiple
-- regions (e.g. YVR could be in both "BC Coast" and "Pacific Northwest").
-- Creating, modifying, or deleting a region does not touch any underlying
-- IATA-scoped data.

CREATE TABLE regions (
  id            SERIAL PRIMARY KEY,
  slug          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  description   TEXT,
  display_order INT DEFAULT 0,
  center_lat    DOUBLE PRECISION,
  center_lng    DOUBLE PRECISION,
  zoom_level    INT DEFAULT 8,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Many-to-many association between regions and IATAs
CREATE TABLE region_iatas (
  region_id  INT NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
  iata       CHAR(3) NOT NULL REFERENCES iata_codes(iata) ON DELETE CASCADE,
  added_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (region_id, iata)
);

CREATE INDEX idx_region_iatas_iata ON region_iatas(iata);

-- ============================================================
-- OBSERVERS
-- ============================================================

-- An observer is any client that authenticates to the MeshCore MQTT broker with a
-- MeshCore keypair and publishes packets. Observer clients identify themselves with
-- a string like "{stream}/{client}:{version}" or "{stream}/{version}". Known types:
--   meshcoretomqtt           - Python script connected to a repeater via serial
--   meshcore                 - Firmware-native MQTT publisher (the repeater itself)
--   meshcore-dev             - Same as above but on the dev firmware stream
--   meshcore-ha              - Home Assistant plugin talking to a companion
--   meshcore-packet-capture  - Standalone Python packet-capture observer
--   meshcore-custom-repeater - Custom repeater builds
--   pymc                     - Raspberry Pi acting as a repeater, publishing via MQTT
--   meshcore-terminal        - Companion device addressed by a host program
--   unknown                  - Fallback when we can't determine
CREATE TABLE observers (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_key        BYTEA UNIQUE NOT NULL,
  display_name      TEXT,                  -- best-effort name from /status or packets
  observer_type     TEXT,                  -- one of the codes above; NULL until determined
  software_version  TEXT,                  -- version of the observer client (script or native firmware)
  -- Hardware and MeshCore firmware of the underlying repeater (for non-native observers
  -- this is the connected device, not the observer process). All from /status.
  hardware_model    TEXT,                  -- e.g. "Roba Stick-E22-30dBm (Gen_ref52)"
  firmware_version  TEXT,                  -- MeshCore firmware version, e.g. "v1.14.1"
  firmware_build    TEXT,                  -- build identifier, e.g. "20 Mar 2026"
  radio_freq_mhz    REAL,                  -- e.g. 910.525
  radio_sf          SMALLINT,              -- spread factor, e.g. 7
  radio_bw_khz      REAL,                  -- bandwidth, e.g. 62.5
  radio_cr          SMALLINT,              -- coding rate, e.g. 5
  -- Latest snapshot of mutable observer state
  battery_level     REAL,                  -- convenience copy of latest telemetry battery
  uptime_seconds    BIGINT,                -- convenience copy of latest telemetry uptime
  status_metadata   JSONB,                 -- full latest /status payload for forward-compat
  last_status_at    TIMESTAMPTZ,
  -- Activity tracking
  first_seen        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  observation_count BIGINT DEFAULT 0,
  metadata          JSONB                  -- raw JWT claims and other auth-time data
);

CREATE INDEX idx_observers_last_seen ON observers(last_seen DESC);
CREATE INDEX idx_observers_pubkey ON observers(public_key);
CREATE INDEX idx_observers_type ON observers(observer_type) WHERE observer_type IS NOT NULL;

-- Which broker(s) we've seen each observer publishing to.
-- An observer can be configured to publish to multiple brokers simultaneously.
CREATE TABLE observer_brokers (
  observer_id     UUID NOT NULL REFERENCES observers(id) ON DELETE CASCADE,
  broker_name     TEXT NOT NULL,           -- "mqtt1", "mqtt2"
  first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_packet_at  TIMESTAMPTZ,             -- last actual /packets message via this broker
  auth_ok         BOOLEAN DEFAULT TRUE,    -- false if recent connections failed auth
  PRIMARY KEY (observer_id, broker_name)
);

CREATE TABLE observer_locations (
  observer_id   UUID NOT NULL REFERENCES observers(id) ON DELETE CASCADE,
  iata          CHAR(3) REFERENCES iata_codes(iata),
  latitude      DOUBLE PRECISION,
  longitude     DOUBLE PRECISION,
  reported_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (observer_id, reported_at)
);

CREATE INDEX idx_observer_locations_recent ON observer_locations(observer_id, reported_at DESC);

-- Time series of observer telemetry, one row per /status message.
-- Subject to the same retention policy as packet_observations.
-- Used to graph metrics over time on the observer detail page.
CREATE TABLE observer_telemetry (
  id                  BIGSERIAL PRIMARY KEY,
  observer_id         UUID NOT NULL REFERENCES observers(id) ON DELETE CASCADE,
  reported_at         TIMESTAMPTZ NOT NULL,
  battery_voltage_mv  INT,
  airtime_tx_secs      REAL,
  airtime_rx_secs      REAL,
  noise_floor_db      REAL,
  uptime_seconds      BIGINT,
  queue_length        INT,
  debug_flags         INT,
  receive_errors      INT,
  UNIQUE (observer_id, reported_at)
);

CREATE INDEX idx_telemetry_reported_brin ON observer_telemetry USING BRIN (reported_at);
CREATE INDEX idx_telemetry_observer_recent ON observer_telemetry(observer_id, reported_at DESC);

-- Private owner mapping for each observer. NEVER exposed via the public API; this
-- data is internal-only and reserved for future features (see "Remote observer
-- console" in Future Features). When that feature ships, this table will be
-- populated from the broker's /internal subtopic (which carries PII and is Role 1
-- only), so the analyzer would need a Role 1 SUBSCRIBER account for the privileged
-- ingest path. owner_node_id optionally links the observer to an actual MeshCore
-- node (typically the operator's companion device).
CREATE TABLE observer_owners (
  observer_id   UUID PRIMARY KEY REFERENCES observers(id) ON DELETE CASCADE,
  owner_node_id UUID REFERENCES nodes(id),
  owner_pubkey  BYTEA,           -- the auth pubkey for future remote-console feature
  contact_name  TEXT,
  contact_email TEXT,
  notes         TEXT,
  source        TEXT,            -- "internal_mqtt", "manual", future sources
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_observer_owners_node ON observer_owners(owner_node_id) WHERE owner_node_id IS NOT NULL;

-- ============================================================
-- NODES (Repeaters, Room Servers, Companions)
-- ============================================================

CREATE TABLE nodes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_key      BYTEA UNIQUE NOT NULL,
  node_type       SMALLINT NOT NULL,    -- 1=companion, 2=repeater, 3=room_server
  name            TEXT,                  -- from advert payload
  latitude        DOUBLE PRECISION,      -- from advert payload
  longitude       DOUBLE PRECISION,
  location_source TEXT,                  -- "advert", "manual"
  last_advert_at  TIMESTAMPTZ,
  -- Firmware capability flags, set when we observe the node in unambiguous multi-byte paths.
  -- These map to MeshCore firmware features that landed in known releases.
  supports_multibyte_paths  BOOLEAN NOT NULL DEFAULT FALSE,  -- seen in 2 or 3 byte regular packet paths (firmware 1.14.0+)
  supports_multibyte_traces BOOLEAN NOT NULL DEFAULT FALSE,  -- seen in 2 or 4 byte trace paths (firmware 1.11.0+)
  -- Derived minimum firmware version from the capability flags above.
  -- Reports the strongest minimum we can prove from direct observation.
  min_firmware_version TEXT GENERATED ALWAYS AS (
    CASE
      WHEN supports_multibyte_paths  THEN '1.14.0+'
      WHEN supports_multibyte_traces THEN '1.11.0+'
      ELSE NULL
    END
  ) STORED,
  first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata        JSONB                  -- raw appData from advert
);

CREATE INDEX idx_nodes_type_last_seen ON nodes(node_type, last_seen DESC);
CREATE INDEX idx_nodes_location ON nodes(latitude, longitude)
  WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX idx_nodes_pubkey ON nodes(public_key);
CREATE INDEX idx_nodes_multibyte_paths  ON nodes(supports_multibyte_paths)  WHERE supports_multibyte_paths;
CREATE INDEX idx_nodes_multibyte_traces ON nodes(supports_multibyte_traces) WHERE supports_multibyte_traces;
CREATE INDEX idx_nodes_min_firmware ON nodes(min_firmware_version) WHERE min_firmware_version IS NOT NULL;

-- Tracks which IATAs have heard each node. A node can be heard from many IATAs
-- (e.g. a Vancouver repeater heard by observers in both YVR and YYJ).
CREATE TABLE node_iatas (
  node_id           UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  iata              CHAR(3) NOT NULL REFERENCES iata_codes(iata) ON DELETE CASCADE,
  first_heard       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_heard        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  observation_count BIGINT DEFAULT 0,
  PRIMARY KEY (node_id, iata)
);

CREATE INDEX idx_node_iatas_iata ON node_iatas(iata, last_heard DESC);

-- Pre-computed 4-byte prefix of each node's hash, per IATA they've been heard in.
-- The single 4-byte prefix covers all path hash sizes used by MeshCore (1, 2, 3, or 4 bytes).
-- Generated columns expose shorter prefixes for fast indexed lookups.
CREATE TABLE node_short_ids (
  node_id   UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  iata      CHAR(3) NOT NULL REFERENCES iata_codes(iata) ON DELETE CASCADE,
  prefix_4  BYTEA NOT NULL,    -- first 4 bytes of node hash
  prefix_1  BYTEA GENERATED ALWAYS AS (substring(prefix_4 from 1 for 1)) STORED,
  prefix_2  BYTEA GENERATED ALWAYS AS (substring(prefix_4 from 1 for 2)) STORED,
  prefix_3  BYTEA GENERATED ALWAYS AS (substring(prefix_4 from 1 for 3)) STORED,
  PRIMARY KEY (node_id, iata)
);

CREATE INDEX idx_short_ids_p1 ON node_short_ids(iata, prefix_1);
CREATE INDEX idx_short_ids_p2 ON node_short_ids(iata, prefix_2);
CREATE INDEX idx_short_ids_p3 ON node_short_ids(iata, prefix_3);
CREATE INDEX idx_short_ids_p4 ON node_short_ids(iata, prefix_4);

-- ============================================================
-- PACKETS (unique content, deduped by content hash)
-- ============================================================

CREATE TABLE packets (
  packet_hash             BYTEA PRIMARY KEY,    -- content-based hash from decoder
  header_byte             SMALLINT NOT NULL,    -- raw header byte (VVPPPPRR bit-packed)
  payload_type            SMALLINT NOT NULL,    -- 0x00..0x0F, bits 2-5 of header
  payload_version         SMALLINT NOT NULL,    -- bits 6-7 of header
  route_type              SMALLINT NOT NULL,    -- bits 0-1 of header (set by sender)
  -- Transport codes (only present for TRANSPORT_FLOOD or TRANSPORT_DIRECT)
  transport_codes_present BOOLEAN DEFAULT FALSE,
  region_code             INT,                  -- uint16 LE, optional
  sub_region_code         INT,                  -- uint16 LE, optional
  -- Content
  origin_pubkey           BYTEA,                -- if extractable (e.g. from advert payload)
  raw_payload             BYTEA NOT NULL,
  parsed_payload          JSONB,                -- decoded structured data
  decrypted               BOOLEAN DEFAULT FALSE,
  channel_hash            BYTEA,                -- 1-byte channel ID, if group/channel packet
  first_heard_at          TIMESTAMPTZ NOT NULL,
  last_heard_at           TIMESTAMPTZ NOT NULL,
  observation_count       INT DEFAULT 0         -- denormalized count for UI
);

CREATE INDEX idx_packets_first_heard_brin ON packets USING BRIN (first_heard_at);
CREATE INDEX idx_packets_payload_type ON packets(payload_type, first_heard_at DESC);
CREATE INDEX idx_packets_route_type ON packets(route_type, first_heard_at DESC);
CREATE INDEX idx_packets_origin ON packets(origin_pubkey, first_heard_at DESC)
  WHERE origin_pubkey IS NOT NULL;
CREATE INDEX idx_packets_channel ON packets(channel_hash, first_heard_at DESC)
  WHERE channel_hash IS NOT NULL;

-- ============================================================
-- PACKET OBSERVATIONS (per-observer hearings)
-- ============================================================

CREATE TABLE packet_observations (
  id                  BIGSERIAL PRIMARY KEY,
  packet_hash         BYTEA NOT NULL REFERENCES packets(packet_hash) ON DELETE CASCADE,
  observer_id         UUID NOT NULL REFERENCES observers(id),
  iata                CHAR(3) NOT NULL REFERENCES iata_codes(iata),
  heard_at            TIMESTAMPTZ NOT NULL,
  -- Per-observation path data (varies per hop as packet propagates)
  path_length_byte    SMALLINT NOT NULL,    -- raw path_length byte (encodes hash_size + hop_count)
  hash_size           SMALLINT NOT NULL,    -- derived: 1, 2, 3, or 4
  hop_count           SMALLINT NOT NULL,    -- derived: 0-63
  path_bytes          BYTEA,                -- raw path bytes (hash_size * hop_count bytes)
  -- Reception quality
  rssi                SMALLINT,
  snr                 REAL,
  propagation_time_ms INT,
  -- Radio parameters
  radio_freq_mhz      REAL,
  spread_factor       SMALLINT,
  bandwidth_khz       REAL,
  coding_rate         SMALLINT,
  -- Origin tracking
  source_broker       TEXT,                 -- "mqtt1" or "mqtt2"
  -- Full wire-format bytes as received by this observer (header + optional transport
  -- codes + path_length_byte + path_bytes + payload). Differs per observation because
  -- path bytes accumulate as the packet hops through repeaters.
  raw_packet          BYTEA NOT NULL,
  -- Dedup across both brokers
  UNIQUE (packet_hash, observer_id, heard_at)
);

CREATE INDEX idx_observations_heard_brin ON packet_observations USING BRIN (heard_at);
CREATE INDEX idx_observations_iata_heard ON packet_observations(iata, heard_at DESC);
CREATE INDEX idx_observations_observer ON packet_observations(observer_id, heard_at DESC);
CREATE INDEX idx_observations_packet ON packet_observations(packet_hash);

-- ============================================================
-- CHANNELS AND CHAT MESSAGES (group text)
-- ============================================================

CREATE TABLE channels (
  id            SERIAL PRIMARY KEY,
  channel_hash  BYTEA UNIQUE NOT NULL,
  name          TEXT,
  is_hashtag    BOOLEAN DEFAULT FALSE,
  is_public     BOOLEAN DEFAULT FALSE,
  key_known     BOOLEAN DEFAULT FALSE,
  first_seen    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message_count BIGINT DEFAULT 0
);

CREATE INDEX idx_channels_last_seen ON channels(last_seen DESC);

-- Which IATAs each channel has been heard in, maintained at ingest and
-- pruned on the packet retention cutoff. Backs the channel list IATA
-- filter without touching packet_observations. trace_iatas does the
-- same for trace tags.
CREATE TABLE channel_iatas (
  channel_hash BYTEA NOT NULL,
  iata         CHAR(3) NOT NULL REFERENCES iata_codes(iata) ON DELETE CASCADE,
  last_heard   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_hash, iata)
);

CREATE INDEX idx_channel_iatas_iata ON channel_iatas(iata, last_heard DESC);

CREATE TABLE trace_iatas (
  trace_tag  BYTEA NOT NULL,
  iata       CHAR(3) NOT NULL REFERENCES iata_codes(iata) ON DELETE CASCADE,
  last_heard TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (trace_tag, iata)
);

CREATE INDEX idx_trace_iatas_iata ON trace_iatas(iata, last_heard DESC);

-- Channel decryption keys, loaded from the server config file on startup.
-- Adding or rotating a key requires updating the config and restarting (or SIGHUP).
CREATE TABLE channel_keys (
  channel_id INT PRIMARY KEY REFERENCES channels(id) ON DELETE CASCADE,
  key_bytes  BYTEA NOT NULL,
  added_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  added_by   TEXT          -- "config" or, in the future, an admin user identifier
);

CREATE TABLE channel_messages (
  id            BIGSERIAL PRIMARY KEY,
  channel_id    INT NOT NULL REFERENCES channels(id),
  packet_hash   BYTEA NOT NULL REFERENCES packets(packet_hash),
  sender_name   TEXT,             -- decrypted, from message body
  sender_pubkey BYTEA,            -- if known/resolvable
  content       TEXT,             -- decrypted message body
  sent_at       TIMESTAMPTZ NOT NULL,
  UNIQUE (packet_hash)
);

CREATE INDEX idx_channel_messages_channel ON channel_messages(channel_id, sent_at DESC);
CREATE INDEX idx_channel_messages_sent_brin ON channel_messages USING BRIN (sent_at);

-- ============================================================
-- MATERIALIZED VIEWS
-- ============================================================

CREATE MATERIALIZED VIEW mv_hourly_iata_stats AS
SELECT
  iata,
  date_trunc('hour', heard_at) AS hour,
  COUNT(*) AS observation_count,
  COUNT(DISTINCT packet_hash) AS unique_packets,
  COUNT(DISTINCT observer_id) AS active_observers
FROM packet_observations
WHERE heard_at > NOW() - INTERVAL '7 days'
GROUP BY iata, date_trunc('hour', heard_at);

CREATE UNIQUE INDEX idx_mv_hourly_iata
  ON mv_hourly_iata_stats(iata, hour);

-- Super-region stats are derived on demand by joining mv_hourly_iata_stats
-- through region_iatas. Cheap because the IATA-level rollups are pre-computed.

CREATE MATERIALIZED VIEW mv_top_nodes_by_iata AS
SELECT
  ni.iata,
  ni.node_id,
  n.name,
  n.node_type,
  ni.observation_count,
  ni.last_heard
FROM node_iatas ni
JOIN nodes n ON n.id = ni.node_id
WHERE ni.last_heard > NOW() - INTERVAL '7 days';

CREATE UNIQUE INDEX idx_mv_top_nodes
  ON mv_top_nodes_by_iata(iata, node_id);
```

---

## Operations and configuration

### Retention

Packets and their observations are retained for **30 days by default**, configurable via the `PACKET_RETENTION_DAYS` environment variable. Change the value and restart the service to apply.

A daily cleanup job runs at a configurable hour (default 3am local) and:
1. Deletes `packet_observations` rows older than the retention window
2. Deletes `packets` rows that have no remaining observations (cascades cleanly via FK)

Materialized view aggregates (`mv_hourly_iata_stats`, `mv_top_nodes_by_iata`) persist beyond the retention window so historical stats survive raw data pruning. Refresh them on a 1-minute schedule via `pg_cron` or a Go goroutine.

### Configuration

v1 has no authentication or web-based admin UI. All operational state that isn't derived from MQTT traffic is managed via files on the server. The server reads them on startup; for v1, changes require a restart (or `SIGHUP` to trigger a reload, TBD).

**Environment variables** for runtime tuning:

```
PACKET_RETENTION_DAYS=30
POSTGRES_DSN=postgres://...
REDIS_ADDR=...
MQTT_BROKER_1_URL=wss://mqtt1.meshcore.ca
MQTT_BROKER_1_USERNAME=...
MQTT_BROKER_1_PASSWORD=...
MQTT_BROKER_2_URL=wss://mqtt2.meshcore.ca
MQTT_BROKER_2_USERNAME=...
MQTT_BROKER_2_PASSWORD=...
LISTEN_ADDR=:8080
```

**YAML config file** (`config.yaml`) for content the API exposes (super-regions, channel keys):

```yaml
regions:
  - slug: ottawa
    name: Ottawa Mesh
    description: National Capital Region
    centerLat: 45.42
    centerLng: -75.69
    zoomLevel: 9
    iatas: [YOW]
  - slug: bc-coast
    name: BC Coast
    iatas: [YVR, YYJ, YCD, YQQ]

channelKeys:
  - channelHash: "f3"
    name: "#ottawa"
    keyHex: "0123456789abcdef0123456789abcdef"
  - channelHash: "a1"
    name: "#public"
    keyHex: "fedcba9876543210fedcba9876543210"
```

IATAs are still auto-created when packets arrive from unrecognized codes. The config file is only needed to override the default display name/coordinates, or to assign an IATA to a super-region.

Channel hashes also auto-populate as messages arrive; adding a key in the config retroactively decrypts existing rows on next startup (or on `SIGHUP`).

Admin login, web-based config UI, and per-user accounts are tracked in Future Features.

### IATA and super-region seeding

IATA codes are auto-created on first sight: when a packet arrives from an unrecognized IATA, the ingest service creates the `iata_codes` row and logs it. No operator action is needed for the data to start flowing.

Super-regions (the virtual containers in the `regions` table) are defined in the server config file. The operator creates a region entry, then attaches one or more IATAs to it. A single IATA can belong to multiple super-regions simultaneously (e.g. YVR could be in both "BC Coast" and "Pacific Northwest"), and creating, deleting, or reshuffling a super-region does not touch any of the IATA-scoped data underneath.

---

## Ingestion pipeline

The ingest service subscribes to `meshcore/#` on both brokers and routes incoming messages by subtopic.

### For `/packets` messages

1. Parse MQTT topic to extract `iata` and `publisher_pubkey`
2. Upsert `observers` row (by publisher_pubkey)
3. Upsert `observer_brokers` row for the source broker
4. Upsert `iata_codes` row if this IATA hasn't been seen before
5. Decode the raw hex packet from MQTT JSON:
   - Parse the bit-packed header (route_type, payload_type, payload_version)
   - If route_type is TRANSPORT_FLOOD or TRANSPORT_DIRECT, parse the 4-byte transport codes
   - Parse path_length byte → extract hash_size and hop_count
   - Read hash_size × hop_count path bytes
   - The remainder is the payload
6. Compute the content-based packet hash from the payload
7. UPSERT into `packets` ON CONFLICT (packet_hash) DO UPDATE SET last_heard_at, observation_count = observation_count + 1
8. INSERT into `packet_observations` with the per-observation path data, RSSI, SNR, radio params. ON CONFLICT DO NOTHING using the UNIQUE constraint (handles dual-broker dedup)
9. **Capability detection:** if the observation INSERT succeeded and `hash_size >= 2`, attempt path resolution against `node_short_ids` for the observer's IATA. If every hop resolves to exactly one node AND no two hops share the same hash prefix, then for each resolved node:
   - If `payload_type != 0x09` and `hash_size` is 2 or 3: set `supports_multibyte_paths = TRUE`
   - If `payload_type == 0x09` (trace) and `hash_size` is 2 or 4: set `supports_multibyte_traces = TRUE`
   
   Skip silently if the path has duplicate hashes or any ambiguous hops. Never downgrade an existing TRUE.
10. If payload_type is `0x04` (advert), upsert `nodes` with pubkey/name/role/location and update `node_iatas` + `node_short_ids` for the observer's IATA
11. If payload_type is `0x05` (group text), try to decrypt with known channel keys, store in `channel_messages` on success
12. If the observation INSERT actually succeeded (no conflict), fan out to live WebSocket subscribers via internal Go channel

### For `/status` messages

1. Parse MQTT topic to extract `publisher_pubkey`
2. Upsert `observers` row, updating:
   - `status_metadata` with the full JSON payload
   - `last_status_at` with current time
   - `battery_level`, `uptime_seconds` if present in the payload
   - `software_version` if present
   - `observer_type` if we can detect it from explicit fields or signature heuristics (never downgrade from known to unknown)
   - `display_name` if present and current value is NULL
3. Upsert `observer_brokers` row for the source broker

### For `/internal` messages
Not subscribed (Role 2 access).

---

## Path resolution function

```
function resolvePath(pathBytes, hashSize, iatas):
    # Inputs:
    #   pathBytes  - raw bytes from the packet observation (length = hashSize * hopCount)
    #   hashSize   - 1, 2, 3, or 4 (derived from the path_length byte during decoding)
    #   iatas      - set of IATA codes to scope the lookup
    #                  narrow scope: { observerIata }
    #                  super-region scope: all IATAs from region_iatas for the region
    #
    # Returns: ordered list of hops, one per hash chunk in pathBytes
    #   { confidence: HIGH,      node: <node>        }   exactly one match
    #   { confidence: AMBIGUOUS, candidates: [<n>+], idBytes: <bytes> }   multiple matches
    #   { confidence: NONE,      idBytes: <bytes>    }   no match in scope

    hops := []
    for each chunk of size hashSize in pathBytes:
        matches := lookup nodes where
            node_short_ids.iata is in iatas
            AND node_short_ids.prefix_<hashSize> equals chunk
            return distinct nodes

        if matches.count == 1:
            append { confidence: HIGH, node: matches[0] } to hops
        else if matches.count > 1:
            append { confidence: AMBIGUOUS, candidates: matches, idBytes: chunk } to hops
        else:
            append { confidence: NONE, idBytes: chunk } to hops

    return hops
```

The implementation picks the correct prefix column based on `hashSize` (`prefix_1`, `prefix_2`, `prefix_3`, or `prefix_4`), and the lookup must return distinct nodes because a single node heard in multiple IATAs has multiple `node_short_ids` rows that would otherwise be counted separately when the scope spans those IATAs.

**Resolution philosophy:** when ambiguous, we never guess and we never smooth it over. We return all candidates and the UI shows them honestly so the user can see what's actually happening on their mesh. Working around ambiguity for users reduces their incentive to fix the underlying cause (which is generally firmware needing to be upgraded so multi-byte paths become the norm). Visibility is the point. Scoping by IATA keeps the candidate set small enough that listing them is useful rather than overwhelming.

**UI rule:** render the path on the map only if every hop has confidence HIGH. For AMBIGUOUS hops, show the candidates in a list. For NONE hops, show the raw byte ID with a "not found in this scope" note.

---

## API contract

Moved to its own document: **[API Contract](api_contract.md)**

Covers REST endpoints (`/api/v1/`), WebSocket protocol (`/ws`), search, backpressure/reconnection, and mobile-specific concerns.

---

## Feature to schema mapping

### Live Packets Channel
- **Top-level view:** one row per packet, showing summary from the most recent observation. Click to expand.
- **Live updates:** WebSocket pushes new observations. UI either bumps the existing packet row's observation count or inserts a new packet row at the top.
- **Filtering:** by IATA (direct), by super-region (expands to `WHERE iata IN (SELECT iata FROM region_iatas WHERE region_id = $X)`), payload_type, route_type, time range. All filters server-enforced.
- **Per-row data:** `(packet_hash, payload_type, parsed_payload.sub_type, latest observer name, latest IATA, observation_count, last_heard_at)`

### Expanded packet view (per-packet detail)
- Top: invariant packet info from `packets` (payload type, parsed content, channel if applicable)
- Tabs or stacked sections:
  - "Observations" list of all `packet_observations` for this packet, each row showing observer name, IATA, heard_at, RSSI, SNR, propagation_time, path_bytes, resolved path
  - "Byte breakdown" visual byte-level layout (matches the screenshot UI)
  - "Map" for each observation with a high-confidence resolved path, render its hops. Path bytes resolve against the observer's IATA (or the active super-region's IATA set if the user is viewing through that lens).

### Packet analyzer drawer
- Slide-out from clicked observation row
- Header byte breakdown (route_type, payload_type, version)
- Path length and path bytes with IATA-scoped resolution
- Payload byte breakdown
- Payload-type-specific section: for advert show pubkey/name/role/location, for group text show decrypted sender/content if key available, for control show flags/sub-type/tag

### Node Map
- `SELECT * FROM nodes WHERE latitude IS NOT NULL AND longitude IS NOT NULL`
- Filter by IATA or super-region via `node_iatas` join (and `region_iatas` for super-regions)
- Click marker opens panel with name, role, pubkey (truncated), last seen, IATAs heard in, recent packet count
- Marker styling encodes node_type and recency

### Channels
- List: `SELECT * FROM channels ORDER BY last_seen DESC`
- Per-channel page: paginated `channel_messages` with decrypted content where `key_known`. These are the actual chat messages (payload type 0x05) sent to a channel, distinct from other packet types.
- **Key management:** channel keys are defined in the server config file. Adding or rotating a key requires updating the config and restarting (or sending `SIGHUP`). On startup, the service retroactively decrypts any existing packets that now have a known key.

### Nodes List
- Three tabs filtered by `node_type`: Repeaters, Room Servers, Companions
- Columns: name, public key (truncated), IATAs heard in (chip list from `node_iatas`), location (if known), last seen, observation contribution count, **firmware tier** (from `min_firmware_version`: `1.14.0+`, `1.11.0+`, or "Unknown")
- Filter pills: "1.14.0+ only", "1.11.0+ and above", "Unknown firmware" (the inverse query, surfaces likely upgrade candidates and unobserved nodes); IATA / super-region scoping pills

### Observers List
- `SELECT * FROM observers ORDER BY last_seen DESC` with `observer_brokers` joined for broker badges
- Per-observer columns: name, public key (truncated), **type** (with icon: HA, repeater, mctomqtt, terminal, pymc, or unknown), **broker badges** (mqtt1, mqtt2, or both), current IATA, last status time, observation count, last seen
- Per-observer page: payload type breakdown of their contributions, recent observations, battery and uptime curves from `status_metadata` history (if we capture deltas), software version
- Filter pills: by observer type, by broker (mqtt1-only / mqtt2-only / both), by IATA or super-region

### Stats
- Queries against `mv_hourly_iata_stats` and `mv_top_nodes_by_iata`. Super-region rollups are computed on demand by joining through `region_iatas` and summing.
- Top-line: total packets last 24h, total observations last 24h, active observers, active IATAs, unique nodes seen
- Charts: observations over time by IATA (with optional super-region rollup), payload type breakdown, top contributing observers, top contributing nodes

---

## UI pattern: collapsed vs expanded packet rows

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ▸ 9E9B7D6A91CAB445  Advert "WW7STR/PugetMesh Cougar"  Heard by 15       │
│   route=Flood  type=Advert  latest: 02:37 PM by FlightlessDt in KEH     │
└─────────────────────────────────────────────────────────────────────────┘

(clicked, expanded:)

┌─────────────────────────────────────────────────────────────────────────┐
│ ▾ 9E9B7D6A91CAB445  Advert "WW7STR/PugetMesh Cougar"  Heard by 15       │
│                                                                         │
│   ┌─ Observation by FlightlessDt (KEH) at 02:37:36 ─────────────────┐  │
│   │ Path: [AE]  RSSI: -98  SNR: 10.75  Prop: 1.936s                 │  │
│   │ [Open analyzer]  [Show on map]                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─ Observation by NodeRunner (SEA) at 02:37:38 ───────────────────┐  │
│   │ Path: [AE, BF]  RSSI: -105  SNR: 7.20  Prop: 4.122s             │  │
│   │ [Open analyzer]  [Show on map]                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ... 13 more observations ...                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

New observations of the same packet arrive via WebSocket and appear inline in the expanded view in real time, without re-fetching.

---

## Future features

These are out of scope for v1 but worth keeping in mind so the schema and architecture don't paint us into a corner.

### Admin authentication and web-based config UI
v1 manages all configuration via files on the server. A future version would add:

- `admin_users` table with password hashing
- `POST /api/v1/auth/login` / `logout` / `me` endpoints
- Bearer-token auth on a `/api/v1/admin/*` namespace
- Write endpoints for regions, channel keys, and retention overrides
- A web UI for these operations so the operator doesn't need shell access
- Optional `?token=` query param on the WebSocket for receiving admin-only event types (config change notifications, etc.)
- Audit log of who changed what, when

The config-file approach should remain the primary source of truth; admin UI writes would update the file (or a parallel DB table that overlays it) so a snapshot of operational state is always version-controllable.

### Trace packet visualization (payload type 0x09)
Trace packets carry per-hop SNR values (`[snr_1][snr_2]...[snr_N]` where each is a signed byte representing SNR × 4). Once decoded, these unlock a dedicated per-hop signal quality view: for any traced path, render the actual SNR at each hop on the map, color-coded by signal strength. This is the only way to see real RF link quality between specific repeaters rather than just observer-reported reception. The schema already supports this since trace packets parse into `parsed_payload` like any other type. A future trace explorer view would query packets where `payload_type = 0x09` and pivot the per-hop SNR data into a visualization.

### Live pew pew map
A real-time animated map showing packets propagating across the mesh as they happen. Each new observation fires an animated arc or pulse from the resolved sending node (or first known hop) to the observing node's location, color-coded by payload type. Multiple observations of the same packet from different observers light up in sequence, visualizing flood propagation as it spreads. Filterable by region, payload type, and channel. The schema already supports this since every observation has timestamps, observer coordinates, and (when paths resolve) node coordinates. Mostly useful as an "is the mesh alive right now?" glance view and as eye candy for the project landing page.

**Constraints for whoever builds this:**
- Must handle high traffic without melting the browser (likely needs WebGL or canvas, not SVG)
- Must degrade gracefully under load (throttle, drop frames, queue events)
- Must NOT draw ambiguous paths (any hop without confidence "high" → don't animate that segment)
- Must NOT zoom-jump the map as new observations come in
- Must support payload-type filters so users can isolate (e.g.) only chat traffic
- Must work from slim WebSocket events where possible to keep bandwidth low, fetch enrichment lazily

### Live neighbor activity graph
Different from pew pew: less detail, more focused on local pathing. Shows live packet activity flowing node-to-node so users can answer "did my local pathing go the way I wanted?" Less about flood visualization, more about understanding whether a specific node's traffic is taking the expected routes through nearby repeaters.

### Neighbor maps (static topology)
Node response payloads can carry full neighbor tables with SNR values per neighbor. This is similar to traces but for adjacency rather than path. A future view could render a graph of node-to-node SNR relationships, giving a true picture of the mesh topology beyond just observer-reported sightings.

### Mobile push notifications
The Flutter app could let users set up notifications for specific events: a keyword appearing in a specific channel, a specific node starting to talk, an observer going offline, a packet matching arbitrary filter criteria. The `channelMessage` and `packetObservation` WebSocket events already carry everything a push service would need. This is purely a feature of the mobile app plus a notification dispatch service (Firebase or APNs).

### Remote observer console
Letsmesh has a feature where users can remote console into their own observer and run commands via MQTT, useful for diagnosing a misbehaving repeater or just managing it without going onsite. The auth flow uses the public key set as the owner on the observer: users authenticate to the web UI by signing a challenge with their companion device (USB-to-web), proving they own the pubkey, and the server then proxies a console session to the observer over MQTT.

For Tower, this requires a few things we don't have in v1:
- A privileged ingest path that subscribes to the broker's `/internal` subtopic to populate the private `observer_owners` table with the canonical owner pubkey for each observer. This requires a Role 1 SUBSCRIBER account.
- A companion-device WebAuthn-style flow on the web frontend for signing the owner challenge.
- An MQTT command path back to the observer (so we'd be publishing as well as subscribing, a change from our current Role 2 read-only stance).
- A scoped command surface on the console (which commands are safe to expose, rate limits, audit logging).

The `observer_owners` table in the schema is already shaped to support this. It's intentionally never exposed via the public API since the owner pubkey is private auth material until the console feature ships.

---

## Questions and Answers

Responses to dev feedback on this design. Captures decisions and rationale for things that came up after the initial draft was circulated.

### Q: Docker stack, all 4 under one stack, or 4 containers on the same docker network?

**A:** One stack, one compose file. I like the idea of shipping everything required in a single file. Makes setup turnkey and avoids the "did you bring up the right networks first" problem.

### Q: pprof endpoints, internal only with auth middleware, or exposed for perf stats?

**A:** Undecided for now. If anyone on the team needs access, all the servers already have a Tailscale connection, I can share that with you so you can reach pprof over the tailnet. That probably covers it without us having to build out auth middleware for v1.

### Q: MQTT brokers, internal WSS to our own broker for distribution? Should we include Mosquitto or EMQX as a deploy option for other communities?

**A:** Honestly we likely need to change the MQTT brokers from the letsmesh one to support exposing a single IATA worth of data, or fork his. But we can worry about this later. Nobody has actually asked for that yet, so I don't want to design around it preemptively.

### Q: How should we create Role 2 accounts for the broker? Manually in .env? Onboarding form for trust?

**A:** Manually for now. I think it's out of scope of Project Tower, it's a side thing we should support but it's broker config, not Tower config. Don't want to mix concerns.

### Q: Path resolution scoped to IATA is great. Should we lean heavily on observers to provide confidence? Ambiguous prefix is the CoreScope killer that we need to solve.

**A:** I think this is a much easier problem to solve than people think. We've done it with MeshMapper. I don't want to make guesses, and I also don't want to over-engineer around ambiguity. The more we work around it for users, the less incentive anyone has to fix the underlying problem (upgrading firmware so multi-byte paths become the norm). Show the ambiguous candidates clearly so the user understands what's actually happening on their mesh, and let that visibility push the community toward fixing it. No guessing, no smoothing it over.

### Q: When the path has duplicate hash prefixes within itself, do we dump the path compute, log it as ambiguous, or suppress to encourage upgrades?

**A:** We say ambiguous and show the possible matching repeaters. Scoping by IATA/region makes this way more tractable; the candidate set is small enough that listing them is useful information rather than overwhelming.

### Q: Using multi-byte traces and paths to determine firmware looks like a good way to set a pre-1.14 / pre-1.11 baseline. Never downgrading once a flag is set seems safe, who reflashes old firmware on new devices?

**A:** Yeah, the "never downgrade" rule is safe in practice. We frame it as "based on observed data, we assume X" so users understand it's an inference from what we've seen, not a definitive read from the device itself. NULL firmware tier means unknown, not old.

### Q: `michaelhart/meshcore-decoder`, should we peek deeper?

**A:** Don't need to. I just often reference it because he has already decoded most things. We're using the `github.com/meshcore-go/meshcore-go` Go library directly; meshcore-decoder is just our behavioral reference if we ever need to sanity-check output.

### Q: "There's no replay buffer for missed events, REST is the source of truth for history." Does this prevent thousands of concurrent open connections calling for stale data?

**A:** Yeah, exactly. WS is for live, REST is for history, that's it. If you reconnect after a dropped connection you don't get a replay, you just hit REST for whatever you missed and resume streaming from now. Keeps the server stateless per-connection, no per-client buffers piling up in memory, and reconnection is cheap. If we tried to replay we'd have to track per-client cursors and hold events in memory waiting for slow clients.

### Q: SSE as a WebSocket fallback?

**A:** Skip. WS should work for 99% of users. We'll deal with it if we ever see real evidence someone's blocked.

### Q: Per-subscription rate limiting? Limit big drawdowns by connection, or by Role 2 sub? Or just restrict to the IATA/super-region that's relevant for the Role 2 sub?

**A:** Nobody will be DB-calling; we only grant access to regions to read off the MQTT bus, to keep load off live.meshcore.ca. So the rate-limiting concern is really about runaway WS subscriptions, not abusive queries. A simple per-connection event cap (with `lagged` overflow) is enough.

### Q: Mobile push notifications for keywords in channel messages?

**A:** Yeah, this would be awesome. Setting up a notify on the Flutter app when a specific keyword appears in a specific channel, or when a specific node starts talking. Added to Future Features.

### Q: Neighbor graph, live packet activity flowing node-to-node, less detail than pew pew, more "did my local pathing go the way I wanted"?

**A:** Yes, added to Future Features. Different from pew pew (which is about live flood propagation). This one is about understanding the local routing topology and whether traffic is taking the paths you'd expect.

### Q: Compose default vs with-broker variants?

**A:** I think MQTT is separate and shouldn't be included in Tower. One default compose, Tower-only services (app + postgres + redis + caddy). Bring your own broker.

### Q: pprof protection, auth middleware, IP allowlist, separate port, or behind admin auth?

**A:** Tailscale handles this for us. All the servers already have a tailnet connection, I can share that with the team for access. No need to build auth in front of pprof for v1.

### Q: Add scoped auth earlier than planned?

**A:** Open to this if we think a web admin panel will add value sooner rather than later. Worth a separate discussion. What specifically would the admin panel do in v1 that the config file doesn't? If there's a strong answer, let's move it up.

### Q: Add observationId / afterId REST backfill so WS recovery is deterministic?

**A:** Yes, sounds good. Lets clients say "I last saw observation 12345, give me everything since then" without needing a timestamp. Simpler reconnection logic and no edge cases around clock skew between server and client. Now reflected in the Backpressure and reconnection section.
