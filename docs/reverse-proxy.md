# Reverse proxy

However you front Beacon, the proxy has the same three jobs:

- Send `/api/*` and `/ws` to beacon-server (port `8080`) and everything else to beacon-web. `/ws`
  is a WebSocket, so the proxy must pass the upgrade through and keep idle sockets open for more
  than 90 seconds (the browser pings every 30 seconds; the server drops a socket after 90 seconds
  of silence).
- Overwrite `X-Real-IP` with the connecting client's address and pass the original `Host`
  header. beacon-server ignores `X-Forwarded-For` and `True-Client-IP` entirely.
- Be listed in beacon-server's `server.trusted_proxies` (CIDR: `/32` for one IPv4 host, `/128`
  for IPv6). Only those peers may set `X-Real-IP`. Get this wrong and every visitor shares the
  proxy's rate limit and WebSocket connection cap.

`VITE_API_BASE` and `VITE_WS_URL` then point at the public paths, for example
`https://beacon.example.com/api/v1` and `wss://beacon.example.com/ws`.

## Caddy

Caddy is the default in both Docker deployments:
[`Caddyfile.proxy`](../docker-deployment-type1/data/Caddy/CaddyFile/Caddyfile.proxy). The
relevant part:

```caddy
handle /api/* {
	reverse_proxy app:8080 {
		header_up X-Real-IP {remote_host}
	}
}
handle /ws {
	reverse_proxy app:8080 {
		header_up X-Real-IP {remote_host}
	}
}
handle {
	reverse_proxy web:80
}
```

Caddy handles the WebSocket upgrade and keeps the `Host` header by itself. It reaches the app
over the compose network, so `data/app/config.yaml` trusts that subnet:

```yaml
server:
  trusted_proxies: [172.30.0.0/24]
```

## Behind a CDN

Behind Cloudflare or another CDN, `{remote_host}` is the CDN, not the visitor. The comment at
the top of `Caddyfile.proxy` shows how to trust the CDN's ranges and forward `{client_ip}`
instead. The same idea applies to nginx and Apache: trust the CDN at the edge and pass its
validated client address, never a header the client could have set.

## nginx

[`app_config/nginx/beacon.conf`](../app_config/nginx/beacon.conf) is a complete server block for
nginx on the host in front of the containers. The essentials:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
location = /ws {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;   # map is in the example file
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 120s;
}
location / {
    proxy_pass http://127.0.0.1:8081;   # beacon-web published on loopback
}
```

nginx sends the upstream address as `Host` by default, which fails the WebSocket origin check,
so keep `proxy_set_header Host $host`. When nginx reaches the containers through published
ports, the app sees the Docker network's gateway as the peer, so trust the compose subnet
(`[172.30.0.0/24]`). For a beacon-server running directly on the host, use
`["127.0.0.1/32", "::1/128"]`.

## Apache

Apache works the same way. [`app_config/apache/analyzer-vhost.snippet.conf`](../app_config/apache/analyzer-vhost.snippet.conf)
is a working virtual host snippet, including the `RequestHeader set X-Real-IP` line that
replaces whatever the client sent.

## Rate limits and connection caps

REST requests under `/api/v1` are rate limited per client IP, 300 a minute by default. IPv6
clients share one budget per /64. A client over the limit gets `429` with `rate_limited` in the
body and a `Retry-After` header.

WebSocket has two separate limits. At most 5 open connections per IP: a connection over the cap
is accepted and then closed with code `1013` (try again later) before `hello`. At most 10
upgrade attempts per IP per minute: beyond that the handshake gets `429` with `Retry-After: 60`.
Both are set under `websocket:` in `config.yaml`.

Behind a reverse proxy all of these only work with `server.trusted_proxies` set, or every
visitor counts as the proxy's IP. Without it every visitor shares the proxy's budget and the
site gets 429s under normal load. Beacon logs a warning at startup when limits are on and no
proxy is trusted, and once at runtime when a request carries forwarding headers it is ignoring.

## Split origins

When the web app and the API are on different hosts, browsers may only open `/ws` from the
page's own host unless the web origin is listed in `websocket.allowed_origins`
(`https://*.example.com` covers every subdomain). REST CORS allows any origin by default.

## Abuse controls

Access logs, a manual block list and fail2ban jails for both Caddy and Apache are in
[`app_config/fail2ban/`](../app_config/fail2ban/README.md).
