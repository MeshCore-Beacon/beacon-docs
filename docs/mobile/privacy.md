# BEACON Mobile Privacy Policy

_Last updated: October 6, 2026_

BEACON Mobile ("the app") is an open-source iOS and Android client for Beacon, a
real-time analyzer for MeshCore radio mesh networks. This policy explains what
the app does and does not do with your information.

## The short version

- No account, no sign-in.
- No analytics, advertising, tracking or crash-reporting SDKs.
- The app does not access your location, contacts, photos, microphone or
  camera.
- Your settings stay on your device.

## What stays on your device

The app stores its settings locally, using the platform's standard app storage:
the Beacon servers you have added, your selected region, theme, language and map
preferences. This data never leaves your device unless you back up your device
through Apple or Google. Deleting the app deletes it.

## Network connections the app makes

To work, the app connects to:

1. **The Beacon server you choose.** By default this is `dev.meshcore.ca`; you
   can add or switch to any other Beacon server, including one you host. The app
   requests packet, node, observer and statistics data from it over HTTPS or
   WebSocket. Like any web server, that server sees your IP address and the
   requests made. A server you add yourself is run by its own operator, under
   that operator's own policies.
2. **Map tile providers.** Map imagery is loaded from
   [OpenFreeMap](https://openfreemap.org) and elevation data from the public
   AWS Terrain Tiles dataset. These providers see your IP address and the map
   areas requested, as with any map.

The app sends no personal information to these services beyond what any network
request carries, such as your IP address.

## Mesh data shown in the app

The app displays radio traffic that MeshCore devices broadcast publicly, as
collected by Beacon servers: node names, public keys, advertised positions,
packet routes, signal readings and messages on public channels. This is not
data about you as an app user. If you operate a MeshCore node and want data
about it removed from a Beacon server, contact that server's operator. For the
default server, open an issue at
[github.com/MeshCore-Beacon/beacon-docs/issues](https://github.com/MeshCore-Beacon/beacon-docs/issues).

## Children

The app is not directed at children and collects no personal information from
anyone.

## Changes

Updates to this policy will be published on this page with a new date.

## Contact

Questions about this policy: [MrAlders0n@smal.ca](mailto:MrAlders0n@smal.ca)
or [open an issue](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues).
