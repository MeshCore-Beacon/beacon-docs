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
| `BEACON_SECRET_KEY` | unset | 32 random bytes in base64. Seals the guest passwords of [telemetry requests](telemetry-requests.md). See [BEACON_SECRET_KEY](#beacon_secret_key). |
| `BEACON_PORTAL_SECRET` | unset | The client secret for sign-in through the MeshMapper portal. Required when `accounts.mode` is `portal`; has no YAML key. See [Sign-in through the MeshMapper portal](portal-sign-in.md). |
| `BEACON_PUSH_CREDENTIALS` | unset | Path to a Google service account key file for push alerts. Required when `alerts.delivery` is `push`. See [Alerts](alerts.md#push). |
| `BEACON_SMTP_PASSWORD` | unset | Password for `accounts.smtp.username`. Read only when `accounts.mode` is `local`; it has no YAML key. See [User accounts](#user-accounts). |
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
| `VITE_DISABLED_TABS` | no | Comma-separated tabs to hide. Options: `Packets,Channels,Map,Nodes,Observers,Routes,Traces,Analytics,Atlas`. |
| `VITE_ENABLED_THEMES` | no | Comma-separated theme ids. When set, only these themes are offered. Listing `meshmapper_dark` or `meshmapper_light` is the only way to enable those two. |
| `VITE_APP_NAME` | no | Wordmark text in the top left. Default `BEACON`. The server also reads it as the instance name in the mail it sends: the sender name (when `accounts.smtp.from` is a bare address), the subjects and the bodies. Unset, blank or `BEACON` in any case reads as `Beacon` in mail; other values are used as written, with control characters removed, spaces collapsed and the length capped at 60 characters. The server container must receive the variable too, which it does when it shares the web container's `.env`. |
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
| `server` | `trusted_proxies`: the proxy addresses allowed to tell Beacon the real client IP. `admin_listen`: an optional private listener for Prometheus `/metrics`. `read_only`: boot a server that never writes, for comparing two builds (default `false`). | Always, if Beacon sits behind a proxy. See [Reverse proxy](reverse-proxy.md) and [Read-only mode](#read-only-mode). |
| `ratelimit` | Per-client REST limits for `/api/v1/*`. On by default at 600 requests a minute. | You get 429s you did not expect. |
| `database` | `api_plan_layout`: how API statements are spread over database connection pools. | You check `max_connections`, or need the rollback layout. See [Database pools and cost guards](#database-pools-and-cost-guards). |
| `planguard` | `daily_check`: a daily read-only check that the database still plans Beacon's queries the way they were designed. Off by default. | You run a large deployment. See [Daily plan check](#daily-plan-check). |
| `readmodels` | `cmi.enabled`: whether region and scope channel message pages may read the `channel_message_iatas` read model. `packet_sites.enabled`: whether region packet pages may read the `packet_sites` read model. Both default to `true`. `fill`: how hard the one-off backfills may work the disk. | You suspect a read model serves wrong pages, or a backfill starves a small server's disk. See [Read models](#read-models). |
| `guards` | Which request families the cost guards may refuse. All of them only observe by default. | After a week of observing. See [Database pools and cost guards](#database-pools-and-cost-guards). |
| `meshmapper` | Import transport scopes, IATA borders, region groups and public channels from MeshMapper instead of listing them by hand, and add repeater site details to node detail. Requires a [MeshMapper API key](#meshmapper-api-key). | You are in a region MeshMapper covers. |
| `iatas` | Display names, coordinates and optional border files for airport codes. IATAs are created automatically when traffic arrives; this block only decorates them. A `borderFile` path is relative to `config.yaml`; in Docker the compose file mounts only `config.yaml`, so add a mount for the folder too (`- ./data/app/borders:/app/borders:ro` under the `app` service). | You want names on the map or a border drawn. |
| `regions` | Groups of IATAs with a name, map centre and zoom. | Always, unless MeshMapper imports them. |
| `channel_keys` | Hashtag channels and explicit keys for decrypting group messages. | Always. Without keys, channel messages are stored as hashes only. |
| `scopes` | Transport scope names for matching `TRANSPORT_FLOOD` packets. Each needs a `region`. | Your mesh uses transport scopes. |
| `telemetry` | How long observer telemetry snapshots are kept and how often one is stored. | Disk is tight. |
| `polling` | Repeater polling: whether Beacon coordinates observers polling repeaters, which broker hosts they publish to, and how long readings are kept. Off by default. | You want [Repeater polling](repeater-polling.md). See [Repeater polling](#repeater-polling). |
| `accounts` | User accounts: sign-in for Beacon Web and BEACON Mobile. Off by default; with it off no account route is served. `local` needs SMTP; `portal` signs in through the MeshMapper portal. | You want people to have accounts. See [User accounts](#user-accounts) and [User accounts](accounts.md). |
| `alerts` | `delivery`: `off`, `push` or `email`. Off by default. Needs accounts. | You want [Alerts](alerts.md). See [Alerts](#alerts). |
| `backup` | Turns on the admin backup download. Off by default. | You want [Backup and export](backup-export.md). |
| `packets` | How long packets, observations and channel messages are kept. Default 7 days. | Disk is tight, or you want more history. |
| `analytics` | How long hourly stats rollups are kept. Default 90 days. They outlive raw packets. | You want longer stats windows. |
| `presence` | How observer and packet last-seen timestamps are batched before writing. | Rarely. |
| `routes` | How long known routes are kept, with a shorter window for routes seen only a few times, and `reconfirm_rows_per_hour`: how many routes an hour are rechecked for a departed or now-ambiguous hop (default `81000`, run in 5-minute slices; `0` or omitted means the default). | Rarely. |
| `websocket` | Connections per client, upgrade attempts per minute, the live-event send budget per connection, which other sites may open `/ws`, and `require_origin`: whether a client with no `Origin` needs a ticket from `/api/v1/ws-ticket` (off by default; on raises the minimum app version). | The web app is served from a different host than the API, real clients keep getting `lagged` notices from the send budget, or scripts with no `Origin` read the live feed. |
| `nodes` | When a node is marked stale, when it is deleted, the clock-drift threshold, and the optional foreign repeater flag. | You want `possiblyForeign` on repeaters. |
| `observers` | Optional deletion of observers not seen for a long time. Off by default. | Rarely. |
| `mobile` | `min_app_version`: the oldest BEACON Mobile release allowed to use this server. Older apps show an update screen. Unset by default. | You need users on a newer app release. |
| `web` | `min_web_version`: the oldest Beacon Web release allowed to use this server. Older web builds show a blocking "reload" screen. The server has a built-in floor (2.0.3 today); this can raise it, not lower it. | Your web container lags the server and you want stale browsers to reload. |
| `cors` | Browser cross-origin rules for REST: `allowed_origins`, `allowed_methods`, `allowed_headers`, `allow_credentials`, `max_age`. Default allows any origin, read-only methods, no credentials. | You are building an admin UI on another origin, or the web app is on another origin than the API and uses accounts (see [Same site](accounts.md#same-site-and-a-web-app-on-another-origin)). |
| `cache` | Redis TTLs per response category. | Rarely. |
| `ingest` | Only store packets from observers in listed countries or continents. | You run a regional instance and want to ignore the rest of the world. |
| `background` | How often cleanup, route retention and preset rebuilds run. `reconfirm` (default `1h`) sets the route retention run, which also clears stale neighbor edges; the route recheck itself always runs every 5 minutes at `routes.reconfirm_rows_per_hour`. | Rarely. |

### Things that stop startup

Beacon checks the file when it starts and refuses to run rather than run with a setting it
cannot honour. These are the ones people hit:

- A manual `scopes:` entry without `region:`, or with a slug that is not under `regions:`.
- `server.trusted_proxies` entries that are not CIDRs. One host is `10.0.0.5/32`, not `10.0.0.5`.
- `packets.retention` or `analytics.rollup_retention` under `24h`, or any negative duration
  (`observers.delete_after` is the exception: zero or negative turns it off).
- MeshMapper refresh intervals outside their range: `scopes.refresh_interval` and
  `repeaters.refresh_interval` 1h to 24h, `zones.refresh_interval` and
  `channels.refresh_interval` 24h to 168h.
- A `borderFile` that is missing or not a valid GeoJSON Polygon or MultiPolygon Feature, or
  `nodes.mark_foreign: true` with no border source at all.
- `display.temperature_unit` other than `c` or `f`, or `display.distance_unit` other than `metric` or `imperial`.
- `log.level` or `log.format` set to anything other than the listed values.
- `mobile.min_app_version` or `web.min_web_version` that is not a plain `X.Y.Z` release (`v1.2.3` and `1.2.3-beta` are rejected).
- An admin key under 16 characters or containing whitespace.
- `database.api_plan_layout` other than `custom_all`, `split` or `single`; a `guards.enforce`
  entry that is not a family name; `guards.budget` other than `shadow`; `server.admin_listen`
  that is not `host:port` with a port from 1 to 65535.
- `planguard.daily_check: true` together with `server.read_only: true`. A read-only server runs
  no background jobs, so it cannot run the check.
- A negative `ratelimit.requests_per_minute`, `ratelimit.burst`, `websocket.max_connects_per_minute`,
  `websocket.max_send_bytes_per_second`, `websocket.send_burst_bytes` or
  `routes.reconfirm_rows_per_hour`.
  A negative `websocket.max_connections_per_ip` is not caught at startup and rejects every
  connection instead, so leave it at a positive number.

## Database pools and cost guards

Beacon opens one PostgreSQL connection pool per workload. Pools open connections only when
needed, so these are peaks:

| `database.api_plan_layout` | `api_legacy` | `api_custom` | `api_cached` | `ingest` | `maint` | Total |
|---|---:|---:|---:|---:|---:|---:|
| `custom_all` (default) | - | 8 | - | 6 | 4 | 18 |
| `split` | - | 7 | 5 | 6 | 4 | 22 |
| `single` (rollback) | 8 | - | - | 6 | 4 | 18 |

`ingest` has one connection per CPU on hosts with more than 6 CPUs, which adds to each total.
The startup log line `database pools open` shows the real figure. Postgres `max_connections`
must cover it plus every other client. A `pool_max_conns` in `POSTGRES_DSN` is ignored; the
layout sets the sizes.

- **`custom_all`** plans every API statement for its own parameters on every call, so no
  statement can switch to a slow generic plan. Use it.
- **`split`** runs the statements the plan corpus admits as safe on cached generic plans, in
  the `api_cached` pool. Today that is `GetNodeByID`, `GetObserverTelemetrySince`,
  `ListKnownRoutesByIATA`, `ListKnownRoutesGlobal`, `ListObserverAdverts`, `ListPacketsByTypes`
  and `ListPacketsPage`. `ListObserverAdverts` runs there only once the
  [payload-type backfill](operations.md#after-upgrading-observation-payload-types) is done. Keep
  `custom_all` unless the [plan check](operations.md#plan-checks-planguard) has run clean against
  this deployment's database.
- **`single`** is the rollback: one API pool (`api_legacy`) on the server's own settings, and
  every guard family only observes, whatever `guards.enforce` says.

`database.slow_pool_size` is no longer read. It sized the `api_slow` pool of the 2.1 development
builds, which ran region and message statements that could read whole site histories; those
pages now seek from their window (see
[Deep region and message pages](operations.md#deep-region-and-message-pages)) and run on the
pools above. A config that still sets the key loads as before, and the server logs
`config: database.slow_pool_size is no longer used and is ignored; remove it` at `WARN` at
startup. Remove the key.

The layout changes at a restart. What each pool sets is in
[Operations](operations.md#database-pools-and-connections).

```yaml
database:
  api_plan_layout: custom_all

guards:
  enforce: []      # routes, channel_messages, packets_global, packets_region,
                   # packets_window, packet_detail, stats, other
  budget: shadow
```

The cost guards cover public `/api/v1` requests, not `/ws` or `/api/v1/admin/*`. Each request
belongs to a family and a class (the table is in the
[API contract](api-contract.md#cost-guards)). Per family, three guards decide whether a request
may use the database: at most 4 database-backed requests at once per client IP, waiting up to
5 s for a slot; a database connection within 5 s; and a database time limit of 5 s (entity),
10 s (list) or 30 s (aggregation). A family listed in `guards.enforce` refuses with `429` or
`503`. Every other family only counts what it would have refused, in
`beacon_guard_would_refuse_total`. The default `[]` refuses nothing.

`guards.enforce` is the boot default. `PUT /api/v1/admin/config` replaces it at runtime, and a
restart goes back to the file, so make the same change in both. When to enforce a family is in
[Operations](operations.md#enforcing-a-guard-family).

`guards.budget` must be `shadow`. The per-client database time budget (30 s, refilling at one
second per second) only counts; it never refuses.

`server.admin_listen` (default empty, off) opens a second listener, for example
`127.0.0.1:9090`, that serves only `GET /metrics`. It has no authentication, so bind it to
loopback or a private network and never publish it through the proxy. See
[Operations](operations.md#metrics).

## Read-only mode

```yaml
server:
  read_only: false
```

`server.read_only: true` boots a server that never writes to the database. It skips the
migrations, the seeding of configured IATAs, regions and scopes, the boot backfill of channel
messages, MQTT ingest, the presence writer, the rollup catch-up, every background job and the
MeshMapper imports. Every database session it opens is read-only
(`default_transaction_read_only`), so anything that would still write, such as
`POST /api/v1/admin/accounts`, fails with SQLSTATE `25006` instead of changing data. The server
logs a warning at startup saying so. The one thing it still runs is a read-only check of each
read model (channel messages and packets by site) every 5 minutes; see [Read models](#read-models).
When `meshmapper.scopes.enabled` is on, it also loads the writer's saved MeshMapper scope
catalogues once at boot, reading only, so region and IATA scope lists (`/scopes?region=`,
`/stats/scopes?region=`) match the writer's as of that boot. They don't refresh until the next
restart.

The REST API and `/ws` still serve what is in the database, but nothing new arrives. Because no
migrations run, the database must already be at the schema the build expects. Its use is
comparing two builds side by side against one copy of a database; see
[Operations](operations.md#comparing-two-builds). Do not run it as a production instance.

## Daily plan check

```yaml
planguard:
  daily_check: false
```

`planguard.daily_check: true` makes the server check, once a day, that PostgreSQL still plans
each of Beacon's statements the way it was designed: the expected driving index and no
forbidden scans, in both custom and generic plan mode. The first run is about an hour after
startup. It plans only, with plain `EXPLAIN` on the maintenance pool, inside read-only
transactions with a 1 s lock timeout and 5 s per plan, so it never executes a statement or
changes data.

It is off by default because the expected plans assume production-sized tables. On a small
database the planner legitimately picks other plans, and the check would report failures that
are not real. Turn it on for a large deployment; see
[Operations](operations.md#turning-on-the-daily-check). The report is served at
`GET /api/v1/admin/db/planguard` ([API contract](api-contract.md#admin)) and exported as
metrics.

It cannot be combined with `server.read_only: true`; the server refuses to start with both.

## Read models

```yaml
readmodels:
  cmi:
    enabled: true
  packet_sites:
    enabled: true
  fill:
    duty: 0.5
    min_pause: 100ms
    packet_sites_slice: 500000
    cmi_batch: 10000
```

`channel_message_iatas` holds one row for each channel message and each site that heard it.
Channel message pages filtered by `iatas`, or by `scope` without `since`, are served from it,
and only while the server process trusts the table. While it does not (the first fill after an
upgrade, a repair, a failed verification), those pages answer `503` with `Retry-After: 30`; see
[Operations](operations.md#read-models-channel-messages-by-site).

`readmodels.cmi.enabled: false` is the kill switch, for when you suspect the table serves wrong
pages. It turns those pages off: they answer `503` until the key is `true` again. Pages that do
not read the table (no `iatas`, `scope` with `since`, and `iatas` with `since` or `scope`
across every channel) are not affected. The server still maintains and repairs the table, so
setting it back to `true` needs only a restart. Omitting the key means `true`. Like every key in
this file, a change needs a restart.

`packet_sites` holds one row for each packet and each site that heard it. `/packets` pages
filtered by `iatas`, `iata`, `region` or `regionId` are served from it, and only while the
server process trusts the table; until then they answer `503` with `Retry-After: 30`. See
[Operations](operations.md#read-models-packets-by-site).

`readmodels.packet_sites.enabled: false` is its kill switch: region packet pages answer `503`
until it is `true` again. The server still maintains and sweeps the table, so setting it back
to `true` needs only a restart. Omitting the key means `true`.

Observer advert pages (`/observers/{id}/adverts`) have no switch: they answer `503` until the
[payload-type backfill](operations.md#after-upgrading-observation-payload-types) is done, which
is at once on a deployment where every observation already carries its payload type.

On a [read-only server](#read-only-mode) both keys work the same way. Such a server never
writes the tables; it trusts each one only while the writing server keeps it up to date.

### Backfill pacing

`readmodels.fill` paces the one-off backfills: the `packet_sites` and `channel_message_iatas`
fills after an upgrade or a rebuild, and the
[payload-type backfill](operations.md#after-upgrading-observation-payload-types). The
[channel message backfill](operations.md#channel-message-backfill) after each start uses `duty`
only, with no `min_pause`. After each
slice or batch a fill sleeps `max(min_pause, elapsed × (1 − duty) / duty)`, where `elapsed` is
how long that slice took. A slow disk makes each slice take longer, so it stretches the pauses
on its own. Pacing changes only when the fills run, never what they write.

| Key | Default | Range | What it does |
|---|---|---|---|
| `duty` | `0.5` | 0.01 to 1 | The share of time a fill may be busy. `0.5` waits as long as each slice took; `0.25` waits three times as long; `1` waits only `min_pause`. No single pause is longer than 10 minutes. |
| `min_pause` | `100ms` | `0s` to `1m` | The shortest pause after a slice or batch. |
| `packet_sites_slice` | `500000` | 1 to 10,000,000 | Observations one `packet_sites` backfill slice covers, however far apart their ids are. |
| `cmi_batch` | `10000` | 1 to 1,000,000 | Message ids one `channel_message_iatas` backfill batch covers. |

The defaults suit a small server. On a slow (rotational or shared) disk, set `duty: 0.25`. A
value out of range stops the server at startup with an error naming the key. The startup log
line `config: loaded` shows the values in force (`fillDuty`, `fillMinPause`,
`fillPacketSitesSlice`, `fillCmiBatch`). See [Pacing the backfills](operations.md#pacing-the-backfills).

## Repeater polling

The `polling` block turns on [Repeater polling](repeater-polling.md). It is off by default.
Zero or omitted values use the default. A value out of range stops startup with an error naming
the key.

| Key | Default | Range | What it does |
|---|---|---|---|
| `enabled` | `false` | | Turns polling on. Needs `mqtt_hosts`. |
| `mqtt_hosts` | none | 1 to 4 hosts when enabled | Broker hosts observers publish to. Plain hostnames of 1 to 63 letters, digits, dots or hyphens, no port. Sent to observers so they pick the matching MQTT slot. |
| `direct_window` | `1h` | `30m` to `24h` | How old the newest reading may get before the poller asks again. |
| `grace` | `30m` | `10m` to `2h` | The extra wait for each standby rank. |
| `max_requests` | `2` | 1 to 3 | Poll starts per repeater per window, sent to observers. |
| `reading_retention` | `744h` | at least `1h` | How long readings are kept, but never less than the freshness window of the working-poll check (4 hours by default, four times `direct_window`, at most 48 hours). A shorter value is raised to it. |
| `min_client_version` | empty | `X.Y.Z` | The oldest observer firmware allowed to poll. Empty allows all. Observer firmware that sends no version fails the check when this is set. Any other value stops Beacon at startup. |
| `excluded_nodes` | none | up to 16 | Repeater public keys, 64 hex characters each, that are never polled. |
| `paused` | `false` | | Tells every observer to stop. Overrides the admin route. |
| `authority` | `evidence` | `evidence` or `approved` | Who can be elected to poll. `evidence`: any observer, ranked on the advert evidence it reports. `approved`: only observers approved through the admin route. See [Trust](repeater-polling.md#trust). |
| `requests_per_user` | `3` | 0 to 20 | How many [telemetry requests](telemetry-requests.md) one user may hold. `0` turns requests off. |
| `offline_disable_days` | `7` | 1 to 365 | Days no observer hears a repeater before its requests are turned off. |
| `request_observers` | `approved` | `approved` or `all` | Which observers may be handed a requested repeater and its guest password. `approved`: only observers you approved. `all`: any observer with advert evidence, which lets anyone who runs an observer present evidence and be handed a guest password. Use `all` only where you know every observer. |

Telemetry requests also need accounts on and `BEACON_SECRET_KEY`; see
[Requested telemetry](telemetry-requests.md#turn-it-on). The gates are checked in this order:
polling on, `requests_per_user` above `0`, accounts on, then the key. The first one that fails turns
requests off (with accounts off the request routes answer `accounts_disabled`); polling off logs no
reason, the others log one line.

```yaml
polling:
  enabled: true
  mqtt_hosts: [mqtt1.example.com]
```

Pause, exclusions and blocked observers can also change at runtime through
`/api/v1/admin/polling`, with no restart. Config and runtime exclusions are added together and
may name at most 16 different repeaters between them; the admin route refuses a list that would
go over.

## User accounts

The `accounts` block turns on [User accounts](accounts.md). It is off by default. A value out of range
stops startup with an error naming the key. With `mode: off` the rest of the block is not read.

| Key | Default | What it does |
|---|---|---|
| `mode` | `off` | `off`, `local` or `portal`. |
| `public_url` | none | Required with `local` and `portal`. The web app's address, `https` (plain `http` only for `localhost` and `127.0.0.1`), no path. Used for mailed links and the cookie's `Secure` flag. |
| `registration` | `open` | `open` or `closed`. |
| `smtp.host` | none | Required with `local`. |
| `smtp.port` | `587` | 1 to 65535. |
| `smtp.username` | empty | Empty means no authentication. |
| `smtp.from` | none | Required with `local`. One address, for example `"Beacon <no-reply@example.org>"`. |
| `smtp.starttls` | `true` | When true the send fails unless the server offers STARTTLS. |
| `portal.url` | none | Required with `portal`. The portal's `https` base address, with no credentials, query or fragment. |
| `portal.client_id` | none | Required with `portal`. The id the portal knows this instance by. |

With `portal`, the `smtp` block is not used and registration is always closed. The client secret is
`BEACON_PORTAL_SECRET`, never in the file. See [Sign-in through the MeshMapper portal](portal-sign-in.md).

The SMTP password is `BEACON_SMTP_PASSWORD` in the environment, never in the file.

```yaml
accounts:
  mode: local
  public_url: https://beacon.example.org
  smtp:
    host: smtp.example.org
    username: beacon@example.org
    from: "Beacon <no-reply@example.org>"
```

A web app on another origin than the API also needs `cors.allowed_methods`, `cors.allowed_headers`
(with `X-Beacon-CSRF`) and `cors.allow_credentials`. Same origin needs nothing. See
[User accounts](accounts.md#same-site-and-a-web-app-on-another-origin).

## Alerts

The `alerts` block turns on [Alerts](alerts.md). It needs [User accounts](accounts.md).

| Key | Default | What it does |
|---|---|---|
| `delivery` | `off` | `off`, `push` or `email`. `email` needs `accounts.mode: local`; with `portal` startup fails. `push` needs `BEACON_PUSH_CREDENTIALS` in the environment, and startup fails without it. Anything else stops startup. |

```yaml
alerts:
  delivery: email
```

`BEACON_PUSH_CREDENTIALS` is the path, inside the container, of a Google service account key file
(JSON with `project_id`, `client_email` and `private_key`). Mount the file read-only and keep it out
of source control. See [Push](alerts.md#push).

## Display units

The `display` block sets the units this instance shows. It is optional and the same for every user.

| Key | Default | What it does |
|---|---|---|
| `temperature_unit` | `c` | `c` or `f`. Case does not matter. Anything else stops startup. |
| `distance_unit` | `metric` | `metric` or `imperial`. Case does not matter. Anything else stops startup. |

```yaml
display:
  temperature_unit: f
  distance_unit: imperial
```

Clients read both from `display` in [Server info](api-contract.md#server-info). On `f`, the web and the app show temperatures in degrees F, and [alert](alerts.md) mail and push text give temperatures in F. Users also type and see temperature alert limits in whole degrees F. On `imperial`, clients show distances in miles and feet. The API does not change: it still stores and sends Celsius and metric.

## BEACON_SECRET_KEY

`BEACON_SECRET_KEY` seals the guest passwords users enter for [telemetry requests](telemetry-requests.md)
before they are stored (AES-256-GCM). Generate it once:

```bash
openssl rand -base64 32
```

Put it in `.env` as `BEACON_SECRET_KEY=...`. It must decode to exactly 32 bytes (standard or URL
base64, padded or not). The key is read only after the other gates pass (`polling.enabled` on,
`polling.requests_per_user` above `0`, accounts on). Then a value that is not valid stops startup;
when any of those gates fails, a malformed key is ignored and Beacon starts. When the key is unset,
Beacon starts with telemetry requests off and logs why (except with polling off, which logs no
reason). See [Requested telemetry](telemetry-requests.md#turn-it-on).

Back it up with your other secrets. If you lose it or change it, stored passwords cannot be opened:
Beacon stops sending those repeaters' passwords to observers and logs "requested password does not
open". Users enter their guest passwords again, which seals them under the new key. Requests that
use no password are not affected. Nothing else Beacon stores is sealed with it, so it does not
protect or affect accounts, sessions or any other data.

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

Beacon sends `X-API-Key` to `get_zones.php`, `get_geojson.php`, `get_scopes.php`,
`get_channels.php`, and `get_repeaters.php`. Requests use trusted HTTPS MeshMapper
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
