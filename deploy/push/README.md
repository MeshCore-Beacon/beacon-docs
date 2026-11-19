# Push relay (push.meshcorebeacon.ca)

The project's own [beacon-push](https://github.com/MeshCore-Beacon/beacon-push) relay. Self-hosted
Beacon servers send alerts here, and it forwards them to phones: iPhones straight to Apple (APNs),
Android through Firebase Cloud Messaging. Forks that ship their own app can use these files as a
starting point.

```text
/opt/docker/beacon-push/
├── docker-compose.yml   Caddy and beacon-push
├── Caddyfile            TLS for push.meshcorebeacon.ca
├── backup.sh            daily database backup
├── .env                 relay settings, chmod 600
├── secrets/             firebase.json and apns.p8, readable by uid 10001 only
├── data/                SQLite database and backups, owned by uid 10001
└── caddy/               certificates
```

## What you need

- A host with Docker, TCP 80 and 443 and UDP 443 open, and an A record for the relay's name.
- The Firebase service-account key (Android) as `secrets/firebase.json`.
- The APNs auth key (`.p8`) from developer.apple.com > Keys, with its Key ID and Team ID, as
  `secrets/apns.p8`. One key works for both sandbox and production.
- An SMTP account for registration mail.

## Set up

1. Copy this folder to `/opt/docker/beacon-push` and create the folders the relay writes to. The
   container runs as uid 10001:

   ```bash
   sudo mkdir -p data secrets caddy
   sudo chown 10001:10001 data
   ```

2. Put the two keys in `secrets/`, then lock them down:

   ```bash
   sudo chown 10001:10001 secrets/firebase.json secrets/apns.p8
   sudo chmod 600 secrets/firebase.json secrets/apns.p8
   ```

3. Create `.env` from the relay's
   [`.env.example`](https://github.com/MeshCore-Beacon/beacon-push/blob/dev/.env.example) and
   `chmod 600 .env`. The compose file already sets the listen address, database path and key
   paths. Set at least `PUSH_PUBLIC_URL`, `PUSH_TRUST_PROXY=true`, the `PUSH_APNS_*` IDs and
   topic (`meshcorebeacon.app`), the `PUSH_SMTP_*` settings and `PUSH_ADMIN_EMAIL`.

4. Start it and check it:

   ```bash
   sudo docker compose up -d
   sudo docker compose logs beacon-push
   curl -fsS https://push.meshcorebeacon.ca/healthz
   ```

   The log should show the relay starting with no config errors. `docker inspect` on the image
   shows the commit in the `org.opencontainers.image.revision` label.

5. Install the backup as a daily cron job:

   ```bash
   echo "17 3 * * * root /opt/docker/beacon-push/backup.sh >/dev/null 2>&1" | sudo tee /etc/cron.d/beacon-push-backup
   ```

   It keeps 14 days in `data/`. Copy them off the box as well; a backup on the same disk does not
   survive losing the box.

## Update

```bash
cd /opt/docker/beacon-push
sudo docker compose pull beacon-push
sudo docker compose up -d beacon-push
```

## Restore

Stop the relay, put the backup in place of `data/beacon-push.db` (owned by uid 10001), and start it
again. Device handles registered after the backup are lost, so those phones get no notices until
they register again.

## Rotate a key

Put the new file in `secrets/` with the same name and owner, then `sudo docker compose restart
beacon-push`. Delete the old key at its source (Google Cloud IAM, or developer.apple.com > Keys)
only after the relay runs on the new one.
