# Observer directory

The observer list with traffic counts for a time window. It shipped in server 2.0.2. The
`/observers` endpoint is unchanged.

## Requests

`GET /api/v1/observers/directory?iata=YVR&sort=traffic&limit=50`

| Parameter | Contract |
|---|---|
| `sort` | `traffic` (default) or `name`. |
| `limit` | Positive integer, default 50, capped at 200 per page. No directory-wide row cap. |
| `cursor` | Nonnegative integer offset, default 0. Pass the returned `nextCursor`. |
| `since`, `until` | Positive epoch milliseconds, inclusive start and exclusive end, used exactly as sent. The window must be positive and at most 31 days; `until` cannot be in the future. Both are required when cursor is nonzero. |
| `iata`, `iatas` | Case-insensitive IATA or comma-separated IATAs. Nonempty `iatas` takes precedence. |
| `regionId`, `region` | Expand region ID or slug and union with explicit IATAs. ID takes precedence. An empty region without explicit IATAs matches nothing. |
| `name` | Case-insensitive display-name substring using SQL ILIKE semantics (`%` and `_` are wildcards). |
| `type`, `broker`, `scope` | Exact observer type, broker membership or transport scope name. URL-encode `#` in scopes. |
| `status` | `online` or `offline`. |

All filters apply before ordering and pagination. Type, broker, name and scope
are limited to 200 UTF-8 bytes each. At most 200 IATAs are accepted after region
expansion and before deduplication. Unknown/repeated parameters return 400.

The first page defaults to `until` = the request time and `since` = `until` minus
seven days. A `since` sent without `until` runs to the request time, and an `until`
sent without `since` starts seven days before it.

For every continuation, repeat all filters and sort, pass the first response's
`windowStart` as `since` and `windowEnd` as `until`, and use `nextCursor`:

```text
/api/v1/observers/directory?iata=YVR&sort=traffic&since=1767225600000&until=1767312000000&cursor=50&limit=50
```

## Response

Items contain the existing `ObserverSummary` fields plus `observationCount`, which
is always a number. Optional names, type, radio and empty scopes may be omitted.

```json
{
  "items": [
    {"id": "00000000-0000-0000-0000-000000000001", "displayName": "North receiver", "iata": "YVR", "status": "online", "observationCount": 1200}
  ],
  "nextCursor": 1,
  "hasMore": true,
  "generatedAt": 1767314100000,
  "windowStart": 1767225600000,
  "windowEnd": 1767312000000,
  "sort": "traffic",
  "effectiveSort": "traffic",
  "coverage": {"status": "partial", "expectedHours": 24, "completeHours": 22, "partialHours": 2, "missingHours": 0},
  "maxObservationCount": 1200,
  "observerTypes": ["meshcore-ha", "meshcoretomqtt"]
}
```

Timestamps are epoch milliseconds. `items` and `observerTypes` are always arrays.
A terminal page has `hasMore: false` and no `nextCursor`. A cursor past the end
returns an empty terminal page.

Counts are stored hearings per observer in the window, deduplicated across brokers,
not MQTT messages or the observer detail's cumulative presence counter. A whole UTC
hour inside the window that has a complete rollup is read from
`analytics_hourly_observer_identity`. Every other hour is counted from the
observations still retained for it: an hour not rolled up yet, a partial one, and
the slices at the window's two edges. The process that ingests also keeps recent
counts in memory and uses them for the newest hours, reading only the last minutes
from the table. Directory membership uses the observer's current IATA; counts
include only observations in the selected IATAs, or all IATAs without a location
filter. Broker and scope filter membership, not the source of counted observations.

Counts are always numbers. An observer with nothing counted in the window has `0`,
`maxObservationCount` is never null, and `effectiveSort` always equals `sort`.
Where history is missing, a count covers only what is still stored, so read
`coverage` before treating a low number as quiet.

`coverage` counts the UTC hours the window touches. An hour is complete when it
lies wholly inside the window and its rollup is complete. It is partial when it is
not served from a complete rollup but has a rollup record or counted observations.
It is missing when it has neither. `status` is `complete` when every hour is
complete, `partial` when at least one hour is complete or partial, and
`unavailable` otherwise. A window that does not start and end on the hour, the
default one included, has edge hours that are never complete, so `partial` is the
normal answer.

Traffic order is count descending, then lowercase display name ascending using
PostgreSQL `C` collation, then UUID ascending. Name order uses the last two keys.
Missing names sort as empty strings. Online status means last status or last
seen within five minutes at request time.

`maxObservationCount` covers the whole filtered result, including in name order.
It is 0 when nothing matches. `observerTypes` includes all distinct
nonempty types matching every filter except the type filter itself, independent
of pagination.

## Consistency and client behavior

Each request reads current data. There is no stored snapshot, expiry, new table
or snapshot capacity limit. Keeping the window fixed stops it drifting between
pages, but late observations, analytics corrections and metadata changes can still move rows between
pages, causing repeats or skips. Counts, coverage, type choices and maximum can
also change. This endpoint is a browsing list, not a consistent export.

Use one infinite query keyed by server, filters, window and sort. A query change
starts from page one and discards stale responses. Preserve server order, allow
one continuation in flight, deduplicate by observer UUID, and stop on
`hasMore=false` or a missing/repeated cursor. Fetch again near the scroll end,
including when the viewport is not filled. No per-row count requests or separate
top-observers request is needed.

For stable bars while scrolling, retain the first page's maximum and clamp
count/max to [0,1]; reset on refresh. Draw zero width when the maximum is zero.
Live status badges can update separately. Refresh the list without `since` and
`until` to get a new rolling window and update membership or order; selection and
deep links continue to use UUIDs.

Invalid parameters and unknown regions return 400. Database failures return 500;
retain loaded rows and offer retry. The database read has a five-second budget, and
a read that runs out of time answers 503 with `Retry-After`. Successful pages and
store errors send `Cache-Control: no-store`.

To decide whether a server has the directory, read `GET /api/v1/info` (see
[Server info](api-contract.md#server-info)). The directory shipped in server 2.0.2
and `/info` in 2.0.3, so Beacon Web treats a `serverVersion` of 2.0.2 or later as
supported, and a malformed version as supported too. A 404 on `/info` means the
server predates the directory. Any other failure is an error: show it with a
retry, not a fallback. On an unsupported server use an explicitly limited legacy
fallback or request a server upgrade; do not assume the old `/observers` route
honors new parameters. The Flutter app requests the directory directly and relies
on its version gate, which also reads `/info`.
