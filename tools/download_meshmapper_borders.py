"""Download a reviewed border snapshot; never edit Beacon's config or database.

Usage: python3 tools/download_meshmapper_borders.py --beacon-api https://dev.meshcore.ca/api/v1 --output borders-20260930
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024
MAX_VERTICES = 100_000


def read_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Beacon-boundary-snapshot/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Response exceeds 5 MiB")
        return json.loads(data), response.headers.get("ETag")


def select_border(document, code):
    """Select an exact member, never a group's entire collection or a radius circle."""
    if document.get("type") != "FeatureCollection":
        raise ValueError("Expected FeatureCollection")
    matches = [f for f in document.get("features", []) if f.get("properties", {}).get("code") == code]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous region feature")
    feature = matches[0]
    geometry = feature.get("geometry")
    if geometry is None:
        return None
    if feature.get("type") != "Feature" or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Expected polygon geometry")
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    vertices = 0
    if not polygons:
        raise ValueError("Empty geometry")
    for polygon in polygons:
        if not polygon:
            raise ValueError("Empty polygon")
        for ring in polygon:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("Unclosed polygon ring")
            for position in ring:
                vertices += 1
                if vertices > MAX_VERTICES or len(position) != 2:
                    raise ValueError("Invalid or oversized coordinates")
                if any(type(value) not in (int, float) or not math.isfinite(value) for value in position):
                    raise ValueError("Non-finite coordinate")
                if not (-180 <= position[0] <= 180 and -90 <= position[1] <= 90):
                    raise ValueError("Coordinate outside geographic bounds")
    return feature


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beacon-api", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--countries", nargs="+", choices=("CA", "US"), default=["CA", "US"])
    args = parser.parse_args()
    address = urllib.parse.urlsplit(args.beacon_api)
    if address.scheme not in ("http", "https") or address.username or address.password or address.query or address.fragment:
        parser.error("Use a public API base URL without credentials, query or fragment")
    if args.output.exists():
        parser.error("Output must be a new directory; existing snapshots are preserved")
    known, _ = read_json(args.beacon_api.rstrip("/") + "/iatas")
    codes = {row["iata"] for row in known}
    zones = {}
    for country in dict.fromkeys(args.countries):
        catalogue, _ = read_json("https://meshmapper.net/get_zones.php?country=" + country)
        for zone in catalogue["zones"]:
            code = zone["code"]
            if code in codes and re.fullmatch(r"[A-Z0-9]{2,6}", code) and zone.get("country") == country and zone.get("has_boundary"):
                zones[code] = zone
    args.output.mkdir(parents=True)

    def download(item):
        code, zone = item
        # Catalogue-controlled URLs are not arbitrary download destinations.
        address = urllib.parse.urlsplit(zone["url"])
        if address.scheme != "https" or address.hostname != code.lower() + ".meshmapper.net" or address.username or address.password or address.port not in (None, 443):
            return {"code": code, "error": "Unexpected region URL"}
        url = "https://" + address.hostname + "/get_geojson.php"
        try:
            document, etag = read_json(url)
            feature = select_border(document, code)
            if feature is None:
                return {"code": code, "source": url, "status": "no_boundary"}
            raw = (json.dumps(feature, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            filename = code + ".geojson"
            (args.output / filename).write_bytes(raw)
            return {"code": code, "source": url, "etag": etag, "file": filename, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        except (OSError, ValueError, KeyError, TypeError) as error:
            return {"code": code, "source": url, "error": str(error)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(download, sorted(zones.items())))
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "beacon_api": args.beacon_api, "countries": args.countries, "entries": entries}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": sum("file" in row for row in entries), "errors": sum("error" in row for row in entries), "manifest": str(args.output / "manifest.json")}))


if __name__ == "__main__":
    main()
