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

Server 2.1.0 adds exact page cursors (`nextPageCursor` and `pageCursor`) to `/packets`, `/nodes`
and `/observers`; see [Exact page cursors](api-contract.md#exact-page-cursors). The API change is
additive, but server 2.1 requires Beacon Web 2.1 (`minWebVersion` 2.1.0): older web versions do not
wait out the 503s that region, scope and advert pages answer while a read model is not ready, and
they skip rows tied on a page boundary. Deploy Beacon Web 2.1 together with the server; an open
tab on an older web version shows the reload screen. The minimum app version stays 2.0.0.

Migrations `025` to `033` add two checks, four indexes and a statistics object to `packets`.
Before deploying, run the [pre-deploy check](operations.md#before-deploying-a-release) and the
type check in the same section. A large deployment can pre-build the four indexes off-peak; see
[Pre-building the packets indexes](operations.md#pre-building-the-packets-indexes). Other
deployments can skip that: the server builds them at startup and serves the API once they are
done.

## Observer adverts index and payload-type backfill

The release that adds migration `034` changes no API and keeps the minimum web and app versions.
On a large deployment, pre-build `idx_observations_adverts` off-peak before deploying; see
[Pre-building the observer adverts index](operations.md#pre-building-the-observer-adverts-index).
Other deployments can skip that: the server builds it at startup.

After the deploy, a background job fills in missing observation payload types; on a large
deployment it takes about 80 minutes, or under a minute where every observation already has
its type. Until it reports done, observer adverts pages answer `503` with `Retry-After`. See
[After upgrading: observation payload types](operations.md#after-upgrading-observation-payload-types),
which also shows how to mark it done by hand. Five stats and traces statements move to the
`api_custom` pool; see
[After upgrading: stats and traces on the custom pool](operations.md#after-upgrading-stats-and-traces-on-the-custom-pool).

- Turn on the [daily plan check](operations.md#turning-on-the-daily-check) only after migration
  `034` is recorded.
- Don't upgrade to a release that drops `idx_observations_observer_id` until
  `SELECT value FROM background_state WHERE key = 'observation_payload_type'` shows
  `"done": true`.
- To roll back, deploy the previous image. See the rollback notes in the two operations
  sections above.

## Channel messages by site

The release that adds migrations `035` to `041` changes no API and keeps the minimum web and app
versions. It adds `channel_message_iatas`, a read model that channel message pages filtered by
`iatas` or `scope` read once the server trusts it. Run the
[pre-deploy check](operations.md#before-deploying-a-release) first. No pre-build is needed: the
new indexes build at startup in well under a second.

After the deploy, the server fills the table in the background and verifies it once; on a large
deployment that takes 3 to 5 minutes. Until the log shows
`cmi trusted: region and scope message pages read channel_message_iatas`, channel message pages
filtered by `iatas` (or by `scope` without `since`) answer `503` with `Retry-After`; see
[Pages that wait for a read model](operations.md#pages-that-wait-for-a-read-model). See
[Read models: channel messages by site](operations.md#read-models-channel-messages-by-site) for
what to watch, the metrics and alerts, and how read-only servers decide.

- To turn those pages off without rolling back, set `readmodels.cmi.enabled: false` and
  restart; they answer `503` until it is `true` again. See
  [Configuration](configuration.md#read-models).
- To roll back, deploy the previous image. Rolling forward again later repairs the table at
  startup before any page reads it; nothing to do by hand.
- Run this release for at least a week before upgrading to the release that drops
  `idx_channel_messages_channel` and `idx_channel_messages_sent_brin`.

## Packets by site

The release that adds migrations `042` to `045` adds `packet_sites`, a read model that `/packets`
pages filtered by `iatas`, `iata`, `region` or `regionId` read once the server trusts it. It
keeps the minimum web and app versions. Those pages gain `nextPageCursor`, which current web and
app versions already send back as `pageCursor`; see
[Exact page cursors](api-contract.md#exact-page-cursors). Run the
[pre-deploy check](operations.md#before-deploying-a-release) first: migration `042` takes a brief
lock on `packets`. No pre-build is needed: the new indexes build on an empty table in seconds.

After the deploy, the server fills the table in the background and verifies it once; on a large
deployment expect roughly 5 to 20 minutes and a few GB of WAL, then a few minutes of
`VACUUM (ANALYZE)`. Until the log shows
`packet_sites trusted: region packet pages read packet_sites`, region pages answer `503` with
`Retry-After`; see [Pages that wait for a read model](operations.md#pages-that-wait-for-a-read-model).
See
[Read models: packets by site](operations.md#read-models-packets-by-site) for what to watch, the
metrics and alerts, and how read-only servers decide.

- Each stored observation now costs about 15-21% more insert time and 37-53% more WAL. After
  the deploy, compare `InsertObservation` in `pg_stat_statements` for the hour before and after
  and watch `beacon_ingest_queue_depth`; see
  [Ingest cost](operations.md#ingest-cost). A growing queue or WAL beyond your budget means
  rolling back.
- To turn region pages off without rolling back, set `readmodels.packet_sites.enabled: false`
  and restart; they answer `503` until it is `true` again. See
  [Configuration](configuration.md#read-models).
- To roll back, deploy the previous image. Rolling forward again later repairs the table at
  startup before any region page reads it; nothing to do by hand.

## The slow pool, lookup-table indexes and a dropped column

The release that adds migrations `047` to `053` keeps the minimum web and app versions.

- **Pools.** `api_legacy` opens only under the `single` layout. A new `api_slow` pool (8
  connections by default, `database.slow_pool_size`; 120 s statement limit; ungated) runs the
  statements that may read whole site histories: the region statement for pages whose bounded
  reads run out of budget, `/messages` with `iatas` and `since` or `scope`, and the previous
  statements that serve region and scope pages while a read model is not trusted. The default
  total stays at 26 connections (api_slow's 8 replace api_legacy's 8); set `slow_pool_size` only
  to override that. See
  [Slow region and message statements](operations.md#slow-region-and-message-statements).
- **Alerts.** Load `BeaconSlowPoolBusy` and the two sequence rules from
  [Example alert rules](operations.md#example-alert-rules).
- **Migrations.** `047` to `052` drop six cold lookup-table indexes; `053` drops
  `known_routes.last_reconfirmed_at`. Run the [pre-deploy check](operations.md#before-deploying-a-release)
  first and make sure no `pg_dump` is running.

**Rolling back is a one-way door.** Migration `053` removes a column that every older image
(2.0.7 and every build before this release) reads or writes. Before starting an older image,
put the column back:

```sql
ALTER TABLE known_routes ADD COLUMN last_reconfirmed_at timestamp with time zone DEFAULT now() NOT NULL;
```

It is a catalog change, not a rewrite: 8 ms on a 10.5-million-row copy of a large database,
under a brief `ACCESS EXCLUSIVE` lock on `known_routes`. This covers this release only; the
rollback steps of the earlier releases you are going back past still apply. In particular, once
the drops release (migration `046`) has run, 2.0.7 needs `idx_observations_observer_id` again:
rebuild it with
`CREATE INDEX CONCURRENTLY idx_observations_observer_id ON packet_observations USING btree (observer_id, id);`
and confirm `SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid = 'idx_observations_observer_id'::regclass;`
prints `t` before switching images. The six dropped indexes are optional after a rollback; their rebuild statements are in
[Lookup-table indexes and the route stamp column](operations.md#lookup-table-indexes-and-the-route-stamp-column),
which also covers rolling forward again.

## Read-model pages without fallback

The release that removes the read-model fallbacks follows the one above. It keeps the minimum
web and app versions.

- **Pages that wait.** Region `/packets` pages, channel message pages filtered by `iatas` (or by
  `scope` without `since`), and observer advert pages are served only from their read model or
  backfilled data. While that is not ready they answer `503` with `Retry-After: 30`; there is no
  fallback to the previous statements any more. If the read models fill for the first time in
  the same upgrade, those pages are unavailable for the whole first fill (minutes for channel
  messages, roughly 5 to 20 minutes for region packets on a large deployment). The web and app
  retry for about 90 s and then show an error with a retry, so users retry by hand after that.
  Upgrade at a quiet hour and watch the `... backfill progress` log lines. See
  [Pages that wait for a read model](operations.md#pages-that-wait-for-a-read-model).
- **Kill switches.** `readmodels.cmi.enabled: false` and `readmodels.packet_sites.enabled: false`
  now turn those pages off (`503`) instead of serving them from the previous statements.
- **Pool.** `api_slow` no longer serves untrusted pages, so `slow_pool_size` now defaults to `2`
  and the default total goes from 26 to 20 connections. An explicit `slow_pool_size` still wins.
- **Alerts.** Load the two read-model `Untrusted` rules (15 minutes) and `BeaconAdvertsNotReady`
  from [Example alert rules](operations.md#example-alert-rules).
- **Getting the fallbacks back.** Revert this release's server change (one commit); that also
  restores `slow_pool_size`'s default of 8. See
  [Reverting to the read-model fallbacks](operations.md#reverting-to-the-read-model-fallbacks).

## Changes that need a restart

Beacon reads `config.yaml` once at startup. After editing it, run
`docker compose restart app`. On the next start:

- A newly added channel key decrypts the matching stored messages. Look for
  `config: backfilled N previously-undecrypted channel message(s)` in the log.
- Border file and MeshMapper import changes take effect.
- Changed admin or MeshMapper keys in the YAML file are picked up.

For environment changes in `.env`, use `docker compose up -d --force-recreate app` instead.
A container restart reuses its old environment.

The one runtime-only setting is CORS origins: `PUT /api/v1/admin/config` changes them without a
restart, and nothing is written to the file, so a restart reloads whatever the file says.
