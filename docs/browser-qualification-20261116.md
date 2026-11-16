# Beacon browser qualification — 16 November 2026

**Completed and deployed to Canadaverse preview only.** Current frontend:
`4ee1fc304411a879626b3878d9ab2182264f36df`. Backend remains
`6292a743aaeb088132cc86320dc7f92343cb1e7e`. No backend container, configuration,
credential, database, retention or radio-service change was made. Dev/dev1/live
were not deployed to. The strict-dev feature policy remains in effect.

## Focused dev PRs

| PR | Reproduced problem | Fix |
| --- | --- | --- |
| [#204](https://github.com/MeshCore-Beacon/beacon-web/pull/204) | A long French Atlas label hid its last-seen value | Truncate the label, keep the timestamp visible |
| [#205](https://github.com/MeshCore-Beacon/beacon-web/pull/205) | The phone channel name was squeezed to 15 px although Public needs 50 px | Separate channel identity from wrapping phone controls |
| [#206](https://github.com/MeshCore-Beacon/beacon-web/pull/206) | Switching language on an open map left native controls in English | Update existing labels and tooltips without rebuilding the canvas; unsubscribe on removal |
| [#207](https://github.com/MeshCore-Beacon/beacon-web/pull/207) | Jumping to older history consumed the saved scroll anchor before data arrived | Apply the anchor only when the older-page fetch settles |
| [#208](https://github.com/MeshCore-Beacon/beacon-web/pull/208) | Hidden reach labels extended the document beyond the scroller, reproducing [#170](https://github.com/MeshCore-Beacon/beacon-web/issues/170) | Make the scrolling element their positioning container |

All five remain separate drafts targeting `dev`, with passing checks on their
current heads. [Fork integration #33](https://github.com/n30nex/beacon-web-contributions/pull/33)
contains the tested preview composition. No combined org bug-fix PR or reviewer
request was introduced.

## Browser matrix

The final deployed files were tested in isolated Chrome Beta **143.0.7499.17**
contexts using Playwright 1.65.1. The original browser profile was not attached to
the test runner. Test cards and language preferences belonged to disposable contexts.
The temporary desktop inspection window was closed; no user Atlas pins were edited.

| View | Language | Pages checked | Result |
| --- | --- | ---: | --- |
| Desktop 1440 × 900 | English | 9 | Pass |
| Desktop 1440 × 900 | French | 9 | Pass |
| Touch/mobile 390 × 844 | English | 9 | Pass |
| Touch/mobile 390 × 844 | French | 9 | Pass |

Pages: Packets, Channels, Map, Nodes, Observers, Routes, Traces, Atlas and Analytics.
All 36 page checks completed without an uncaught application exception, API failure
or document-width overflow. The tests also exercised mobile More navigation,
language switching/persistence, Atlas search/add/persistence in isolated storage,
Public channel selection and map play/stop. The selected channel's height and
history scroll behavior were checked separately; an initial directory screenshot
alone would not have caught the scrolling defects.

The existing CSP blocks Cloudflare's automatically inserted optional analytics
script. That external failure is distinct from an application error; CSP was not
relaxed. No synthetic packet or RF polling request was sent.

## Map behavior and work limits

Both final desktop and phone runs passed eight checks: in-place language updates
with the same canvas, real live animations, shared-region switching, light/dark
style changes during animation, stopping updates, disposal on navigation,
returning without stale animation, and an initially stopped map under the
reduced-motion preference. Native resolved-path requests turn on/off with the UI.

The test waits for a real eligible route before sampling. An initial fixed
ten-second window observed no animation updates; that quiet sample was retained
as evidence and was not treated as a rendering defect or replaced with fake RF
traffic. Test-only instrumentation counts worker message metadata and does not
save packet bodies or coordinates.

| Final sample | Seconds | Trail updates | Dot updates | Lit-node updates | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Desktop | 10.051 | 282 | 282 | 282 | Within the existing 30 Hz source budget |
| Phone | 10.012 | 213 | 213 | 213 | Within the existing 30 Hz source budget |

Both runs recorded zero further animated-source updates after stop and after
leaving the map. These are source-submission measurements in this browser, not
universal rendering FPS, phone battery-life or production capacity claims.

## Scrolling and responsive regression proof

Before #208, opening Public could grow the document to **3,572 px** in an **844 px**
viewport. Moving the positioning boundary alone returned it to 844 px while
retaining the accessible labels. On the final public build the document stays
at **844 px**. Both the message list and channel sidebar
reach their own bottom with **zero blank scroll gap**, while the outer document
stays at scroll position zero.

Loading 50 additional older messages preserved the previous reading anchor within
**0.125 px**. The delayed-response
unit regression fails on the old implementation (`scrollTop` 0 instead of 400)
and passes on the fix. Phone landscape **844 × 390** also stays within its viewport.

## Build, deployment and recovery

- [Exact-head CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/43817532056): **2,212 tests in 209 files**, build and lint
  passed. The two existing React/TanStack compiler warnings remain non-failing.
- [Actions-built frontend](https://github.com/n30nex/beacon-web-contributions/actions/runs/43817531234): source archive and
  all **85 public web files** verified against their hashes. No local build was
  substituted for the deployment artifact.
- All five PRs have passing current-head CI and clean independent merges against
  the checked dev baseline. Final public matrix, map and scrolling checks passed
  after the last cutover, not merely against a local candidate.
- Checkpoint **browser-web-20261116T063805Z** restores the preceding strict-dev frontend
  `9bafb430759c`, preserving backend/data. From the existing Pi preview root use
  `sudo python3 evidence/browser-qualification-20261116/scroll-fix/deploy-web.py rollback`.
  The earlier web checkpoint can subsequently restore `a647dd66f995` if explicitly
  needed; older full-stack recovery instructions are not interchangeable.
- Recovery copies and hashes were checked. This follow-up's rollback was not
  executed as a live rehearsal. No database migration or container restart occurred.

These are browser/emulation checks, including touch input and responsive layouts.
They do not establish physical Safari/iOS/Android behavior, BLE/Wi-Fi collection,
background OS operation, RF delivery, or a long production-load soak. Those
separate release gates remain in the wider audit roadmap.

This completes the browser portion left open in the
[full audit handoff](https://canadaverse.org/beacon-dev/audit-handoff-20261116.md).
Private detailed receipts remain under `evidence/browser-qualification-20261116`.
