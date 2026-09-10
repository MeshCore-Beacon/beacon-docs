# Beacon API abuse controls: edge log, block list, fail2ban

Staged posture: **log → throttle (beacon-server 429s) → firewall-ban repeat offenders.** Real
users include mobile users behind carrier CGNAT, so thresholds are generous and bans are short.

Two deployment shapes, two file sets:

| Shape | Edge | Files |
|---|---|---|
| Caddy in Docker (type 1, e.g. dev.meshcore.ca) | `docker-deployment-type1/data/Caddy/…` | `fail2ban/caddy/` |
| Host Apache in front of the containers (analyzer.meshmapper.net) | `app_config/apache/analyzer-vhost.snippet.conf` | `fail2ban/apache/` |

## 1. Edge: log + client-IP hygiene + manual block list

**Caddy.** `Caddyfile.proxy` now writes a JSON access log to `data/Caddy/logs/access.json`, strips
`True-Client-IP` and overwrites `X-Real-IP` on the way to the app (beacon-server trusts those headers
for the client IP), and 403s anything listed in `data/Caddy/conf.d/blocklist.caddy`. The compose
file mounts `conf.d` and `logs`; new mounts need one `docker compose up -d caddy`, after that:

```bash
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose exec caddy caddy reload   --config /etc/caddy/Caddyfile
```

**Apache.** Apply the snippet to the `*:443` vhost and create `/etc/apache2/beacon-blocklist.conf`
and `/etc/apache2/beacon-blocklist-ua.conf`, then `apachectl configtest && systemctl reload apache2`.

**Two ways to block.** By source IP (`remote_ip` / `Require not ip`) or by User-Agent signature
(`@blocked_ua` / `SetEnvIfNoCase`). A scraper that identifies itself, like the
`mesh.hansimgamr.net am-i-connected` client found on day 0, is better blocked by UA: it survives an
IP change and leaves the operator's own browser alone. Both apply to `/api/*` and `/ws` only.

Smoke test on either box (chi's log line must show the real client IP, not 1.2.3.4):

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'True-Client-IP: 1.2.3.4' -H 'X-Real-IP: 1.2.3.4' https://$DOMAIN/api/v1/scopes
docker compose logs --tail 5 app
```

## 2. fail2ban

Three jails per box, same thresholds:

| Jail | Counts | Trips at | Why |
|---|---|---|---|
| `beacon-api-flood` | every `/api/` request | 900 in 60 s | a browser session peaks ~150 in its first 30 s (auto-chained pages), then ~2/min; 15 req/s for a full minute is no browser |
| `beacon-api-429` | `/api/` responses with status 429 | 300 in 10 min | only fires on clients that keep hammering through the server's throttle |
| `beacon-api-sustained` | every `/api/` request | 1,000 in 1 h | a paced scraper (the day-0 Pi ran ~135/min for hours) never trips the flood rule; real sessions peak ~300/h |

Both use `backend = polling` (the Debian default `systemd` cannot tail files) and a flat 10 min ban.
Install:

```bash
sudo cp filter.d/*.conf /etc/fail2ban/filter.d/
sudo cp jail.d/beacon-http.conf /etc/fail2ban/jail.d/
# Caddy box only: the ban chain must come up after dockerd
sudo install -D fail2ban.service.d/after-docker.conf /etc/systemd/system/fail2ban.service.d/after-docker.conf
sudo systemctl daemon-reload && sudo systemctl restart fail2ban
sudo fail2ban-regex <logpath> /etc/fail2ban/filter.d/beacon-api-flood.conf   # date hits > 0, matches == /api/ lines
sudo fail2ban-client status beacon-api-flood
```

**Observe first.** The Caddy jail file ships with `banaction = dummy`; on the Apache box add the same
line per jail. Would-be bans land in `/var/run/fail2ban/fail2ban.dummy`. Run 3–7 days; every IP
there must be an obvious scraper, otherwise raise `maxretry`.

**Enforce.** Caddy box: traffic to Docker-published ports is DNAT'ed through the FORWARD path, which
the default nftables action (input hook) never sees, so switch to
`banaction = nftables[type=allports, chain=f2b-forward, chain_hook=forward]` (a second chain in the
existing `f2b-table`; `iptables-allports[chain=DOCKER-USER]` is equivalent). Apache box: remove the
`dummy` line, the inherited nftables input-hook action works because Apache listens on the host.
Then:

```bash
sudo fail2ban-client reload
sudo nft list table inet f2b-table          # addr-set-beacon-api-flood present
sudo fail2ban-client set beacon-api-flood banip <phone-on-cellular>   # site unreachable from it
sudo fail2ban-client set beacon-api-flood unbanip <phone-on-cellular>
```

Once beacon-server's per-IP limit is live, re-derive the flood `maxretry` as ~3× the per-minute
allowance. Consider `bantime.increment` only after a clean week.

## 3. Finding scrapers by hand

Caddy JSON (`LOG=/opt/docker/beacon/data/Caddy/logs/access.json`):

```bash
# top IPs, last hour
jq -r 'select(.ts > (now-3600)) | .request.remote_ip' "$LOG" | sort | uniq -c | sort -rn | head -20
# IPs with >200 /api/ hits and zero /ws upgrades, last 24h (the SPA always opens a socket)
jq -r 'select(.ts > (now-86400)) | [.request.remote_ip, (.request.uri|startswith("/api/")|tostring), (.request.uri=="/ws"|tostring)] | @tsv' "$LOG" \
 | awk -F'\t' '{a[$1]+=($2=="true"); w[$1]+=($3=="true")} END {for (ip in a) if (a[ip]>200 && w[ip]==0) print a[ip], ip}' | sort -rn | head
# IPs asking limit= above 200 (the SPA never does)
jq -r '(.request.uri|capture("[?&]limit=(?<n>[0-9]+)")?) as $c | select($c != null and ($c.n|tonumber) > 200) | .request.remote_ip' "$LOG" | sort | uniq -c | sort -rn | head
# Referer / Origin hosts hitting /api/ (a reverse-proxying site usually forwards its visitors' Referer)
jq -r 'select(.request.uri|startswith("/api/")) | [(.request.headers.Referer[0] // "-"), (.request.headers.Origin[0] // "-")] | @tsv' "$LOG" \
 | sed -E 's#(https?://[^/[:space:]]+)[^[:space:]]*#\1#g' | sort | uniq -c | sort -rn | head -30
# IPs with >50 /api/ hits and no SPA/asset fetch, last 24h (a native app looks like this too)
jq -r 'select(.ts > (now-86400)) | [.request.remote_ip, (.request.uri|startswith("/api/")|tostring), ((.request.uri|startswith("/api/")|not) and .request.uri!="/ws"|tostring)] | @tsv' "$LOG" \
 | awk -F'\t' '{a[$1]+=($2=="true"); s[$1]+=($3=="true")} END {for (ip in a) if (a[ip]>50 && s[ip]==0) print a[ip], ip}' | sort -rn | head
# peak /api/ requests per IP per minute: calibrate maxretry / the server limit at ~3x the largest legitimate bucket
jq -r 'select(.request.uri|startswith("/api/")) | "\(.request.remote_ip) \((.ts/60)|floor)"' "$LOG" | sort | uniq -c | sort -rn | head -20
# spoof attempts (client-sent IP headers are logged as received)
jq -r 'select(.request.headers["True-Client-IP"] or .request.headers["X-Real-IP"]) | [.request.remote_ip, (.request.headers["True-Client-IP"][0]//"-")] | @tsv' "$LOG" | sort | uniq -c | sort -rn | head
```

Apache combined (`LOG=/var/log/apache2/analyzer-ssl-access.log`, run with sudo; `$7` is the request
path, `$11` the quoted Referer):

```bash
awk '{print $1}' "$LOG" | sort | uniq -c | sort -rn | head -20
awk '$7 ~ /^\/api\// {a[$1]++} $7=="/ws" {w[$1]++} END {for (ip in a) if (a[ip]>200 && !(ip in w)) print a[ip], ip}' "$LOG" | sort -rn | head
awk '$7 ~ /^\/api\/.*[?&]limit=/ {match($7,/[?&]limit=[0-9]+/); n=substr($7,RSTART+7,RLENGTH-7); if (n+0>200) print $1}' "$LOG" | sort | uniq -c | sort -rn | head
awk '$7 ~ /^\/api\// {print $11}' "$LOG" | sed -E 's#"(https?://[^/"]+).*#\1#' | sort | uniq -c | sort -rn | head -30
awk '$7 ~ /^\/api\// {a[$1]++} $7 !~ /^\/api\// && $7!="/ws" {s[$1]++} END {for (ip in a) if (a[ip]>50 && !(ip in s)) print a[ip], ip}' "$LOG" | sort -rn | head
awk '$7 ~ /^\/api\// {print $1, substr($4,2,17)}' "$LOG" | sort | uniq -c | sort -rn | head -20
```

A site that reverse-proxies the API shows up as one high-volume, API-only IP with no `/ws` and
usually a foreign Referer. Put it in the block list and reload.

Operations: `fail2ban-client status <jail>`, `fail2ban-client get <jail> banip --with-time`,
`fail2ban-client set <jail> unbanip <ip>`, `fail2ban-client reload <jail>` after editing a filter.
