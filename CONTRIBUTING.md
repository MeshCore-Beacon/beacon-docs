# Contributing to Beacon Docs

Thank you for your interest in contributing. This repository holds the
project-wide documentation and the ready-to-run Docker deployments for Beacon.
The application code lives elsewhere:

- [beacon-server](https://github.com/MeshCore-Beacon/beacon-server) — the API backend
- [beacon-web](https://github.com/MeshCore-Beacon/beacon-web) — the web frontend

Please read this guide before opening a PR.

---

## Before you start

**Issues are disabled on this repository.** To discuss a change before doing the
work — a docs restructure, a new deployment type, a correction you're unsure
about — reach out on the [MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf)
first. For small fixes (typos, broken links, clarifications) just open a PR.

**One thing per PR.** Each pull request should cover one logical change — a fixed
section, a new deployment type, a corrected variable table. PRs that touch many
unrelated docs at once are hard to review.

**No fully AI-generated contributions.** We welcome contributors who use AI tools
to assist their work, but PRs should reflect the author's own understanding and
judgement. PRs that appear to be unreviewed AI output may be closed without
further comment.

---

## Branches

- `main` — the published documentation. PRs target `main`.

## Workflow

1. Fork or create a branch from `main`
2. Make your changes
3. Run the checklist below
4. Open a pull request against `main` with a clear description of what changed
   and why

---

## Checklist before opening a PR

- **Docs match reality.** If you change a variable, path, command, or image
  name, confirm it matches the actual files in `docker-deployment-*/` and
  `app_config/`. The README's variable tables must stay in sync with
  `app_config/.env.example` and `app_config/config.yaml.example`.
- **Links resolve.** Internal links point at files that exist; external links
  load.
- **Compose still parses.** If you touched a `docker-compose.yml`, validate it:
  ```bash
  docker compose -f docker-deployment-type1/docker-compose.yml config
  ```
- **No secrets.** Never commit a real `.env`, real passwords, channel keys, or
  MQTT credentials. Use placeholder values like `CHANGE_ME` in examples, and
  keep real secrets in the gitignored `.env`.

---

## Documentation style

- Write for an operator deploying Beacon for the first time — assume Docker
  knowledge, not knowledge of this project.
- Prefer concrete, copy-pasteable commands over prose.
- Use fenced code blocks with a language tag (` ```bash `, ` ```yaml `,
  ` ```text `).
- Keep tables aligned with the example config files; when a config field
  changes, update both the example file and the README in the same PR.
- Use relative links between files in this repo so they work on GitHub and in
  local clones.

---

## Adding or changing a deployment

The deployment folders are meant to be copied to a server and run as-is. When
editing one:

- Keep the folder self-contained: `docker-compose.yml`, the `data/` tree, and a
  `.env` that is created from `app_config/.env.example`.
- Every variable a user must set should appear in `app_config/.env.example` (for
  `.env`) or `app_config/config.yaml.example` (for app config), and be documented
  in the README's variable tables.
- Keep service names, container names, and the Caddyfile upstreams consistent —
  the reverse proxy must resolve the names it proxies to.
- If you add a new deployment type, give it its own `docker-deployment-typeN/`
  folder, add a Caddyfile template under `app_config/caddy/`, and add a section
  to the README walkthrough.

---

## Commit messages

Use the conventional commits format:

```
docs(readme): clarify VITE_MAP_CENTER fallback behaviour
docs(deploy): add Type 2 split server/web compose files
fix(config): correct postgres password mismatch note
chore: update logos
```

Common scopes: `readme`, `deploy`, `config`, `caddy`, `docs`.

---

## Repo structure

```
docker-deployment-type1/   — single-server (all-in-one) Docker Compose deployment
docker-deployment-type2/   — split server/web deployment (WIP)
app_config/                — example .env, config.yaml, proxy configs (Caddy, nginx, Apache), fail2ban
app_documentation/         — project-wide design & API docs
logos/                     — brand assets
```

---

## Recognition

If you'd like to be listed as a contributor, add yourself to
[CONTRIBUTORS.md](CONTRIBUTORS.md) in your PR.
