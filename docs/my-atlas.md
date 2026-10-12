# My Atlas

A per-browser watchlist of up to twelve nodes, each shown as a card of recent activity and signal.
It is the last tab in the desktop row and under **More** on a phone; the URL is `?tab=MyAtlas`.
Hide it for a deployment with `VITE_DISABLED_TABS=MyAtlas` (see [Configuration](configuration.md)).

## What is stored, and where

Pins live only in the visitor's browser, under the localStorage key `beacon-my-atlas-v1`:
node ID, full public key, last known name, card order and the activity window (24h or 3d).
There is no account and no sync between browsers or devices; clearing site data removes the
collection. If storage is unavailable, the page says so and edits last for the visit.

Pins are keyed by the full public key. If a server reset changes a node's ID, the page looks the
key up again before loading anything and saves the new ID; it never adopts a different node at
the old ID. A node that cannot be loaded stays on the page and can still be removed.

## Search

**Add nodes** searches every region by name or hexadecimal public-key prefix (the region picker
does not apply to this tab). A search needs at least two characters, and a non-hex key is not sent
to the server; the card says which rule is holding a search back. Each result shows its key prefix
(the full key on hover) so two nodes with the same name can be told apart before adding one.

## Reading a card

Each card is the Analytics Signal row for one node, over the selected window:

- **Observations** — stored receptions of packets originating from that key. The card loads the
  latest 200; when those do not reach back to the start of the window, the tile says "latest 200"
  and the bars start at the oldest loaded reception rather than drawing empty hours the sample
  cannot speak for.
- **Mean SNR / Mean RSSI** — averages of the observers' last-hop measurements, with an hourly
  sparkline. The zero-RSSI / zero-SNR "no measurement" sentinel is excluded; a real zero SNR is
  included. These describe the receivers' side, not the node's radio health.
- **Active hours** — hours in the window with at least one reception.
- The freshness badge is the server's `stale` verdict; the client does not infer online/offline.
- **Heard by** swaps the tiles for the observers of the newest loaded packet, with when it was
  heard, and a link to open that packet in the analyzer; the button then reads **Analytics** to
  flip back. The card keeps its height either way. It is not lifetime reach.
- On a narrow card the action buttons drop under the name rather than crowding it.

Cards are reordered by dragging the grip at the top right of a card to another slot (mouse or
touch); the Left and Right arrow keys on a focused grip move it one slot. The order is saved with
the rest of the collection.

Every card polls once a minute while the tab is open, keeps polling through a failed refresh, and
pauses while the server is rate-limiting.
