# Experimental n30nex-test preview

Verified 30 September 2026. The contributor requested separate `n30nex-test`
branches, Atlas in the Pi preview, and daily checks against upstream dev/main.
This work is experimental. Existing server #192 and docs #7 remain drafts; do not
request reviews, mention reviewers or promote the work until asked. The web branch
has no new pull request. The stable 1.4.0 release handoff remains separate.

[Open My Atlas](https://canadaverse.org/beacon-dev/?tab=MyAtlas) ·
[Corresponding source and changelog](https://canadaverse.org/beacon-dev/source.html)

| Repository | Experimental branch | Validated/deployed source |
|---|---|---|
| Server | `n30nex-test`, `9505ad444268c552e08e46613ed8f2e0f8fd78a8` | Same revision; includes upstream dev `5b177d6f`, release parent #189 and the route-prefix fix in draft #192 |
| Web | `n30nex-test`, `dc3268f7468bd9b3ae280243411c231fde6dd6ae` | Built as `b99b6e779d7bc4ec47e0e5202191d6aac9510ee0`; both have exactly the same `29d2513fe6f57f2aada079977e8eed40d72bc1dd` source tree |
| Docs | `n30nex-test`, draft #7 | Active phased roadmap, experiment contract and this record |

## Included work

- Saved routes update the current processed prefix representation without changing
  their stable IATA/node-chain identity. New cursors and copied links pin one exact
  width/path and time window; unrelated bytes or missing identities cannot silently
  select another chain. The existing indexed observation query and schema are reused.
- My Atlas includes the two feature commits from web #97, adapted to the current
  upstream navigation and translations. Existing tab order stays intact, with Atlas
  beside Observers. Saved full-key cards, activity bars, signal meters, expandable
  Heard by and statistics work in English and French. The cards remain bounded
  samples of up to 200 origin-key reports, not complete node totals.
- The ingestion status-text and logging corrections from upstream `5b177d6f` are
  included. Public admin/backup, automatic zones and foreign classification remain
  disabled; saved configuration and retention are unchanged.

## Compatibility and validation

Trial merges are clean for server and web against upstream dev and main, and for
docs against main. Web main `5ac36ce` was squash-created from `6daf342c` in release
PR #27. Both have the identical `03ab89640d90d77bc844b59b4945c4ad899f9cf0` tree;
the original is already an ancestor of current dev. A source-preserving ancestry
merge records that fact and removes the otherwise inherited 45 merge conflicts.
No source file was replaced during that reconciliation. The deployed web build
keeps its actual b99b6e7 identity and matching source archive; it is not relabelled.

Native Go/PostgreSQL tests and server CI pass. The route regression changes widths
between pages and checks shared links, repeats, malformed selectors, missing and
colliding identities, and exact indexed plans. The 200,000-row fixture used the
existing index under custom and generic plans (0.097/0.090 ms execution in this
fixture). The 3,200-input replay retained the expected 100 packets, 800 observations,
100 decrypted messages and 800 ordinary/2,400 opted-in events with zero fixture
drops. These are bounded checks, not production capacity or losslessness claims.

The final combined frontend passes native Pi build/lint and all **1,066 tests**.
Windows build/lint and 58 focused combined checks pass; the preceding route-only
tree also passed all 1,046 Windows and Pi tests. Public verification matches all
**23 assets**, both source archives and **26 boundaries**. Saved cards, expansion,
node inspection, French phone layout, LIVE delivery and pinned route pagination
were checked. The browser clipboard tool did not expose copied URL text; copy
construction is regression-tested and explicit shared-link navigation passes.
Physical Safari and a representative production-load soak remain unverified.

## Preview recovery and follow-up

The private full dump was restore-tested and checksum-verified on and off the Pi.
The phase-owned validation databases were retired after checking they were idle.
Only the Beacon app restarted; the other 23 containers were unchanged. Frontend
publication restarted none of the 24 containers. New traffic is preserved.

The preview owner's guarded backend recovery is
`evidence/route-prefix-20260930/deploy-server.py rollback`, checkpoint
`routes-cutover-20260930T225443Z`. It restores server `61b0322a` / web `157525ef`,
rolling the experimental frontend back first if necessary. Frontend-only recovery
is `evidence/route-prefix-20260930/deploy-beacon-web.py rollback --evidence-dir route-prefix-20260930`,
checkpoint `web-20260930T232611Z`. This phase adds no migration or database restore.

Daily compatibility checks run at 09:00 America/Toronto. They inspect upstream
changes and isolated trial merges, preserving active work and reporting meaningful
changes only. They do not push, rebase, deploy or ping reviewers automatically.
Use the [phased roadmap](post-140-roadmap.md) for subsequent work; node/trace
dashboards and deeper investigation are next, alongside the separate retained-window
decision. Atlas remains excluded from the stable 1.4.0 release even though it is
enabled in this experiment.
