#!/usr/bin/env bash
# bake-panel.sh — copy the Sinister Panel Next.js build into the airootfs overlay
# Author: RKOJ-ELENO :: 2026-05-24
#
# What this does:
#   1. cd into the Panel dashboard source
#   2. install + build with output: 'standalone' (next.config.mjs must set it)
#   3. copy the .next/standalone/ + .next/static + public/ to airootfs/srv/sinister-panel/
#
# Pre-reqs: Node.js 20+ + npm on the build host (NOT inside Docker — Docker
# only runs mkarchiso, the JS build runs on the operator's machine for speed).

set -euo pipefail

ISO_BUILD_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PANEL_SRC="${ISO_BUILD_DIR}/../../../sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard"
STAGING="${ISO_BUILD_DIR}/../../build/_panel-staging"
DEST="${ISO_BUILD_DIR}/airootfs/srv/sinister-panel"
# Safety fix 2026-05-24 (RKOJ-ELENO): build into a side-by-side _new dir and
# atomic-swap into $DEST only on success. Prevents losing a known-good prior
# bundle if npm/build fails mid-way (idempotency rule from no-bullshit doctrine).
DEST_NEW="${DEST}.new"
DEST_OLD="${DEST}.old"

if [ ! -d "$PANEL_SRC" ]; then
  echo "!! Panel source not found at: $PANEL_SRC"
  exit 1
fi

# Safety fix 2026-05-24 (RKOJ-ELENO): cleanup trap so a half-built staging or
# half-swapped DEST_NEW gets surfaced (not silently left behind) on failure.
_bake_panel_failed() {
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "!! bake-panel.sh FAILED (exit $rc). Inspect:"
    echo "   STAGING:  $STAGING"
    echo "   DEST_NEW: $DEST_NEW (half-built; safe to rm -rf)"
    echo "   DEST:     $DEST (unchanged from prior successful run, if any)"
  fi
  return $rc
}
trap _bake_panel_failed EXIT

echo "==> Copying Panel source to staging (lane discipline: never edit sinister-panel/source)..."
rm -rf "$STAGING"
mkdir -p "$(dirname "$STAGING")"
cp -r "$PANEL_SRC" "$STAGING"

echo "==> Patching staging copy with output: 'standalone' for OS bundling..."
# Replace next.config.mjs with a thin wrapper that re-exports + injects standalone
cat >"$STAGING/next.config.mjs" <<'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    optimizePackageImports: ["lucide-react", "@tanstack/react-query"],
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${process.env.BACKEND_URL || "http://localhost:5055"}/api/:path*` },
    ];
  },
};
export default nextConfig;
EOF

echo "==> Building Sinister Panel for standalone output..."
pushd "$STAGING" >/dev/null
# Safety fix 2026-05-24 (RKOJ-ELENO): bound network calls so a flaky
# registry doesn't hang the build forever. --fetch-retries default is 2;
# bump + add explicit timeouts. Behavior is unchanged on a healthy network.
npm ci --no-audit --no-fund \
  --fetch-retries=5 \
  --fetch-retry-mintimeout=20000 \
  --fetch-retry-maxtimeout=120000 \
  --fetch-timeout=300000
npm run build
popd >/dev/null

# Safety fix 2026-05-24 (RKOJ-ELENO): build into DEST_NEW first, then
# atomic-swap. If anything below fails, prior $DEST is untouched.
echo "==> Staging into side-by-side overlay at $DEST_NEW..."
rm -rf "$DEST_NEW"
mkdir -p "$DEST_NEW"

# Standalone layout: .next/standalone/ has server.js + minimal node_modules
cp -r "$STAGING/.next/standalone/." "$DEST_NEW/"
# Static assets must be copied into the standalone tree
mkdir -p "$DEST_NEW/.next"
cp -r "$STAGING/.next/static" "$DEST_NEW/.next/static"
# Public assets
if [ -d "$STAGING/public" ]; then
  cp -r "$STAGING/public" "$DEST_NEW/public"
fi

# Sanity check: refuse to swap if server.js didn't land — build.sh requires it.
if [ ! -f "$DEST_NEW/server.js" ]; then
  echo "!! DEST_NEW missing server.js — build produced no standalone entrypoint. Aborting swap."
  exit 1
fi

echo "==> Atomic-swap DEST_NEW -> $DEST (prior bundle preserved at $DEST_OLD until next run)..."
rm -rf "$DEST_OLD"
if [ -d "$DEST" ]; then
  mv "$DEST" "$DEST_OLD"
fi
mv "$DEST_NEW" "$DEST"

echo "==> Panel bundle staged. Contents:"
ls -la "$DEST"
echo
echo "==> Ready to run ./build.sh"
