# beacon-docs

Documentation, architecture, and **ready-to-run Docker deployments** for MeshCore Beacon.

This repo is the single place to:

1. **Grab a deployment** — copy the Docker Compose folder for the topology you want, fill in your variables, and `docker compose up -d`.
2. **Read the docs** — project-wide design and API documentation that describe how the whole system works.

> **Upgrading from 1.x?** Beacon 2.0.0 needs a fresh database and a few config changes. Read
> [Upgrading to 2.0.0](#upgrading-to-200) before pulling new images.

---

## Deploy Beacon

Two deployment topologies are provided. Pick one, copy its folder to your server, set your variables, and bring it up.

| Type | Folder | What it is | Status |
|---|---|---|---|
| **Type 1 — All-in-One** | [`docker-deployment-type1/`](docker-deployment-type1/) | Full stack on a single server: API (`app`), Postgres (`db`), Redis (`redis`), web frontend (`web`), and Caddy reverse proxy with automatic TLS. | ✅ Ready |
| **Type 2 — Split Server + Web** | [`docker-deployment-type2/`](docker-deployment-type2/) | API backend on one server, web frontend on a dedicated server. | 🚧 Not done yet (WIP) |

### Step-by-step (Type 1)

**1. Get the files onto your server**

Clone the repo (you only need the deployment folder, but cloning is the simplest way to grab it):

```bash
git clone https://github.com/MeshCore-Beacon/beacon-docs.git
cd beacon-docs/docker-deployment-type1
```

The folder is self-contained:

```text
docker-deployment-type1/
├── docker-compose.yml          # the stack (pins the network to 172.30.0.0/24)
├── .env                        # your secrets (you create this — see step 2)
└── data/                       # persistent state, bind-mounted into the containers
    ├── app/config.yaml         # Beacon app config (regions, channels, retention, proxy trust)
    ├── Caddy/CaddyFile/Caddyfile.proxy
    ├── Caddy/conf.d/blocklist.caddy   # manual IP / User-Agent block list
    ├── Caddy/logs/             # JSON access log (read by fail2ban, created on first run)
    ├── postgres/               # ← Postgres database files live here (created on first run)
    └── redis/                  # ← Redis data lives here (created on first run)
```

> **`data/postgres/` and `data/redis/` are empty in git on purpose.** They're bind-mount targets: the `db` and `redis` containers write their data into them, so your database and cache **survive `docker compose down` and restarts**. Don't delete them unless you intend to wipe all data — `rm -rf data/postgres` resets the database. They populate automatically the first time you run `docker compose up -d`.
>
> A `data/postgres/` left over from Beacon 1.x must be moved away first: 2.0.0 won't start on a 1.x database. See [Upgrading to 2.0.0](#upgrading-to-200).

**2. Create and fill in your `.env`**

Copy the template from [`app_config/.env.example`](app_config/.env.example) and edit it:

```bash
cp ../app_config/.env.example .env
nano .env
```

Set every `CHANGE_*` value. The variables you must fill in:

| Variable | Service | What to set |
|---|---|---|
| `POSTGRES_DSN` | `app` | Database connection string. Change the password (`CHANGE_DB_PASS`) to a strong one. |
| `REDIS_ADDR` | `app` | `redis:6379` — points the API at the compose Redis service. Leave it out and the server runs uncached, so every read hits Postgres. |
| `BEACON_API_KEY` | `app` | *(Optional)* Bearer key for the `/api/v1/admin/*` endpoints, at least 16 characters (e.g. `openssl rand -hex 32`). Without one, admin routes return `503`; public reads and the live feed are unaffected. |
| `LOG_LEVEL` / `LOG_FORMAT` | `app` | *(Optional)* `debug`/`info`/`warn`/`error` and `text`/`json`. Default `info` / `text`. |
| `MQTT_BROKER_1_*` / `MQTT_BROKER_2_*` | `app` | URL, username, and password for your live MeshCore MQTT packet sources. |
| `DOMAIN` | `caddy` | Your public domain (e.g. `beacon.example.com`). Caddy auto-provisions a Let's Encrypt cert for it. |
| `VITE_API_BASE` | `web` | `https://<your-domain>/api/v1` — must be the **public** domain, never localhost. |
| `VITE_WS_URL` | `web` | `wss://<your-domain>/ws` |
| `VITE_MAP_CENTER` / `VITE_MAP_ZOOM` | `web` | *(Optional)* Fallback "All" map view. The app auto-fits the map to all IATA locations from `config.yaml`; these values are only used as a fallback when those IATAs have no location set. Omit for a world view. |

> ⚠️ **Password must match in two places.** The password inside `POSTGRES_DSN` (in `.env`) must equal `POSTGRES_PASSWORD` in `docker-compose.yml`. Update both before bringing the stack up.

**3. Fill in the app config**

Edit [`data/app/config.yaml`](docker-deployment-type1/data/app/config.yaml) to define your network:

```bash
nano data/app/config.yaml
```

- **`iatas`** — the airport-code anchor points for your coverage area (name + lat/lng).
- **`regions`** — map regions that group IATAs together.
- **`channel_keys`** — hashtag channels and/or explicit channel keys to decrypt.
- **`scopes`** — transport scopes. Each manual scope needs a `region` that is one of the slugs under `regions`.
- **`telemetry`**, **`packets`**, **`analytics`**, **`routes`** — retention windows (packets default to 7 days).
- **`ingest`** — optional geographic ingest filter.
- **`server.trusted_proxies`** — already set to the compose subnet so Beacon sees real client IPs through Caddy. Change it only if you change the subnet in `docker-compose.yml`.

[`app_config/config.yaml.example`](app_config/config.yaml.example) documents every other key (rate limits, WebSocket limits, MeshMapper imports, CORS, cache, background intervals).

**4. Point DNS at the server**

Create an `A`/`AAAA` record for your `DOMAIN` pointing at the server's public IP. Caddy needs ports **80** and **443** reachable to issue the TLS certificate.

**5. Bring it up**

```bash
docker compose up -d
```

Check it's healthy:

```bash
docker compose ps
docker compose logs -f
```

Visit `https://<your-domain>` and you're off to the races. 🚀

> After changing any `VITE_*` value later, recreate the web container so the new values get baked into the JS bundle:
> ```bash
> docker compose up -d --force-recreate web
> ```
> (then hard-refresh / use incognito, since `/assets/*` is cached immutable.)

### Container images

The `app` and `web` services pull public images from GitHub Container Registry
(`ghcr.io/meshcore-beacon/beacon-server` and `…/beacon-web`) — **no `docker login`
is required**.

Tags: `latest` follows stable releases on `main`, `dev` follows the development branch, and each
release is also published as `X.Y.Z` and `X.Y`. The compose file uses `latest`; to control when
upgrades happen, pin both images to a release line, e.g. `beacon-server:2.0` and `beacon-web:2.0`
(server and web share major.minor versions).

> **Troubleshooting — `403 Forbidden` on pull.** If `docker compose up` fails with a
> `... manifests/<tag>: 403 Forbidden` error, the package has been set (or defaulted)
> to **Private** on GHCR. A maintainer must set it back to Public — see
> [Maintainers: publishing images](#maintainers-publishing-images).

### Type 2 — Split Server + Web

🚧 **Not done yet.** [`docker-deployment-type2/`](docker-deployment-type2/) is a placeholder; instructions and compose files will land here.

### Reverse proxy

However you front Beacon, the proxy has the same three jobs:

- Send `/api/*` and `/ws` to beacon-server (port `8080`) and everything else to beacon-web. `/ws` is a
  WebSocket, so the proxy must pass the upgrade through and keep idle sockets open for more than 90 s
  (the browser pings every 30 s; the server drops a socket after 90 s of silence).
- Overwrite `X-Real-IP` with the connecting client's address and pass the original `Host` header.
  beacon-server ignores `X-Forwarded-For` and `True-Client-IP` entirely.
- Be listed in beacon-server's `server.trusted_proxies` (CIDR: `/32` for one IPv4 host, `/128` for
  IPv6). Only those peers may set `X-Real-IP`. Get this wrong and every visitor shares the proxy's
  rate limit and WebSocket connection cap.

`VITE_API_BASE` and `VITE_WS_URL` then point at the public paths, e.g.
`https://beacon.example.com/api/v1` and `wss://beacon.example.com/ws`.

**Caddy** (the type 1 default): [`Caddyfile.proxy`](docker-deployment-type1/data/Caddy/CaddyFile/Caddyfile.proxy).
The relevant part:

```caddy
handle /api/* {
	reverse_proxy app:8080 {
		header_up X-Real-IP {remote_host}
	}
}
handle /ws {
	reverse_proxy app:8080 {
		header_up X-Real-IP {remote_host}
	}
}
handle {
	reverse_proxy web:80
}
```

Caddy handles the WebSocket upgrade and keeps the `Host` header by itself. It reaches the app over
the compose network, so `data/app/config.yaml` trusts that subnet:

```yaml
server:
  trusted_proxies: [172.30.0.0/24]
```

Behind Cloudflare or another CDN, `{remote_host}` is the CDN. The comment at the top of
`Caddyfile.proxy` shows how to trust the CDN's ranges and forward `{client_ip}` instead.

**nginx** on the host: [`app_config/nginx/beacon.conf`](app_config/nginx/beacon.conf) is a complete
server block. The essentials:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
location = /ws {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;   # map is in the example file
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 120s;
}
location / {
    proxy_pass http://127.0.0.1:8081;   # beacon-web published on loopback
}
```

nginx sends the upstream address as `Host` by default, which fails the WebSocket origin check, so
keep `proxy_set_header Host $host`. When nginx reaches the containers through published ports, the
app sees the Docker network's gateway as the peer, so trust the compose subnet (`[172.30.0.0/24]`).
For a beacon-server running directly on the host, use `["127.0.0.1/32", "::1/128"]`.

Apache works the same way: see [`app_config/apache/analyzer-vhost.snippet.conf`](app_config/apache/analyzer-vhost.snippet.conf).
Abuse controls (access log, block list, fail2ban) are in [`app_config/fail2ban/`](app_config/fail2ban/README.md).

**Split origins** (web and API on different hosts): add the web origin to
`websocket.allowed_origins`, or browsers can't open `/ws`. REST CORS allows any origin by default.

---

## Upgrading to 2.0.0

**2.0.0 needs a fresh database.** It starts from a new schema baseline; pointed at a 1.x database it
refuses to start with `database schema predates Beacon 2.0.0; 2.0.0 needs a fresh database`. 1.x
history does not carry over. For the type 1 stack:

```bash
docker compose down
mv data/postgres data/postgres-1.x   # or rm -rf data/postgres once you no longer need it
docker compose pull
docker compose up -d
```

`docker compose down` also lets the network come back with the new fixed subnet. If `172.30.0.0/24`
is already used on your host, pick another in `docker-compose.yml` and change
`server.trusted_proxies` to match.

Config that **fails startup** if left as it was:

- Every manual `scopes:` entry needs `region:` set to one of your `regions:` slugs.
- MeshMapper refresh intervals must be within bounds: `meshmapper.scopes.refresh_interval` 1h–24h,
  `meshmapper.zones.refresh_interval` and `meshmapper.channels.refresh_interval` 24h–168h.
- `packets.retention` and `analytics.rollup_retention` must be at least `24h`.
- `server.trusted_proxies` entries must be CIDRs (`10.0.0.5/32`, not `10.0.0.5`).

Other changes to review:

- `meshmapper.scopes.sources` is ignored (with a warning). Scope catalogues are now found through
  MeshMapper's zone list for every known IATA.
- **REST rate limiting is on by default:** 300 requests per minute per client IP on `/api/v1/*`
  (IPv6 clients share a /64), answered with `429` and `Retry-After`. Behind a proxy, set
  `server.trusted_proxies` and have the proxy send `X-Real-IP` (see [Reverse proxy](#reverse-proxy));
  `X-Forwarded-For` and `True-Client-IP` are not trusted. Tune or turn it off under `ratelimit:`.
- **WebSocket upgrades are rate limited** to `websocket.max_connects_per_minute` (default 10) per
  client IP, on top of `max_connections_per_ip` (default 5). Only the page's own host may open `/ws`
  unless you list other origins in `websocket.allowed_origins`, e.g. when the web app is served from
  a different host than the API.
- `packets.retention` now defaults to **7 days** and also covers observations and channel messages.
  Historical stats come from hourly rollups kept for `analytics.rollup_retention` (90 days).
- Admin endpoints under `/api/v1/admin/` need `BEACON_API_KEY` (or `auth.api_key`).
- Image tags: `latest` is the newest stable release from `main`. Pin `:2.0` on both images if you
  want to choose when to move to the next minor release.

[`app_config/config.yaml.example`](app_config/config.yaml.example) is the full 2.0.0 reference.

---

## Project documentation

Project-wide docs that describe the entire system live in [`app_documentation/`](app_documentation/):

- [**High Level Design**](app_documentation/high_level_design.md) — single source of truth. System overview, database schema, ingestion pipeline, and future features.
- [**API Contract**](app_documentation/api_contract.md) — REST endpoints, auth and rate limits, WebSocket protocol, backpressure/reconnection, and mobile-specific concerns.

## Source repositories

- **Beacon Server (API):** [github.com/MeshCore-Beacon/beacon-server](https://github.com/MeshCore-Beacon/beacon-server) — image `ghcr.io/meshcore-beacon/beacon-server`
- **Beacon Web (Frontend):** [github.com/MeshCore-Beacon/beacon-web](https://github.com/MeshCore-Beacon/beacon-web) — image `ghcr.io/meshcore-beacon/beacon-web`

## Maintainers: publishing images

Container images are published automatically by each repo's `docker-publish.yml`
workflow on pushes to `main`/`dev` and on `v*` tags. **GHCR packages are Private by
default**, which makes anonymous `docker pull` fail with `403 Forbidden`. To make a
package publicly pullable (one-time, per package):

1. GitHub → the **MeshCore-Beacon** org → **Packages** → select `beacon-server`.
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**.
3. Repeat for `beacon-web`.

Once a package is Public, every future CI push to it stays Public. `GITHUB_TOKEN`
cannot change package visibility, so this step can't be automated in the workflow.

## Repo structure

- `/docker-deployment-type1` — Single-server (all-in-one) Docker Compose deployment ✅
- `/docker-deployment-type2` — Split server/web Docker Compose deployment 🚧 WIP
- `/app_config` — Example `.env`, `config.yaml`, Caddy/nginx/Apache proxy configs, and fail2ban rules
- `/app_documentation` — Project-wide design & API docs
- `/logos` — Brand assets

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the
workflow and the [Code of Conduct](CODE_OF_CONDUCT.md). Issues are disabled on
this repo; to discuss a change first, reach out on the
[MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf). Security reports go
through [SECURITY.md](SECURITY.md), not public channels.

## License

Beacon is licensed under the [GNU Affero General Public License v3.0](LICENSE)
(AGPL-3.0), the same license as [beacon-server](https://github.com/MeshCore-Beacon/beacon-server).
