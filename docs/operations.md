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

Migrations `025` to `033` (2.1.0) change `packets`:

- `025` and `027` add the checks `packets_payload_type_domain` (`payload_type` 0 to 15) and
  `packets_route_type_domain` (`route_type` 0 to 3) without checking existing rows. Each needs
  a brief lock on `packets`.
- `026` and `028` validate them. Each scans `packets`; writes continue meanwhile.
- `029` to `032` build four indexes with `CREATE INDEX CONCURRENTLY`; see
  [Pre-building the packets indexes](#pre-building-the-packets-indexes).
- `033` creates the statistics object `packets_heard_inverted_stat` and runs `ANALYZE packets`.

Ingest only stores types decoded from the packet header, which always fit, so only rows
changed by hand can fail the checks. Before upgrading, confirm none exist; when none do, this
reads the whole table, so run it off-peak:

```sql
SELECT EXISTS (SELECT 1 FROM packets WHERE payload_type NOT BETWEEN 0 AND 15 OR route_type NOT BETWEEN 0 AND 3);
```

It must return `f`. Otherwise `026` or `028` fails and stops startup on every attempt; fix or
delete those rows first.

Migration `034_observations_adverts.sql` builds the partial index `idx_observations_adverts` on
`packet_observations` with `CREATE INDEX CONCURRENTLY`; see
[Pre-building the observer adverts index](#pre-building-the-observer-adverts-index). The same
release starts a background job that fills in missing observation payload types; see
[After upgrading: observation payload types](#after-upgrading-observation-payload-types).

Migrations `035` to `041` add the channel message read model; see
[Read models: channel messages by site](#read-models-channel-messages-by-site).

- `035` creates the table `channel_message_iatas`.
- `036` to `040` build its five indexes with `CREATE INDEX CONCURRENTLY` on the empty table,
  which is instant.
- `041` builds `idx_channel_messages_channel_id` on `channel_messages` with
  `CREATE INDEX CONCURRENTLY`. `channel_messages` is small (about 200,000 rows on a large
  deployment), so it takes well under a second and needs no pre-build.

To pre-build `041` anyway, run the pre-deploy check above, then this text exactly, on its own
in autocommit mode:

```sql
CREATE INDEX CONCURRENTLY idx_channel_messages_channel_id ON channel_messages USING btree (channel_id, id DESC);
SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid = 'idx_channel_messages_channel_id'::regclass;
```

The second statement must print `t`. The migration then records the existing valid index
instead of building it again. After the deploy, check every new index:

```sql
SELECT c.relname, i.indisvalid AND i.indisready FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE c.relname IN ('channel_message_iatas_pkey', 'idx_cmi_channel_site', 'idx_cmi_site', 'idx_cmi_channel_site_scope',
                    'idx_cmi_channel_scope', 'idx_cmi_scope', 'idx_channel_messages_channel_id');
```

It must return 7 rows, all `t`.

Migrations `042` to `045` add the region packet read model; see
[Read models: packets by site](#read-models-packets-by-site).

- `042` creates the table `packet_sites`. Its foreign key to `packets` takes a brief lock on
  `packets`, so run the pre-deploy check above first.
- `043` to `045` build `idx_packet_sites_site`, `idx_packet_sites_site_type` and
  `idx_packet_sites_site_scope` with `CREATE INDEX CONCURRENTLY` on the empty table, which
  takes seconds. No pre-build is needed.

After the deploy, check the table's four indexes:

```sql
SELECT c.relname, i.indisvalid AND i.indisready AS ok
FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE i.indrelid = 'packet_sites'::regclass ORDER BY 1;
```

It must return 4 rows, all `ok = t`.

Migrations `047` to `053` finish the cleanup; see
[Lookup-table indexes and the route stamp column](#lookup-table-indexes-and-the-route-stamp-column).

- `047` to `052` drop six cold indexes on small lookup tables with
  `DROP INDEX CONCURRENTLY IF EXISTS`: milliseconds each, plus any wait for a lock.
- `053` drops the column `known_routes.last_reconfirmed_at` in a transaction. It is a catalog
  change, not a rewrite (179 ms on a 10.5-million-row copy), but it takes an `ACCESS EXCLUSIVE`
  lock on `known_routes`, so run the pre-deploy check above, and make sure no `pg_dump` is
  running: the drop waits for it. While it waits (up to 30 s, three attempts), every other
  session's reads of `known_routes`, read-only servers' included, queue behind it. The
  column's space (about 8 bytes a route, some 80 MB on 10.5 million routes) is reclaimed only
  when the table is next rewritten (`VACUUM FULL` or `pg_repack`); new and updated rows no longer
  carry it. **It is a one-way door for older images**; see
  [Upgrading](upgrading.md).

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

### Pre-building the packets indexes

Migrations `029` to `032` build four indexes on `packets` with `CREATE INDEX CONCURRENTLY`
while the API and ingest wait. On a small database that is seconds. On a large one, build them
yourself off-peak before deploying, in `psql` as above, each statement on its own in
autocommit mode. Use exactly these names and definitions:

```sql
CREATE INDEX CONCURRENTLY idx_packets_last_heard_hash ON packets USING btree (last_heard_at DESC, packet_hash DESC);
CREATE INDEX CONCURRENTLY idx_packets_type_last_heard ON packets USING btree (payload_type, route_type, last_heard_at DESC, packet_hash DESC);
CREATE INDEX CONCURRENTLY idx_packets_scope_last_heard ON packets USING btree (scope_id, last_heard_at DESC, packet_hash DESC) INCLUDE (payload_type, route_type, first_heard_at) WHERE (scope_id IS NOT NULL);
CREATE INDEX CONCURRENTLY idx_packets_heard_inverted ON packets USING btree (first_heard_at) INCLUDE (last_heard_at, packet_hash, payload_type, route_type, scope_id) WHERE ((first_heard_at > last_heard_at) IS TRUE);
```

Then check them. Every row must read `t | t`:

```sql
SELECT c.relname, i.indisvalid, i.indisready, pg_size_pretty(pg_relation_size(c.oid)) AS size
FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE c.relname IN ('idx_packets_last_heard_hash', 'idx_packets_type_last_heard',
                    'idx_packets_scope_last_heard', 'idx_packets_heard_inverted');
```

An invalid index means the build was interrupted; drop it with `DROP INDEX CONCURRENTLY` and
build it again. When the server finds a valid index with one of these names, it records that
migration as applied without building anything. It checks only the name, so a different
definition under the same name is kept as it is.

Pre-build only these indexes. Don't create the two checks or `packets_heard_inverted_stat`
yourself: migrations `025`, `027` and `033` fail on an object that already exists, and
startup stops.

To go back to the previous server image, deploy it. It ignores the new indexes, checks and
statistics. Leave them in place: their migrations stay recorded, so a later upgrade would not
build them again.

### Pre-building the observer adverts index

Migration `034` builds `idx_observations_adverts`, which `/observers/{observerId}/adverts` reads
once the [payload-type backfill](#after-upgrading-observation-payload-types) is done. The
server builds it at startup while the API and ingest wait. On a large `packet_observations`
table (hundreds of millions of rows) that should take a minute or two and about 150 MB of
disk, so build it yourself off-peak before deploying. Run the
[pre-deploy check](#before-deploying-a-release) first: the long-transaction query must return
no rows. Then, in `psql` as above, on its own in autocommit mode, run exactly this text, byte
for byte the same as the migration:

```sql
CREATE INDEX CONCURRENTLY idx_observations_adverts ON packet_observations (observer_id, id) WHERE payload_type = 4;
```

Then check it:

```sql
SELECT indisvalid, indisready, pg_get_indexdef(indexrelid), pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_index WHERE indexrelid = 'idx_observations_adverts'::regclass;
```

It must read `t | t`, with the definition
`CREATE INDEX idx_observations_adverts ON public.packet_observations USING btree (observer_id, id) WHERE (payload_type = 4)`.
If `indisvalid` is `f`, the build was interrupted; drop the index and build it again:

```sql
DROP INDEX CONCURRENTLY idx_observations_adverts;
```

When the server starts and finds a valid index with that name, it records migration `034` as
applied without building anything, so startup is instant. If you skip this step, the same
build runs at startup instead, and the API and ingest wait for it.

Turn on the [daily plan check](#turning-on-the-daily-check) only after migration `034` is
recorded. Some of its adverts checks need this index; without it they take 1 to 16 seconds
instead of 78 ms. To confirm:

```sql
SELECT filename FROM schema_migrations WHERE filename = '034_observations_adverts.sql';
```

To go back to the previous server image, deploy it. The index stays and nothing reads it: about
150 MB, plus one entry for each advert observation stored. You can leave it. If you drop it
(`DROP INDEX CONCURRENTLY idx_observations_adverts;`), also delete its migration record, so a
later upgrade builds it again:

```sql
DELETE FROM schema_migrations WHERE filename = '034_observations_adverts.sql';
```

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

### After upgrading: observation payload types

Observations stored by servers older than the observation `payload_type` column have no payload
type of their own. The release with migration `034` adds a background job, on the `maint` pool,
that gives each of them its own packet's payload type. It walks `packet_observations` by id in
spans of one million ids, ten spans a minute, so about 10 million ids a minute. Each statement
writes at most 50,000 rows, and the job saves its position after every span, so a restart
resumes where it stopped. When the walk passes the highest id it read at the start of its run,
it records `done`. Rows stored later are typed by ingest.

How long it takes depends on the id range, not on how many rows need a type: a database whose
ids run to about 830 million needs about 80 minutes. On a database whose observations are all
typed, each statement reads its span and updates nothing.

Until the job reports `done`, `/observers/{observerId}/adverts` serves the same statement as the
previous release, on the same index, now on the `api_slow` pool (see
[Slow region and message statements](#slow-region-and-message-statements)). Once a server process reads `done`, it switches
to the statement that reads `idx_observations_adverts` and keeps it until restart. The
responses are the same either way.

Check progress, read-only:

```sql
SELECT value, updated_at FROM background_state WHERE key = 'observation_payload_type';
```

`next_id` climbs about 10 million a minute, and the value ends as `{"next_id": ..., "done": true}`.

**Marking it done by hand.** You can skip the walk on a database that has no untyped
observations. First check, read-only. This reads all of `packet_observations` once, so run it
off-peak:

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '10min';
SELECT EXISTS (SELECT 1 FROM packet_observations WHERE payload_type IS NULL) AS any_untyped;
ROLLBACK;
```

Only if it prints `f`, and after the job's first run has created the key (the progress query
returns a row), run:

```sql
UPDATE background_state SET value = '{"next_id": 0, "done": true}'::jsonb, updated_at = now()
WHERE key = 'observation_payload_type';
```

It should report `UPDATE 1`. A run that was already in flight can write `"done": false` once
more, so run the progress query again two minutes later and repeat the `UPDATE` if needed. Each
server process picks up `done` on its next adverts request; no restart is needed.

On a deployment that had untyped observations, the backfill corrects two things: the
per-observer payload breakdown's unknown (`-1`) bucket shrinks into the real types, and route
evidence starts to include those rows.

Don't upgrade to a release that drops `idx_observations_observer_id` until the progress query
shows `"done": true`. Until then the adverts statement of the previous release still runs, and
it uses that index.

Going back to the previous server image needs nothing here. Older servers ignore the
`observation_payload_type` key, and rows the job typed stay typed, which older servers read the
same way.

### After upgrading: stats and traces on the custom pool

In the release with migration `034`, five statements move from the `api_legacy` pool to
`api_custom`, under both `custom_all` and `split`: `GetTopNodes`, `GetStatsTopAdvertisers`,
`GetPathStats`, `GetStatsSeries` and `ListTraceTags`. That pool has a 35 s statement timeout,
`jit=off` and no parallel workers (see [Database pools and connections](#database-pools-and-connections)).
They are also guarded, but a guard's deadline applies only if its family is listed in
`guards.enforce`, which is empty by default.

For top nodes, top advertisers and paths, requests with at most 32 distinct IATAs and
whole-hour bounds use new statements that read the hourly rollups one hour and IATA at a time.
Only wider lists, such as every IATA at once, still run the previous statements, now without
parallel workers. Measured over all 625 IATAs for 7 days on a copy of a large production
database, they stay far inside the timeout:

| Statement | With parallel workers | Without |
|---|---:|---:|
| top nodes | 276 ms | 556 ms |
| top advertisers | 1.47 s | 3.63 s |
| paths | 1.63 s | 1.58 s |

Responses are unchanged. Under `split`, `ListObserverAdverts` and `GetObserverTelemetrySince`
run on cached generic plans; see [Configuration](configuration.md#database-pools-and-cost-guards).

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

## Read models: channel messages by site

`channel_message_iatas` is a small table with one row for each channel message and each site
that heard it. Each row also copies the message's channel and its packet's scope. Ingest keeps
it up to date, and a background reconcile repairs it every 5 minutes. On a large deployment it
takes about 120-150 MB with its five indexes.

While the server process trusts the table, these channel message pages read it:

- `/channels/{id}/messages` with `iatas`, with `iatas` and `scope`, with `scope` alone, and
  with `since` and `iatas`;
- `/messages` with `iatas`, and with `scope` alone.

Each such page now reads about as many index entries as it returns, where the previous
statement read every observation of the channel. While the process does not trust the table,
the same pages are served by the previous release's statements, on the `api_slow` pool. Two shapes always use the
previous statements: `/messages` with `iatas` and `since`, and `/messages` with `iatas` and
`scope`. Pages without `iatas` or `scope` never read the table. Responses are the same in
every case.

### Installing it

The release adds migrations `035` to `041`; see [Before deploying a release](#before-deploying-a-release).
On the first start the server fills the table in the background:

1. It waits until every transaction that started before boot and holds a transaction id has
   finished, then runs one full reconcile.
2. It backfills the table oldest message first, in batches of 10,000 message ids with a 0.1 s
   pause between them. The log shows `cmi backfill progress` lines, then `cmi backfill complete`.
   On a deployment with about 200,000 messages this takes 3 to 5 minutes, mostly the pauses.
3. It runs a one-time verification: an exact check of two ranges of 2,000 messages, and a
   page-by-page comparison of the previous and the new statements on the busiest recent sites
   and scopes. On success it logs `cmi first-time verification passed` and records the time,
   so later starts skip it.
4. It logs `cmi trusted: region and scope message pages read channel_message_iatas`.

Until step 4, every page is served by the previous statements, and users see no difference.
If the verification fails, the server logs
`cmi verification failed; pages stay on the original statements` and tries again every 5
minutes.

Check progress, read-only:

```sql
SELECT value, updated_at FROM background_state WHERE key = 'cmi';
SELECT pg_size_pretty(pg_total_relation_size('channel_message_iatas'));
```

`complete` turns `true` within minutes, then `first_verified_at` appears. After that,
`updated_at` advances every 5 minutes.

### When pages use it

Trust is held in memory by each server process; nothing in the database marks the table as
exact. A process earns it at every start, once the boot reconcile has run, the backfill is
complete and the one-time verification has passed. It drops trust:

- after 3 reconciles in a row that each repaired at least one row. Two clean reconciles in a
  row restore it;
- at once when ingest leaves a message without its sites: a failed site insert, a message
  stored without its sites, or any message insert error. It logs
  `read model untrusted until the next reconcile` with the reason. Trust returns after the
  next reconcile that started after the failure, so pages use the previous statements for at
  most about one interval;
- when the stored state is no longer complete and verified, for example after a rebuild.

A reconcile that repairs rows logs `cmi reconcile repaired N pair(s): a writer bypassed the read model`.
Something stored messages without recording their sites. On a single server running this
release that should not happen. Running two server versions that both write to one database at
the same time is not supported; if it happens, the pairs the older one leaves out are repaired
within one reconcile interval.

A [read-only server](configuration.md#read-only-mode) cannot repair anything. Every 5 minutes it
checks, read-only, that the writing server's saved state is complete and verified, that the
writer saved it within the last 10 minutes (two reconcile intervals, on the database clock), and
that the newest 2,000 messages pass the exact check. While all three hold it logs
`cmi trusted on this read-only server: region and scope message pages read channel_message_iatas`
and serves those pages from the table. Its trust ends on its own 10 minutes after the writer's
last save, unless a later check finds a newer one. A writer that is rolled back, stopped or keeps
failing stops saving, so read-only servers go back to the previous statements within 10 minutes
and log `cmi not trusted on this read-only server: the writer has not saved its state recently`.

### Turning it off

Set `readmodels.cmi.enabled: false` in `config.yaml` and restart; see
[Configuration](configuration.md#read-models). Every page is then served by the previous
statements. The table is still maintained, so turning it back on needs only a restart.

### Metrics and alerts

On the [admin listener](#metrics):

- `beacon_readmodel_trusted{model="cmi"}` is 1 while this process serves pages from the table.
- `beacon_readmodel_repaired_rows_total{model="cmi"}` should stay flat.
- `beacon_readmodel_watermark_age_seconds{model="cmi"}` is the time since the last finished
  reconcile, or on a read-only server since the writer last saved its state. It stays under
  600 s.

Suggested rules are in [Example alert rules](#example-alert-rules): repaired rows in 3
consecutive 5-minute windows, trusted at 0 for 20 minutes, and a watermark older than 15
minutes.

### Rolling back

Deploy the previous image. It ignores `channel_message_iatas`, and the table's rows are deleted
with their messages, so it does not grow stale rows. Leave the table and its indexes in place.

To roll forward again later, deploy the new image. Before it serves any page from the table,
the boot reconcile adds every site the older image stored, starting from the saved watermarks.
The previous statements serve meanwhile: about a second after a short rollback, a few minutes
after days. Nothing to do by hand.

Rebuild the table from scratch only if the verification keeps failing:

```sql
DELETE FROM background_state WHERE key = 'cmi';
TRUNCATE channel_message_iatas;
```

Then restart the server. It backfills and verifies again as on the first install.

A later release will drop `idx_channel_messages_channel` and `idx_channel_messages_sent_brin`.
Run this release for at least a week before upgrading to that one.

## Read models: packets by site

`packet_sites` holds one row for each packet and each site (IATA) that heard it, at that site's
latest hearing. Each row also copies the packet's payload type, route type, scope and first
hearing. The observation insert writes the row in the same statement, so a stored observation
always has its row. A background reconcile repairs the newest rows every 5 minutes, an hourly
audit refills one random older slice, and a front sweep every 30 seconds keeps the newest
index entries dense. On a large deployment (about 7.4 million rows) it takes about 1.6 GB:
heap 484 MB, primary key 285 MB, `idx_packet_sites_site` 419 MB, `idx_packet_sites_site_type`
353 MB, `idx_packet_sites_site_scope` 53 MB.

While the server process trusts the table, `/packets` pages with `iatas`, `iata`, `region` or
`regionId` (region pages) read it:

- one site: one range of the site's index;
- several sites: one range per site;
- payload and route types, up to 8 (payload, route) pairs: one exact range per site and pair;
- a `since`/`until` window, scopes, or more than 8 type pairs: bounded reads of each site range
  that continue, within the same request, until the page is full. If 8 reads do not fill the
  page, the previous release's statement answers that request, on the `api_slow` pool with a
  120 s statement limit (see [Slow region and message statements](#slow-region-and-message-statements)).

Unknown site codes are dropped by a cheap check first. Requests with `hashPrefix` never read
the table. A region page served from the table now returns `nextPageCursor`; see
[Exact page cursors](api-contract.md#exact-page-cursors). While the process does not trust the
table, region pages are served by the previous release's statement as before, on the `api_slow`
pool.

Each page is the previous statement's page, except where that statement loses rows: when a
site's packets are heard by many observers, it can end a page short, end a walk early (an
empty page with `hasMore: false`) or jump `nextCursor` past rows. The new page is full and
skips nothing. Packets tied on their site time come out by packet hash, descending.

On a production-size copy, the heaviest region pages went from seconds to under a second: all
561 sites for the last hour from 19.5 s to 0.3 s, and the 13 busiest sites for the last 75 minutes at
limit 200 from 4.5 s to 31 ms. A filter of rare types on a very sparse site can read a few
buffers more than before. An `until` well in the past often runs out of the read budget, so
the previous statement answers many of those pages, at the previous cost.

### Ingest cost

The site row makes each observation insert about 15-21% slower (mean 104 µs to 119-125 µs)
and adds about 37-53% WAL per stored observation (1,425-1,470 B to 2,008-2,188 B), measured
over 100,000 inserts on a scratch database. Re-sends of an observation still write nothing.

After the deploy, compare `InsertObservation` in `pg_stat_statements` (`mean_exec_time`, and
`wal_bytes / calls`) for the hour before and the hour after, and watch
`beacon_ingest_queue_depth`. `pg_stat_statements` is cumulative, so take this snapshot an hour
before the deploy, at the deploy and an hour after, and divide the differences:

```sql
SELECT now(), sum(calls) AS calls, sum(total_exec_time) AS exec_ms, sum(wal_bytes) AS wal_bytes
FROM pg_stat_statements WHERE query LIKE '-- name: InsertObservation :one%';
```

A growing ingest queue, or WAL beyond what you planned for, means rolling back.

### Installing it

The release adds migrations `042` to `045`; see [Before deploying a release](#before-deploying-a-release).
On the first start the server fills the table in the background:

1. It waits until every transaction that started before boot and holds a transaction id has
   finished (`packet_sites boot repair waits for transactions from before boot` while it
   waits), then runs one reconcile from the saved watermark.
2. It backfills the table newest observation first, in slices of 500,000 observation ids with
   a 0.1 s pause between them. The log shows `packet_sites backfill progress` lines, then
   `packet_sites backfill complete`. On a large deployment (about 766 million ids, 29.4 million
   observations) that is about 1,530 slices: about 3 minutes of pauses plus the fill work, so
   expect roughly 5 to 20 minutes and a few GB of WAL.
3. It runs a one-time verification. It first runs `VACUUM (ANALYZE) packet_sites` (a few
   minutes on a large deployment), then an exact check of two slices of 500,000 observation
   ids, the newest and one random older one, and a page-by-page comparison of region pages of
   the busiest recent sites with pages read straight from the observations. On success it logs
   `packet_sites first-time verification passed` and records the time, so later starts skip it.
4. It logs `packet_sites trusted: region packet pages read packet_sites`.

Until step 4, every region page is served by the previous release's statement, and users see
no difference. If the verification fails, the server logs
`packet_sites verification failed; region pages stay on the original statement` and tries again
every 5 minutes.

Check progress, read-only:

```sql
SELECT value, updated_at FROM background_state WHERE key = 'packet_sites';
SELECT pg_size_pretty(pg_total_relation_size('packet_sites'));
```

`complete` turns `true`, then `first_verified_at` appears. After that, `updated_at` advances
every 5 minutes.

### When pages use it

Trust is held in memory by each server process; nothing in the database marks the table as
exact. A process earns it at every start, once the boot reconcile has run, the backfill is
complete and the one-time verification has passed. It drops trust:

- at once when a reconcile or the hourly audit repairs any row: something bypassed the
  writer. Two clean reconciles in a row restore it. A repair logs
  `packet_sites reconcile repaired N row(s): a writer bypassed the read model` or
  `packet_sites audit repaired N row(s) below the watermark`;
- at once when an observation insert with its site row fails. Ingest never loses the
  observation: it logs `observation site row failed; storing the observation without it` and
  stores it without its row. Trust drops with
  `read model untrusted until the next reconcile` and the reason, and returns after the next
  reconcile that started after the failure, so region pages use the previous statement for at
  most about one interval;
- after 3 failed reconciles in a row, until one succeeds;
- when the saved state is no longer complete and verified, for example after a rebuild.

On a single server running this release, repairs should not happen. Running two server versions
that both write to one database at the same time is not supported; if it happens, the rows the
older one leaves out are repaired within one reconcile interval, and trust returns two clean
reconciles later.

A [read-only server](configuration.md#read-only-mode) cannot repair anything. Every 5 minutes it
checks, read-only, that the writing server's saved state is complete and verified, that the
writer saved it within the last 10 minutes (two reconcile intervals), and that the newest
20,000 observations pass the exact check. While all three hold it logs
`packet_sites trusted on this read-only server: region packet pages read packet_sites` and
serves region pages from the table. Its trust ends on its own 10 minutes after the writer's last
save, unless a later check finds a newer one. Otherwise it logs one of:

- `packet_sites not trusted on this read-only server: backfill or first verification not done`
- `packet_sites not trusted on this read-only server: the writer has not saved its state recently`
- `packet_sites not trusted on this read-only server: the newest observations fail the exact check`

### Turning it off

Set `readmodels.packet_sites.enabled: false` in `config.yaml` and restart; see
[Configuration](configuration.md#read-models). Every region page is then served by the previous
statement. The table is still maintained and swept, so turning it back on needs only a
restart. A later release removes the previous statement once the read model has run in
production.

### Metrics and alerts

On the [admin listener](#metrics):

- `beacon_readmodel_trusted{model="packet_sites"}` is 1 while this process serves region pages
  from the table.
- `beacon_readmodel_repaired_rows_total{model="packet_sites"}` should stay flat.
- `beacon_readmodel_watermark_age_seconds{model="packet_sites"}` is the time since the last
  finished reconcile, or on a read-only server since the writer last saved its state.
- `beacon_packet_sites_sweep_age_seconds` is the time since the last successful front sweep,
  and `beacon_packet_sites_sweep_plan_ok` is 1 while the sweep plans as index scans on the three
  time-ordered indexes. Without that plan the sweep marks no dead entries and the indexes bloat;
  the server logs `packet_sites sweep plan sets no dead-entry hints; the indexes will bloat`.
  Both are written only by the server that runs background jobs.
- `beacon_packet_sites_front_live{index}` is the entries the last sweep visited, and
  `beacon_packet_sites_bytes` the table's size with its indexes, hourly.
- `beacon_index_bloat_ratio` covers the four `packet_sites` indexes. Their baselines are the
  sizes of a fresh build, applied once the table holds 100,000 rows, so the ratio reads against
  a compact index rather than the size the server first saw.

Suggested rules are in [Example alert rules](#example-alert-rules): repaired rows in the last
10 minutes, trusted at 0 for 40 minutes, a watermark older than 15 minutes, a sweep older than
300 s or a sweep plan at 0, a bloat ratio of the three time-ordered indexes over 2.5 (warn) or
3, and the table over 2.5 GiB (warn; scale it for your deployment).

### Rolling back

Deploy the previous image. It ignores `packet_sites`, still has the previous release's
indexes, and the table's rows are deleted with their packets, so it does not grow stale rows.
Leave the table and its indexes in place.

To roll forward again later, deploy the new image. Before it serves any region page from the
table, the boot reconcile adds the rows written meanwhile, starting from the saved watermark;
the previous statement serves until then. Nothing to do by hand.

Rebuild the table from scratch only if the verification keeps failing:

```sql
DELETE FROM background_state WHERE key = 'packet_sites';
TRUNCATE packet_sites;
```

Then restart the server. It backfills and verifies again as on the first install.

## Slow region and message statements

Some requests still read a large part of the observations in one statement:

- a region `/packets` page whose bounded reads ran out of budget (a sparse filter such as a
  narrow window or rare payload types over busy sites);
- `/messages` with `iatas` and `since` or `scope`;
- while a read model is not trusted (its first fill, a repair, a failed verification, its kill
  switch), the previous statements that serve its pages: region `/packets`, channel message
  pages filtered by `iatas` or `scope`, and observer adverts until the payload-type backfill is
  done.

They run on their own pool, `api_slow`: 8 connections by default, the size `api_legacy` had
([`database.slow_pool_size`](configuration.md#database-pools-and-cost-guards)),
`statement_timeout=120s`, no parallel workers, not gated by the cost guards. When every
connection is busy a request waits at most 5 s and then answers `503` with `Retry-After: 5`,
without touching the other pools; `beacon_api_unavailable_total{reason="slow_pool_busy"}` counts
those, and the server logs `api: slow requests refused, every slow connection is busy` at most
once a minute. A statement that passes 120 s ends with a `500`; narrowing the request (fewer
sites, a wider window) avoids it.

During a read model's first fill every region or scope page goes through this pool; the default
of 8 gives those pages the capacity they had on `api_legacy`. Set `slow_pool_size` only to
override that.

Before this release these statements ran on `api_legacy` without a time limit, except the
exact-page-cursor form of the region statement, which ran on `api_custom` (35 s, gated by
`packets_region`).

Measured on a copy of a large production database (29.4 million observations, 561 IATAs), with
the pool's settings:

| Request | Warm | Cold cache |
|---|---:|---:|
| The busiest region (13 IATAs), three rare payload types | 3.1-3.3 s | 22.9 s |
| The 13 busiest IATAs, a one-hour window 60 hours back | 5.5 s | 23.3 s (first run) |
| Every IATA (561), a one-minute window | 50 s | 34 s |
| Every IATA (561), a one-hour window 120 hours back | 115 s | not measured |

Requests naming every IATA are not something the web or app send; the largest region on that
database has 22 IATAs. `beacon_db_time_seconds{pool="api_slow"}` and
`beacon_pool_acquire_seconds{pool="api_slow"}` show how busy the pool is.

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
| `api_legacy` | `beacon-api_legacy` | 8, `single` only | Server defaults. The rollback layout's only API pool. |
| `api_slow` | `beacon-api_slow` | 8 (`slow_pool_size`), not under `single` | Server defaults, with `statement_timeout=120s` and `max_parallel_workers_per_gather=0`. Only the [slow region and message statements](#slow-region-and-message-statements). |
| `api_custom` | `beacon-api_custom` | 8 (7 under `split`) | `plan_cache_mode=force_custom_plan`, `jit=off`, `max_parallel_workers_per_gather=0`, `statement_timeout=35s`, `idle_in_transaction_session_timeout=30s` |
| `api_cached` | `beacon-api_cached` | 5, `split` only | As `api_custom`, with `plan_cache_mode=force_generic_plan` |
| `ingest` | `beacon-ingest` | 6, or one per CPU above 6 | `plan_cache_mode=auto`, `jit=off`, no statement timeout: an ingest write waits out a lock rather than drop a packet |
| `maint` | `beacon-maint` | 4 | `plan_cache_mode=force_custom_plan`, `jit=off`, `max_parallel_workers_per_gather=0`. Background jobs, importers, backups and admin queries. |

The `single` layout opens only `api_legacy`, `ingest` and `maint`; the other layouts never open
`api_legacy`.

- **Headroom.** `SHOW max_connections;` must leave room for the total (26 by default on up to
  6 CPUs) plus every other client: `psql` sessions, backups, monitoring. If your deploy starts
  the new server before the old one stops, count both.
- **Checking.** Parallel workers carry their leader's `application_name`, so count client
  backends only:

  ```sql
  SELECT application_name, count(*) FROM pg_stat_activity
  WHERE application_name LIKE 'beacon-%' AND backend_type = 'client backend' GROUP BY 1;
  ```

  No pool should go above its size, `beacon-api_cached` should be absent under `custom_all`,
  and `beacon-api_legacy` absent except under `single`.
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
| `beacon_readmodel_trusted` | gauge | `model` | 1 while this process serves pages from the read model ([`cmi`](#read-models-channel-messages-by-site) or [`packet_sites`](#read-models-packets-by-site)), 0 while it serves the previous statements |
| `beacon_readmodel_repaired_rows_total` | counter | `model` | Rows the read-model reconcile repaired; above zero, a writer bypassed the model |
| `beacon_readmodel_watermark_age_seconds` | gauge | `model` | Seconds since the last finished reconcile of the read model (on a read-only server, since the writer last saved its state) |
| `beacon_packet_sites_sweep_age_seconds` | gauge | | Seconds since the last successful `packet_sites` front sweep; absent before the first |
| `beacon_packet_sites_sweep_plan_ok` | gauge | | 1 while the front sweep plans as index scans on its three indexes, 0 otherwise; checked at the first sweep, then hourly |
| `beacon_packet_sites_front_live` | gauge | `index` | Index entries written in the last two minutes that the last front sweep visited |
| `beacon_packet_sites_bytes` | gauge | | Total size of `packet_sites`, heap and indexes, hourly |
| `beacon_db_sequence_used_ratio` | gauge | `sequence`, `cycle` | Share of a sequence's usable values already handed out, 0 to 1, each minute. The usable range ends at the sequence's own limit or its column's type limit (`integer` 2,147,483,647), whichever is lower. `cycle="true"` marks a `CYCLE` sequence, whose ratio is its position, not used-up headroom. See [Sequence headroom](#sequence-headroom). |
| `beacon_api_unavailable_total` | counter | `reason`, `model` | `503`s a page answered because `api_slow` had no free connection (`reason="slow_pool_busy"`). `model` is the read model the page reads: `packet_sites`, `cmi` or `observation_payload_types`. |

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
      # The read-model rules don't apply with readmodels.cmi.enabled: false, where trusted stays 0.
      - alert: BeaconReadModelRepairing        # reconciles repaired rows in 3 consecutive 5-minute windows
        expr: min_over_time((increase(beacon_readmodel_repaired_rows_total{model="cmi"}[5m]) > bool 0)[15m:5m]) == 1
      - alert: BeaconReadModelUntrusted        # region and scope message pages on the previous statements
        expr: beacon_readmodel_trusted{model="cmi"} == 0
        for: 20m
      - alert: BeaconReadModelStale            # no finished reconcile (or writer save) for 15 min
        expr: beacon_readmodel_watermark_age_seconds{model="cmi"} > 900
      # The packet_sites trust rules don't apply with readmodels.packet_sites.enabled: false.
      # Install the two sweep rules only for the server that runs background jobs, never for a
      # read-only server: it never sweeps, so its sweep_plan_ok stays 0 and the plan rule would fire.
      - alert: BeaconPacketSitesRepairing      # a reconcile or audit repaired rows: a writer bypassed the model
        expr: increase(beacon_readmodel_repaired_rows_total{model="packet_sites"}[10m]) > 0
      - alert: BeaconPacketSitesUntrusted      # region packet pages on the previous statement
        expr: beacon_readmodel_trusted{model="packet_sites"} == 0
        for: 40m
      - alert: BeaconPacketSitesStale          # no finished reconcile (or writer save) for 15 min
        expr: beacon_readmodel_watermark_age_seconds{model="packet_sites"} > 900
      - alert: BeaconPacketSitesSweepStale
        expr: beacon_packet_sites_sweep_age_seconds > 300
      - alert: BeaconPacketSitesSweepPlan      # the sweep sets no dead-entry hints; the indexes will bloat
        expr: beacon_packet_sites_sweep_plan_ok == 0
        for: 5m
      - alert: BeaconPacketSitesBloatWarn
        expr: beacon_index_bloat_ratio{index=~"idx_packet_sites_site(_type|_scope)?"} > 2.5
      - alert: BeaconPacketSitesBloat
        expr: beacon_index_bloat_ratio{index=~"idx_packet_sites_site(_type|_scope)?"} > 3
      - alert: BeaconPacketSitesSize           # warn; scale 2.5 GiB for your deployment
        expr: beacon_packet_sites_bytes > 2.5 * 1024^3
      - alert: BeaconSlowPoolBusy              # region or message requests refused for want of a slow connection
        expr: sum(increase(beacon_api_unavailable_total{reason="slow_pool_busy"}[15m])) > 10
      # The sequence rules leave out CYCLE sequences, which wrap instead of running out.
      - alert: BeaconSequenceHalfUsed
        expr: beacon_db_sequence_used_ratio{cycle="false"} > 0.5
        for: 1h
        labels: {severity: warning}
        annotations: {summary: "Sequence {{ $labels.sequence }} has used over half of its values"}
      - alert: BeaconSequenceRunsOutIn90Days
        expr: predict_linear(beacon_db_sequence_used_ratio{cycle="false"}[7d], 90 * 86400) >= 1
        for: 6h
        labels: {severity: critical}
        annotations: {summary: "Sequence {{ $labels.sequence }} runs out within 90 days at its current rate"}
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

The four `packet_sites` indexes are never built fresh on a full table, so their first-seen size
would make a poor baseline. They start from the bytes per row of a fresh build instead, once
the table holds 100,000 rows; below that they have no ratio. A rebuild of one of them
re-baselines it from its measured size, as for any index.

The first run, and then one run a week, also logs `indexes with no scans since the last
statistics reset` with each unused non-unique index and its size. An index that stays on that
list for weeks is a candidate to drop; check that no rare job reads it first.

When `BeaconKeysetBloat` fires, rebuild that index as in
[Rebuilding the route keyset indexes](#rebuilding-the-route-keyset-indexes). The rebuild resets
its baseline, and the ratio drops back to about 1 on the next hourly run.

## Lookup-table indexes and the route stamp column

Migrations `047` to `052` drop six indexes that no statement's plan reads; every lookup they
served goes through a primary key or a table of a few hundred rows:

| Index | Table | Why it goes | Rebuild (seconds) |
|---|---|---|---|
| `idx_channel_iatas_iata` | `channel_iatas` | nothing looks up channel sites by IATA | `CREATE INDEX CONCURRENTLY idx_channel_iatas_iata ON channel_iatas USING btree (iata);` |
| `idx_node_neighbors_node` | `node_neighbors` | the primary key `(node_id, neighbor_id, iata)` serves every lookup by node | `CREATE INDEX CONCURRENTLY idx_node_neighbors_node ON node_neighbors USING btree (node_id, iata);` |
| `idx_transport_scopes_fingerprint` | `transport_scopes` | scopes are loaded whole | `CREATE INDEX CONCURRENTLY idx_transport_scopes_fingerprint ON transport_scopes USING btree (key_fingerprint);` |
| `idx_meshmapper_channel_members_fingerprint` | `meshmapper_channel_members` | channel pages read members by IATA through the primary key | `CREATE INDEX CONCURRENTLY idx_meshmapper_channel_members_fingerprint ON meshmapper_channel_members USING btree (key_fingerprint);` |
| `idx_region_iatas_iata` | `region_iatas` | regions are read by id; the IATA lookup reads a tiny table | `CREATE INDEX CONCURRENTLY idx_region_iatas_iata ON region_iatas USING btree (iata);` |
| `idx_trace_tags_first_heard` | `trace_tags` | trace pages walk the keyset index | `CREATE INDEX CONCURRENTLY idx_trace_tags_first_heard ON trace_tags USING btree (first_heard_at);` |

`idx_analytics_scope_sets_scope` stays: `/scopes/{name}` reads it twice, and without it a rare
scope's lookup becomes two full scans of the scope rollup table.

No older image needs the six indexes for its plans; rebuilding them after a rollback is
optional.

Migration `053` drops `known_routes.last_reconfirmed_at`. No statement of this release reads
it: route reconfirm stopped stamping it and its index went in earlier releases. The old values
are gone for good (no client ever saw them). Every older image needs the column back before it
starts, because its route evidence statement lists it and 2.0.7's reconfirm writes it:

```sql
ALTER TABLE known_routes ADD COLUMN last_reconfirmed_at timestamp with time zone DEFAULT now() NOT NULL;
```

This is a catalog change, not a rewrite (8 ms on a 10.5-million-row copy), and takes an
`ACCESS EXCLUSIVE` lock on `known_routes` for that long. Every route reads the time of the
`ALTER`; 2.0.7 then walks routes in arbitrary order on its first reconfirm cycle, which changes
nothing it deletes. To roll forward again, the new image's migration `053` is already recorded,
so drop the column by hand with `ALTER TABLE known_routes DROP COLUMN last_reconfirmed_at;`, or
delete the `053_drop_known_routes_last_reconfirmed_at.sql` row from `schema_migrations` so the
migration runs again.

## Sequence headroom

`beacon_db_sequence_used_ratio{sequence}` is, for every sequence in Beacon's schema, the share
of its usable values already handed out: 0 when unused, 1 when exhausted. The usable range ends
at the sequence's own maximum or at its column's type limit, whichever is lower, so an
`integer` column on a `bigint` sequence counts against 2,147,483,647. A descending sequence
counts from its top. A `CYCLE` sequence wraps to its start instead of running out, so it is
reported by position with `cycle="true"`, and the example rules leave it out; Beacon creates
none.

On a large deployment `channels_id_seq` read about 0.02 and every `bigint` sequence about 0.
`channels_id_seq` used to burn about 2,000 values a minute through upsert conflicts (fixed by
the channel write-through); the `BeaconSequenceRunsOutIn90Days` rule in
[Example alert rules](#example-alert-rules) would have caught that. An `integer` sequence
nearing 1 needs its column changed to `bigint`, a table rewrite to plan off-peak.

After deploying, check that `channels_id_seq` stays flat over an hour:
`delta(beacon_db_sequence_used_ratio{sequence="channels_id_seq"}[1h])` near 0.

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

It puts every API statement, the slow ones included, on one pool (`api_legacy`, 8 connections,
the server's own settings, no statement limit) and makes every guard family observe, whatever
`guards.enforce` says. The alternative is the previous server
image. It ignores migration 010; the `pg_stat_statements` extension stays installed and
harmless.

## CPU profiling

Bounded CPU captures on a running instance are described in [Profiling](profiling.md).
