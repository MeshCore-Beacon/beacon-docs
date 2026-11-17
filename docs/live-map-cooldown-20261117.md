# Live map and Retry-After follow-up

On 17 November 2026, Canadaverse deployed web revision `09049d2787cfe15d084e8db82ed0223da9403795`. The map animates packets with fewer worker messages during the fade. When a rate limit expires, a shared timer wakes waiting readers. Automatic observer lookups also respect that window. The preview backend ran `b54d1bf3afda` throughout. The app build is `f88f0dc3ff07`. [Canadaverse preview](https://canadaverse.org/beacon-dev/)

## Review units

Each draft targets org `dev` independently and is labelled for patch review.

| Draft | Behavior and regression coverage |
| --- | --- |
| [Web #242](https://github.com/MeshCore-Beacon/beacon-web/pull/242) | The live map clears a source once when its last feature disappears. A later packet starts drawing again. The final paint removes the fully faded trail. |
| [Web #243](https://github.com/MeshCore-Beacon/beacon-web/pull/243) | The rate-limit store owns the expiry timer. It notifies subscribers at the deadline, extends a longer window and cancels the timer on early success. Atlas and the header consume that shared state. |
| [Web #245](https://github.com/MeshCore-Beacon/beacon-web/pull/245) | A fixed clock makes the phone header's five-second stale-badge test deterministic. The existing visible text and accessible-label assertions still apply. |
| [Web #247](https://github.com/MeshCore-Beacon/beacon-web/pull/247) | An observer-only card with a cached key follows the observer query's pause state when checking for a matching node. On expiry it can adopt the newly found node and reopen its Observer view. |

An initial map PR CI run caught #245. Two clock reads in the fixture produced a 4,999 ms age, which rounded to four seconds. The original run is retained alongside its successful rerun. The final preview includes the test correction. [Original failure](https://github.com/MeshCore-Beacon/beacon-web/actions/runs/44178600738/attempts/1)

## Measured effects

The browser comparison used the deployed builds before and after the fixes. An isolated desktop English context and a French touch-emulation context received the same two-hop packet and local HTTP 429. A third, empty-Atlas control separated the request's retry timer from timers attributable to the 20 mounted cards.

| Measurement | Before | After |
| --- | ---: | ---: |
| Empty dot-source messages after one known packet arrived, per browser | 31 | 1 |
| Empty lit-node messages for a two-hop route with neither node in the index, desktop / phone | 46 / 47 | 0 / 0 |
| Pending timeouts in the retry-delay range with 20 cards, including the request retry | 101 | 2 |
| Extra such timeouts introduced by adding 20 cards to an empty Atlas | 100 | 0 |
| Header countdown intervals still running after expiry, per browser | 1 | 0 |

The two remaining timeouts are the shared expiry and the request's retry sleep. The same count was observed with zero cards. The moving dot, fading trail and glow still appeared for indexed hops. A controlled-clock observer test on both browsers recorded zero catalogue lookups across two scheduled polls, followed by adoption at expiry. A supplemental channel test also showed a buffered overflow waking at the deadline without waiting for an unrelated successful request.

These counts measure specific work in a controlled scenario. The effect varies with packet arrival and overlap. A sustained CPU or battery estimate would require a separate device profile.

## Public qualification

All four drafts passed full Linux CI. The combined build passed **2,312 tests in 219 files**, plus build and lint. All **82 public files** and the downloadable web source archive matched the Actions build. [Combined CI](https://github.com/n30nex/beacon-web-contributions/actions/runs/44183790426) · [Actions build](https://github.com/n30nex/beacon-web-contributions/actions/runs/44183781485) · [Preview fork PR #42](https://github.com/n30nex/beacon-web-contributions/pull/42)

The final public browser checks covered seven fixture contexts, all nine pages in English and French at desktop and phone sizes (36 page checks), and two real-feed map sessions. Both real sessions checked region and style changes, language switching, Stop, navigation, reopening and reduced motion. Animated-source submissions stopped after Stop and after leaving the map. The controlled packets and 429s stayed inside isolated browsers. Real-feed sessions used read-only subscriptions.

An earlier desktop sweep recorded an OpenFreeMap 404 for the duck emoji glyph range and MapLibre's local rendering fallback. A direct check confirmed that specific provider URL returned 404. The final sweep recorded zero API or resource error responses and the existing CSP block for optional edge analytics. [Glyph resource](https://tiles.openfreemap.org/fonts/Noto%20Sans%20Regular/129280-129535.pbf)

## Route maintenance observation

As a separate read-only check for server #224, three preview samples between 21:20 and 21:55 UTC showed three different stored route cursor positions in cycle 48. The separate route-retention watermark was saved again at 21:50 UTC. This establishes progress during that preview window. Release-host soak and confirmation that neighbour revalidation completes under release traffic remain open. [Server #224](https://github.com/MeshCore-Beacon/beacon-server/issues/224)

## Recovery

Two frontend cutovers were used. From the existing Canadaverse preview root, run the first command to restore the initial build from this batch. Run the second if the intended target is the build from before the batch.

```sh
sudo python3 evidence/live-map-cooldown-20261117/observer-runtime/deploy-web.py rollback
sudo python3 evidence/live-map-cooldown-20261117/web-runtime/deploy-web.py rollback
```

The first checkpoint, `observer-cooldown-web-20261117T215547Z`, restores web `dca02d607a2f`. The second, `live-map-cooldown-web-20261117T214118Z`, restores `71eac3390c3d`. Both use the deployed backend and accumulated database. The cutover verified checkpoint identity and asset integrity. A live rollback rehearsal remains unexercised.
