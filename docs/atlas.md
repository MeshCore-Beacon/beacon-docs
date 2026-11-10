# Atlas

A per-browser watchlist of up to twelve radios, each shown as a card of recent activity and signal.
A card can follow a node, an observer, or a node that is also an observer. The tab sits just before
**Analytics**, in the desktop row and under **More** on a phone; the URL is `?tab=Atlas`. Hide it for a deployment
with `VITE_DISABLED_TABS=Atlas` (see [Configuration](configuration.md)).

## What is stored, and where

Cards live only in the visitor's browser, under the localStorage key `beacon-atlas-v2`: each
card's kind, ID, last known name, card order and the activity window (24h or 3d). A node card also
keeps the node's full public key and, when the node is also an observer, that observer's ID.
A card whose Observer view tiles were changed also keeps its four tiles (see
[Choosing the Observer tiles](#choosing-the-observer-tiles)), and a node card pinned to open on
**Heard by** or **Observer** keeps that tab (see
[The tab a card opens on](#the-tab-a-card-opens-on)).

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

A node card opens on **Analytics** unless it is pinned to another tab (see
[The tab a card opens on](#the-tab-a-card-opens-on)). Analytics is the Analytics Signal row for
that node over the selected window:

- **Observations**: stored receptions of packets originating from that key. The count and the
  hourly bars come from hourly totals the server keeps for the selected window (24 hours or 3
  days), so a busy node is counted in full rather than cut off at its newest receptions. Hours
  the server has not covered are left empty rather than drawn as zero, and the tile then says
  "Partial history" in place of the window.
- **Mean SNR / Mean RSSI**: averages of the observers' last-hop measurements, with an hourly
  sparkline. The zero-RSSI / zero-SNR "no measurement" sentinel is excluded; a real zero SNR is
  included. These describe the receivers' side, not the node's radio health.
- **Active hours**: hours in the window with at least one reception.
- Underneath: when the node was last seen, **Mean hops** (the average hop count of those
  receptions) and the node's neighbor count.
- The **Recent** / **Stale** badge is the server's `stale` verdict; the client does not infer
  online or offline.

**Heard by** swaps the tiles for the observers of the node's most recently heard packet, with when
it was heard and a link to open that packet in the analyzer. It is not lifetime reach. The card
keeps its height when it flips.

On a server that has no node activity endpoint, the tiles have no data, the info tip and the
**Heard by** view say "This server does not provide node activity.", and the card stops asking
for it.

**Observer** appears when the node is also an observer, and is the only view of an observer card.
It shows what that observer received and reported over the window, in four tiles. A new card
shows Airtime, Battery, Packet types and Noise floor, with a line underneath: **Online** or
**Offline**, the last status time, the radio settings, and the uptime when the battery is known
and no tile shows the uptime.

### Choosing the Observer tiles

Each tile's label opens a list of the metrics that are not already on the card; picking one puts
it in that tile's place. The choice is saved per card. **Reset tiles**, shown under the tiles
once a card differs from the default, puts the four defaults back.

There are ten metrics:

- **Airtime**: the share of the window the radio spent transmitting and receiving, from its own
  counters, with the TX and RX shares underneath. When the observer does not report those
  counters, the figure is estimated from the packets it heard, covers receive only, and is marked
  "RX, from heard".
- **Battery**: the latest battery reading. When the observer reports no battery (a mains-powered
  one), the tile shows Uptime instead, unless the card already has an Uptime tile.
- **Uptime**: how long the radio has been up.
- **Packet types**: the number of packets the observer heard, over a bar of the payload types
  they were, busiest first. The five busiest get their own slice and the rest are grouped as
  "other".
- **Packets heard**: the same count, with hourly bars.
- **Mean SNR** and **Mean RSSI**: the signal of what the observer heard, with an hourly
  sparkline. The figure for the window weights each hour's average by that hour's packet count.
- **Noise floor** from the observer's latest status report, or from telemetry when the status has
  none, the same order as the Observers page.
- **Queue length**: the latest reading in the window.
- **Receive errors**: the number of new errors in the window. The radio reports a running
  counter, so the tile adds up the increases between readings; a counter that went backwards
  adds nothing.

Hours the server has not covered are left out of Packet types and Packets heard, and those tiles
then say "Partial history".

Status reports with no readings are ignored. On the Airtime, Battery, Noise floor and Queue
length sparklines, solid segments are readings and dashed segments join across missing hours as a
visual guide only; gaps in Uptime stay open. On a server without observer activity or telemetry,
the info tip says so.

### The tab a card opens on

A card with more than one view has a pin button beside the Analytics / Heard by / Observer
switch. The pin is pressed while the card shows the tab it opens on. Pressing it on another tab
makes that the tab the card opens on, and the choice is saved with the card.

Switching tabs without pressing the pin is temporary: only one card at a time is away from the
tab it opens on, so switching a tab on another card sends the first one back.

A card pinned to Observer whose node has no observer link opens on Analytics; the pin is kept
and applies again once the link is there. An observer card has one view and no pin. When an
observer card becomes a node card, it keeps opening on Observer.

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
    { "kind": "node", "id": "<node UUID>", "publicKey": "<64 hex>", "name": "Hill repeater", "observerId": "<observer UUID, optional>", "view": "observer" },
    { "kind": "observer", "observerId": "<observer UUID>", "name": "Roof listener", "tiles": ["packets", "snr", "rssi", "noise"] }
  ]
}
```

`tiles` is optional on either kind of card and is left out for the default layout. It is exactly
four different metric IDs, in tile order, from `airtime`, `battery`, `uptime`, `types`, `packets`,
`snr`, `rssi`, `noise`, `queue` and `errors`. The file is still version 2. Anything else in
`tiles` is dropped on import and the card keeps the default layout; a build from before the tile
picker ignores the field.

`view` is optional on a node card: `heard` or `observer`, the tab the card opens on, left out
when that is Analytics. Any other value is dropped on import and the card is kept, opening on
Analytics. A build from before the pin ignores the field.

Imports go through the same checks as a saved collection: a file without the format tag is
refused, malformed or duplicate cards are dropped, at most twelve are kept, and the page says how
many were skipped. Files over 256 KB are refused. Node cards work on another Beacon server,
because the public key finds the node there. Observer IDs belong to one server, so an observer
card imported elsewhere shows as no longer known.

## Polling

Cards refresh once a minute while the tab is open and the browser tab is visible. A node card's
observer data loads only while its **Observer** view is open. Polling pauses while the server is
rate-limiting and resumes as soon as the limit ends.
