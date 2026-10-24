# Upgrading

## Upgrading to 2.0.0 from 1.x

**2.0.0 needs a fresh database.** It starts from a new schema baseline. Pointed at a 1.x
database it refuses to start with:

```
database schema predates Beacon 2.0.0; 2.0.0 needs a fresh database
```

1.x history does not carry over. For the all-in-one stack, in this order:

**1. Stop the stack and keep a copy of everything you edited.**

```bash
docker compose down
cp -r ../docker-deployment-type1 ../docker-deployment-type1.bak   # .env, config.yaml, Caddy files, blocklist
```

**2. Update the deployment files.** If the folder is a git clone, `git pull` will refuse
because the 1.x layout tracked `.env` and you edited `docker-compose.yml`:

```bash
git checkout -- . && git pull
```

Then put your own files back from the copy: `.env`, `data/app/config.yaml`, and anything you
changed under `data/Caddy/`. Do not copy `docker-compose.yml` back; re-apply your
`POSTGRES_PASSWORD` to the new one instead.

**3. Fix the database names.** The user and database are called `beacon` now, not `tower`.
In `.env`, change both in `POSTGRES_DSN` (`postgres://beacon:...@db:5432/beacon`). The new
`docker-compose.yml` already uses `beacon`. The names only have to agree with each other, so
if you have already initialised a 2.0.0 database under `tower`, either keep `tower` in both
places or move that data directory away as well.

**4. Move the 1.x database away and start.** Postgres only creates the user and database on
an empty data directory, so do this after step 3, not before:

```bash
mv data/postgres data/postgres-1.x   # or rm -rf data/postgres once you no longer need it
docker compose pull
docker compose up -d
```

`docker compose down` also lets the network come back with the new fixed subnet. If
`172.30.0.0/24` is already used on your host, pick another in `docker-compose.yml` and change
`server.trusted_proxies` in `data/app/config.yaml` to match.

Config that **stops startup** if left as it was:

- Every manual `scopes:` entry needs `region:` set to one of your `regions:` slugs.
- MeshMapper refresh intervals must be within bounds: `meshmapper.scopes.refresh_interval` 1h
  to 24h, `meshmapper.zones.refresh_interval` and `meshmapper.channels.refresh_interval` 24h to
  168h.
- `packets.retention` and `analytics.rollup_retention` must be at least `24h`.
- `server.trusted_proxies` entries must be CIDRs (`10.0.0.5/32`, not `10.0.0.5`).

Other changes to review:

- `meshmapper.scopes.sources` is ignored, with a warning. Scope catalogues are now found
  through MeshMapper's zone list for every known IATA.
- **REST rate limiting is on by default:** 300 requests per minute per client IP on
  `/api/v1/*` (IPv6 clients share a /64), answered with `429` and `Retry-After`. Behind a
  proxy, set `server.trusted_proxies` and have the proxy send `X-Real-IP` (see
  [Reverse proxy](reverse-proxy.md)); `X-Forwarded-For` and `True-Client-IP` are not trusted.
  Tune or turn it off under `ratelimit:`.
- **WebSocket upgrades are rate limited** to `websocket.max_connects_per_minute` (default 10)
  per client IP, on top of `max_connections_per_ip` (default 5). Only the page's own host may
  open `/ws` unless you list other origins in `websocket.allowed_origins`, for example when the
  web app is served from a different host than the API.
- `packets.retention` now defaults to **7 days** and also covers observations and channel
  messages. Historical stats come from hourly rollups kept for `analytics.rollup_retention`
  (90 days).
- Admin endpoints under `/api/v1/admin/` need `BEACON_API_KEY` (or `auth.api_key`).
- Image tags: `latest` is the newest stable release from `main`. Pin `:2.0` on both images if
  you want to choose when to move to the next minor release.

[`app_config/config.yaml.example`](../app_config/config.yaml.example) is the full 2.0.0
reference.

## Routine upgrades

Pin both images to the same release line in `docker-compose.yml` (see
[Image tags](releases.md#image-tags)), then:

```bash
docker compose pull
docker compose up -d
```

Database migrations run when the server starts. Read the release notes first; a release that
needs a config change says so there. Keep server and web on the same `X.Y`.

Since server 2.0.4, a server can require a minimum Beacon Web version (`minWebVersion` at
`GET /api/v1/info`; see `web.min_web_version` in [Configuration](configuration.md)). An older web
build shows a "reload" screen instead of the app, so pull the web image together with the server.

## MeshMapper API authentication rollout

When upgrading to a Beacon build with MeshMapper API authentication, configure the key
before relying on imports. Ask your local MeshMapper regional or grouped-region admin
for a key covering the required APIs and your region or all member regions. Confirm
MeshMapper Server supports `X-API-Key` before enforcement; see
[MeshMapper API key](configuration.md#meshmapper-api-key) for the rollout details.

Set `MESHMAPPER_API_KEY` in the backend `.env`, then recreate the `app` container:

```bash
docker compose up -d --force-recreate app
```

Without a key, Beacon keeps running and retains saved imports, but MeshMapper refreshes
are unconfigured. Existing IP exemptions are not a substitute for a key. After configuring
one, check the MeshMapper logs for successful refreshes; existing backoff still applies.
If you use backups, leave `meshmapper.api_key` empty in the saved YAML and keep the key in
the environment. Exports refuse a nonempty saved YAML key.

## REST rate limit raised to 600

Newer builds default `ratelimit.requests_per_minute` (and `burst`) to 600 a minute instead
of 300. Opening the Map and Nodes tabs on a region of a few thousand nodes could run past
300 and leave the map half loaded. The shipped `config.yaml` templates set the value
explicitly, so an existing deployment keeps 300 until you change it:

```yaml
ratelimit:
  enabled: true
  requests_per_minute: 600
  burst: 600
```

Then run `docker compose restart app`. If you run the [fail2ban jails](../app_config/fail2ban/README.md),
the flood jail's `maxretry` of 900 still sits above the new limit.

## Upgrading to 2.1

Server 2.1.0 is one upgrade from any 2.0.x release. It runs migrations `004` to `053` at startup,
adds two read models that region and scope pages are served from, and drops indexes and one
column nothing reads any more. No config change is required. Beacon Web must move to 2.1 at the
same time (`minWebVersion` is 2.1.0; an older web build shows the reload screen). The minimum app
version stays 2.0.0, so installed apps keep working.

The upgrade has two phases. First the server runs its migrations while the API and ingest are
down. Then it serves the API again and fills the read models in the background; until each one
is ready, the pages it serves answer `503` with `Retry-After`. Web and app retry for about 90 s,
then show an error with a retry button.

### Before you upgrade

1. **Back up** the database; see [Backing up](operations.md#backing-up). The
   [rollback](#rolling-back-from-21) does not need the backup, but it is the only way back from
   anything unexpected.
2. **Disk.** On a large deployment the release adds about 1 GB net (the new `packet_sites` table
   is about 2.3 GB; dropped indexes free the rest), and the first fill writes about 8 GB of WAL
   within minutes. Keep that much free on the volume under `data/postgres/`, with room to spare.
3. **Slow disk or small VM** (rotational, network or shared storage, or a few GB of RAM): set
   `readmodels.fill.duty: 0.25` and `readmodels.fill.packet_sites_slice: 100000` in `config.yaml`
   before upgrading. At full speed the first fill can stall such a machine; paced, it takes
   longer but the server stays responsive. See [Pacing the backfills](operations.md#pacing-the-backfills).
4. **Connections.** The server now opens one pool per workload: 18 connections by default, plus
   one for each CPU above 6. Check that Postgres `max_connections` leaves room for that and your
   own sessions; see [Database pools and connections](operations.md#database-pools-and-connections).
5. **Large deployments only** (tens of millions of routes, hundreds of millions of observations):
   pre-build the new indexes off-peak, while the old version keeps running, to shorten the
   startup pause:
   - [the route hop index](operations.md#pre-building-the-route-hop-index) (10 to 25 minutes
     at startup otherwise),
   - [the four packets indexes](operations.md#pre-building-the-packets-indexes),
   - [the observer adverts index](operations.md#pre-building-the-observer-adverts-index).

   Everyone else can skip this: the server builds them at startup. The four indexes of
   [`054` to `057`](operations.md#indexes-for-deep-region-and-message-pages-054-to-057) need no pre-build: three build on
   tables the same startup creates, and `idx_channel_messages_sent` reads `channel_messages` in
   well under a second. A server already on a 2.1 development build builds all four on full
   tables in a few seconds; pre-build them there only if you want, with the text in that
   section.
6. Run the [pre-deploy check](operations.md#before-deploying-a-release) (no long transactions,
   no anti-wraparound vacuum, no `pg_dump` running), and pick a quiet hour.

### Upgrade

Pull and start the server and web images together, as in [Routine upgrades](#routine-upgrades):

```bash
docker compose pull
docker compose up -d
```

### What happens, and how long

| Phase | Pages affected | Small deployment | Large deployment |
|---|---|---|---|
| Startup migrations | Whole API and ingest down; packets arriving meanwhile are not stored | Seconds | Under a minute with the indexes pre-built; add 10 to 25 minutes for the route hop index and a few more for the others if not. Two checks on `packets` (`026`, `028`) always run here |
| Channel messages by site | Channel message pages filtered by `iatas`, `region` or `scope` answer `503` | Seconds | About 1 to 5 minutes |
| Packets by site | `/packets` filtered by `iatas`, `iata`, `region` or `regionId` answer `503` | Seconds to minutes | Roughly 5 to 20 minutes at `duty: 1`; about twice that at the default `0.5`, four times at `0.25` |
| Observation payload types | Observer advert pages answer `503` | About a minute when every observation already has its type | Up to about 80 minutes when many observations have none |

A slow disk stretches every phase: on a test server with a rotational disk and about 6 million
observations, the migrations took 8 minutes and the fills at `duty: 0.25` about an hour.

**Measured on a large deployment** (8 vCPU, 8 GB RAM, NVMe; 91 GB database with 35 million
routes, 30 million observations and 3 million packets; default pacing):

| Step | Time |
|---|---|
| Pre-building the eight indexes, old version still serving | 1 min 50 s (route hop index 72 s, adverts index 16 s, the rest under 8 s each) |
| Migrations `004` to `053` at startup | 7.4 s (the two `packets` checks 3.7 s and 1.8 s) |
| API and ingest down | about 15 s |
| Channel message pages by site back | 8 min after startup |
| Observer advert pages | at once (no untyped observations) |
| Region packet pages back | 50 min after startup |
| Database size | 91 GB before, 71 GB after |

The region packet fill walks the whole observation id range, newest to oldest, so a database that
still holds a few very old observations fills for longer than its row count suggests, and the
`eta` in its progress lines overstates the time left.

Watch the log for these lines; each one ends a phase:

- `Beacon listening on :8080`: migrations done, API up.
- `cmi trusted: region and scope message pages read channel_message_iatas`
- `packet_sites trusted: region packet pages read packet_sites`
- `... backfill progress` lines show a fill moving.

After that the server keeps both read models up to date as it ingests, and earns their trust
again within a second or two of every later restart. If trust ever drops, the log says
`read model untrusted ...` and later `read model trusted again: its pages are served from it`;
see [Pages that wait for a read model](operations.md#pages-that-wait-for-a-read-model).

### After upgrading

- **Ingest cost.** Each stored observation now costs about 15 to 21 % more insert time and 37 to
  53 % more WAL. Watch `beacon_ingest_queue_depth` for the first hours; see
  [Ingest cost](operations.md#ingest-cost).
- **Alerts.** Load the read-model `Untrusted` rules, `BeaconAdvertsNotReady` and the sequence
  rules from
  [Example alert rules](operations.md#example-alert-rules).
- **Route maintenance.** The first route retention run after the upgrade is a full pass; on a
  large deployment it takes 12 to 14 minutes in short statements. See
  [After upgrading: route maintenance](operations.md#after-upgrading-route-maintenance).
- **Optional, large deployments, once, off-peak:**
  [compact `observers` and `channels`](operations.md#after-upgrading-compacting-observers-and-channels)
  and [rebuild the route keyset indexes](operations.md#rebuilding-the-route-keyset-indexes).
- **Stats pages.** Top nodes, top advertisers and paths for a region get faster as hours rolled
  before the upgrade leave the window: fully within 7 days for the default view. See
  [After upgrading: stats rollup row order](operations.md#after-upgrading-stats-rollup-row-order)
  for an optional one-off `CLUSTER` that heals it at once.
- **Plan checks.** Turn on the [daily plan check](operations.md#turning-on-the-daily-check) only
  after the upgrade, if you want it.

### Rolling back from 2.1

Lighter steps first, without changing images:

- Region or scope pages misbehave: set `readmodels.cmi.enabled: false` or
  `readmodels.packet_sites.enabled: false` and restart. Those pages answer `503` until it is
  `true` again; see [Configuration](configuration.md#read-models).
- Pool or plan trouble: `database.api_plan_layout: single` and restart; see
  [Rolling back the pool layout](operations.md#rolling-back-the-pool-layout).

To go back to 2.0.7, two objects it needs must come back first, because migrations `046` and
`053` removed them:

```sql
ALTER TABLE known_routes ADD COLUMN last_reconfirmed_at timestamp with time zone DEFAULT now() NOT NULL;
CREATE INDEX CONCURRENTLY idx_observations_observer_id ON packet_observations USING btree (observer_id, id);
SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid = 'idx_observations_observer_id'::regclass;
```

The `ALTER` is a catalog change (milliseconds, brief lock on `known_routes`). Run the `CREATE` on
its own in autocommit mode; on a large deployment it takes about a minute or two, and the
`SELECT` must print `t`. Then deploy the 2.0.7 server and a matching 2.0 web build. The other
dropped indexes are optional; their statements are in
[Lookup-table indexes and the route stamp column](operations.md#lookup-table-indexes-and-the-route-stamp-column).
Upgrading again later needs nothing by hand: the server repairs both read models at startup
before any page reads them.

### What changed, by area

Reference for operators who want the detail behind each phase above.

#### Packets: checks, indexes and exact cursors (`025` to `033`)

Exact page cursors (`nextPageCursor` and `pageCursor`) on `/packets`, `/nodes` and `/observers`;
see [Exact page cursors](api-contract.md#exact-page-cursors). Two checks, four indexes and a
statistics object on `packets`. The checks (`026`, `028`) scan `packets` at startup and cannot be
pre-built. Pre-build only the four indexes; don't create the checks or the statistics object
yourself, or startup stops on an object that already exists.

#### Observer adverts index and payload-type backfill (`034`)

A partial index for `/observers/{observerId}/adverts`, read once a background job has filled in
missing observation payload types. Until it reports done, advert pages answer `503`. See
[After upgrading: observation payload types](operations.md#after-upgrading-observation-payload-types),
which also shows how to mark it done by hand. Five stats and traces statements move to the
`api_custom` pool; see
[After upgrading: stats and traces on the custom pool](operations.md#after-upgrading-stats-and-traces-on-the-custom-pool).

#### Channel messages by site (`035` to `041`)

`channel_message_iatas`, the read model behind channel message pages filtered by `iatas` or
`scope`. Its indexes build on an empty table in under a second. See
[Read models: channel messages by site](operations.md#read-models-channel-messages-by-site) for
what to watch, the metrics and alerts, and how read-only servers decide.

#### Packets by site (`042` to `045`)

`packet_sites`, the read model behind `/packets` filtered by `iatas`, `iata`, `region` or
`regionId`. Those pages gain `nextPageCursor`. Migration `042` takes a brief lock on `packets`.
See [Read models: packets by site](operations.md#read-models-packets-by-site).

#### Pools, dropped indexes and a dropped column (`046` to `053`)

- `api_legacy` opens only under the `single` layout. The 2.1 development builds also had an
  `api_slow` pool and a `database.slow_pool_size` key; both are gone (see below).
- `046` drops `idx_observations_observer_id`, `047` to `052` drop six cold lookup-table indexes,
  and `053` drops `known_routes.last_reconfirmed_at`. Every 2.0.x image reads or writes that
  column, hence the rollback steps above.

#### Deep region and message pages (`054` to `057`)

Region `/packets` pages with a `since`/`until` window or scopes seek from the window instead of
reading each site from its newest row, and `/messages` with `iatas` and `since` or `scope` read
`channel_message_iatas`; no page reads a whole site history in one statement any more. Two
partial indexes on `packet_sites` (`054`, `055`), one on `channel_message_iatas` (`056`) and one
on `channel_messages` (`057`), all small. Pages are full until the last; rows, order and cursors
are unchanged. On production the busiest region with `until` 24 hours back took 48-51 s before;
on a production-size copy it went from 131,591 buffers to 2,442. See
[Deep region and message pages](operations.md#deep-region-and-message-pages).

The 2.1 development builds ran those pages on a two-connection `api_slow` pool. It is gone, and
so is `beacon_api_unavailable_total{reason="slow_pool_busy"}` (and the `BeaconSlowPoolBusy`
alert in the examples). A `database.slow_pool_size` left in `config.yaml` is ignored, with a
`WARN` at startup; remove it. The default connection total drops from 20 to 18 (22 under
`split`).

#### Read-model pages without fallback

Region `/packets` pages, channel message pages filtered by `iatas` (or by `scope` without
`since`), and observer advert pages are served only from their read model or backfilled data.
While that is not ready they answer `503` with `Retry-After: 30`; there is no fallback to the
previous statements. The kill switches above turn those pages off instead of serving them from
the previous statements. To get the fallbacks back, revert their two server commits; see
[Reverting to the read-model fallbacks](operations.md#reverting-to-the-read-model-fallbacks).

#### Statement timeouts answer 503

Every `/api/v1` read whose statement runs past its pool's limit (35 s)
now answers `503` `deadline_exceeded` with `Retry-After: 10` instead of a `500`. The heavy
stats endpoints and route searches already answered `503` when their own time limit ran out;
that `503` now carries `Retry-After: 10` and code `deadline_exceeded` (was
`service_unavailable`), and also covers a statement timeout. Web and app retry it like the other
`503`s. In the server log a timeout is one `request complete` line at `WARN` with `status=503`
instead of an `ERROR` pair; a real `500` still logs `api: error 500: <message>` at `ERROR`, now
with the database error in `error`. Only pages that read a read model count timeouts in
`beacon_api_unavailable_total{reason="timeout"}`.

#### Runtime image on Alpine 3.24

The server image moved from Alpine 3.19, which is out of support, to Alpine 3.24 with the
PostgreSQL 16 client tools. Nothing to change for a PostgreSQL 16 database. A self-built image
with `POSTGRES_CLIENT_MAJOR=17` or `18` now works too; see
[Backup export](backup-export.md).

#### Channel message backfill after startup

The retry of stored, undecrypted channel messages against the configured keys no longer
delays startup: it runs in the background once the server listens. On a slow disk that was
most of the boot time (reading every undecrypted packet), so MQTT ingest and the API start
sooner. Its log lines changed: `config: backfilled N previously-undecrypted channel
message(s)` is now `channel message backfill started` (with `packets`) and `channel message
backfill done: N previously-undecrypted channel message(s)`, logged on every run. Keys that a
MeshMapper import adds queue on the same job. A message a live hearing decrypts first, before
the backfill reaches its packet, is stored once and its earlier hours are re-rolled, as the
backfill does.

## Changes that need a restart

Beacon reads `config.yaml` once at startup. After editing it, run
`docker compose restart app`. On the next start:

- A newly added channel key decrypts the matching stored messages, in the background once
  the server listens. Look for
  `channel message backfill done: N previously-undecrypted channel message(s)` in the log.
- Border file and MeshMapper import changes take effect.
- Changed admin or MeshMapper keys in the YAML file are picked up.

For environment changes in `.env`, use `docker compose up -d --force-recreate app` instead.
A container restart reuses its old environment.

The one runtime-only setting is CORS origins: `PUT /api/v1/admin/config` changes them without a
restart, and nothing is written to the file, so a restart reloads whatever the file says.
