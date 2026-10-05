# Observer directory

Status: pending [server PR #212](https://github.com/MeshCore-Beacon/beacon-server/pull/212),
not yet deployed. The existing `/observers` endpoint remains unchanged.

## Requests

`GET /api/v1/observers/directory?iata=YVR&sort=traffic&limit=50`

| Parameter | Contract |
|---|---|
| `sort` | `traffic` (default) or `name`. |
| `limit` | Positive integer, default 50, capped at 200 per page. No directory-wide row cap. |
| `cursor` | Nonnegative integer offset, default 0. Pass the returned `nextCursor`. |
| `since`, `until` | Positive epoch milliseconds, inclusive start and exclusive end, rounded down to UTC hours. Window must be 1 hour through 31 days; `until` cannot be in the future. Required when cursor is nonzero. |
| `iata`, `iatas` | Case-insensitive IATA or comma-separated IATAs. Nonempty `iatas` takes precedence. |
| `regionId`, `region` | Expand region ID or slug and union with explicit IATAs. ID takes precedence. An empty region without explicit IATAs matches nothing. |
| `name` | Case-insensitive display-name substring using SQL ILIKE semantics (`%` and `_` are wildcards). |
| `type`, `broker`, `scope` | Exact observer type, broker membership or transport scope name. URL-encode `#` in scopes. |
| `status` | `online` or `offline`. |

All filters apply before ordering and pagination. Type, broker, name and scope
are limited to 200 UTF-8 bytes each. At most 200 IATAs are accepted after region
expansion and before deduplication. Unknown/repeated parameters return 400.

The first page defaults to `until = floorToUtcHour(now - 95 minutes) + 1 hour`,
and `since = until - 24 hours`. This excludes the latest 35 to 95 minutes;
these are hourly analytics counts, not live packet counters.

For every continuation, repeat all filters and sort, pass the first response's
`windowStart` as `since` and `windowEnd` as `until`, and use `nextCursor`:

```text
/api/v1/observers/directory?iata=YVR&sort=traffic&since=1767225600000&until=1767312000000&cursor=50&limit=50
```

## Response

Items contain the existing `ObserverSummary` fields plus required nullable
`observationCount`. Optional names, type, radio and empty scopes may be omitted.

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
  "coverage": {"status": "complete", "expectedHours": 24, "completeHours": 24, "partialHours": 0, "missingHours": 0},
  "maxObservationCount": 1200,
  "observerTypes": ["meshcore-ha", "meshcoretomqtt"]
}
```

Timestamps are epoch milliseconds. `items` and `observerTypes` are always arrays.
A terminal page has `hasMore: false` and no `nextCursor`. A cursor past the end
returns an empty terminal page.

Counts sum `analytics_hourly_observer_identity` for the requested window. They
represent stored hearings per observer, deduplicated across brokers, not MQTT
messages or the observer detail's cumulative presence counter. No raw observation
scan is needed. Directory membership uses current observer IATA; counts include
only observations in selected IATAs, or all IATAs without a location filter.
Broker and scope filter membership, not the source of counted observations.

When every requested hour is complete, missing observer analytics mean **0**.
If any hour is partial or missing, every count and `maxObservationCount` is
**null**, and `effectiveSort` is `name`. Coverage is `complete` when all hours are
complete, `partial` when some are complete or partial but not all complete, and
`unavailable` when all are missing. Absent rollup records count as missing.
Never render null as zero.

Traffic order is count descending, then lowercase display name ascending using
PostgreSQL `C` collation, then UUID ascending. Name order uses the last two keys.
Missing names sort as empty strings. Online status means last status or last
seen within five minutes at request time.

`maxObservationCount` covers the whole filtered result, including in name order.
It is 0 for an empty complete result. `observerTypes` includes all distinct
nonempty types matching every filter except the type filter itself, independent
of pagination.

## Consistency and client behavior

Each request reads current data. There is no stored snapshot, expiry, new table
or snapshot capacity limit. Keeping the window fixed avoids hourly window drift,
but analytics corrections and metadata changes can still move rows between
pages, causing repeats or skips. Counts, coverage, type choices and maximum can
also change. This endpoint is a browsing list, not a consistent export.

Use one infinite query keyed by server, filters, window and sort. A query change
starts from page one and discards stale responses. Preserve server order, allow
one continuation in flight, deduplicate by observer UUID, and stop on
`hasMore=false` or a missing/repeated cursor. Fetch again near the scroll end,
including when the viewport is not filled. No per-row count requests or separate
top-observers request is needed.

For stable bars while scrolling, retain the first page's maximum and clamp
count/max to [0,1]; reset on refresh. Render unavailable when count or maximum is
null, and zero width when the maximum is zero. If `effectiveSort` changes between
pages as coverage changes, restart from page one rather than mixing orderings.
Live status badges can update separately. Refresh the list to update membership
or order; selection and deep links continue to use UUIDs.

Invalid parameters and unknown regions return 400. Database failures return 500;
retain loaded rows and offer retry. Successful pages and store errors send
`Cache-Control: no-store`; database reads have a five-second operation budget.

Probe `/api/v1/observers/directory?limit=1` for compatibility. A supported server
returns the response above. Older servers may return 404, or the legacy detail
route's 400 with message `failed to parse observer UUID`. Other errors do not
prove lack of support. Use an explicitly limited legacy fallback or request a
server upgrade; do not assume the old `/observers` route honors new parameters.
