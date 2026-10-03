# Troubleshooting

Each heading is a symptom. Under it: the usual cause, then the fix.

## `docker compose up` fails with `403 Forbidden` pulling an image

The error looks like `... manifests/<tag>: 403 Forbidden`. The GHCR package has been switched,
or defaulted, to private. A maintainer has to set it back to public; the steps are under
[Maintainers: publishing images](../README.md#maintainers-publishing-images). Nothing on your
side fixes it.

## Everyone is getting 429

Beacon rate limits per client IP, and behind a proxy every visitor arrives from the proxy's
address unless Beacon is told otherwise. Two things have to be true:

1. `server.trusted_proxies` in `config.yaml` lists the proxy's address as a CIDR: `/32` for one
   IPv4 host, `/128` for one IPv6 host, `172.30.0.0/24` for the all-in-one compose network. A
   bare address stops startup with `server.trusted_proxies[0] must be a valid CIDR`.
2. The proxy overwrites `X-Real-IP` with the connecting client's address. The shipped Caddy,
   nginx and Apache configs do; see [Reverse proxy](reverse-proxy.md).

Beacon logs a warning at startup when limits are on and no proxy is trusted. The same mistake
makes the WebSocket connection cap (5 per IP) hit for everyone at once.

## The page loads but nothing is live

The browser could not open the WebSocket. Open the browser's developer tools, Network tab,
filter `WS`, and look at the `/ws` request. Causes, most common first:

- The proxy is not passing the upgrade, or sends the upstream address as `Host`. nginx needs
  `proxy_http_version 1.1`, the `Upgrade` and `Connection` headers, and
  `proxy_set_header Host $host`.
- The web app is served from a different host than the API and that origin is not in
  `websocket.allowed_origins`.
- The per-IP connection cap is being hit because every visitor looks like the proxy. See the
  429 item above.
- `VITE_WS_URL` points at the wrong place. It must be the public `wss://` address, not
  `localhost`.

## Caddy never gets a certificate

`docker compose logs caddy` shows ACME errors. Either DNS for `DOMAIN` is not pointing at this
server yet, or ports 80 and 443 are not reachable from the internet. Fix that and Caddy
retries on its own.

## Startup fails with `database schema predates Beacon 2.0.0`

The database was created by Beacon 1.x. 2.0.0 cannot migrate it. Move the old data directory
aside and start with an empty one; see
[Upgrading](upgrading.md#upgrading-to-200-from-1x).

## Startup fails on a config value

Beacon refuses to run with a setting it cannot honour. The message names the key:

| Message | Fix |
|---|---|
| `scope "x" needs a region` | Add `region: <slug>` to that `scopes:` entry. |
| `scope "x" region "y" is not a configured region` | Use a slug that appears under `regions:`. |
| `server.trusted_proxies[0] must be a valid CIDR` | Write `10.0.0.5/32`, not `10.0.0.5`. |
| `packets.retention must be at least 24h` | Raise it. Same for `analytics.rollup_retention`. |
| `meshmapper.scopes.refresh_interval must be between 1h and 24h` | Set it inside that range. Zones and channels intervals are 24h to 168h. |
| `nodes.mark_foreign requires an iatas.*.borderFile or meshmapper.zones` | Add a border source or turn `mark_foreign` off. |
| `not a well-formed GeoJSON Feature`, `ring 0 is not closed`, `geometry must be Polygon or MultiPolygon` | The border file is invalid. It must be a single GeoJSON Feature with a closed Polygon or MultiPolygon in longitude, latitude order. |
| `log level must be debug, info, warn or error` | Check `log.level` and `LOG_LEVEL`. `log format must be text or json` is the same for format. |
| `auth.api_key / BEACON_API_KEY must be at least 16 characters` | Use a longer key, with no whitespace inside it. |

## No packets are arriving

Check `GET /api/v1/brokers` first.

- **A broker shows disconnected.** `MQTT_BROKER_1_URL` must be the WebSocket endpoint,
  usually `wss://host:443`, and the username and password must be a subscriber account on that
  broker. `docker compose logs app` shows the connect error. See
  [Getting packets in](getting-packets-in.md).
- **Connected but nothing stored.** No observers are publishing to that broker, or
  `ingest.allow_countries` / `allow_continents` in `config.yaml` is filtering them out.
  `GET /api/v1/observers` shows who Beacon has heard from.
- **Packets arrive but with no signal data.** The account is Role 3, which strips `snr` and
  `rssi`. Ask for a Role 2 account.

## Every path hop says `"confidence": "none"`

Path resolution needs to know which nodes exist, and Beacon learns that from adverts. On a
fresh database every hop is `none` and `supportsMultibytePaths` is `false` until nodes have
advertised. This fills in on its own as the mesh is observed.

## Channel messages show a hash but no text

The channel's key is not configured, or it was added without a restart. Add it under
`channel_keys:` in `config.yaml` and run `docker compose restart app`. On start, Beacon decrypts
the stored messages for the new key and logs
`config: backfilled N previously-undecrypted channel message(s)`.

## I changed a `VITE_*` value and nothing changed

Run `docker compose up -d web`. The web container writes the values to `/config.js` when it
starts, so an edited `.env` does nothing until the container is recreated. Then hard-refresh
the page.
