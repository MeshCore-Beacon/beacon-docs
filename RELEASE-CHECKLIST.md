# Beacon 1.4.0 release checklist

1.4.0 replaces the planned 1.3.2 release. Alderson controls acceptance, stable tags
and the production switch. Earlier receipts remain in the [historical preparation
record](app_documentation/release-132-preparation.md) and dated evidence documents.

## Destinations and scope

- `live.meshcore.ca`: production Beacon 1.4.0, replacing CoreScope after approval.
- `dev.meshcore.ca`: kept online for development testing only, with separate
  application, database, cache and configuration.
- `canadaverse.org/beacon-dev/`: the exact contributor review candidate with source
  downloads and rollback. It is not the production deployment.
- My Atlas #97: held until after 1.4.0; resolve conflicts and validate it separately.
- Server releases keep their independent version history. Do not downgrade the
  existing v1.6.0 server version to web 1.4.0.

## Candidate verification

- [x] Web package and lockfile identify 1.4.0; dependencies are unchanged by the bump.
- [x] Development, main and prerelease events cannot publish `latest`; eight official
  metadata-action v5 fixture cases pass across both application workflows.
- [x] Both deployment templates accept explicit production/development image references
  and matching URLs; missing image selection fails before deployment.
- [x] Native server/PostgreSQL tests, restored-copy migration and bounded ingestion
  replay pass. These checks do not establish production capacity.
- [x] Source/assets, public reads, fresh packets and 26 boundaries are verified on
  the review preview. Active revisions and the frontend receipt are in the
  [candidate manifest](app_documentation/release-140-heads.json).
- [x] A restored/checksummed private dump and prior application/configuration/assets
  are retained. Unrelated Pi services are preserved.

## Alderson's release gates

- [ ] Review/accept server #189, web #105 and docs #5. Verify CI on the actual
  accepted commits, including changes after the recorded candidate.
- [ ] Resolve the earlier 24h/3d raw-history requirement against upstream's restored
  7d/30d controls and the conversion of old 3d observer links to 7d.
- [ ] Verify desktop and physical iPhone Safari, English/French, keyboard, Back,
  maps and expired-history states on the production candidate.
- [ ] Stage independent production Beacon data/configuration; restore-test its backup
  and migrations and record available history. Do not run Beacon migrations against
  CoreScope's database or share the development database.
- [ ] Validate the intended production host over a representative busy period for
  ingestion, database load, CPU/memory and latency. Keep profiles private.
- [ ] Promote accepted release source under the repository process, publish web
  `v1.4.0`, choose the server version independently, and verify Actions-produced
  images, revision labels, immutable digests and corresponding source.
- [ ] Save/verify the CoreScope rollback route, images, configuration and data.
  After approval, switch `live.meshcore.ca` web/API/WebSocket traffic together to
  Beacon and preserve the CoreScope rollback window.
- [ ] Confirm production version/digests, fresh packets, brokers, TLS, API/WebSocket
  destinations and boundaries. Independently verify `dev.meshcore.ca` remains
  online and uses only its development backend/data.

[Detailed cutover and rollback](app_documentation/release-140-preparation.md) ·
[Review source/changelog](https://canadaverse.org/beacon-dev/source.html).
