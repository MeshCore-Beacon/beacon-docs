# Basic Atlas and future phone packet forwarding

Basic Atlas and Topology belong to the core release. They must remain usable
without a collection gateway, a connected companion, or collected repeater
telemetry. Existing observer activity/status is part of Beacon's ordinary read
API; it is separate from the optional repeater-polling telemetry service.

## Current implementation boundary

Atlas pins use full node public keys and recover the server's current node ID.
Its activity and Heard by views use ordinary node/observer/packet endpoints.
Topology consumes the bounded node/route snapshot and the existing live packet
stream. Neither needs to know whether an accepted observation originally came
from a fixed observer or a future mobile receiver.

The optional Flutter collection draft currently polls selected repeaters and
uploads attributed telemetry. That is not passive raw-packet forwarding. The
core API does not yet advertise a supported mobile raw-packet upload capability.
Do not treat the telemetry endpoint as a generic packet endpoint or enable a
mobile upload button against a server that has not explicitly offered it.

## Requirements for the later packet-ingest feature

1. **Explicit opt-in and discovery.** Negotiate a versioned, optional packet-ingest
   capability through the selected Beacon instance. An absent capability means
   unavailable. Keep polling, passive capture and viewer-only operation separate.
2. **Client and instance binding.** Reuse automatic enrollment where appropriate,
   with scoped, renewable credentials and signed, replay-resistant submissions.
   Key possession is not proof of physical hardware or of an RF reception.
   Radio admin passwords and private keys remain on the user's device. Do not
   distribute shared MQTT publishing credentials in the app.
3. **A receiver record, not a claimed origin.** Attribute uploads to a separately
   identified mobile receiver. Derive packet identity and advertised node identity
   on the server. Do not let a client impersonate an existing fixed observer or
   mark an arbitrary message as verified Public text.
4. **Preserve evidence.** Validate frame length, header/path widths and payload
   structure with the normal ingest decoder. Preserve the raw frame and distinguish
   measured signal fields from absent values. A decoded companion notification
   without a raw frame is not automatically equivalent to an observer capture.
5. **Separate clocks and retries.** Record capture time and server receipt time;
   define the accepted age/skew and offline-replay policy before enabling queues.
   A durable capture ID makes upload retries idempotent without collapsing a
   genuinely later reception of the same packet into the earlier reception.
6. **Bound work before accepting it.** Cap payload/batch sizes, queue depth, age
   and submission rate. An acceptance receipt must reflect successful intake,
   not merely a local MQTT publish call. Reuse Beacon's ingest/read-model path
   after validation rather than creating a second Atlas-specific packet store.
7. **Keep background operation deliberate.** BLE/Wi-Fi capture needs physical
   screen-off, reconnect, unlock and notification-action qualification. Use the
   app's existing background controls, with capture/queue/delivery counters that
   distinguish this mode from repeater polling. Precise phone location is not a
   prerequisite for basic Atlas and must not become an implicit upload.

## Acceptance before enabling the capability

Verify real companion-to-server-to-Atlas delivery; invalid enrollment and replay
rejection; duplicate-upload versus later-reception behavior; missing signal data;
clock skew and delayed delivery; bounded outage recovery; and normal Beacon
operation when the optional intake is unavailable. Confirm that accepted mobile
observations reach the same API and live-stream projections used by basic Atlas
and Topology. Keep software fixtures, actual RF evidence and physical background
qualification distinct in the release record.

These are the integration requirements for the future feature, not a statement
that packet upload, hardware attestation or offline replay is already implemented.
