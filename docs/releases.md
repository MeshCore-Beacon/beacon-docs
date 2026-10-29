# Releases and versioning

## Version numbers

From 2.0.0, beacon-server and beacon-web share the same major and minor version. Patch numbers
move on their own, so server 2.0.3 runs with web 2.0.1. Keep both on the same `X.Y`.

The `/api/v1` in request paths is the API contract version. It does not change with releases;
see the [API contract](api-contract.md#versioning).

## Image tags

Both images live on GitHub Container Registry and are public, so no `docker login` is needed:
`ghcr.io/meshcore-beacon/beacon-server` and `ghcr.io/meshcore-beacon/beacon-web`.

| Event | Tags published |
|---|---|
| push to `main` | `latest`, `sha-<short>` |
| push to `dev` | `dev`, `sha-<short>` |
| tag `vX.Y.Z` | `X.Y.Z`, `X.Y`, `sha-<short>` |

`latest` is the newest release on `main`. To decide for yourself when to upgrade, pin both
images to the same release line (`:2.0`) or an exact release (`:2.0.0`). `dev` follows the
development branch and can break between pushes. Prerelease tags (`v2.1.0-rc1`) get `2.1.0-rc1`
but not `2.1`.

If a pull fails with `403 Forbidden`, the package has been switched back to private on GHCR;
see [Troubleshooting](troubleshooting.md#docker-compose-up-fails-with-403-forbidden-pulling-an-image).

## Cutting a release

Maintainers only. Releases are cut by hand, not from the GitHub UI, and release commits are
signed. The flow is the same in both repos; only the version bump differs.

1. Make sure `dev` is green in CI.
2. Bump the version on `dev`:
   - beacon-server: the `@version` annotation in `cmd/beacon/main.go`, then regenerate Swagger
     with `swag init -g cmd/beacon/main.go -o docs --parseInternal --parseDependency`.
   - beacon-web: `version` in `package.json`.

   Commit as `chore: bump version to vX.Y.Z`.
3. Open a PR from `dev` into `main` titled `Release vX.Y.Z` and merge it with **Create a merge
   commit**. `main` only accepts merge commits, so `dev`'s own commits land on `main` and the next
   release PR lists only what is new.
4. Tag the merge commit and push it: `git tag -a vX.Y.Z origin/main -m "vX.Y.Z" && git push origin vX.Y.Z`.
5. The tag builds and publishes the container image in both repos. In beacon-server it also
   builds binaries for every supported platform and attaches them to a draft GitHub release.
   Open the draft (or create the release in beacon-web), paste the release notes and publish it.
6. Fast-forward `dev` to `main` so the branches match: `git push origin origin/main:dev`.

## Where to find release notes

Each repo's GitHub Releases page:
[beacon-server](https://github.com/MeshCore-Beacon/beacon-server/releases) and
[beacon-web](https://github.com/MeshCore-Beacon/beacon-web/releases).
