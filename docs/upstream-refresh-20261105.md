# Current development compatibility

**Later on 5 November:** Atlas landed on web dev at `38017d8`. The
[current review map](review-map-20261105.md) supersedes the morning PR counts and
targets below. It preserves the dated source/build qualification recorded here.

Checked 5 November 2026. Server and web main/dev remain at the v2.1.1 release
already incorporated into the current development candidates. Refresh the mobile
and documentation drafts before accepting the optional collection work.

| Repository | Current upstream | Development review |
| --- | --- | --- |
| beacon-server | `d0a55db` main/dev | Core #266/#267; optional intake #268/#269; scopes #290/#292; profiles #293 |
| beacon-web | `ccf7899` main/dev | Core #182/#183; optional telemetry #184/#185; scopes #190/#192; profiles #193 |
| beacon-docs | `008f988` dev, `3b3e48b` main | Core/roadmap #43, optional collection #44 |
| beacon-flutter-app | `0d58d8b` main/dev, 2.1.1 | Optional BLE/Wi-Fi collection #11 |

All fourteen server/web drafts were freshly checked as mergeable with passing
required checks. They retain the latest released ancestry; no server/web code
refresh is needed. Older overlapping drafts remain historical review lanes,
not additional features to merge in date order.

## Connection and mobile compatibility

The [API contract](api-contract.md) and [configuration guide](configuration.md)
now include the outgoing WebSocket byte budget, shared IPv6 /64 connection cap,
optional `/ws-ticket` access and Safari/iOS compression behavior. Default send
capacity is 1 MiB/s with an 8 MiB burst. These limits are independent of the
development candidate's inbound control/subscription bounds.

Flutter #11 includes upstream ticket acquisition, reconnect grace, sortable
last-heard node data and incremental list loading. The viewer closes its live
feed in the background while an explicitly opted-in collection session keeps
its separate BLE/Wi-Fi and Android foreground-service lifecycle. A connection
ticket is not collector enrollment or radio authorization.

The telemetry draft is `2.1.1+4`. Analysis, tests and native Android CI qualify
the source/build; physical companion polling, unlock/reconnect, overnight
collection and iOS still require their device acceptance checks. No physical
device test is implied by this refresh.

## Preview and collection policy

The preview continues to serve server `c564a985` and web `745fde38`,
`2.7.1-n30nex.1`, based on upstream 2.1.1 plus the development features.
Its public build metadata was checked on 5 November. The full November 2
qualification covered Atlas, 24h Topology, scope overlays, MeshMapper profiles,
100 public assets, both source archives, both brokers and six retained telemetry
histories. That is dated qualification, not a new November 5 runtime audit.

Flutter is the intended polling client. Keep the legacy Pi polling worker and
RemoteTerm disabled. Retain the shared intake for enrollment, report submission
and history; stopping the old RF worker does not retire the Flutter backend.
No new RF polling or host deployment is part of this repository refresh.

Core Atlas/Topology remain independent of collected telemetry. Optional mobile
collection remains a separate acceptance lane and does not implement generic
phone packet forwarding. See [the forwarding boundary](mobile-packet-forwarding.md).

## Operator handoff

Review core server/web first, then the optional intake/mobile and scope/profile
layers according to the desired release scope. Keep org PRs draft until operator
acceptance. Repository updates do not merge or deploy dev, dev1 or live.

The active preview recovery helper is
`evidence/upstream-refresh-20261102/deploy-preview.py rollback`, checkpoint
`upstream-refresh-20261102T224834Z`. It restores the previous application pair,
keeps schema 64/history and disabled radio services, and preserves the Flutter
intake. Consult its deployment handoff before recovery; older mixed rollback
recipes have different service assumptions.

Earlier reports such as [29 October](atlas-topology-refresh-20261029.md) and the
[project roadmap](project-roadmap.md) retain their dated evidence. This page
supersedes their current-source and legacy-poller status, not their recorded tests.
