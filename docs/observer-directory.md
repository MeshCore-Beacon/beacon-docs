# Observer directory

Status: pending [server PR #212](https://github.com/MeshCore-Beacon/beacon-server/pull/212),
not yet deployed. Web and Flutter can use this contract once server support is available.
The existing `/observers` endpoint and its cursor semantics are unchanged.

## Requests

`GET /api/v1/observers/directory`

First page example:

```text
/api/v1/observers/directory?iata=YVR&sort=traffic&limit=50
```

| Parameter | Contract |
|---|---|
| `sort` | `traffic` (default) or `name`. |
| `limit` | Positive integer, default 50, capped at 200. This limits a page, not the directory. |
| `since`, `until` | Positive epoch milliseconds, inclusive start and exclusive end. Both round down to UTC hours. Rounded window must be 1 hour through 31 days; `until` cannot be in the future. |
| `iata`, `iatas` | Case-insensitive IATA or comma-separated IATAs. Nonempty `iatas` takes precedence over `iata`. |
| `regionId`, `region` | Expand a region ID or slug to IATAs and union with explicit IATAs. Region ID takes precedence over slug. An empty region with no explicit IATAs matches nothing. |
| `name` | Case-insensitive display-name substring match, using SQL ILIKE semantics (`%` and `_` are wildcards). |
| `type`, `broker`, `scope` | Exact observer type, broker membership or transport scope name. URL-encode `#` in scope names. |
| `status` | `online` or `offline`. |

All filters apply before ordering and pagination. Type, broker, name and scope
values are limited to 200 UTF-8 bytes each. At most 200 IATAs may be supplied after
region expansion and before deduplication. Unknown or repeated parameters fail
with 400 instead of being ignored.

The default `until` is `floorToUtcHour(now - 95 minutes) + 1 hour`, the end of the
latest hour eligible for rollup. Default `since` is 24 hours before `until`.
Counts therefore exclude the latest 35 to 95 minutes and are not live counters.
Explicit windows can include unrolled hours, but those have unavailable counts.

Continue using only the returned snapshot and cursor, plus an optional page size:

```text
/api/v1/observers/directory?snapshot=2cb04420-719d-4b8c-9c74-2c1b9c43fdc3&cursor=50&limit=50
```

The snapshot is an opaque UUID. The cursor is a nonnegative integer position,
not an observer ID or timestamp. Treat it as opaque and use `nextCursor` exactly;
do not compute offsets. A nonzero cursor without a snapshot fails with 400.
Continuation rejects all filter, sort and window parameters, even unchanged ones.
The page size may change between requests. Omitting cursor with a snapshot
replays its first page. A cursor past the end returns an empty terminal page.

## Response

Example shape; timestamps and identifiers are illustrative:

```json
{
  "items": [
    {
      "id": "00000000-0000-0000-0000-000000000001",
      "displayName": "North receiver",
      "observerType": "meshcoretomqtt",
      "iata": "YVR",
      "status": "online",
      "radio": "910.525,62.5,7",
      "scopes": ["#test"],
      "observationCount": 1200
    }
  ],
  "nextCursor": 1,
  "hasMore": true,
  "snapshot": "2cb04420-719d-4b8c-9c74-2c1b9c43fdc3",
  "generatedAt": 1767314100000,
  "expiresAt": 1767315000000,
  "windowStart": 1767225600000,
  "windowEnd": 1767312000000,
  "sort": "traffic",
  "effectiveSort": "traffic",
  "coverage": {
    "status": "complete",
    "expectedHours": 24,
    "completeHours": 24,
    "partialHours": 0,
    "missingHours": 0
  },
  "maxObservationCount": 1200,
  "observerTypes": ["meshcore-ha", "meshcoretomqtt"]
}
```

Each item contains the existing `ObserverSummary` fields plus a required nullable
`observationCount`. Optional names, type, radio and empty scopes may be omitted.
All timestamps are epoch milliseconds. `items` and `observerTypes` are arrays,
including for an empty result. On the last page `hasMore` is false and
`nextCursor` is omitted.

`observationCount` sums stored observation counts from
`analytics_hourly_observer_identity` over `[windowStart, windowEnd)`. These are
packet hearings per observer, deduplicated across MQTT brokers. They are not
unique packets across observers, MQTT message counts, or the observer detail's
cumulative presence counter. The directory performs no raw-observation scan.

Directory location membership uses each observer's current IATA at snapshot
creation. Within that listing, counts include only observations in the selected
IATAs; without a location filter, they include all IATAs. Broker and scope filter
observer membership, not the source of counted observations. Observers deleted
before snapshot creation are excluded even if historical analytics remain.

Every requested hour must be marked complete to report any count. For complete
coverage, an observer without matching analytics has count **0**. If any hour is
partial or missing, every count and `maxObservationCount` is **null**, and
`effectiveSort` is `name`, including when `sort` requested `traffic`. Coverage is
`complete` when every hour is complete, `partial` when at least one hour is
complete or partial but not all complete, and `unavailable` when all are missing.
Missing includes hours with no rollup status record. Never render null as zero.

Traffic order is count descending, then lowercase display name ascending using
PostgreSQL `C` collation, then observer UUID ascending. Name order uses the latter
two keys. Missing names sort as empty strings. Clients must preserve server order.

`maxObservationCount` is the maximum across the entire filtered snapshot, even
with name ordering. It is 0 for a complete empty result. Use count/max for bars
when max is positive, zero-width bars when both are zero, and an unavailable
state when either is null. It never changes between pages.

`observerTypes` contains every distinct nonempty type matching all active filters
**except the type filter itself**. It is independent of pagination and can populate
the type selector without loading every observer.

## Lifetime and errors

Rows, metadata, status, counts, coverage, ordering, type choices and maximum are
frozen for 15 minutes from `generatedAt`. Online means a last status or last seen
within five minutes at creation. Ingestion, renames, moves, offline transitions,
rollup corrections and observer deletion do not alter existing pages.
Snapshots persist in PostgreSQL and work across server replicas and restarts.
Identical first-page criteria may reuse a snapshot until expiry, irrespective of
page size. A first-page reload therefore need not produce fresh metadata.

| Status | Meaning and client action |
|---|---|
| 400 | Invalid parameters or unknown region. Correct the request; do not retry unchanged. |
| 404 | An older server without this endpoint (for a valid default probe). |
| 410 | Snapshot absent or expired. Discard its pages and restart from page one. |
| 503 | Snapshot creation busy or capacity exceeded. `Retry-After: 5`; retain existing rows and retry with backoff. |
| 500 | Store/query failure. Retain existing rows and offer retry. |

Errors use the existing `APIError` envelope. Successful pages and store errors
send `Cache-Control: no-store`. Creation has a five-second database operation
budget, a global maximum of 1,024 active distinct snapshots, a 128 MiB combined
stored JSON budget (items plus metadata), and a 16 MiB items limit per snapshot.
The stored JSON budget excludes table/index overhead and PostgreSQL working memory. Capacity failure returns an error; it never truncates the listing.
Expired snapshots are removed on subsequent creation. New searches can consume
capacity, so debounce name input and avoid requesting on every keystroke.
Existing snapshots remain readable when creation capacity is exhausted.

## Web and Flutter integration

Use one infinite query keyed by server, location, window, sort and all filters.
Default to traffic order. On any query change, cancel or ignore previous responses
and start a new snapshot; never append old-query pages. Do not combine this API
with a separate top-observers request or fetch counts per row.

Fetch the next page near the scroll end, including when the viewport is not yet
filled. Allow only one continuation in flight, deduplicate by observer ID, and
stop on `hasMore=false`, a missing cursor or a repeated cursor. Keep loaded rows
on transient next-page errors and retry the same snapshot/cursor. On 410, replace
the whole list with a new first page; never append a replacement snapshot.

Live status badges may update separately, but must not reorder rows or change
snapshot filter membership/counts. Selection and deep links use observer UUIDs;
detail requests may return 404 for an observer deleted after the snapshot formed.

For compatibility, probe `/api/v1/observers/directory?limit=1`. Support means a
200 response with the snapshot contract. Older servers may return 404, or the
legacy detail route's 400 with message `failed to parse observer UUID`. Recognize
that specific response only; arbitrary 400/500/503 responses do not prove lack of
support. Keep the legacy listing as an explicitly limited fallback or show an
upgrade-required state. Do not send new parameters to the old `/observers` route
and assume they were honored. Retry capability detection after server upgrades.
