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

If you run the [daily plan check](#turning-on-the-daily-check), also confirm its report is clean
before and after the deploy. Maintainers run the plan checks before every server release; see
[Before a release](#before-a-release).

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

Migrations `011` to `024` (the small-table release) are one statement per file: one small
`CREATE INDEX CONCURRENTLY` on `node_iatas`, eleven small index drops on `node_iatas`, `nodes`,
`observers` and `channels`, one rename, and `fillfactor = 50` on `observers` and `channels`.
Together they take seconds at boot. Each drop needs a brief lock on its table, so run the
check above first and don't start an external `pg_dump` or a long transaction against those
four tables during the upgrade; a blocked drop stops startup after about two minutes as
described below, and the next start resumes where it stopped. Afterwards, compact the two
tables once; see [Compacting observers and channels](#after-upgrading-compacting-observers-and-channels).

### Pre-building the route hop index

Migration `006_known_routes_hop_iata.sql` builds `idx_known_routes_hop_iata`, which `/routes`
uses when a request filters by `hopCount`. The server builds it with `CREATE INDEX
CONCURRENTLY` during startup and does not serve the API until it finishes. On a large
`known_routes` table (tens of millions of rows) that takes 10 to 25 minutes and needs 0.2 to
0.4 GB of disk. To keep that out of the upgrade, build it yourself off-peak before deploying,
in `psql` as above:

```sql
CREATE INDEX CONCURRENTLY idx_known_routes_hop_iata ON known_routes (hop_count, iata);
SELECT indisvalid, indisready FROM pg_index WHERE indexrelid = 'idx_known_routes_hop_iata'::regclass;
```

Run the `CREATE` on its own in autocommit mode, not inside a transaction block. The check must
return `t | t`. Anything else means the build was interrupted and left an invalid index; drop
it and build again:

```sql
DROP INDEX CONCURRENTLY idx_known_routes_hop_iata;
CREATE INDEX CONCURRENTLY idx_known_routes_hop_iata ON known_routes (hop_count, iata);
```

When the server starts and finds a valid index with that name, it records the migration as
applied without building anything. If you skip this step, the migration still works; startup
just takes longer. Run the pre-deploy check above before either.

### After upgrading: route maintenance

The release that adds migration 006 changes how known routes are cleaned up. Deploy it
off-peak and expect the following.

- Route retention runs every `background.reconfirm` (default `1h`). Its first run after the
  upgrade is a full pass over the grace window (routes under `routes.min_observations` older
  than `routes.grace`). On a table of about 30 million routes that takes 12 to 14 minutes, in
  statements of a minute or less. The clock hour of that first run becomes the hour of a weekly
  full pass; a change to `routes.grace` or `routes.min_observations` also triggers one. Other
  runs only cover what aged out since the previous run.
- Stale neighbor edges are cleared at the end of every retention run. The first run may
  delete a backlog; later runs take a few seconds.
- The route recheck (routes with a hop that has departed or become ambiguous) runs every 5
  minutes and works through the table at `routes.reconfirm_rows_per_hour` (default `81000`). A
  full cycle takes the route count divided by that rate: about 16 days for 32.5 million routes.
  The first cycle reaches routes older releases never got to, and deletes the ones the same
  rule already condemned, typically a few percent of the table. About half of those come back
  the next time they are heard.

### After upgrading: compacting observers and channels

The small-table release (migrations `011` to `024`) drops the indexes that made every observer
presence update and every channel hearing rewrite index entries, and sets `fillfactor = 50` on
`observers` and `channels` so those updates stay on the same page (HOT updates). The fillfactor
only applies to pages written from then on. A table that bloated before the upgrade keeps its
size until it is rewritten once: on a large deployment `observers` held about 4,000 rows in
52 MB, and about 6 MB after the rewrite.

**When.** Once, off-peak, after the release is live and its last migration is recorded. This
must return `1`:

```sql
SELECT count(*) FROM schema_migrations WHERE filename LIKE '024_%';
```

Not before: without the fillfactor and the dropped indexes, the tables bloat again.

**Is it worth it?** Check the sizes in `psql` as above:

```sql
SELECT relname, relpages, pg_size_pretty(pg_relation_size(oid)) AS heap, reltuples::bigint AS rows
FROM pg_class WHERE relname IN ('observers', 'channels');
```

If both are already a few MB, skip it.

**Run** as the table owner (the `beacon` user) or a superuser, each statement on its own in
autocommit mode, not inside a transaction block:

```sql
SET lock_timeout = '3s';
VACUUM FULL observers;
VACUUM FULL channels;
```

- Each `VACUUM FULL` rewrites the table and its indexes under an `ACCESS EXCLUSIVE` lock, which
  blocks reads and writes on that table while it runs. On tables of this size that is a few
  seconds, so ingest's observer and channel updates and the observer and channel API pages
  wait that long.
- If it reports `canceling statement due to lock timeout`, another session held the table;
  run the same statement again.
- It needs free disk equal to the table's new size plus its indexes, a few MB here. The old
  files are freed when it finishes.

**Verify.** Re-run the size query: `relpages` and the heap size should drop. With fillfactor
50 a table is about twice its packed size, so `observers` ends near 6 MB for 4,000 rows. Then
check that updates are now HOT. The counters are cumulative, so take two samples an hour or so
apart and compare the change:

```sql
SELECT relname, n_tup_upd, n_tup_hot_upd,
       round(100.0 * n_tup_hot_upd / nullif(n_tup_upd, 0), 1) AS hot_pct
FROM pg_stat_user_tables WHERE relname IN ('observers', 'channels');
```

Between the two samples, nearly all new updates (`n_tup_hot_upd` growth over `n_tup_upd`
growth) should be HOT; before this release only a few percent were. Sessions holding long
snapshots lower it somewhat.

**Rollback.** None needed for the rewrite; it changes no data.

To go back to the previous server image, just deploy it: it works without the dropped
indexes, but type-filtered node pages (`/nodes` with a node type) are slower until the indexes
are rebuilt. It ignores the channel id cache and goes back to using a sequence value per
channel hearing. If you want the indexes back, rebuild them with `CREATE INDEX CONCURRENTLY`
using the definitions in the server's `db/migrations/001_baseline.sql`, for example:

```sql
CREATE INDEX CONCURRENTLY idx_nodes_type_last_seen ON nodes USING btree (node_type, last_seen DESC);
```

The baseline's `idx_node_iatas_iata` on `(iata, last_heard DESC)` has been replaced by an index
of the same name on `(iata)`; leave it in place.

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
  restart. If it is not there yet, add it at the restart in the next section. Beacon's
  migration 010 creates the extension itself where it can; see
  [Statement statistics](#statement-statistics).
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

## Rebuilding the route keyset indexes

`/routes` paging and route retention read two indexes on `known_routes`,
`idx_known_routes_keyset` and `idx_known_routes_iata_keyset`. Steady deletes and upserts leave
them bloated, so rebuild them every 7 to 14 days, and once after upgrading to the release that
drops the unused route indexes (`idx_known_routes_last_seen`, `idx_known_routes_hop_count`
and `idx_known_routes_reconfirm`).

Rebuild one index at a time, off-peak. Each rebuild writes a full new copy before it drops
the old one, so check first that the volume under `data/postgres/` has more than twice the
index's size free:

```sql
SELECT pg_size_pretty(pg_relation_size('idx_known_routes_keyset')),
       pg_size_pretty(pg_relation_size('idx_known_routes_iata_keyset'));
```

```bash
df -h data/postgres
```

Then run the pre-deploy check above and, in autocommit mode:

```sql
REINDEX INDEX CONCURRENTLY idx_known_routes_keyset;
```

When it has finished, check the disk again and run:

```sql
REINDEX INDEX CONCURRENTLY idx_known_routes_iata_keyset;
```

Reads and writes carry on during the rebuild. If one is interrupted (cancelled, connection
lost, server restarted), it leaves an invalid copy named after the index with a `_ccnew`
suffix. The original index is still in place and still used. Find the leftover and drop it
before trying again:

```sql
SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;
DROP INDEX CONCURRENTLY IF EXISTS idx_known_routes_keyset_ccnew;       -- or idx_known_routes_iata_keyset_ccnew
```

## Database pools and connections

Beacon opens a separate connection pool per workload, sized by `database.api_plan_layout`
(see [Configuration](configuration.md#database-pools-and-cost-guards)). Each pool sets its own
session settings and an `application_name`, so `pg_stat_activity` shows which one a
connection belongs to:

| Pool | `application_name` | Size | Session settings |
|---|---|---:|---|
| `api_legacy` | `beacon-api_legacy` | 8 | Server defaults. Runs the few API statements that keep the previous plan behaviour. |
| `api_custom` | `beacon-api_custom` | 8 (7 under `split`) | `plan_cache_mode=force_custom_plan`, `jit=off`, `max_parallel_workers_per_gather=0`, `statement_timeout=35s`, `idle_in_transaction_session_timeout=30s` |
| `api_cached` | `beacon-api_cached` | 5, `split` only | As `api_custom`, with `plan_cache_mode=force_generic_plan` |
| `ingest` | `beacon-ingest` | 6, or one per CPU above 6 | `plan_cache_mode=auto`, `jit=off`, no statement timeout: an ingest write waits out a lock rather than drop a packet |
| `maint` | `beacon-maint` | 4 | `plan_cache_mode=force_custom_plan`, `jit=off`, `max_parallel_workers_per_gather=0`. Background jobs, importers, backups and admin queries. |

The `single` layout opens only `api_legacy`, `ingest` and `maint`.

- **Headroom.** `SHOW max_connections;` must leave room for the total (26 by default on up to
  6 CPUs) plus every other client: `psql` sessions, backups, monitoring. If your deploy starts
  the new server before the old one stops, count both.
- **Checking.** Parallel workers carry their leader's `application_name`, so count client
  backends only:

  ```sql
  SELECT application_name, count(*) FROM pg_stat_activity
  WHERE application_name LIKE 'beacon-%' AND backend_type = 'client backend' GROUP BY 1;
  ```

  No pool should go above its size, and `beacon-api_cached` should be absent under
  `custom_all`.
- **`pool_max_conns`.** A `pool_max_conns` in `POSTGRES_DSN` is overridden by the pool sizes;
  the server logs that at startup.
- **PgBouncer.** The session settings are sent as startup parameters. Behind PgBouncer,
  `ignore_startup_parameters` must list `plan_cache_mode`, `jit`, `statement_timeout`,
  `idle_in_transaction_session_timeout` and `max_parallel_workers_per_gather`, or connections
  are refused. PgBouncer then drops them, so the pools run on the server defaults; connect
  Beacon to Postgres directly where you can.
- **Background jobs** share the 4 `maint` connections without parallel plans, so a job may
  take a little longer than before. `beacon_job_duration_seconds` shows it.

### Small hosts

Each hourly analytics rollup sets `work_mem` to 256 MB for its own transaction, and Postgres
may use that much for every sort or hash step in it. On a host with little memory, watch the
`db` container's memory while rollups run (about 95 minutes past each hour).

## Statement statistics

`GET /api/v1/admin/db/statements` sums `pg_stat_statements` by statement name (format in the
[API contract](api-contract.md#admin)). It needs the extension created and preloaded:

- **Created.** Migration `010_pg_stat_statements.sql` creates the extension when the server
  offers it and the database role may. If not, it logs a notice and is still recorded, so
  startup never fails over it. The shipped stacks connect as the superuser, so it is created.
  Otherwise run `CREATE EXTENSION pg_stat_statements;` as a superuser.
- **Preloaded.** It only collects once `shared_preload_libraries` includes it, which needs a
  Postgres restart. Add it to the `db` service's command at the next restart (see
  [Settings that need a restart](#settings-that-need-a-restart)), keeping any `-c` values
  already there:

  ```yaml
    db:
      command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]
  ```

Until both are true the endpoint returns `503`. Check with `SHOW shared_preload_libraries;`
and a request to the endpoint with the admin key.

Planning time (`plan_ms`) is only recorded while `pg_stat_statements.track_planning` is on. It
adds overhead, so turn it on for one day to measure, then off again; both apply on reload:

```sql
ALTER SYSTEM SET pg_stat_statements.track_planning = on;
SELECT pg_reload_conf();
-- a day later
ALTER SYSTEM RESET pg_stat_statements.track_planning;
SELECT pg_reload_conf();
```

API statements are planned on every call, so summed `plan_ms` should stay a small fraction of
summed `exec_ms`, under about 7%.

## Metrics

With `server.admin_listen` set, the server opens a second listener that serves only
`GET /metrics` in Prometheus format. It has no authentication. `/metrics` is not served on the
public port.

In the Docker stack the listener runs inside the `app` container, so bind it to all of the
container's interfaces and publish it on the host's loopback only:

```yaml
# config.yaml
server:
  admin_listen: "0.0.0.0:9090"
```

```yaml
# docker-compose.yml, app service
    ports:
      - "127.0.0.1:8080:8080"
      - "127.0.0.1:9090:9090"
```

Never route it through Caddy. Scrape it from the host:

```yaml
scrape_configs:
  - job_name: beacon
    static_configs:
      - targets: ["127.0.0.1:9090"]
```

| Metric | Type | Labels | What it is |
|---|---|---|---|
| `beacon_http_request_seconds` | histogram | `route`, `family` | HTTP request time by route pattern |
| `beacon_db_time_seconds` | histogram | `statement`, `pool` | Time per database statement |
| `beacon_pool_acquire_seconds` | histogram | `pool` | Wait for a pooled connection |
| `beacon_guard_db_seconds` | histogram | `family`, `class` | Database time per guarded request |
| `beacon_guard_would_refuse_total` | counter | `family`, `guard` | Requests a guard would refuse if its family enforced |
| `beacon_guard_refused_total` | counter | `family`, `guard` | Requests a guard refused |
| `beacon_ingest_queue_depth` | gauge | | Messages waiting in the ingest queue |
| `beacon_ingest_dropped_total` | counter | | Messages dropped because the ingest queue was full |
| `beacon_job_duration_seconds` | histogram | `job` | Background job run time (`cleanup`, `analytics_rollup`, `reconfirm`, `route_retention`, ...) |
| `beacon_job_rows_total` | counter | `job` | Rows removed by background jobs, today `reconfirm` and `route_retention` |
| `beacon_index_bytes` | gauge | `index` | Size of each index, hourly |
| `beacon_index_bloat_ratio` | gauge | `index` | Bytes per row against the last rebuild, hourly. See [Index health](#index-health). |
| `beacon_pg_wal_bytes_total` | counter | | WAL written, cluster-wide |
| `beacon_pg_checkpoints_total` | counter | `kind` | Checkpoints, `timed` or `requested` |
| `beacon_pg_xid_age` | gauge | | Age of the oldest transaction ID in the database |
| `beacon_planguard_failures` | gauge | `entry`, `mode` | 1 for each corpus entry and plan mode that failed the last [plan check](#turning-on-the-daily-check) |
| `beacon_planguard_last_run_timestamp_seconds` | gauge | | Unix time the last successful plan check finished; 0 until the first one |

`guard` is `deadline`, `cap`, `admission` or `budget`. The Postgres counters are read once a
minute; the index gauges first appear an hour after startup. The two `beacon_planguard_*`
gauges exist only with `planguard.daily_check: true`. Go runtime and process metrics
are included too.

### Example alert rules

```yaml
groups:
  - name: beacon
    rules:
      - alert: BeaconGuardWouldRefuse          # any would-refuse delays enforcing that family
        expr: sum by (family, guard) (increase(beacon_guard_would_refuse_total[1h])) > 0
      - alert: BeaconDeadlineHits
        expr: sum(increase(beacon_guard_refused_total{guard="deadline"}[1h])) > 20
      - alert: BeaconListSlow                  # list-class database time p99 over 1 s
        expr: histogram_quantile(0.99, sum by (le) (rate(beacon_guard_db_seconds_bucket{class="list"}[15m]))) > 1
        for: 15m
      - alert: BeaconPoolAcquireSlow
        expr: histogram_quantile(0.99, sum by (le, pool) (rate(beacon_pool_acquire_seconds_bucket[5m]))) > 0.5
        for: 10m
      - alert: BeaconCleanupLong               # a cleanup run over 10 min in the last 2 h
        expr: increase(beacon_job_duration_seconds_count{job="cleanup"}[2h]) - increase(beacon_job_duration_seconds_bucket{job="cleanup",le="600"}[2h]) > 0
      - alert: BeaconKeysetBloat
        expr: beacon_index_bloat_ratio{index=~"idx_known_routes_(iata_)?keyset"} > 4
      - alert: BeaconCheckpointsRequested
        expr: increase(beacon_pg_checkpoints_total{kind="requested"}[1d]) > increase(beacon_pg_checkpoints_total{kind="timed"}[1d])
      - alert: BeaconWALAboveBaseline          # set the baseline from your own steady state
        expr: rate(beacon_pg_wal_bytes_total[1h]) > <baseline bytes/s>
      - alert: BeaconXIDAge
        expr: beacon_pg_xid_age > 300e6
      # The two plan check rules only matter with planguard.daily_check: true.
      - alert: BeaconPlanguardFailures         # the last plan check found a regression
        expr: sum(beacon_planguard_failures) > 0
      - alert: BeaconPlanguardStale            # no successful plan check for 26 h
        expr: time() - beacon_planguard_last_run_timestamp_seconds > 26*3600 and on() time() - process_start_time_seconds > 26*3600
```

Replace `<baseline bytes/s>` with your normal WAL rate before loading the rules. The route
recheck has no metric yet; at `debug` level it logs a `route reconfirm` line per slice, and
`wrapped=true` marks the end of a full cycle.

## Enforcing a guard family

Every guard family only observes until you enforce it (see
[Configuration](configuration.md#database-pools-and-cost-guards)). Observe for 7 days with
metrics on, then enforce a family only when all three hold for it over those 7 days. With
`routes` as the example (Prometheus needs at least 7 days of retention):

1. No would-refuse from any guard. Every series must be 0:

   ```promql
   sum by (guard) (increase(beacon_guard_would_refuse_total{family="routes"}[7d]))
   ```

2. The p99 database time of each class is at most a quarter of its limit: entity 1.25 s, list
   2.5 s, aggregation 7.5 s.

   ```promql
   histogram_quantile(0.99, sum by (le, class) (rate(beacon_guard_db_seconds_bucket{family="routes"}[7d])))
   ```

3. No request used more than half its limit. Histograms have no exact maximum, so check that
   no request landed above the bucket at or under half the limit: `le="2.5"` for entity,
   `le="5"` for list, `le="10"` for aggregation (stricter than 15 s, which has no bucket). Each
   must be 0:

   ```promql
   sum(increase(beacon_guard_db_seconds_count{family="routes",class="list"}[7d]))
     - sum(increase(beacon_guard_db_seconds_bucket{family="routes",class="list",le="5"}[7d]))
   ```

Then enforce it at runtime, listing every family that should enforce (the list replaces the
current one):

```bash
curl -s -X PUT https://<your-domain>/api/v1/admin/config \
  -H "Authorization: Bearer $BEACON_API_KEY" -H 'Content-Type: application/json' \
  -d '{"guards":{"enforce":["other","routes"]}}'
```

The response's `config.guards.enforce` shows the new list. Add the same list to
`guards.enforce` in `config.yaml`, or the next restart goes back to the old one. To stop
enforcing, `PUT` the list without that family (`[]` for none). `beacon_guard_refused_total`
then counts real refusals.

`other` and `routes` are the families to start with. The rest are not ready in this release:
`channel_messages` statements are not guarded yet, and the packet and stats families still
run statements that later releases make cheaper. Their release notes will say when each is
ready, roughly `channel_messages` first, then `packets_global`, then `packets_region` and
`packets_window`, then `stats` and `packet_detail`. `packets_window` may stay observed for
good.

## Index health

Once an hour the server records each index's size (`beacon_index_bytes`) and its bytes per
row against a baseline (`beacon_index_bloat_ratio`). The baseline is taken the first time the
server sees the index and again whenever it is rebuilt, so the ratio is growth since the last
rebuild, not absolute bloat: 1 means as compact as then, 4 means four times the bytes per
row. An index that has never been analyzed has no ratio.

The first run, and then one run a week, also logs `indexes with no scans since the last
statistics reset` with each unused non-unique index and its size. An index that stays on that
list for weeks is a candidate to drop; check that no rare job reads it first.

When `BeaconKeysetBloat` fires, rebuild that index as in
[Rebuilding the route keyset indexes](#rebuilding-the-route-keyset-indexes). The rebuild resets
its baseline, and the ratio drops back to about 1 on the next hourly run.

## Plan checks (planguard)

planguard checks that PostgreSQL still plans each of Beacon's statements the way it was designed.
Its corpus, in the server repo under `db/planguard/`, lists every API and job statement with
parameters and what its plan must look like: the driving index and its index conditions, the
scans it must never use, and buffer, row and time budgets. It runs at three tiers against three
databases:

| Tier | Database | How it plans | Checks | Who runs it |
|---|---|---|---|---|
| `fixture` | A synthetic database built through the migrations | Plain `EXPLAIN` | Plan shapes, against the committed `baseline/fixture` | CI, on every server pull request |
| `local` | A copy of a large production database, or a restored dump | `EXPLAIN (ANALYZE, BUFFERS)`, read-only | Plan shapes and budgets, against your own `baseline/local` | Maintainers, before a release |
| `prod` | A live production database | Plain `EXPLAIN`, read-only, 5 s per plan | Plan shapes only, no baseline | The server's [daily check](#turning-on-the-daily-check), or by hand through psql |

Every tier runs each statement inside a `READ ONLY` transaction with a 1 s lock timeout and rolls
it back. Only the `local` tier executes statements, and then only reads; writes are only ever
planned.

Each run gets a verdict:

| Verdict | Meaning | Blocks a release |
|---|---|---|
| `ok` | The plan matches its expectations. | No |
| `FALSE_POSITIVE` | A statement that should pass broke a rule: a real regression, or an expectation that no longer holds on this database. | Yes |
| `MISSED` | A planted regression (an entry that must fail) passed, so the check itself is not catching what it should. | Yes |
| `ERROR` | The statement could not be planned. | Yes |
| `DETECTED` | A planted regression failed, as it should. | No |
| `RETIRED_INDEX` | The only failures name an index that a pending change drops. Expected until that change ships. | No |
| `KNOWN_ISSUE` | A failure the corpus already records as known. | No |
| `SKIP` | The run was not made, for example a statement whose feature is not built yet or whose parameters found no value. | No |

The command line tool is `cmd/planguard` in the server repo. Run it from a checkout of the commit
you are about to release. It exits 0 when no run fails and 1 when one does, and writes its
results to `planguard-out/`.

### Fixture tier

CI builds the fixture and runs this tier on every pull request. To run it yourself you need an
empty database with C collation on PostgreSQL 16 (CI pins 16.15):

```sql
CREATE DATABASE planguard TEMPLATE template0 LC_COLLATE 'C' LC_CTYPE 'C' ENCODING 'UTF8';
```

```bash
go run ./cmd/planguard run --tier fixture --dsn 'postgres://...:5432/planguard'
```

The first run builds the fixture through the migrations, which takes a minute or two; later runs
reuse it while its inputs are unchanged. The builder refuses a database that already holds data
or is not C-collated.

### Local tier

The local tier is the release gate. Run it against a copy of a large production database, or a
restored dump, never against the live one: it executes every read statement. The copy needs its
own baseline (written to `db/planguard/baseline/local/` in your checkout), so write one on the
first run, review it, then check against it:

```bash
go run ./cmd/planguard run --tier local --dsn "$COPY_DSN" --baseline write
go run ./cmd/planguard run --tier local --dsn "$COPY_DSN"      # --baseline check is the default
```

A plan that changes against the baseline fails the check run. When the change is intended, write
the baseline again and keep it with the copy. `--only` and `--skip` take a regular expression of
entry ids to narrow a run.

### Prod tier through psql

The server's daily check runs the prod tier itself. To get the same evidence from a database the
server does not check, for example before turning the check on, emit read-only psql scripts and
run them yourself. Nothing connects from the tool; you run each script and hand its output back:

```bash
go run ./cmd/planguard run --tier prod --emit resolvers > resolvers.sql
docker compose exec -T db psql -X -U beacon -d beacon < resolvers.sql > resolvers.out

go run ./cmd/planguard run --tier prod --emit plans --params resolvers.out > plans.sql
docker compose exec -T db psql -X -U beacon -d beacon < plans.sql > plans.out

go run ./cmd/planguard run --tier prod --params resolvers.out --plans plans.out
```

The first script looks up parameter values (20 s statement timeout); the second runs plain
`EXPLAIN`s with them. Both set `default_transaction_read_only` and a 1 s lock timeout. Each
script carries a random marker, and the last step rejects output that is truncated or does not
match the script.

### Before a release

Before tagging a server release, maintainers confirm:

1. CI's fixture tier is clean.
2. The local tier, against your copy and its baseline, is clean.
3. On a deployment with the daily check on, `GET /api/v1/admin/db/planguard?fresh=true` returns
   `"clean": true`, before and after the deploy.

`RETIRED_INDEX` runs are expected while an index drop is pending; each names the index that will
go.

### Turning on the daily check

The daily check is for large deployments only. Its expectations assume production-sized
tables, and on a small database the planner rightly picks other plans, which the check reports
as failures. Before turning it on, run the prod tier through psql once and look at the result.
Then set:

```yaml
planguard:
  daily_check: true
```

and restart the server. It cannot be combined with `server.read_only`. The first check runs
about an hour after startup and then once a day; a failed run is retried every hour. Read the
last report, or run one now (at most one new run per 5 minutes), with the admin key:

```bash
curl -s https://<your-domain>/api/v1/admin/db/planguard \
  -H "Authorization: Bearer $BEACON_API_KEY"
curl -s 'https://<your-domain>/api/v1/admin/db/planguard?fresh=true' \
  -H "Authorization: Bearer $BEACON_API_KEY"
```

`clean` must be true. `failures` lists each failing run with the rules it broke and the indexes
it used. The response is described in the [API contract](api-contract.md#admin).

With [metrics](#metrics) on, add the two plan check alerts from the
[example rules](#example-alert-rules):

- `BeaconPlanguardFailures` fires when the last check had a failing run.
  `beacon_planguard_failures` names the entry and mode.
- `BeaconPlanguardStale` fires when no check has succeeded for 26 hours. The last-run gauge is
  0 from startup until the first success, so a check that never succeeds fires it too. The
  `process_start_time_seconds` condition keeps a recent restart from firing it before the first
  run has had time to happen.

To turn the check off, set `daily_check: false` and restart. Nothing is stored in the database.

### Comparing two builds

`server.read_only: true` (see [Configuration](configuration.md#read-only-mode)) lets two server
builds serve the same database copy side by side, so a change to a query can be checked against
real data before it ships. `planguard storediff` then walks the same API pages on both and
compares the whole JSON of every page.

1. Build the base and the candidate server binaries.
2. Give each a `config.yaml` with `server.read_only: true` and `ratelimit.enabled: false`, and
   leave `REDIS_ADDR` unset so neither serves cached responses. Point both `POSTGRES_DSN`s at
   the same copy, already migrated to the schema both builds expect. Indexes or other objects
   only the candidate needs can live in a scratch schema on that copy, put first on the
   candidate's search path with `?search_path=<scratch>,public` in its DSN.
3. Start them on two ports, for example 8481 and 8482. Each logs a read-only warning at startup
   and no migration lines.
4. Compare them:

   ```bash
   go run ./cmd/planguard storediff --old http://127.0.0.1:8481 --new http://127.0.0.1:8482 \
     --cases db/planguard/storediff/smoke.yaml --walk 1,2,3,web --out storediff-out
   ```

`--walk` lists the page sizes to walk; `web` is each case's web page size. Small page sizes catch
pagination that skips or repeats rows. The tool exits non-zero when any page differs, and with
`--out` writes `storediff_report.md` there. Never use read-only mode on your live instance: it
ingests nothing.

## Rolling back the pool layout

If the new pools or plans misbehave, set this and restart the server:

```yaml
database:
  api_plan_layout: single
```

It puts every API statement on one pool with the previous session settings and makes every
guard family observe, whatever `guards.enforce` says. The alternative is the previous server
image. It ignores migration 010; the `pg_stat_statements` extension stays installed and
harmless.

## CPU profiling

Bounded CPU captures on a running instance are described in [Profiling](profiling.md).
