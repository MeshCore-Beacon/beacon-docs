# Contributing to Beacon

Thank you for your interest in contributing. This page is the shared workflow for all three
Beacon repositories:

- [beacon-docs](https://github.com/MeshCore-Beacon/beacon-docs), this repo: deployment,
  configuration and operator documentation.
- [beacon-server](https://github.com/MeshCore-Beacon/beacon-server): the API and ingest. Its own
  [CONTRIBUTING.md](https://github.com/MeshCore-Beacon/beacon-server/blob/main/CONTRIBUTING.md)
  covers Go style, tests, database and API changes.
- [beacon-web](https://github.com/MeshCore-Beacon/beacon-web): the frontend. Its own
  [CONTRIBUTING.md](https://github.com/MeshCore-Beacon/beacon-web/blob/main/CONTRIBUTING.md)
  covers TypeScript style, tests and the feature layout.

Please read this before opening a PR anywhere.

## Before you start

**Talk first for anything bigger than a small fix.** On beacon-server and beacon-web, open or
comment on an issue before starting work, so maintainers can say if something is already in
progress or out of scope. Issues are disabled on beacon-docs; for a docs restructure, a new
deployment type or a correction you are unsure about, reach out on the
[MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf). For typos, broken links and small
clarifications, just open a PR.

**One thing per PR.** Each pull request covers one logical change: a bug fix, a new endpoint, a
corrected variable table. PRs that touch many unrelated things are hard to review and hard to
revert.

**No fully AI-generated contributions.** We welcome contributors who use AI tools to assist
their work, but a PR should reflect the author's own understanding and judgement. PRs that
appear to be unreviewed AI output may be closed without further comment.

## Branches

beacon-server and beacon-web:

- `main` holds stable releases only and is protected. Never target it directly.
- `dev` is active development. All PRs target `dev`.

beacon-docs has only `main`. PRs target `main`, and the docs there describe the current
release.

## Workflow

1. Fork, or create a branch from `dev` (code repos) or `main` (docs).
2. Make your change.
3. Run that repo's checklist (below for docs; in each code repo's CONTRIBUTING for code).
4. Open a pull request with a clear description of what changed and why, referencing any
   related issue.

## Running the full stack locally

Most changes to either code repo are easier to check against the other one running next to it.

**beacon-server**, with a throwaway PostgreSQL in Docker:

```bash
git clone https://github.com/MeshCore-Beacon/beacon-server.git && cd beacon-server
cp env.example .env
cp config.yaml.example config.yaml
docker run -d --name beacon-postgres -p 5432:5432 \
  -e POSTGRES_USER=beacon -e POSTGRES_PASSWORD=beacon -e POSTGRES_DB=beacon postgres:16-alpine
go run ./cmd/beacon
```

Set `POSTGRES_DSN` and your broker credentials in `.env` (every variable is described in
[Configuration](docs/configuration.md)). Migrations run on startup. The API is on
`http://localhost:8080` and Swagger at `http://localhost:8080/swagger/index.html`.

**beacon-web**, in a second terminal:

```bash
git clone https://github.com/MeshCore-Beacon/beacon-web.git && cd beacon-web
npm install
cp .env.example .env.local
npm run dev
```

In `.env.local`, uncomment and set:

```
VITE_DEV_PROXY=http://localhost:8080
VITE_API_BASE=/api/v1
VITE_WS_URL=ws://localhost:5173/ws
```

Vite then proxies `/api` and `/ws` to the server and presents the server's own origin on the
WebSocket, so beacon-server's same-origin rule is satisfied without touching its config. If
you would rather have the browser talk to `localhost:8080` directly, add
`websocket: {allowed_origins: [http://localhost:5173]}` to the server's `config.yaml` instead.
Open `http://localhost:5173`.

## Checklist before opening a docs PR

- **Docs match reality.** If you change a variable, path, command or image name, check it
  against the actual files in `docker-deployment-*/` and `app_config/`, and against the code
  in beacon-server or beacon-web when the behaviour lives there.
- **Links resolve.** Relative links point at files that exist; anchors match a heading.
- **Compose still parses.** If you touched a `docker-compose.yml`:
  ```bash
  docker compose -f docker-deployment-type1/docker-compose.yml config
  ```
- **No secrets.** Never commit a real `.env`, real passwords, channel keys or MQTT credentials.
  Use placeholders like `CHANGE_ME` in examples.
- **No em dashes.** Use a comma, a period or a new sentence.

## Documentation style

- Write for an operator deploying Beacon for the first time. Assume Docker knowledge, not
  knowledge of this project.
- Lead with the action. "Set `DOMAIN` to your public hostname", not "the `DOMAIN` variable
  should be configured".
- Say why only where the why prevents a mistake.
- Prefer concrete, copy-pasteable commands over prose, in fenced blocks with a language tag.
- One page, one job. Headings are things a reader searches for, not categories.
- Keep tables in step with the example config files; when a key changes, update
  `app_config/config.yaml.example` and the page that describes it in the same PR.
- Relative links between files in this repo, so they work on GitHub and in local clones.

## Adding or changing a deployment

The deployment folders are meant to be copied to a server and run as-is. When editing one:

- Keep the folder self-contained: `docker-compose.yml`, the `data/` tree, and a `.env` the
  user creates from `app_config/.env.example`.
- Every variable a user must set appears in `app_config/.env.example` (for `.env`) or
  `app_config/config.yaml.example` (for app config), and in [Configuration](docs/configuration.md).
- Keep service names and Caddyfile upstreams consistent; the proxy must resolve the names it
  proxies to.
- A new deployment type gets its own `docker-deployment-typeN/` folder with a README, Caddyfile
  templates under `app_config/caddy/`, and a line in the main README.

## Commit messages

Conventional commits, imperative, one line under 72 characters, with an optional scope:

```
docs(readme): clarify VITE_MAP_CENTER fallback behaviour
docs(deploy): add type 2 split server and web compose files
feat(routes): add observation_count to known routes response
fix(ingest): correct lat/lon divisor for advert payloads
chore: update logos
```

## Releases

Versioning, image tags and the release flow are in
[Releases and versioning](docs/releases.md).

## Repo structure

```
docker-deployment-type1/   all-in-one Docker Compose deployment
docker-deployment-type2/   split server and web deployment
app_config/                example .env and config.yaml, proxy configs (Caddy, nginx, Apache), fail2ban
docs/                      operator and design documentation
logos/                     brand assets
```

## Recognition

If you would like to be listed as a contributor, add yourself to
[CONTRIBUTORS.md](CONTRIBUTORS.md) in your PR.
