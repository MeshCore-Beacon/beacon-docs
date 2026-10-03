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

## Changes that need a restart

Beacon reads `config.yaml` once at startup. After editing it, run
`docker compose restart app`. On the next start:

- A newly added channel key decrypts the matching stored messages. Look for
  `config: backfilled N previously-undecrypted channel message(s)` in the log.
- Border file and MeshMapper import changes take effect.
- A changed admin key is picked up.

The one runtime-only setting is CORS origins: `PUT /api/v1/admin/config` changes them without a
restart, and nothing is written to the file, so a restart reloads whatever the file says.
