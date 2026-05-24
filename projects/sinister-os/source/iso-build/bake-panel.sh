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

if [ ! -d "$PANEL_SRC" ]; then
  echo "!! Panel source not found at: $PANEL_SRC"
  exit 1
fi

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
npm ci --no-audit --no-fund
npm run build
popd >/dev/null

echo "==> Staging into airootfs overlay at $DEST..."
rm -rf "$DEST"
mkdir -p "$DEST"

# Standalone layout: .next/standalone/ has server.js + minimal node_modules
cp -r "$STAGING/.next/standalone/." "$DEST/"
# Static assets must be copied into the standalone tree
mkdir -p "$DEST/.next"
cp -r "$STAGING/.next/static" "$DEST/.next/static"
# Public assets
if [ -d "$STAGING/public" ]; then
  cp -r "$STAGING/public" "$DEST/public"
fi

echo "==> Panel bundle staged. Contents:"
ls -la "$DEST"
echo
echo "==> Ready to run ./build.sh"
