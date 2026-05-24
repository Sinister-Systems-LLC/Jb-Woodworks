<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

# Guacamole Branding Install — Two Paths

Guacamole 1.5.5 ships its UI as a packaged Java webapp. There are two ways to apply the Sinister overlay (`sinister.css` in this directory). Path B is recommended for now; Path A is deferred.

## Path A — Official extension JAR (deferred, heavy)

The supported route is a `guacamole-ext` extension JAR that registers CSS / HTML / image overrides via `guac-manifest.json`. Building one requires:

1. A JDK + Maven build environment.
2. A manifest file declaring CSS resources, mapped under `/extensions` inside `GUACAMOLE_HOME`.
3. Repackaging the JAR on every CSS change.
4. Mounting the JAR into `/etc/guacamole/extensions/` on the `sinister-guacamole` container and restarting it.

Status: **not built this turn**. When the operator gates this in, the JAR build will live at `source/docker-stack/config/guacamole/ext-src/` and the compiled `guacamole-sinister-1.0.jar` will mount into `/etc/guacamole/extensions/`.

## Path B — Reverse-proxy CSS injection (recommended for now)

Inject a `<link rel="stylesheet">` tag into every HTML response from `sinister-guacamole` using the reverse proxy fronting the stack. No container rebuild, no JAR build, no restart of guacamole itself.

### Caddy (when a Caddy reverse proxy is added to the stack)

```caddyfile
:8060 {
    reverse_proxy sinister-guacamole:8080

    # Serve the overlay from a known path:
    handle_path /sinister-branding/* {
        root * /etc/caddy/sinister-branding
        file_server
    }

    # Inject the stylesheet into the HTML <head>:
    @html header_regexp Content-Type "text/html"
    handle @html {
        response_filter {
            replace "</head>" "<link rel=\"stylesheet\" href=\"/sinister-branding/sinister.css\"></head>"
        }
    }
}
```

Mount this directory at `/etc/caddy/sinister-branding/` on the Caddy container so `sinister.css` is served at `/sinister-branding/sinister.css`.

### nginx (alternative)

```nginx
location / {
    proxy_pass http://sinister-guacamole:8080;
    sub_filter '</head>' '<link rel="stylesheet" href="/sinister-branding/sinister.css"></head>';
    sub_filter_once on;
    sub_filter_types text/html;
}
location /sinister-branding/ {
    alias /etc/nginx/sinister-branding/;
}
```

## Current state

- `sinister.css` is written and parse-validated.
- Neither Path A nor Path B is wired into `docker-compose.yml` this turn (no reverse proxy exists in the stack yet).
- Open caveat for the next turn: when a Caddy/nginx front-door container is added, wire Path B by mounting `./config/guacamole/branding:/etc/caddy/sinister-branding:ro` and adding the injection snippet above.
