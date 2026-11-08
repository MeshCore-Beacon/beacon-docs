# My Atlas

A per-browser watchlist of up to twelve radios, each shown as a card of recent activity and signal.
A card can follow a node, an observer, or a node that is also an observer. The tab sits just before
**Analytics**, in the desktop row and under **More** on a phone; the URL is `?tab=MyAtlas`. Hide it for a deployment
with `VITE_DISABLED_TABS=MyAtlas` (see [Configuration](configuration.md)).

## What is stored, and where

Cards live only in the visitor's browser, under the localStorage key `beacon-my-atlas-v2`: each
card's kind, ID, last known name, card order and the activity window (24h or 3d). A node card also
keeps the node's full public key and, when the node is also an observer, that observer's ID.
A collection saved by an earlier version under `beacon-my-atlas-v1` is still read when there is
nothing under the new key, and moves to the new key on the next change; the old entry is left alone.

There is no account and no sync between browsers or devices; use
[Export and import](#export-and-import) to move a collection. Clearing site data removes it. If
storage is unavailable, the page says so and edits last for the visit.

Node cards are keyed by the full public key. If a server reset changes a node's ID, the page looks
the key up again before loading anything and saves the new ID; it never adopts a different node at
the old ID. A node or observer the server no longer knows stays on the page, is checked again
every ten minutes, and can still be removed.

## Adding cards

The search bar has three fields:

- **Name** and **Public Key** search nodes in every region (the region picker does not apply to
  this tab). A key search must be hexadecimal; a non-hex key is not sent to the server.
- **Observer** searches observers by name. An observer whose radio also advertises is saved as
  that node, with the observer linked, so the card gets all three views. If that node is already
  saved, it just gains the link.

A search needs at least two characters and shows up to eight results; the card says which rule is
holding a search back. Node results show their key prefix (the full key on hover) so two nodes
with the same name can be told apart.

An observer saved on its own becomes a node card by itself once its radio starts advertising.

## Reading a card

A node card opens on **Analytics**, the Analytics Signal row for that node over the selected window:

- **Observations**: stored receptions of packets originating from that key. The card loads the
  latest 200; when those do not reach back to the start of the window, the tile says "latest 200"
  and the bars start at the oldest loaded reception rather than drawing empty hours the sample
  cannot speak for.
- **Mean SNR / Mean RSSI**: averages of the observers' last-hop measurements, with an hourly
  sparkline. The zero-RSSI / zero-SNR "no measurement" sentinel is excluded; a real zero SNR is
  included. These describe the receivers' side, not the node's radio health.
- **Active hours**: hours in the window with at least one reception.
- The **Recent** / **Stale** badge is the server's `stale` verdict; the client does not infer
  online or offline.

**Heard by** swaps the tiles for the observers of the newest loaded packet, with when it was heard
and a link to open that packet in the analyzer. It is not lifetime reach. The card keeps its height
when it flips.

**Observer** appears when the node is also an observer, and is the only view of an observer card.
It shows what that observer received and reported over the window:

- **Packets heard** and **Mean SNR heard** (weighted by packets) from the observer's activity.
  Hours the server has no data for are left empty, and the tile says "Partial history".
- **Noise floor** from the observer's latest status report, or from telemetry when the status has
  none, the same order as the Observers page.
- **Battery**, or **Uptime** for a mains-powered observer, with online status, last status time
  and radio settings underneath.

Solid sparkline segments are readings; dashed segments join across missing hours and are only a
visual guide. Only one card at a time is away from its default view.

## Arranging cards

Drag the grip at the top right of a card to another slot (mouse or touch). With the grip focused,
the arrow keys move it one slot; Up and Down work too, since a phone shows one column. The order is
saved with the rest of the collection.

## Export and import

**Export** downloads the collection as `beacon-atlas-YYYY-MM-DD.json`. **Import** loads such a file
and replaces the current collection, asking first if there are cards to lose. The Beacon app reads
and writes the same file, so a collection can move between browsers, phones and the web. On a
phone the two buttons sit under the cards.

The file is the saved collection plus a format tag:

```json
{
  "format": "beacon-atlas",
  "version": 2,
  "exportedAt": 1793923200000,
  "range": "24h",
  "pins": [
    { "kind": "node", "id": "<node UUID>", "publicKey": "<64 hex>", "name": "Hill repeater", "observerId": "<observer UUID, optional>" },
    { "kind": "observer", "observerId": "<observer UUID>", "name": "Roof listener" }
  ]
}
```

Imports go through the same checks as a saved collection: a file without the format tag is
refused, malformed or duplicate cards are dropped, at most twelve are kept, and the page says how
many were skipped. Files over 256 KB are refused. Node cards work on another Beacon server,
because the public key finds the node there. Observer IDs belong to one server, so an observer
card imported elsewhere shows as no longer known.

## Polling

Cards refresh once a minute while the tab is open and the browser tab is visible. A node card's
observer data loads only while its **Observer** view is open. Polling pauses while the server is
rate-limiting and resumes as soon as the limit ends.
