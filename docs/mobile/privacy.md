# BEACON Mobile Privacy Policy

_Last updated: November 15, 2026_

BEACON Mobile ("the app") is an open-source iOS and Android client for Beacon, a
real-time analyzer for MeshCore radio mesh networks. This policy explains what
the app does and does not do with your information.

## The short version

- An account is optional. The app works fully without one.
- No analytics, advertising, tracking or crash-reporting SDKs.
- The app does not access your location, contacts, photos, microphone or
  camera.
- Your settings stay on your device.

## Optional accounts

Some Beacon servers offer accounts. You never need one to view packets, nodes, maps or statistics.
If you choose to sign in, you do it on the server operator's web page, and the app then holds a sign-in
token for that server.

- **What the server stores about you:** your username, display name, email address, a hash of your
  password (never the password itself), and your signed-in devices with a label, the IP address and
  app or browser name they connected from, and when they were last used. This is held by the
  operator of that server, under that operator's policies. The server sends you email to confirm your
  address, reset a password, and tell you when a new app signs in.
- **What the app stores:** the sign-in token, kept in the platform's secure storage (the iOS Keychain or
  Android Keystore) and removed when you sign out. The app does not keep your password.
- **Ending it:** you can sign out of any device and delete your account in the app's profile screen or on
  the web. Deleting removes your user record, sessions and everything attached to the account from that
  server. A sign-in lasts at most a year, and you can end it earlier from the devices list.

### If the server turns on more features

A server operator can add more features for signed-in users. Each one is held by the operator of
that server, and deleting your account removes it.

- **Synced Atlas.** Your Atlas (up to twelve pinned nodes and observers, their names, the tiles you
  chose and the activity range) is stored on the server so your web and app lists match.
- **Telemetry requests.** You can ask the server to have a repeater polled. The server stores which
  repeater you asked for. If you enter a guest password, it is stored encrypted and shared, sealed,
  with the observer that polls the repeater. Never enter an admin password.
- **Alert rules.** The server stores the alerts you set for radios on your Atlas and when each last
  fired.
- **Push token.** If the server sends alerts by push, the app registers a push token with the server
  and with Apple's or Google's notification service. The token is tied to your account and signed-in
  device, is never shown back to you, stops being used when that app sign-in ends, and is deleted with your
  account. Alerts can name a radio and carry only a short sentence about it. Alerts can instead
  be sent by email to your account's address.
- **Sign-in through a portal.** Some servers sign you in through the MeshMapper portal. The server
  then stores only the username and display name the portal gives it, and no password or email
  address.

## What stays on your device

The app stores its settings locally, using the platform's standard app storage:
the Beacon servers you have added, your selected region, theme, language and map
preferences. This data never leaves your device unless you back up your device
through Apple or Google. Deleting the app deletes it.

## Network connections the app makes

To work, the app connects to:

1. **The Beacon servers you add.** The app has no built-in server: it only
   connects to servers whose address you enter, including ones you host. It
   requests packet, node, observer and statistics data from it over HTTPS or
   WebSocket. Like any web server, that server sees your IP address and the
   requests made. Each server is run by its own operator, under that operator's
   own policies.
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
about it removed from a Beacon server, contact that server's operator.

## Children

The app is not directed at children. It collects no personal information itself; an
account, if you create one, is held by the server operator.

## Changes

Updates to this policy will be published on this page with a new date.

## Contact

Questions about this policy: [MrAlders0n@smal.ca](mailto:MrAlders0n@smal.ca)
or [open an issue](https://github.com/MeshCore-Beacon/beacon-flutter-app/issues).
