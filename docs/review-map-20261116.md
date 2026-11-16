# Current review map — November audit

Status: focused fixes are being qualified and published. This index is updated with final PR and CI links before the preview handoff.

All fix PRs target `dev`; there are no duplicate `dev1` targets. Topology and scope extensions are outside the strict dev-plus-fixes preview baseline.

| Component | Focus | Branch |
| --- | --- | --- |
| server | Return a structured error when JSON encoding fails | `codex/audit-json-response-20261116` |
| server | Coalesce cache-outage reads and recheck late misses | `codex/audit-cache-outage-20261116` |
| server | Bound boot backfill writes without losing progress | `codex/audit-backfill-budget-20261116` |
| server | Bound WebSocket control work and fail closed on missing regions | `codex/audit-ws-controls-20261116` |
| server | Notify clients when the global live queue drops events | `codex/audit-stream-gaps-20261116` |
| server | Reject oversized MQTT envelopes before queue admission | `codex/audit-mqtt-bounds-20261116` |
| server | Preserve known scopes when a neighbor report omits its list | `codex/audit-neighbor-presence-20261116` |
| server | Keep missing and invalid signal measurements out of averages | `codex/audit-signal-presence-20261116` |
| server | Validate TRACE evidence before resolving or promoting hops | `codex/audit-trace-evidence-20261116` |
| server | Pin route evidence cursors to the observed hash representation | `codex/audit-route-cursor-20261116` |
| server | Count the inserted advert in clock-history retention | `codex/audit-clock-window-20261116` |
| server | Include late hearings of older packets in node activity | `codex/audit-late-activity-20261116` |
| server | Keep rebuilding activity history from looking like zero traffic | `codex/audit-activity-readiness-20261116` |
| server | Expose optional artifact identity separately from API version | `codex/audit-build-identity-20261116` |
| web | Bound live-map worker updates on high-refresh displays | `codex/audit-map-frame-budget-20261116` |
| web | Coalesce chart resizes and cancel pending work on disposal | `codex/audit-chart-resize-20261116` |
| web | Show TRACE quality and original wire SNR evidence | `codex/audit-trace-evidence-20261116-web` |
| web | Keep copied route links tied to their evidence window | `codex/audit-route-links-20261116` |
| flutter | Bound mobile HTTP request lifetimes and account responses | `codex/audit-request-bounds-20261116` |
| flutter | Skip mobile reads after their screen has been superseded | `codex/audit-stale-reads-20261116` |
| web | Keep future-dated channel messages from pinning the conversation | `codex/audit-channel-order-web-20261116` |
| flutter | Keep future-dated channel messages from pinning the conversation | `codex/audit-channel-order-flutter-20261116` |
| docs | Bound Docker logs in every deployment template | `codex/audit-container-logs-20261116` |
| docs | Correct TRACE widths and performance claims in the design guide | `codex/audit-architecture-claims-20261116` |

Atlas rename compatibility remains its own existing [web #195](https://github.com/MeshCore-Beacon/beacon-web/pull/195).

The original combined audit drafts (server #296, web #196 and Flutter #21) will be closed with replacement links after the small PRs are published. Their source remains recoverable.

The previous optional collection stack is superseded by upstream native polling for this baseline. Historical feature branches are retained; no org base branch or production host is merged/deployed by this cleanup.
