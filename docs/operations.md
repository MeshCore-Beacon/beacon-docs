# Day-to-day operations

Everything here assumes the all-in-one Docker stack. The commands translate to the split
deployment by running them on the server host.

## Checking it is healthy

Beacon has no health endpoint yet. Use these instead:

- `docker compose ps` shows every container `Up`. `db` and `redis` have health checks; `app`
  waits for both before it starts.
- `curl -s https://<your-domain>/api/v1/brokers` lists each MQTT broker with its connection
  status. A broker that never connects is a URL or credentials problem; see
  [Getting packets in](getting-packets-in.md).
- Open `wss://<your-domain>/ws` in a WebSocket client. The first frame is `hello`.
- `docker compose logs -f app` shows a `connected` line per broker. Individual packets are
  not logged at the default `info` level, so a quiet log after that is normal; use the
  observers endpoint or the web app to see traffic.

## Logs

Logs go to stderr and Docker collects them. Docker's default `json-file` driver does not
rotate, so on a long-running host set a cap, either in `/etc/docker/daemon.json` for every
container or per service in `docker-compose.yml`:

```yaml
    logging:
      driver: json-file
      options: { max-size: "50m", max-file: "5" }
```

Set `log.level` (`debug`, `info`,
`warn`, `error`; default `info`) and `log.format` (`text` or `json`) in `config.yaml`, or
override them with `LOG_LEVEL` and `LOG_FORMAT`. Invalid values stop startup.

Every record has a `component`. Ingest records add the broker name; HTTP completion records
add the validated client address, route, status and duration. Query strings and WebSocket
hello payloads are never logged. Expected ingest skips and routine WebSocket lifecycle events
are at debug level.

```bash
docker compose logs -f app      # the API and ingest
docker compose logs -f caddy    # the proxy
```

Caddy also writes a JSON access log to `data/Caddy/logs/access.json`, which the fail2ban rules
in [`app_config/fail2ban/`](../app_config/fail2ban/README.md) read.

## Where the data lives

Everything persistent is under `data/` next to `docker-compose.yml`:

- `data/postgres/` is the database. Deleting it deletes all history.
- `data/redis/` is the cache. It can be removed while the stack is down; Beacon rebuilds it.
- `data/Caddy/data/` holds TLS certificates. Deleting it means a new certificate request on
  the next start, which counts against Let's Encrypt rate limits.
- `data/app/config.yaml` and `.env` are your configuration. Keep copies of both somewhere
  else; no backup below includes `.env`.

## Retention

Everything below is a duration in `config.yaml`. Shorten them if disk is tight, lengthen them
if you want more history.

| Setting | Default | What it covers |
|---|---|---|
| `packets.retention` | `168h` (7 days) | Packets, observations and channel messages |
| `analytics.rollup_retention` | `2160h` (90 days) | Hourly stats rollups. Also the longest window the stats endpoints accept |
| `telemetry.retention` | `744h` (31 days) | Observer telemetry snapshots |
| `routes.retention` | `336h` (14 days) | Known routes, counted from when a route was last seen |
| `nodes.delete_after` | `720h` (30 days) | Nodes not heard from |
| `observers.delete_after` | off | Observers not heard from. Opt in by setting a duration |

Historical stats read the hourly rollups, not raw packets. Each UTC hour is rolled about 95
minutes after it closes, and packet cleanup holds back up to 24 hours of raw rows until their
hours are rolled, so raw data lives a little longer than `packets.retention` says. An hour
whose raw rows were deleted first is reported as partial, with no values.

## Backing up

Two options.

**A plain `pg_dump`** from the host, which is enough for most operators:

```bash
docker compose exec -T db pg_dump -U beacon -d beacon -Fc > beacon-$(date +%F).dump
```

Keep `data/app/config.yaml` and `.env` with it. The dump holds message data and anything you
have decrypted, so treat it as private.

**The admin backup endpoint** produces an archive of the database and the saved
`config.yaml`, with a manifest and checksums, and a command-line tool that verifies it. It is
off by default and needs the admin key. See [Backup and export](backup-export.md).

## Restoring

Restore into an empty database, never over live data. With the stack running and the app
stopped, drop and recreate the database, load the dump, and only then start the app:

```bash
docker compose stop app
docker compose exec -T db psql -U beacon -d postgres -c 'DROP DATABASE beacon;' -c 'CREATE DATABASE beacon;' \
  && docker compose exec -T db pg_restore -U beacon -d beacon < beacon-YYYY-MM-DD.dump \
  && docker compose start app
```

If `pg_restore` reports errors the app is not started; read them before trying again.

A 1.x dump cannot be restored into 2.0.0; the server refuses the old schema. See
[Upgrading](upgrading.md#upgrading-to-200-from-1x).

## CPU profiling

Bounded CPU captures on a running instance are described in [Profiling](profiling.md).
