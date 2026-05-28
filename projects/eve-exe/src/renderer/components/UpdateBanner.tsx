/**
 * Lane MX-EVE-UPDATER :: UpdateBanner
 *
 * Two responsibilities:
 *
 *   (a) UPDATE_READY banner — listens for the main-process IPC event emitted
 *       by `src/main/updater.ts` after electron-updater has downloaded a new
 *       EVE.exe. Sticky top banner: "EVE v{newVer} is ready. Restart to
 *       apply. [Restart Now] [Later]". "Restart Now" calls
 *       window.electron.applyUpdate(). "Later" hides until next session.
 *
 *   (b) Welcome-back banner — on mount, compares EVE_VERSION to the cached
 *       prior version in `~/.eve/last-version.json`. If different, shows
 *       "Welcome back — updated to v{ver} (Sinister Sanctum)" for 5s. Then
 *       writes the new version into the cache for next boot.
 *
 * Style: pink/purple sanctum gradient inline (theme tokens TBD by the design
 * lane). Z-index 9999 so it sits above any tab chrome. Frameless-safe.
 *
 * Preload contract (defined by MX-EVE-FULL preload.ts — this file documents
 * what it consumes):
 *   window.electron = {
 *     onUpdateReady(cb: (info: { version: string; currentVersion: string }) => void): () => void,
 *     applyUpdate(): Promise<{ applied: boolean; reason?: string }>,
 *     getVersion(): Promise<string>,
 *     readPriorVersion(): Promise<string | null>,   // reads ~/.eve/last-version.json
 *     writeCurrentVersion(v: string): Promise<void>, // writes ~/.eve/last-version.json
 *   };
 */

import React, { useCallback, useEffect, useState } from 'react';
import { EVE_VERSION, EVE_VERSION_BADGE } from '../../shared/version';

// Minimal ambient declaration so this file type-checks before preload.d.ts exists.
declare global {
  interface Window {
    electron?: {
      onUpdateReady?: (
        cb: (info: { version: string; currentVersion: string }) => void,
      ) => () => void;
      applyUpdate?: () => Promise<{ applied: boolean; reason?: string }>;
      getVersion?: () => Promise<string>;
      readPriorVersion?: () => Promise<string | null>;
      writeCurrentVersion?: (v: string) => Promise<void>;
    };
  }
}

const SANCTUM_GRADIENT = 'linear-gradient(90deg, #ff4fb3 0%, #8a2be2 100%)';

const BANNER_BASE: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  zIndex: 9999,
  padding: '10px 16px',
  color: '#fff',
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  fontSize: 14,
  fontWeight: 500,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  boxShadow: '0 2px 12px rgba(0,0,0,0.35)',
  background: SANCTUM_GRADIENT,
  WebkitAppRegion: 'no-drag' as any,
};

const BTN: React.CSSProperties = {
  marginLeft: 8,
  padding: '6px 12px',
  borderRadius: 6,
  border: '1px solid rgba(255,255,255,0.45)',
  background: 'rgba(0,0,0,0.18)',
  color: '#fff',
  cursor: 'pointer',
  fontSize: 13,
  fontWeight: 600,
};

type PendingState = { version: string } | null;

export const UpdateBanner: React.FC = () => {
  const [pending, setPending] = useState<PendingState>(null);
  const [dismissedThisSession, setDismissedThisSession] = useState(false);
  const [welcomeBack, setWelcomeBack] = useState<string | null>(null);

  // (a) Subscribe to main-process UPDATE_READY events.
  useEffect(() => {
    const sub = window.electron?.onUpdateReady;
    if (!sub) return;
    const off = sub((info) => {
      setPending({ version: info.version });
    });
    return () => off?.();
  }, []);

  // (b) Welcome-back detection on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const prior = (await window.electron?.readPriorVersion?.()) ?? null;
        if (cancelled) return;
        if (prior && prior !== EVE_VERSION) {
          setWelcomeBack(EVE_VERSION);
          setTimeout(() => !cancelled && setWelcomeBack(null), 5000);
        }
        await window.electron?.writeCurrentVersion?.(EVE_VERSION);
      } catch {
        // Non-fatal: cache helpers may be missing during early bootstrap.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onRestart = useCallback(async () => {
    try {
      await window.electron?.applyUpdate?.();
    } catch {
      /* swallow — main will surface error via status IPC */
    }
  }, []);

  const onLater = useCallback(() => setDismissedThisSession(true), []);

  // Welcome-back has highest visual priority but auto-dismisses; render first.
  if (welcomeBack) {
    return (
      <div style={BANNER_BASE} role="status" aria-live="polite" data-testid="eve-welcome-back">
        <span>
          Welcome back — updated to v{welcomeBack} (Sinister Sanctum)
        </span>
        <span style={{ opacity: 0.85, fontWeight: 400 }}>{EVE_VERSION_BADGE}</span>
      </div>
    );
  }

  if (!pending || dismissedThisSession) return null;

  return (
    <div style={BANNER_BASE} role="alert" aria-live="assertive" data-testid="eve-update-ready">
      <span>
        UPDATING — EVE v{pending.version} is ready. Restart to apply.
      </span>
      <span>
        <button type="button" style={BTN} onClick={onRestart} data-testid="eve-update-restart">
          Restart Now
        </button>
        <button type="button" style={BTN} onClick={onLater} data-testid="eve-update-later">
          Later
        </button>
      </span>
    </div>
  );
};

export default UpdateBanner;
