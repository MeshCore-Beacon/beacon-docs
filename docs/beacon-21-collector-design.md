# Beacon 2.1: Atlas and Collector planning scratchpad

> **Primary roadmap:** [Beacon 2.1–2.2](../ROADMAP.md), adopted 4 October 2026,
> controls priorities and agreed requirements. It includes Atlas/Topology plus an
> initial Beacon agent and working MQTT setup in 2.1.0; telemetry/collection
> expansion in 2.1.1–2.1.9; and complete Atlas, Topology refinement, bug fixes and
> performance in 2.2. Mobile BLE and Windows/Linux USB collectors share the hourly
> maximum, three-hop requirement and flood/learned-route/fallback policy. The
> hardware enforcement and qualification caveats below remain important. Earlier
> “proposed,” USB-first, open-hop-threshold and provisional-release statements in
> this dated scratchpad are historical, not competing primary instructions.

3 October 2026. This is a source-backed planning note, not a deployment instruction
or an accepted upstream release contract. The supplied discussion proposes Atlas
and Collector as the 2.1 focus, USB/Wi-Fi first, and MQTT forwarding. Maintainer
thoughts and the future private repository handoff are still pending. No access,
repository transfer, MQTT switch, RF policy change or remote-control permission is
inferred from that discussion.

## Scope and sequence

| Milestone | Proposed scope | Status |
|---|---|---|
| **2.1** | My Atlas with useful battery/environment graphs; a separate Collector with simple contact selection and conservative polling | Proposed release focus. USB preview exists; wider rollout still has gates below. |
| **2.1.x** | Compatibility, correctness and usability fixes for the accepted 2.1 scope | Patch releases; no automatic jump to a new major. |
| Later transport work | BLE qualification and browser collectors | BLE code exists but is not fully hardware-qualified. It need not block the USB/TCP first release. |
| **2.5, provisional** | Authenticated observer/repeater console or MQTT control | Exploration only. Read-only telemetry enrollment must not grant administration. |
| Future firmware | Reuse the agreed contract in observer firmware | An interoperability goal, not a prerequisite or a firmware-change request. |

Topology and the other experimental pages remain available in the Pi preview.
Their later integration and the broader CoreScope parity backlog are separate
from the proposed Atlas/Collector release cut. The previous possible 3.0 pairing
was exploratory; this discussion proposes a 2.1 path, conditional on its gates.
Work remains on `n30nex-test`, with existing PRs in draft and no review pings.

Keep requirements specific to Beacon. A MeshMapper change belongs in the plan
only when a concrete Beacon use case and a minimal API requirement are identified.
This document is the shared scratchpad; no new bot, account or task is required.

## Existing decisions to preserve

- Any compatible Beacon instance can receive data; Canadaverse remains the initial
  preview destination. Users select contacts by full public key and can provide a
  guest/password/admin credential locally. The operator does not approve each client.
- User-selected intervals remain **1–72 hours**, with six hours the normal default.
  A timeout, restart, reconnect or manual refresh must not bypass the minimum.
- Initial discovery floods; successful learned routes are reused. Channel-2 LPP
  readings retain their channel, type and units. Missing readings stay missing.
- Intake is a separate service/database. Collector source remains private under
  its existing license. Repository privacy is not an RF enforcement mechanism.
- The user-facing result is a pinned Atlas card with real readings, history,
  freshness and gaps. Full-key identity, collector attribution and optional API
  compatibility remain necessary for independent Atlas integration.

## What MeshCore HA actually does

Inspected public source, pinned rather than relying on moving release notes:

- Stable **v2.10.0**, `0f99da64be8a0ab6eacd4e87246f2a70e624f2b6`.
- Beta **v3.0.0-beta**, `e9e60552f671e6c6d765c4826c18839ac54f22ce`.
  The beta tag is updated in place; this SHA identifies the reviewed snapshot.

The stable implementation starts with a **20-credit** shared bucket and refills
one credit per **120 seconds**: about **30 requests/hour**, with an initial burst
allowance. Login and data requests consume credits separately. A depleted bucket
skips work; some stable polling paths count that skip as a failure. Credits are
held in memory, so this is not a persistent, network-wide polling lease.
Sources: [bucket](https://github.com/meshcore-dev/meshcore-ha/blob/0f99da64be8a0ab6eacd4e87246f2a70e624f2b6/custom_components/meshcore/rate_limiter.py),
[constants](https://github.com/meshcore-dev/meshcore-ha/blob/0f99da64be8a0ab6eacd4e87246f2a70e624f2b6/custom_components/meshcore/const.py#L206),
[polling callers](https://github.com/meshcore-dev/meshcore-ha/blob/0f99da64be8a0ab6eacd4e87246f2a70e624f2b6/custom_components/meshcore/coordinator.py#L1295).

The inspected beta's governed policy separates a flat per-radio budget into:

| Lane | Burst credits | Refill credits/hour |
|---|---:|---:|
| Flood | 5 | 20 |
| Direct | 20 | 120 |
| User messages | 10 | 60 |

These are HA's numbers, **not adopted Beacon defaults or measured airtime limits**.
Adding tracked nodes shares that budget instead of growing it. Governed denial
means deferral rather than a node failure. It persists lane credits and node
schedules, exposes the next eligible time, and applies longer jittered backoff to
flood failures. New beta installations are assigned governed mode; an existing
entry without the setting still resolves to legacy. The module's opening comment
and earlier beta release text are less precise than those current constants.
Sources: [policy and costs](https://github.com/meshcore-dev/meshcore-ha/blob/e9e60552f671e6c6d765c4826c18839ac54f22ce/custom_components/meshcore/traffic.py#L59),
[new/existing defaults](https://github.com/meshcore-dev/meshcore-ha/blob/e9e60552f671e6c6d765c4826c18839ac54f22ce/custom_components/meshcore/const.py#L211),
[persistence](https://github.com/meshcore-dev/meshcore-ha/blob/e9e60552f671e6c6d765c4826c18839ac54f22ce/custom_components/meshcore/coordinator.py#L883),
[policy tests](https://github.com/meshcore-dev/meshcore-ha/blob/e9e60552f671e6c6d765c4826c18839ac54f22ce/tests/test_traffic.py#L233).

Beacon should use the budgeting/deferral ideas while retaining its own stronger
per-target minimum. HA's routed retry spacing and immediate path-healing attempts
are unsuitable defaults for an hourly telemetry collector. Its debounced state
save also does not replace Beacon's requirement to persist the attempt before RF.

**Traffic credits and authentication tokens solve different problems.** HA's
inspected MQTT uploader creates a cached, expiring, optionally audience-bound JWT
using a private key exported from the connected companion. That authenticates a
broker connection; it is not permission to transmit on RF or proof of sensor truth.
Beacon's current challenge signing can keep the radio private key on the device.
An MQTT credential design should retain that property instead of copying HA's
private-key export mechanism.
Source: [beta MQTT signing and export path](https://github.com/meshcore-dev/meshcore-ha/blob/e9e60552f671e6c6d765c4826c18839ac54f22ce/custom_components/meshcore/mqtt_uploader.py#L592).

This was source inspection, not hardware qualification or a security audit of HA.
HA is MIT licensed; any future code reuse must retain the required notices. This
planning change copies no HA implementation into Beacon.

## Proposed Collector design

### Radio traffic

Keep one serialized polling loop. Gate it with the existing persisted target
schedule and local queue/airtime checks, then add a shared **per-radio** budget
with separate flood and direct credits. Both login and data requests count; local
USB statistics reads and resending an already-collected HTTPS/MQTT report do not
create new RF polls. Persist debits before transmission, preserve them through
restarts, and avoid a full startup/catch-up burst. A second configuration must not
open the same radio and obtain a second independent budget.

Budget exhaustion, busy airtime and unavailable airtime are **deferred** states,
with a reason and next eligible time. They do not label a repeater offline. Real
timeouts or rejected credentials remain distinct. Repeated failures get bounded
backoff and an explicit paused/retry state; the chosen nominal interval is not a
promise that congestion can never delay a sample.

For a wider cohort, obtain an atomic **per-repeater lease before RF** from the
Collector service. Scope it to full radio/collector/repeater keys and the service
instance; preserve the cooldown even if the client crashes or the poll fails.
Two clients must not both poll the same repeater at once. A server ingest quota
only rejects a report after transmission and cannot provide this guarantee.
Instance-local leases also do not coordinate separate Beacon operators: any
cross-instance authority or federation must be an explicit later decision.

Hop policy remains open. A maximum permitted **known route length** can defer
long direct paths. It does not cap how far a flood propagates, and scope labels
are not automatically RF hop limits. Confirm firmware support and behavior before
promising a hard flood cap; do not silently change a user's radio configuration.
Use conservative flood budgets and real airtime observations in the meantime.

Exact credit rates, burst sizes, retry backoff and any hop threshold need agreement
and measured preview results. HA's constants are a reference, not proof they suit
this mesh, RF profile or a worldwide rollout.

### Connections and delivery

Qualify **USB and TCP to a Wi-Fi companion first**. TCP is the network transport
to the radio; it is distinct from MQTT delivery to the server. The MeshCore Python
SDK documents serial, TCP and BLE factories, but our current Collector exposes
only serial/BLE. TCP setup, validation, reconnect and physical testing are work
still to do. Treat a raw companion TCP endpoint as a trusted-LAN connection until
its authentication/encryption is verified; do not expose it publicly.
Source: [official SDK connection documentation](https://github.com/meshcore-dev/meshcore_py/blob/main/README.md#connecting-to-your-device).

Keep the existing signed report schema and automatic enrollment. MQTT forwarding
already has an optional adapter and the separate `beacon/telemetry/v1/<collectorKey>`
namespace. A proposed MQTT-first release needs automatic, expiring broker
credentials restricted to that client's publish topic, a broker-side verification
contract, revocation and an intake acceptance receipt. A broker PUBACK alone is
not proof that Beacon validated/stored a report. Reuse the saved reading for
delivery retries and deduplicate it across transports.

The current preview continues to use HTTPS. No broker configuration or delivery
default changes were made for this discussion. HTTPS remains useful for enrollment
and a fallback; selecting MQTT as the release default is an open decision.

Remote command/control is a separate future permission surface. Telemetry upload
credentials must not allow subscriptions or publications that execute commands.
Before any control feature: explicit device-owner opt-in, narrowly allowed
commands, signed short-lived requests, replay protection, revocation, audit records
and a local disable switch. No remote shell, password upload or administration
channel is part of the proposed 2.1 telemetry scope.

### Atlas and operator visibility

Keep setup focused: connect a companion, select saved repeaters, choose access and
interval, and pin the resulting full-key cards. Show battery and available channel-2
environment graphs with units, source and last successful sample. A single sample
is a reading; history requires subsequent successes. Do not infer battery percentage
or manufacture points for missed polls.

Add concise collector health: connected/disconnected, waiting for its interval,
deferred for airtime/budget/another collector, login denied, timed out, delivered,
or waiting for server acceptance. Show the next eligible poll and last delivery
without exposing passwords, radio private keys or enrollment tokens. Atlas must
remain useful when the optional Collector service is absent.

## Work packages and acceptance

| Order | Focused package | Completion evidence |
|---|---|---|
| 1 | Atlas integration and setup/health contract | Standalone Atlas against released Beacon; no required collector core migration; sample/gap/error states in English/French. |
| 2 | Per-radio flood/direct budget and explicit deferrals | Every RF path charged; exhausted/busy states send nothing; crashes, clock changes and restarts cannot refill early; existing 1–72-hour target contract passes. |
| 3 | Shared repeater leases | Concurrent clients: only one grant; expiry/crash/failure retain cooldown; fresh keys/re-enrollment cannot bypass radio/target quotas; service outage does not create a fleet of uncoordinated polls. |
| 4 | TCP companion and USB packaging | Exact supported firmware, saved-contact selection, identity change, disconnect/reconnect and exclusive radio ownership; physical Windows/Linux USB and LAN TCP results. |
| 5 | MQTT ingestion/acceptance and automatic credentials | Wrong topic/audience/key and expired/replayed messages rejected; reconnect/outbox delivery deduplicated; denial/revocation visible; no extra RF to retry upload. |
| 6 | Small closed alpha | Named cohort, agreed defaults, measured airtime and sample success, pause/recovery instructions; expand only after the earlier gates. |

These are proposed packages, not claims of completed implementation. Keep changes
small and independently reviewable. No new feature package was deployed while
writing this note, and the wider parity backlog is retained.

## Decision log for the next discussion

| Question | Suggested starting point | Still needed |
|---|---|---|
| What ships as 2.1? | Atlas + a bounded Collector alpha | Agreement on acceptance and whether wider distribution is gated to a later patch/feature release. |
| Which transport? | USB and LAN TCP qualification first | Supported Wi-Fi firmware/device; BLE/browser later coverage. |
| MQTT default? | Reuse one signed payload; HTTPS enrollment; automatic scoped broker credentials | Broker/verifier owner, topic ACL and intake-receipt contract. |
| How much RF? | Preserve 1–72h target intervals; add independent flood/direct caps | Agreed measured budgets and failure policy; no copied HA defaults. |
| How far? | Optional known-route policy, conservative flood handling | Supported firmware controls and measured coverage; no claimed hard cap yet. |
| Multiple collectors? | One instance grants target leases before polling | Explicit handling of separate Beacon instances. |
| Repository handoff? | Keep current private repository/license until the destination is verified | Actual invitation/permissions and chosen migration path. |

Existing limits: signing proves key possession, not hardware attestation; a
cooperative client policy does not stop unrelated or modified radios transmitting.
As of the latest preview check, five selected repeaters have real readings.
Reservoir's target was corrected from `bbeb6123` to SolarWatch's `9292f89e` identity;
the first corrected poll timed out and is not counted as a successful sample.
