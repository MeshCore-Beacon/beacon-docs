# Getting packets into Beacon

Beacon does not listen to the radio. It subscribes to one or two MeshCore MQTT brokers that
observers publish into, and stores what it hears. No broker, no data.

## How packets reach Beacon

An observer is a MeshCore device, or a bridge next to one, with a network link. It hears a LoRa
packet, notes the signal strength, and publishes it to a broker under its own IATA (airport
code) and public key. Beacon connects to the broker over secure WebSocket MQTT, decodes each
packet, works out whether it has already seen it through another observer or broker, stores it,
and streams it to anyone connected to the web app.

Two brokers can be configured. A packet heard by observers on both is stored once, with one
observation per observer.

## Which broker

- **Use an existing community broker.** The MeshCore Canada brokers (`mqtt1.meshcore.ca` and
  `mqtt2.meshcore.ca`) feed the public Beacon instances. Ask on the
  [MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf) for a subscriber account.
- **Run your own** with [meshcore-mqtt-broker](https://github.com/michaelhart/meshcore-mqtt-broker)
  and point your observers at it. Beacon only needs a subscriber account on it.

## The account Beacon needs

The broker defines three subscriber roles:

| Role | Sees | Notes |
|---|---|---|
| 1, admin | Everything, including `/internal` topics and `$SYS` | Carries observer owners' personal data. Beacon does not need it. |
| 2, full | All public topics, nothing stripped | **This is the one Beacon needs.** |
| 3, limited | Public topics with `snr`, `rssi`, `score`, `stats`, `model` and `firmware_version` removed | Not enough: Beacon stores SNR and RSSI per observation. |

Ask the broker operator for a Role 2 subscriber username and password. Put them in
`MQTT_BROKER_1_USERNAME` and `MQTT_BROKER_1_PASSWORD` (and `_2_` for a second broker), and the
broker's WebSocket endpoint in `MQTT_BROKER_1_URL`, for example `wss://mqtt1.example.com:443`.
See [Configuration](configuration.md#server-environment-variables).

## Topics

Observers publish under `meshcore/{IATA}/{observer public key}/`:

| Subtopic | Contents | What Beacon does with it |
|---|---|---|
| `packets` | Raw LoRa packets with SNR and RSSI | Decode, dedupe, store, stream |
| `status` | Observer health, position and firmware | Update the observer record |
| `internal` | Owner details from the broker login | Nothing. Beacon never subscribes to it. |

Beacon subscribes to `meshcore/#` and routes by subtopic. The IATA in the topic is where the
observer says it is. Beacon creates an IATA the first time it sees one; `iatas:` in
`config.yaml` only adds a name, coordinates and an optional border.

## Checking it works

- `GET /api/v1/brokers` shows each broker and whether it is connected.
- `docker compose logs -f app` shows a `connected` line per broker. Packets are not logged at
  the default level, so do not wait for them there.
- `GET /api/v1/observers` fills in as observers publish.
- Within a few minutes the web app's Packets tab should be moving. If it is not, see
  [Troubleshooting](troubleshooting.md#no-packets-are-arriving).
