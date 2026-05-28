/**
 * Lane MX-EVE-UPDATER :: canonical version constant
 *
 * Single source of truth for the EVE.exe runtime version string.
 *
 * Resolution order (first match wins):
 *   1. process.env.EVE_VERSION             (compile-time override / CI builds)
 *   2. require('../../package.json').version  (canonical; bumped per release)
 *   3. '0.0.0-dev'                          (fallback when package.json is missing
 *      during pre-MX-EVE-FULL bootstrap)
 *
 * IMPORTANT:
 *   - Anything that displays, logs, reports, or transmits a version MUST import
 *     EVE_VERSION from this module. No string literals anywhere else.
 *   - electron-builder will inline package.json#version at build time; this
 *     module just re-exports it so the renderer + main process agree.
 */

let resolved = '0.0.0-dev';

try {
  if (typeof process !== 'undefined' && process.env && process.env.EVE_VERSION) {
    resolved = String(process.env.EVE_VERSION);
  } else {
    // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
    const pkg = require('../../package.json');
    if (pkg && typeof pkg.version === 'string') {
      resolved = pkg.version;
    }
  }
} catch {
  // package.json not present yet (pre-MX-EVE-FULL); keep fallback.
}

export const EVE_VERSION: string = resolved;

/** Convenience: 'v1.2.3' string for UI badges. */
export const EVE_VERSION_BADGE: string = `v${EVE_VERSION}`;

/** Display label including project name. */
export const EVE_VERSION_LABEL: string = `EVE ${EVE_VERSION_BADGE}`;
