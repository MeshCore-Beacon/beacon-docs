# Post-2.0 UI and node telemetry batch

Requested 2 October 2026. Work stays experimental on `n30nex-test`, based on
upstream server `af20beb` / web `0924260` plus Atlas, Topology and exact-route
evidence. Review requests and the daily automation remain on hold.

## Versioned delivery

- **2.0.1 fixes**: Topology left-drag pan/right-drag orbit/wheel zoom, stable
  region labels, route-window refresh, one-screen layout and retained fullscreen;
  remove drag-mode buttons and explanatory sections; compact Routes and Traces.
- **2.1.0 features**: full node detail page with existing-data graphs; observer
  card sparklines; Atlas telemetry where a full-key-linked observer already
  provides it; visible node icons during live map traffic with reception glow.
- Use annotated **`v2.0.1-n30nex.1`** and **`v2.1.0-n30nex.1`** milestone tags on
  contribution forks after validation. These are experimental prerelease tags,
  not upstream stable releases. Bigger user-facing features advance 2.x; fixes
  advance 2.0.x. Server/web major-minor alignment remains the release policy.

## Requested changes and acceptance

| Area | Work | Required proof |
|---|---|---|
| Topology camera | Left mouse pans, right mouse changes the 3D angle, wheel zooms; remove mode buttons; retain touch/keyboard and fullscreen | Mouse buttons, context-menu suppression only on canvas, touch/pinch, keyboard and region focus/isolation |
| Region labels | Anchor labels to projected scene positions; fade/shrink or omit collisions instead of moving them above the scene | Dense mesh and zoomed-out screenshots, hit targets follow visible labels |
| Route window | Fetch fresh route data on a changed window and show the resulting graph | Different time windows produce different route evidence; switching back refreshes; bounded requests remain |
| Layout | Fit the Topology view into available screen space; Live Activity expands inside its allotted panel | Desktop and phone viewport containment, no page scrolling required to reach activity |
| Routes/Traces | Remove verbose explanations; compact trace rows while retaining tag/type/time/count/path/signal and keyboard inspection | Bilingual layout, narrow screens and existing drill-down behavior |
| Map live mode | Keep node icons visible by default, optionally dim them; reuse the existing observed-hop glow | Toggle, selection focus, live pulse and style changes; do not fabricate RX/TX events |
| Node detail | Add an Open full detail action and shareable full-page view, using existing node/report/neighbour data | Full-key identity, back/reload, sample bounds, loading/errors and graphs with real available samples |
| Observer cards | Sparklines for packet, battery, uptime and noise-floor series where supported | Reuse existing queries; preserve gaps/resets and match units/count definitions |
| Atlas telemetry | Show available telemetry for the exact node/observer identity | Never attach telemetry by display name or short prefix; absent data stays absent |

## Telemetry investigation and feasible design

An empty guest password is permission to authenticate to a repeater; it does not
make its directed response ciphertext public. MeshCore's repeater sends responses
with the requesting peer's ECDH shared secret. The Public/hashtag channel keys
apply to group messages, not that peer exchange. A passive MQTT observer cannot
derive the peer secret from two public keys or from the guest password.

Sources: [MeshCore identity exchange](https://github.com/meshcore-dev/MeshCore/blob/main/src/Identity.h),
[repeater response/login code](https://github.com/meshcore-dev/MeshCore/blob/main/examples/simple_repeater/MyMesh.cpp),
[payload format](https://github.com/meshcore-dev/MeshCore/blob/main/docs/payloads.md).

The [solar bot](https://github.com/n30nex/Canadaverse-MeshCore-Discord-Bot) already
uses an authenticated radio poller and stores decoded measurements. Its public
snapshot deliberately strips credentials and node keys, so it is not by itself an
identity-safe telemetry source for Beacon.

Implementation ladder:

1. Display the telemetry Beacon already receives in observer status, only when
   the full public key maps that observer to the displayed node. Reuse existing
   time-bucket queries and show volts/units, freshness and gaps.
2. Add a separately configured collector export from the solar bot/companion
   after a concrete schema is agreed: full target key, poller identity, receive
   time, request correlation, source and typed decoded measurements. Private keys
   and passwords stay on the poller. Beacon does not start network-wide RF polls.
3. Automatically enroll and validate that ingest, deduplicate repeated samples, reject invalid
   values, bound retention and preserve source attribution before storing node
   telemetry. Decode LPP only after the transport is decoded/authenticated.
4. Public-channel telemetry can be parsed as unverified reported values; a sender
   name is not a cryptographic node identity and must not overwrite trusted data.

Battery percentage, panel watts, energy and runtime are not inferred from voltage
alone. Guest permissions and available sensors differ by firmware and node. Keep
that distinction in the data contract rather than filling absent metrics.

## Deployment boundary

The user approved fresh preview history while preserving the old database intact.
The existing `beacon_dev` database is never reset or relabelled. Its private dump
was restored successfully and verified on and off the Pi before cutover. New core
history uses `beacon_post21_preview_20261002`; community telemetry belongs to the
independent `beacon_collector_preview` database. The 1.4 handoff and official
production hosts remain outside this experiment.

## Collector worldwide configuration and congestion policy

The user authorized a standalone USB/BLE collector, initially tested with the Pi
RemoteTerm radio and YKF - 1W Hespeler by full key. The radio's firmware identifies
as Heltec Wireless Paper; the user confirmed this is the intended RemoteTerm unit.
The user later assigned this radio to the collector continuously. RemoteTerm stays
stopped and disabled until the user asks for its return; its original contacts
and route/configuration recovery journal are preserved privately on the Pi.

The collector config chooses the Beacon instance URL and MQTT host/port/TLS,
credentials by environment variable, and topic namespace. Nothing is hardcoded to
Canadaverse. Each repeater gets a configurable **1–72 hour** interval. Attempt times
are persisted before RF, including failed polls, so restarts never trigger an early
retry. Status and sensor telemetry alternate across intervals when both are wanted;
there is only one data request per repeater interval (plus required guest login).

Default cadence is six hours. Requests are staggered. Queue depth and measured
local RX+TX airtime over at least a minute gate transmission; busy/unknown state
causes deferral, not catch-up bursts. Deferral can make the actual gap longer than
the configured interval. Local schedules cannot coordinate different collectors or
Beacon instances; shared polling leases are a future server integration gate.

Collector reports use an independent Ed25519 signing key. Enrollment is automatic through a Beacon challenge signed by both the companion
and collector. No operator authorization or per-client allowlist is required.
HTTPS is the default delivery, with optional MQTT. Radio private keys and repeater
passwords never leave the local device/host. This proves key control, not hardware
attestation or independent sensor truth. Preserve source attribution, validate
signatures, destination, timestamps, replay IDs and measurement bounds, and apply
per-IP API limits plus per-radio report limits.

## Updated collector acceptance, 2 October evening

The end result is an easy My Atlas repeater card with battery sparklines and
optional environmental telemetry. Setup lists contacts already on the user's USB
or BLE companion, allows per-repeater hidden password/admin entry, chooses any
Beacon instance, and starts polling. No manual client approval is part of the
flow. Direct HTTPS avoids broker credentials; MQTT remains optional.

First discovery uses flood, then uses learned routes; failures wait for the next
1–72 hour interval. Explicit telemetry request permission bytes include external
sensors where access permits. Keep channel 2 and actual units. Cards use 30 days
of collector history, bounded to 500 recent reports, so 72-hour polling remains
useful. Telemetry-only cards can be pinned by full key before an advertisement.

The first blank-guest Hespeler test returned no usable reading. The user then
selected the solar bot's six configured repeaters and authorized their Pi-local
admin-password aliases. Across bounded tests and normal operation, Hilltop,
Weaver, Royal City, Starkey and Royal Relay have returned correlated readings.
Reservoir has not returned a usable response. Hilltop supplied channel-2
12.4 C, 64% humidity and 985 hPa, plus 3.99 V battery; later readings may differ.
Royal City has multiple real samples with a longer gap. Hilltop’s next normal
hourly poll arrived through the public service, and all five telemetry sparklines
were verified in the deployed Atlas card.

Temporary test exceptions were confined to a private harness; the distributed
collector retains normal cooldown and congestion rules. Its latest SDK handling
subscribes before a fast reply can arrive and checks the exact response tag before
using decoded telemetry. No admin configuration commands or invented readings are
part of the flow.

## Private repository and independent intake service

The user explicitly chose **private repository + separate service**. GitHub
`n30nex/Beacon-Telemetry-Collector` is private; the existing license is unchanged.
`gateway/` is a separate Go process with its own PostgreSQL role/schema and optional
MQTT listener. It has no Beacon core package or migration dependencies and refuses
to initialize over a core schema. The Python companion collector remains separate
from the intake process as well.

Route `/api/v1/node-telemetry/*` to this gateway before the ordinary Beacon API.
Authentication is automatic dual-key enrollment, with no per-user operator approval.
Trusted proxy addresses are explicit; arbitrary forwarded headers do not affect
rate limits. Health checks include database access. The frontend treats telemetry
as an optional API so the new pages can be integrated without requiring the service.

Accepted prototype samples were copied byte-for-byte into the dedicated database
before removing the experimental core table. The unpublished embedded-gateway
server commits are preserved locally and must never be pushed as public Beacon
history. The public server candidate descends from their clean parent instead.

Release alongside a future Beacon version (possibly 3.0) is still planning. Before
broad release, finish multi-collector per-repeater polling coordination, operator
abuse/revocation controls, long-running delivery/reconnect tests and packaged USB/BLE
onboarding. Key possession is not hardware or sensor attestation, and private
source does not itself enforce RF behavior.
