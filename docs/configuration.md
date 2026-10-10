# Configuration

Beacon takes settings from two places. Secrets and addresses go in environment variables, which
the Docker deployments read from `.env`. Everything that describes your network goes in
`config.yaml`.

## Server environment variables

beacon-server reads these at startup. A missing value that the server needs is logged as a
warning, and the first thing that needs it fails (ingest fails to connect, the database fails
to open).

| Variable | Default | What it does |
|---|---|---|
| `POSTGRES_DSN` | none, required | PostgreSQL connection string, for example `postgres://beacon:password@db:5432/beacon?sslmode=disable`. In the Docker stack the password must match `POSTGRES_PASSWORD` in `docker-compose.yml`. |
| `REDIS_ADDR` | unset | Redis `host:port`. Leave it unset to run without the cache; every read then goes to PostgreSQL. |
| `REDIS_PASSWORD` | unset | Redis password, if the server has one. |
| `REDIS_DB` | `0` | Redis database index. |
| `LISTEN_ADDR` | `:8080` | Address and port the HTTP server listens on. |
| `CONFIG_PATH` | `config.yaml` | Path to the YAML config file. Beacon starts without one, with every setting at its default. |
| `MQTT_BROKER_1_URL` | unset | WebSocket URL of your first MeshCore MQTT broker, for example `wss://mqtt1.example.com:443`. |
| `MQTT_BROKER_1_USERNAME` | unset | Subscriber username for broker 1. See [Getting packets in](getting-packets-in.md) for the account type you need. |
| `MQTT_BROKER_1_PASSWORD` | unset | Subscriber password for broker 1. |
| `MQTT_BROKER_2_URL`, `_USERNAME`, `_PASSWORD` | unset | The same for an optional second broker. A packet heard through both brokers is stored once. |
| `BEACON_API_KEY` | unset | Bearer key for `/api/v1/admin/*`. When set, even to an empty string, it replaces `auth.api_key` from the config file. See [Admin API key](#admin-api-key). |
| `MESHMAPPER_API_KEY` | unset | Regional or grouped-region key for enabled MeshMapper imports. When set, even to an empty string, it replaces `meshmapper.api_key`. Missing keys leave imports unconfigured while Beacon keeps running. See [MeshMapper API key](#meshmapper-api-key). |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn` or `error`. Overrides `log.level`. Anything else stops startup. |
| `LOG_FORMAT` | `text` | `text` or `json`. Overrides `log.format`. Anything else stops startup. |
| `BEACON_CPU_PROFILE_DIR`, `BEACON_CPU_PROFILE_UNTIL` | unset | Enable a bounded CPU capture in production. See [Profiling](profiling.md). |
| `PGDATABASE` | unset | Used only by the admin backup export. See [Backup and export](backup-export.md). |

## Web environment variables

The web container reads these every time it starts and writes them to `/config.js`, which the
browser loads fresh on each visit. To change one, edit `.env` and run `docker compose up -d web` (`beacon-web` in the split deployment).
Visitors get the new values on their next page load. Any characters are fine in values.

| Variable | Required | What it does |
|---|---|---|
| `VITE_API_BASE` | yes | REST base URL as the browser sees it, for example `https://beacon.example.com/api/v1`. It must be the public address, never `localhost`. |
| `VITE_WS_URL` | yes | WebSocket URL as the browser sees it, for example `wss://beacon.example.com/ws`. |
| `VITE_MAP_CENTER`, `VITE_MAP_ZOOM` | no | Fallback map view as decimal `lat,lon` and a zoom from 0 to 22, used before airports load or when the selected region has no location. Unset is a world view. |
| `VITE_DISABLED_TABS` | no | Comma-separated tabs to hide. Options: `Packets,Channels,Map,Nodes,Observers,Routes,Traces,Analytics`. |
| `VITE_ENABLED_THEMES` | no | Comma-separated theme ids. When set, only these themes are offered. Listing `meshmapper_dark` or `meshmapper_light` is the only way to enable those two. |
| `VITE_APP_NAME` | no | Wordmark text in the top left. Default `BEACON`. |
| `VITE_SKIP_SPLASH` | no | `true` skips the once-per-session loading splash. |
| `VITE_BANNER` | no | Notice shown above the header on every page, for example on a test instance. `[label](url)` and bare URLs become links. |

## Deployment variables

These are read by `docker-compose.yml` and Caddy, not by Beacon itself.

| Variable | Used by | What it does |
|---|---|---|
| `DOMAIN` | Caddy, both deployments | The public hostname Caddy serves and requests a certificate for. |
| `WEB_DOMAIN` | Caddy, type 2 server host only | The web frontend's hostname. Anything that is not `/api/*` or `/ws` is redirected there. |
| `BEACON_WEB_IMAGE` | type 2 web host | The image to run, for example `ghcr.io/meshcore-beacon/beacon-web:2.0`. Keep its `X.Y` equal to the server's. |
| `POSTGRES_PASSWORD` | the `db` service | Set in `docker-compose.yml`, not `.env`. It must match the password inside `POSTGRES_DSN`. |

## config.yaml

[`app_config/config.yaml.example`](../app_config/config.yaml.example) documents every key with
its default and is the file to copy from. This is a map of what each block is for, so you know
which ones to read.

| Block | What it controls | Worth reading when |
|---|---|---|
| `auth` | The admin API key, if you would rather keep it in the file than in `BEACON_API_KEY`. | You want the admin endpoints. |
| `log` | Log level and format. | You want JSON logs for a collector. |
| `server` | `trusted_proxies`: the proxy addresses allowed to tell Beacon the real client IP. | Always, if Beacon sits behind a proxy. See [Reverse proxy](reverse-proxy.md). |
| `ratelimit` | Per-client REST limits for `/api/v1/*`. On by default at 300 requests a minute. | You get 429s you did not expect. |
| `meshmapper` | Import transport scopes, IATA borders, region groups and public channels from MeshMapper instead of listing them by hand. Requires a [MeshMapper API key](#meshmapper-api-key). | You are in a region MeshMapper covers. |
| `iatas` | Display names, coordinates and optional border files for airport codes. IATAs are created automatically when traffic arrives; this block only decorates them. A `borderFile` path is relative to `config.yaml`; in Docker the compose file mounts only `config.yaml`, so add a mount for the folder too (`- ./data/app/borders:/app/borders:ro` under the `app` service). | You want names on the map or a border drawn. |
| `regions` | Groups of IATAs with a name, map centre and zoom. | Always, unless MeshMapper imports them. |
| `channel_keys` | Hashtag channels and explicit keys for decrypting group messages. | Always. Without keys, channel messages are stored as hashes only. |
| `scopes` | Transport scope names for matching `TRANSPORT_FLOOD` packets. Each needs a `region`. | Your mesh uses transport scopes. |
| `telemetry` | How long observer telemetry snapshots are kept and how often one is stored. | Disk is tight. |
| `backup` | Turns on the admin backup download. Off by default. | You want [Backup and export](backup-export.md). |
| `packets` | How long packets, observations and channel messages are kept. Default 7 days. | Disk is tight, or you want more history. |
| `analytics` | How long hourly stats rollups are kept. Default 90 days. They outlive raw packets. | You want longer stats windows. |
| `presence` | How observer and packet last-seen timestamps are batched before writing. | Rarely. |
| `routes` | How long known routes are kept, with a shorter window for routes seen only a few times. | Rarely. |
| `websocket` | Connections per client, upgrade attempts per minute, and which other sites may open `/ws`. | The web app is served from a different host than the API. |
| `nodes` | When a node is marked stale, when it is deleted, the clock-drift threshold, and the optional foreign repeater flag. | You want `possiblyForeign` on repeaters. |
| `observers` | Optional deletion of observers not seen for a long time. Off by default. | Rarely. |
| `mobile` | `min_app_version`: the oldest BEACON Mobile release allowed to use this server. Older apps show an update screen. Unset by default. | You need users on a newer app release. |
| `web` | `min_web_version`: the oldest Beacon Web release allowed to use this server. Older web builds show a blocking "reload" screen. The server has a built-in floor (2.0.3 today); this can raise it, not lower it. | Your web container lags the server and you want stale browsers to reload. |
| `cors` | Browser cross-origin rules for REST. Default allows any origin, read-only methods. | You are building an admin UI on another origin. |
| `cache` | Redis TTLs per response category. | Rarely. |
| `ingest` | Only store packets from observers in listed countries or continents. | You run a regional instance and want to ignore the rest of the world. |
| `background` | How often cleanup, route reconfirmation and preset rebuilds run. | Rarely. |

### Things that stop startup

Beacon checks the file when it starts and refuses to run rather than run with a setting it
cannot honour. These are the ones people hit:

- A manual `scopes:` entry without `region:`, or with a slug that is not under `regions:`.
- `server.trusted_proxies` entries that are not CIDRs. One host is `10.0.0.5/32`, not `10.0.0.5`.
- `packets.retention` or `analytics.rollup_retention` under `24h`, or any negative duration
  (`observers.delete_after` is the exception: zero or negative turns it off).
- MeshMapper refresh intervals outside their range: `scopes.refresh_interval` 1h to 24h,
  `zones.refresh_interval` and `channels.refresh_interval` 24h to 168h.
- A `borderFile` that is missing or not a valid GeoJSON Polygon or MultiPolygon Feature, or
  `nodes.mark_foreign: true` with no border source at all.
- `log.level` or `log.format` set to anything other than the listed values.
- `mobile.min_app_version` or `web.min_web_version` that is not a plain `X.Y.Z` release (`v1.2.3` and `1.2.3-beta` are rejected).
- An admin key under 16 characters or containing whitespace.
- A negative `ratelimit.requests_per_minute`, `ratelimit.burst` or `websocket.max_connects_per_minute`.
  A negative `websocket.max_connections_per_ip` is not caught at startup and rejects every
  connection instead, so leave it at a positive number.

## MeshMapper API key

MeshMapper APIs require either a regional API key or a grouped-region API key covering
multiple regions. Your local MeshMapper regional or grouped-region admin can generate
these keys. Request a key for the APIs Beacon uses, covering your IATA or every member IATA
in your group, including members added by `meshmapper.zones.import_groups`.

Set `MESHMAPPER_API_KEY` in the deployment's private `.env` or backend environment. Each
Beacon deployment can use a different key. It overrides `meshmapper.api_key` in
`config.yaml`, even when the environment value is empty. Both examples leave the key empty.
Do not use the mobile app's App key, `BEACON_API_KEY`, or a Coverage API key for this setting.
Never put it in a `VITE_*` value, browser configuration, logs, or git.

After changing `.env`, recreate the backend container from the deployment folder
(`docker-deployment-type2/server` for the split deployment):

```bash
docker compose up -d --force-recreate app
```

A plain `docker compose restart app` does not load changed container environment variables.
If you use the YAML setting instead, restarting Beacon is enough. Prefer the environment
setting when using [backups](backup-export.md): exports refuse a nonempty
`meshmapper.api_key` in the saved YAML so the key cannot enter a download.

Beacon sends `X-API-Key` to `get_zones.php`, `get_geojson.php`, `get_scopes.php`, and
`get_channels.php`. Its shared client supports the same header for `get_repeaters.php`,
although Beacon does not currently fetch repeaters. Requests use trusted HTTPS MeshMapper
endpoints and do not follow redirects. `get_zones.php` still needs its `country` parameter;
a key covering multiple regions does not change the request shape or remove rate limits.
IP exemptions are not authentication.

With no key, MeshMapper imports report unconfigured and make no requests. Beacon keeps
running and restores saved imports. Failed refreshes keep the last successful cached data
and its freshness timestamp; 401 reports authentication failure and 403 reports permission
failure, without falling back to anonymous requests. Existing backoff and longer
`Retry-After` delays on 429/503 remain in effect. See
[MeshMapper troubleshooting](troubleshooting.md#meshmapper-imports-are-unconfigured-or-stale).

### Coordinate the MeshMapper rollout

Before enforcement, confirm with the MeshMapper admin that Server supports `X-API-Key`,
that the key covers the required APIs and IATAs, and that these calls do not consume Coverage
quota. Header support must not be assumed deployed. The first four endpoints can require
keys before the app rollout; repeater enforcement waits for app 1.4.1 and its forced update.
Key issuance, permissions, quotas, and enforcement switches remain MeshMapper Server work,
tracked in [MeshMapper_Server#431](https://github.com/MeshMapper/MeshMapper_Server/issues/431).

Existing `coverage.php` consumers keep their own keys, scopes, quotas, and supported
`?key=` authentication. Do not move them to header-only authentication without confirmed
server support; Beacon's importer does not call `coverage.php`.

## Admin API key

The `/api/v1/admin/*` endpoints need `Authorization: Bearer <key>`. Everything else, including
the WebSocket, is public.

- Set the key with `BEACON_API_KEY` or `auth.api_key`. If the environment variable is set, it
  wins, and setting it to an empty string turns admin access off even if the file has a key.
  Beacon never generates a key for you; `openssl rand -hex 32` makes a good one.
- The key must be at least 16 characters with no whitespace inside it. Surrounding whitespace
  is trimmed. A key that breaks these rules stops startup. Changing the key needs a restart.
- With no key, admin requests return `503`. A missing, wrong or duplicated header returns `401`.
- Send the key only in the header, never in a URL or body, and keep it out of source control
  and logs.
