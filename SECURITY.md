# Security Policy

This is the **documentation and deployment** repository for Beacon. If you have
found a vulnerability in the Beacon application itself (server or web), please
report it against the relevant code repository:

- [beacon-server](https://github.com/MeshCore-Beacon/beacon-server)
- [beacon-web](https://github.com/MeshCore-Beacon/beacon-web)

## Reporting a Vulnerability

Please do not report security issues through public GitHub. Issues are disabled
on this repository.

Instead, contact the maintainers directly via the MeshCore Canada Discord
server: [MeshCore Canada Discord](https://discord.gg/Gz3KvJx2hf); reach out to
**dedskelly** directly. Include as much detail as possible: the nature of the
issue, steps to reproduce, and any potential impact.

We will acknowledge receipt within 48 hours and aim to provide a fix or
mitigation within 14 days depending on severity.

Once a fix is released we will publish a security advisory on the relevant
repository.

## Deployment hardening

The Docker deployments in this repo expose `db`, `redis`, and `app` only on
`127.0.0.1`, with Caddy terminating TLS on ports 80/443. Beacon's REST reads
and WebSocket feed are public by design; only `/api/v1/admin/*` needs a bearer
key (`BEACON_API_KEY`), and abuse is limited by per-IP rate limits. It is
intended to sit behind that reverse proxy, listed in `server.trusted_proxies`.
Keep this in mind when assessing the severity of any findings, and never expose
the database, Redis, or the raw app port to the public internet.
