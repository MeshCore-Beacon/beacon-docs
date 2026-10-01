# Optional MeshMapper scope discovery

Beacon can periodically read the [public Scopes API](https://wiki.meshmapper.net/scopes-api/) to discover additional transport scope names for configured regions. Manual `scopes` remain authoritative. This does not supply channel decryption keys or per-repeater records.

```yaml
meshmapper:
  scopes:
    enabled: true
    refresh_interval: 1h
    sources:
      YOW: https://yow.meshmapper.net/get_scopes.php
```

The IATA must already occur in `regions[].iatas`. Set the exact published regional HTTPS URL; credentials, query strings, other hosts and redirects are rejected. The response must identify the same region and exactly one zone. Group catalogues are rejected because they cannot assign each scope/count to individual member regions. No API key is required.

The default is disabled. Refresh defaults to one hour and accepts 5 minutes through 24 hours. One source is considered every 15 seconds, keeping requests below four per minute per process. Multiple deployments share MeshMapper's per-IP allowance. ETags reduce transfer, HTTP 304 advances the last successful check, and 429 pauses all sources until the later of the normal retry time and `Retry-After`. The pause survives restarts. HTTP 503 also honors that source's `Retry-After`.

Responses are limited to 64 KiB and 64 names per source, with at most 16 sources. Names are case-sensitive and at most 128 bytes before Beacon's usual `#` normalization; existing `#`/`$` prefixes are retained. Zero-count monitored names are kept. Imported matching candidates are limited to their source IATA; manual keys keep their existing global applicability. Manual keys keep their existing first-match priority, including when an imported name has the same short code. Multiple matching imported names remain unresolved when no manual key matches.

Migration 042 stores the last validated response, validator and check/retry timestamps in PostgreSQL. Saving a response and its scope identities is atomic. Timeouts, invalid responses and HTTP errors retain the prior catalogue; startup restores it without HTTP. A successful empty response removes that source's active imported membership. Removing or disabling a source takes effect on restart. Scope identities referenced by historical records are retained. Adding an imported name to the manual list promotes it to manual ownership.

Operator logs under `component=meshmapper.scopes` show the IATA, source, active name count, source generation time, last successful check, next attempt and last error. An empty last error means the latest request succeeded; a zero checked time means no successful response has been stored. A 304 retains the original source generation time because MeshMapper excludes that timestamp from its ETag. Cached names may be old during an outage; use the check/error fields to assess freshness.

Catalogue counts remain source metadata. They never create Beacon packet counts, observer associations or node defaults. Actual packet-code matching supplies those associations through the existing ingest path. New names affect subsequent packets; no historical scan is started. Channel message tags and import-status UI are separate follow-ups. An invalid saved catalogue is logged and excluded until a valid refresh; other sources and manual keys still load. Database access failures remain startup errors. Disabling the importer restores manual-only matching. Previously imported identities remain visible in `/scopes` and historical records; visibility does not imply an active matcher candidate.

Validate and back up PostgreSQL before applying the migration. Rollback to an older server must restore its matching pre-import database and configuration as well as its binary; an older matcher does not understand imported-only ownership or regional candidate limits.
