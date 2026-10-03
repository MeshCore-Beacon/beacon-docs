# MeshCore Beacon

Beacon watches a MeshCore mesh from above. It listens to the MQTT brokers that observers publish
into, decodes every LoRa packet it hears, stores it, and shows the network live: packets,
channels, nodes, observers, routes, traces and stats, on a map and in lists.

This repo is where you deploy and operate it. The code lives in
[beacon-server](https://github.com/MeshCore-Beacon/beacon-server) (the API and ingest) and
[beacon-web](https://github.com/MeshCore-Beacon/beacon-web) (the frontend).

> **Coming from 1.x?** 2.0.0 needs a fresh database and a few config changes. Read
> [Upgrading](docs/upgrading.md) before you pull new images.

The [experimental roadmap](docs/post-140-roadmap.md) and [integration guide](docs/post-20-integration.md) track My Atlas, Topology and the separate Collector service. These changes remain on `n30nex-test`; production acceptance and stable releases remain separate.

## Deploy the all-in-one stack

One server runs everything: the API, Postgres, Redis, the web frontend and Caddy with automatic
HTTPS. You need a domain pointed at the server, ports 80 and 443 open, Docker with the compose
plugin, and a subscriber account on a MeshCore MQTT broker
([where packets come from](docs/getting-packets-in.md)).

If you would rather run the API and the web frontend on different hosts, see
[Split deployment](#split-deployment).

### 1. Get the files onto your server

Clone the repo; you only need the deployment folder, but cloning is the simplest way to get it.

```bash
git clone https://github.com/MeshCore-Beacon/beacon-docs.git
cd beacon-docs/docker-deployment-type1
```

The folder is self-contained:

```text
docker-deployment-type1/
├── docker-compose.yml          # the stack (pins the network to 172.30.0.0/24)
├── .env                        # your secrets (you create this in step 2)
└── data/                       # persistent state, bind-mounted into the containers
    ├── app/config.yaml         # Beacon config: regions, channels, retention, proxy trust
    ├── Caddy/CaddyFile/Caddyfile.proxy
    ├── Caddy/conf.d/blocklist.caddy   # manual IP and User-Agent block list
    ├── Caddy/logs/             # JSON access log (read by fail2ban, created on first run)
    ├── postgres/               # Postgres database files (created on first run)
    └── redis/                  # Redis data (created on first run)
```

`data/postgres/` and `data/redis/` are bind mounts, so your database and cache survive
`docker compose down` and restarts. Do not delete `data/postgres/` unless you mean to wipe all
data. A `data/postgres/` left over from Beacon 1.x must be moved away first; 2.0.0 will not
start on a 1.x database (see [Upgrading](docs/upgrading.md)).

### 2. Create and fill in your `.env`

```bash
cp ../app_config/.env.example .env
nano .env
```

Set every `CHANGE_*` value. The ones you cannot skip:

| Variable | What to set |
|---|---|
| `BEACON_SERVER_IMAGE` / `BEACON_WEB_IMAGE` | Reviewed tags or immutable digests. Keep server/web major and minor versions aligned; patches may differ. |
| `POSTGRES_DSN` | The database connection string. Change `CHANGE_DB_PASS` to a strong password. **The same password must go in `POSTGRES_PASSWORD` in `docker-compose.yml`.** |
| `MQTT_BROKER_1_URL`, `_USERNAME`, `_PASSWORD` | Your MeshCore MQTT broker and the subscriber account on it. The template also lists a second broker; if you have only one, clear `MQTT_BROKER_2_URL` (an empty URL disables that worker). |
| `DOMAIN` | Your public hostname, for example `beacon.example.com`. Caddy requests a Let's Encrypt certificate for it. |
| `VITE_API_BASE` | `https://<your-domain>/api/v1`. The browser calls this, so it must be the public domain, never `localhost`. |
| `VITE_WS_URL` | `wss://<your-domain>/ws` |

Everything else in the file is optional and explained in
[Configuration](docs/configuration.md): the admin API key, log settings, Redis, and the
web app's map view, tabs, themes, name and banner.

### 3. Describe your network in `config.yaml`

```bash
nano data/app/config.yaml
```

- `iatas`: the airport codes your observers report under, with a name and coordinates.
- `regions`: groups of IATAs that become the region picker in the web app.
- `channel_keys`: hashtag channels and explicit keys to decrypt. Without them, channel messages
  are stored as hashes only.
- `scopes`: transport scopes, if your mesh uses them. Each one needs a `region`.
- `packets`, `telemetry`, `analytics`, `routes`: how long things are kept. Packets default to
  7 days.
- `ingest.allow_countries` is set to `[CA]`, so packets from observers outside Canada are
  dropped. Change it to your country, or delete the `ingest` block to accept everything.
- `server.trusted_proxies` is already set to the compose subnet so Beacon sees real visitor
  addresses through Caddy. Change it only if you change the subnet in `docker-compose.yml`.

Every other key, with its default, is documented in
[`app_config/config.yaml.example`](app_config/config.yaml.example); the
[Configuration](docs/configuration.md#configyaml) page is the map of what each block does.

### 4. Point DNS at the server

Create an `A` or `AAAA` record for `DOMAIN` pointing at the server's public IP. Caddy needs
ports 80 and 443 reachable from the internet to get its certificate.

### 5. Bring it up

```bash
docker compose up -d
docker compose ps
docker compose logs -f app
```

Within a minute `app` should log a `connected` line for each broker. Packets themselves are
not logged at the default level; open `https://<your-domain>` and watch the Packets tab, or
check `https://<your-domain>/api/v1/observers` fills in. If something is off, [Troubleshooting](docs/troubleshooting.md)
lists the usual suspects.

To change a `VITE_*` value later, edit `.env` and run `docker compose up -d web`. The web
container writes those values to `/config.js` on every start, so visitors get them on their
next page load.

## Split deployment

API, database and ingest on one host, the web frontend on another:
[docker-deployment-type2](docker-deployment-type2/README.md).

## Container images

The `app` and `web` services pull public images from GitHub Container Registry
(`ghcr.io/meshcore-beacon/beacon-server` and `ghcr.io/meshcore-beacon/beacon-web`). No
`docker login` is needed.

The compose files use `latest`, which follows stable releases. To decide for yourself when to
upgrade, pin both images to the same release line (`:2.0`) or an exact release (`:2.0.0`); server
and web share `major.minor`. Tags, versioning and the release process are in
[Releases and versioning](docs/releases.md). A `403 Forbidden` on pull means the package has
gone private; see [Troubleshooting](docs/troubleshooting.md#docker-compose-up-fails-with-403-forbidden-pulling-an-image).

## Documentation

**Run it**

- [Getting packets in](docs/getting-packets-in.md): brokers, the account Beacon needs, topics.
- [Configuration](docs/configuration.md): every environment variable and a map of `config.yaml`.
- [Reverse proxy](docs/reverse-proxy.md): Caddy, nginx, Apache, rate limits, split origins.
- [Securing a deployment](docs/security.md): the admin key, the listener, origins, bans.
- [Day-to-day operations](docs/operations.md): health, logs, retention, backup and restore.
- [Upgrading](docs/upgrading.md): 2.0.0 from 1.x, and routine upgrades.
- [Troubleshooting](docs/troubleshooting.md): symptom, cause, fix.
- [Releases and versioning](docs/releases.md): image tags and how releases are cut.

**Understand it**

- [High level design](docs/high-level-design.md): how it works, the schema, the ingest pipeline.
- [API contract](docs/api-contract.md): REST, WebSocket, admin endpoints, errors.
- [Backup and export](docs/backup-export.md) and [CPU profiling](docs/profiling.md).

**Change it**

- [Contributing](CONTRIBUTING.md): the workflow for all three repos and running the full stack
  locally.
- beacon-server: [historical stats](https://github.com/MeshCore-Beacon/beacon-server/blob/main/docs/historical-stats.md),
  how the hourly rollups work.
- beacon-web: [translations](https://github.com/MeshCore-Beacon/beacon-web/blob/main/docs/translations.md),
  adding a language.

Deployment folders are `docker-deployment-type1/` and `docker-deployment-type2/`; templates
and proxy configs (`.env`, `config.yaml`, Caddy, nginx, Apache, fail2ban) are in `app_config/`;
brand assets are in `logos/`.

## Source repositories

- **beacon-server** (API and ingest): [github.com/MeshCore-Beacon/beacon-server](https://github.com/MeshCore-Beacon/beacon-server), image `ghcr.io/meshcore-beacon/beacon-server`
- **beacon-web** (frontend): [github.com/MeshCore-Beacon/beacon-web](https://github.com/MeshCore-Beacon/beacon-web), image `ghcr.io/meshcore-beacon/beacon-web`

## Maintainers: publishing images

Container images are published automatically by each repo's `docker-publish.yml` workflow on
pushes to `main` and `dev` and on `v*` tags. GHCR packages are private by default, which makes
anonymous `docker pull` fail with `403 Forbidden`. To make a package publicly pullable, once per
package:

1. GitHub, the **MeshCore-Beacon** org, **Packages**, select `beacon-server`.
2. **Package settings**, **Danger Zone**, **Change visibility**, **Public**.
3. Repeat for `beacon-web`.

Once a package is public, every future push keeps it public. `GITHUB_TOKEN` cannot change
package visibility, so this step cannot be automated in the workflow.

## Contributing

Contributions are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) has the workflow and the
[Code of Conduct](CODE_OF_CONDUCT.md) applies. Issues are disabled on this repo; to discuss a
change first, reach out on the [MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf).
Security reports go through [SECURITY.md](SECURITY.md), not public channels.

## License

Beacon is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0), the
same license as [beacon-server](https://github.com/MeshCore-Beacon/beacon-server) and
[beacon-web](https://github.com/MeshCore-Beacon/beacon-web).
