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
3. Fast-forward `main` to `dev`: `git checkout main && git merge --ff-only dev`.
4. Tag and push: `git tag vX.Y.Z && git push origin main --tags`.
5. The tag builds and publishes the container image in both repos. In beacon-server it also
   builds binaries for every supported platform and attaches them to a draft GitHub release.
   Open the draft, paste the release notes and publish it.
6. Rebase `dev` on `main` so the histories stay in sync: `git checkout dev && git rebase main`.

## Where to find release notes

Each repo's GitHub Releases page:
[beacon-server](https://github.com/MeshCore-Beacon/beacon-server/releases) and
[beacon-web](https://github.com/MeshCore-Beacon/beacon-web/releases).
