# Channel-message transport scope

Channel history, the global/hash message APIs, reconnect backfill and `channelMessage` events now include `scope` and `scopeStatus`. Live events also include their stored message `id`; existing fields, endpoints and cursors are unchanged.

| Status | Meaning |
|---|---|
| `matched` | `scope` names the scope recorded on the first stored packet. |
| `unscoped` | The first stored packet has no transport codes; `scope` is null. |
| `unknown` | Transport codes were recorded but no scope name was resolved, including ambiguous matches. |
| `unavailable` | Scope/capture metadata is missing. |

These labels belong to the first stored packet, not every later reception of the same payload. Later paths may differ. Live delivery reads that same evidence while inserting the channel message, so a later reception cannot relabel it differently from history. Existing scope query filters retain their meaning. Imported catalogue membership and channel names are never used as message evidence.

The insertion query returns metadata only for a new message. Duplicate deliveries still produce no extra live message. Adding a decryption key later uses the existing backfill path, retains the stored packet evidence and does not broadcast old messages as new traffic. This change adds no keys, migration or historical scan. Expired packet/message detail remains unavailable.

Deploy this API before its web consumer. Older clients may ignore the added fields; clients reading older servers must treat absent metadata as unavailable, not assume a message is unscoped. Scope filtering of live events requires the new fields. The channel encryption key and the packet transport scope are separate concepts.
