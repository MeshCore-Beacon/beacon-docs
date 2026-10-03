# Type 2: API on one host, web on another

Use this when the frontend should live on a different server from the database and ingest, or
when more than one web frontend should share one API. If one server is enough, use the
all-in-one stack in the [main README](../README.md#deploy-the-all-in-one-stack) instead.

```text
docker-deployment-type2/
├── server/     API (app), Postgres (db), Redis (redis), Caddy  →  https://api.example.com
└── web/        web frontend, Caddy                             →  https://beacon.example.com
```

## What you need

- Two hosts with Docker and ports 80 and 443 open.
- Two DNS names pointing at them, for example `api.example.com` and `beacon.example.com`.
- A subscriber account on a MeshCore MQTT broker. See
  [Getting packets in](../docs/getting-packets-in.md).

## Server host

1. Copy `server/` to the host.
2. Create `.env` from [`app_config/.env.example`](../app_config/.env.example) and fill in every
   `CHANGE_*` value. Only the `app` and `caddy` lines matter here; the `VITE_*` lines can be
   deleted. From inside `server/` in a clone of this repo:

   ```bash
   cp ../../app_config/.env.example .env
   nano .env
   ```

   Set `DOMAIN` to the API hostname (`api.example.com`) and add one line this stack needs that
   the all-in-one one does not:

   ```
   WEB_DOMAIN=beacon.example.com
   ```

   Caddy redirects anything that is not `/api/*` or `/ws` to that host. The password inside
   `POSTGRES_DSN` must match `POSTGRES_PASSWORD` in `docker-compose.yml`.

3. Edit `data/app/config.yaml` for your network (see
   [Configuration](../docs/configuration.md#configyaml)). Because the web app will be served
   from another origin, browsers may only open the WebSocket if that origin is listed:

   ```yaml
   websocket:
     allowed_origins: [https://beacon.example.com]
   ```

   `server.trusted_proxies` is already set to the compose subnet so Beacon sees real client
   addresses through Caddy.

4. Point DNS for `DOMAIN` at this host and bring it up:

   ```bash
   docker compose up -d
   ```

   `https://api.example.com/api/v1/brokers` should answer with your brokers.

## Web host

1. Copy `web/` to the host.
2. Create `.env` from `web/.env.example` and set:

   | Variable | Value |
   |---|---|
   | `DOMAIN` | the web hostname, `beacon.example.com` |
   | `BEACON_WEB_IMAGE` | `ghcr.io/meshcore-beacon/beacon-web:2.0` or an exact release; keep its `X.Y` equal to the server's |
   | `VITE_API_BASE` | `https://api.example.com/api/v1` |
   | `VITE_WS_URL` | `wss://api.example.com/ws` |

   The optional `VITE_*` values are described in
   [Configuration](../docs/configuration.md#web-environment-variables).

3. Point DNS for `DOMAIN` at this host and bring it up:

   ```bash
   docker compose up -d
   ```

   Open `https://beacon.example.com`. If the page loads but nothing is live, the server host's
   `websocket.allowed_origins` is the first thing to check; see
   [Troubleshooting](../docs/troubleshooting.md#the-page-loads-but-nothing-is-live).

## How the two connect

The browser talks to the API host directly; the web host only serves files. That is why the
API host has to allow the web origin for WebSocket. REST CORS allows any origin by default.
Rate limits and connection caps work the same as in the all-in-one stack because each host's
Caddy sets `X-Real-IP` and is trusted through `server.trusted_proxies`; see
[Reverse proxy](../docs/reverse-proxy.md).

To change a `VITE_*` value later, edit the web host's `.env` and run
`docker compose up -d beacon-web`.
