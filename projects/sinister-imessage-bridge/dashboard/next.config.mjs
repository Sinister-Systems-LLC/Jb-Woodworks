// next.config.mjs — Sinister iMessage Bridge dashboard
// RKOJ-ELENO :: 2026-05-24
/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: true },
  productionBrowserSourceMaps: false,
  images: { unoptimized: true },
  // Proxy /api/* to the local bridge_daemon on 127.0.0.1:8731 so the
  // dashboard can `fetch('/api/threads')` without CORS plumbing.
  async rewrites() {
    const target = process.env.BRIDGE_DAEMON_URL ?? 'http://127.0.0.1:8731';
    return [
      { source: '/api/:path*', destination: `${target}/:path*` },
    ];
  },
};
export default nextConfig;
