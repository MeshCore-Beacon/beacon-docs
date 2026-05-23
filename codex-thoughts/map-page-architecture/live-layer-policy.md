# Live Layer Policy

The Tower map treats live traffic as an explicit overlay, not as the default map
state.

## Defaults

- Live is off on first load.
- Static nodes, observers, and high-confidence routes may render without Live.
- Packet comets, route glows, observer auras, message bubbles, and live-follow
  movement require Live to be on.

## Safety Rules

- Do not animate ambiguous or unresolved paths.
- Do not animate stale events outside the accepted live window.
- Do not zoom or pan the map in response to packet traffic.
- Prefer frame drops over UI jank under load.
- Keep live visuals separate from route and node source truth.

## Subscription Rules

The map should attach live handlers only while Live is enabled. Turning Live off
must clear transient overlays and detach map-specific listeners without affecting
the packet list's WebSocket behavior.

## Future Controls

- Payload type filters.
- Channel filters when channel visibility exists.
- Optional observer-only activity aura.
- Optional message bubbles for sanitized decoded public messages.

VCR playback and scrub controls stay out of scope.
