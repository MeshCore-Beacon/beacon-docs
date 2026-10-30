# MeshMapper boundary snapshots

Beacon can display published MeshMapper polygons through its existing `iatas.<code>.borderFile` setting. This release uses reviewed files, with no additional background importer or per-packet network request.

Run the download tool from this repository, using the public API of the Beacon instance you administer:

```sh
python3 tools/download_meshmapper_borders.py --beacon-api https://dev.meshcore.ca/api/v1 --output borders-20260930
```

The output must be a new directory. The tool checks the CA and US [Zones API](https://wiki.meshmapper.net/zones-api/) catalogues against Beacon's known IATAs, downloads the corresponding region GeoJSON, and keeps only the exact `properties.code` member. Group collections are not combined; null geometry does not become a radius circle. Downloads are limited to 5 MiB and polygons to 100,000 vertices. The manifest records source URLs, ETags, file hashes and per-region failures. Inspect every error before installation. This command does not change Beacon configuration, the database or services.

Preserve existing manual borders. Review the downloaded shape and source, then configure only missing boundaries, for example:

```yaml
iatas:
  YKF:
    borderFile: borders-20260930/YKF.geojson
```

Keep any existing name, latitude and longitude in this entry. Relative paths resolve against Beacon's configuration directory. Containers need a read-only bind mount that makes these files available at that path. Beacon validates Polygon/MultiPolygon features at startup; stage the files with the exact candidate before replacing a working service. Invalid geometry must not replace the last working files. Border changes require a restart. Do not enable foreign-repeater classification merely to draw map boundaries.

Before deployment, retain the old configuration, runner/mounts and affected IATA metadata as well as a verified database backup. Configuration is imported into IATA records at startup: restoring files alone may leave newly imported metadata in the database. A rollback must restore the previous border/name/centre fields for affected IATAs without deleting new traffic rows. Invalidate the affected IATA/border cache entries or allow their expiry. Verify each `/api/v1/iatas/{iata}/border` response and the map layer after restart.

Refresh snapshots deliberately; respect the provider's minimum one-hour polling period and retain the previous snapshot. This tool is a one-shot download, not an automatic conditional-refresh service. Automatic refresh with last-known-good handling remains a later feature.

On 30 September the development Pi accepted 26 exact region polygons, about 1 MiB before Beacon normalization. Both country catalogues were considered; the installed matches were Canadian IATAs. Existing manual polygons were preserved. This is not a claim that every US region has a boundary, nor that a named scope proves a geographic crossing. Scope-name import remains independently configured.
