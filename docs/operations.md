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

## Before deploying a release

Migrations run when the server starts, and some need a lock on a busy table. Check two things
in `psql` before you pull a new image:

```bash
docker compose exec db psql -U beacon -d beacon
```

```sql
-- No transaction older than five minutes. This must return no rows.
SELECT pid, now()-xact_start, state, left(query,80) FROM pg_stat_activity WHERE xact_start < now() - interval '5 minutes';

-- No anti-wraparound autovacuum on the tables the release touches.
SELECT pid, now()-xact_start, query FROM pg_stat_activity WHERE query LIKE 'autovacuum:%to prevent wraparound%';
```

A long transaction holds back the locks a migration waits for. An anti-wraparound autovacuum
does not give way to a lock request the way an ordinary autovacuum does, so a migration on
that table waits until the vacuum ends. Let either finish, or end a stuck client session with
`SELECT pg_cancel_backend(<pid>);`, then deploy.

### How startup migrations wait for locks

Each migration statement runs with `lock_timeout = 30s`. When a statement times out on a lock,
the server logs a `migration lock wait timed out` warning listing the sessions that blocked it
(pid, state, `xact_start` and the first 200 characters of the query), waits, and tries the
file again: three attempts in all, 10 s after the first and 20 s after the second. A file
still blocked after about two minutes stops startup with `migrations failed`, the server exits
with status 1, and Docker restarts it (`restart: unless-stopped`), which starts the same check
again. A restart loop with these warnings means a session in the blocker list is holding the
lock; deal with it and the next start goes through.

Retrying is safe. A file without `CONCURRENTLY` runs in one transaction and rolls back whole.
An interrupted `CREATE INDEX CONCURRENTLY` leaves an invalid index, which the server drops and
rebuilds on the next attempt. An interrupted `DROP INDEX CONCURRENTLY` is finished by the
`IF EXISTS` drop on the next attempt.

Migration `004_drop_known_routes_iata_last_seen.sql` drops `idx_known_routes_iata_last_seen`,
which no query reads and which can reach about 10 GB on a large deployment. If you already
dropped it by hand (see below), the migration does nothing.

## Postgres settings

The stacks in this repo run stock `postgres:16-alpine` with no tuning. The settings below suit
a busy deployment. Run them as the database superuser (`POSTGRES_USER`, `beacon` in the shipped
compose files) in `psql` as above.

### Command line or `ALTER SYSTEM`

A setting passed on the Postgres command line (`postgres -c name=value`, in the `command:` of
the `db` service) wins over `ALTER SYSTEM`, and `ALTER SYSTEM` cannot change it. Check where
each setting comes from first:

```sql
SELECT name, setting, source FROM pg_settings WHERE name IN ('jit','wal_compression','max_wal_size','checkpoint_timeout','checkpoint_completion_target','bgwriter_lru_maxpages','bgwriter_lru_multiplier','bgwriter_delay','track_io_timing','session_preload_libraries','log_autovacuum_min_duration','log_lock_waits','log_temp_files','log_min_duration_statement');
```

For a row whose `source` is `command line`, change the value in the container command instead;
it takes effect at the next Postgres restart. The shipped compose files set no command, so
there everything comes from `ALTER SYSTEM` or the defaults.

### Settings that apply on reload

These take effect without a restart. Two checks first:

- `docker compose exec db pg_test_timing` must report a per-loop time under 100 ns. If it is
  higher, skip `track_io_timing`; timing every read would cost more than it tells you.
- `LOAD 'auto_explain';` must succeed in `psql`. If it fails, do not set
  `session_preload_libraries`: a library that cannot load there breaks every new connection,
  Beacon's included.

Then:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;      -- track=top, max=5000 are already the defaults
ALTER SYSTEM SET jit = off;
ALTER SYSTEM SET max_wal_size = '16GB';
ALTER SYSTEM SET checkpoint_timeout = '30min';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET bgwriter_lru_maxpages = 1000;
ALTER SYSTEM SET bgwriter_lru_multiplier = 4;
ALTER SYSTEM SET bgwriter_delay = '100ms';
ALTER SYSTEM SET log_autovacuum_min_duration = '60s';
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET log_temp_files = '64MB';
ALTER SYSTEM SET log_min_duration_statement = '5s';
ALTER SYSTEM SET wal_compression = 'zstd';               -- only if its source is not 'command line'
LOAD 'auto_explain';                                     -- must succeed first: a bad name breaks every new connection
ALTER SYSTEM SET session_preload_libraries = 'auto_explain';
ALTER SYSTEM SET auto_explain.log_min_duration = '2s';
ALTER SYSTEM SET auto_explain.log_format = 'json';
ALTER SYSTEM SET auto_explain.log_analyze = off;
ALTER SYSTEM SET track_io_timing = on;                   -- only after pg_test_timing in the container shows < 100 ns
SELECT pg_reload_conf();
DROP INDEX CONCURRENTLY idx_known_routes_iata_last_seen;
```

Notes:

- `max_wal_size = '16GB'` lets WAL grow that far between checkpoints. Make sure the volume
  under `data/postgres/` has the room, or pick a smaller value on a small host.
- `pg_stat_statements` only collects once it is in `shared_preload_libraries`, which needs a
  restart. If it is not there yet, add it at the restart in the next section.
- `DROP INDEX CONCURRENTLY` cannot run inside a transaction block; run it on its own in
  autocommit mode, as `psql` does by default. It takes a brief `SHARE UPDATE EXCLUSIVE` lock
  and waits for older transactions, so run the pre-deploy check above first. It frees about
  10 GB on a large deployment. Leave `idx_packets_payload_type` and `idx_packets_route_type`
  alone; packet queries still use them.

Verify:

```sql
SELECT name, setting, source, pending_restart FROM pg_settings WHERE name IN ('jit','wal_compression','max_wal_size','checkpoint_timeout','checkpoint_completion_target','bgwriter_lru_maxpages','bgwriter_lru_multiplier','bgwriter_delay','track_io_timing','session_preload_libraries','log_autovacuum_min_duration','log_lock_waits','log_temp_files','log_min_duration_statement');
SELECT to_regclass('idx_known_routes_iata_last_seen');  -- NULL once the index is gone
```

`pending_restart` must be false on every row. Open a new `psql` session and run
`SHOW session_preload_libraries;`; it should connect and show `auto_explain`. Statements over
2 s then appear in `docker compose logs db` with their plans as JSON.

Rollback: `ALTER SYSTEM RESET <name>;` for each setting, then `SELECT pg_reload_conf();`. If
new connections fail after the `session_preload_libraries` change, reset that one first from a
session that is still open. The dropped index had no readers; if you ever want it back, build
it with `CREATE INDEX CONCURRENTLY idx_known_routes_iata_last_seen ON known_routes (iata, last_seen DESC);`.

### Settings that need a restart

Raise the freeze ages, so autovacuum starts its anti-wraparound passes later and less often:

```sql
ALTER SYSTEM SET autovacuum_freeze_max_age = 400000000;
ALTER SYSTEM SET vacuum_freeze_table_age = 300000000;
```

`autovacuum_freeze_max_age` only changes at a restart, so restart Postgres off-peak. It takes
about 10 seconds; expect a short ingest catch-up after it.

At the same restart, apply anything from the reload step whose source is `command line`, for
example `wal_compression=zstd`, and `shared_preload_libraries=pg_stat_statements` if that is
not loaded yet. Put them in the `db` service's command:

```yaml
  db:
    image: postgres:16-alpine
    command: ["postgres", "-c", "wal_compression=zstd"]
```

If the service already has a `command:`, edit its `-c` values rather than adding a second one.
Then `docker compose up -d db` if you changed the command, or `docker compose restart db` if
you only ran the `ALTER SYSTEM` lines.

Verify:

```sql
SHOW autovacuum_freeze_max_age;
SHOW wal_compression;
SELECT max(age(datfrozenxid)) FROM pg_database;
```

Rollback: `ALTER SYSTEM RESET autovacuum_freeze_max_age; ALTER SYSTEM RESET vacuum_freeze_table_age;`,
put the old command back, and restart again.

## CPU profiling

Bounded CPU captures on a running instance are described in [Profiling](profiling.md).
