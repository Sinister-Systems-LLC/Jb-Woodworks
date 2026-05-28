/**
 * Lane MX-LEO-WELCOME-BANNER :: WelcomeBanner
 *
 * Top-center banner shown every time EVE.exe boots (manual launch OR
 * auto-update relaunch). Reads its content from the main process via the
 * `GET_WELCOME_CONTEXT` IPC channel registered by src/main/welcome.ts.
 *
 * Three variants (driven by `banner_type` from the main process):
 *   - first_boot:  "Welcome, {user} — First boot. Quick tour?"
 *   - updated:     "Welcome back, {user}. Updated from v{prev} -> v{cur} — see what's new"
 *   - returning:   "Welcome back, {user}. v{cur} — last seen {relative-time}"
 *
 * UX:
 *   - Fixed position, top, full-width (matches UpdateBanner so the two never
 *     fight for the same pixel — see TopBannerSlot for coordination).
 *   - Slides down on mount, slides up on dismiss.
 *   - Sinister pink/purple gradient (matches UpdateBanner / VersionCornerBadge).
 *   - Auto-dismisses after 5s (prop-overridable). User click on X or on the
 *     CTA link dismisses immediately.
 *   - After mount, fires PLAY_WELCOME_VOICE IPC (no-op if MX-VOICE hasn't
 *     wired the renderer-side playback yet).
 *
 * Frameless-safe: WebkitAppRegion=no-drag so the close button is clickable
 * inside a draggable title bar.
 *
 * Safety: never renders raw env vars or credentials. `user` is the friendly
 * display name resolved in main (e.g. "Andrew", "Leo", "friend").
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { EVE_VERSION, EVE_VERSION_BADGE } from '../../shared/version';

type BannerType = 'first_boot' | 'updated' | 'returning';

export interface WelcomeContext {
  user: string;
  version: string;
  banner_type: BannerType;
  prev_version: string | null;
  last_seen: string | null;
  release_notes_url: string | null;
}

// Ambient declaration — preload.ts (owned by MX-EVE-FULL) is expected to
// expose these. Each call is optional so partial preloads don't crash.
declare global {
  interface Window {
    electron?: {
      getWelcomeContext?: () => Promise<WelcomeContext>;
      playWelcomeVoice?: () => Promise<{ played: boolean; clip?: string | null }>;
      // (defined by sibling lanes — listed here so TS doesn't complain about
      // re-declaration when both banners share the file)
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

const SLIDE_MS = 220;

const banner = (open: boolean): React.CSSProperties => ({
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
  transform: open ? 'translateY(0)' : 'translateY(-110%)',
  transition: `transform ${SLIDE_MS}ms ease-out`,
  WebkitAppRegion: 'no-drag' as any,
});

const linkStyle: React.CSSProperties = {
  color: '#fff',
  textDecoration: 'underline',
  marginLeft: 6,
  cursor: 'pointer',
  background: 'transparent',
  border: 'none',
  padding: 0,
  font: 'inherit',
};

const closeBtn: React.CSSProperties = {
  marginLeft: 12,
  padding: '2px 8px',
  borderRadius: 4,
  border: '1px solid rgba(255,255,255,0.45)',
  background: 'rgba(0,0,0,0.18)',
  color: '#fff',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 700,
  lineHeight: 1,
};

const versionBadgeStyle: React.CSSProperties = {
  opacity: 0.85,
  fontWeight: 400,
  marginLeft: 12,
  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
  fontSize: 12,
};

function relativeTime(iso: string | null): string {
  if (!iso) return '';
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return '';
  const deltaMs = Date.now() - then;
  if (deltaMs < 0) return 'just now';
  const sec = Math.floor(deltaMs / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const days = Math.floor(hr / 24);
  return `${days}d ago`;
}

export interface WelcomeBannerProps {
  /** Auto-dismiss timeout in ms. Default 5000. Set to 0 to disable. */
  autoDismissMs?: number;
  /** Test override — bypass the IPC fetch and render with the given context. */
  contextOverride?: WelcomeContext;
  /** Suppress the voice ping (e.g. when another banner already played it). */
  silent?: boolean;
  /** Notified when the banner finishes its exit animation. */
  onDismissed?: () => void;
}

export const WelcomeBanner: React.FC<WelcomeBannerProps> = ({
  autoDismissMs = 5000,
  contextOverride,
  silent = false,
  onDismissed,
}) => {
  const [ctx, setCtx] = useState<WelcomeContext | null>(contextOverride ?? null);
  const [open, setOpen] = useState(false);
  const [removed, setRemoved] = useState(false);
  const dismissTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const exitTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const votedRef = useRef(false);

  // Fetch context from main once.
  useEffect(() => {
    if (contextOverride) return;
    let cancelled = false;
    (async () => {
      try {
        const got = await window.electron?.getWelcomeContext?.();
        if (cancelled) return;
        if (got) {
          setCtx(got);
        } else {
          // Preload not wired yet — render nothing rather than a broken banner.
          setRemoved(true);
        }
      } catch {
        setRemoved(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [contextOverride]);

  // Slide-in + voice trigger + auto-dismiss timer.
  useEffect(() => {
    if (!ctx || removed) return;
    // Slide in on next tick so the initial translateY(-110%) is committed first.
    const showT = setTimeout(() => setOpen(true), 16);

    if (!silent && !votedRef.current) {
      votedRef.current = true;
      // Fire-and-forget. Never throws.
      void window.electron?.playWelcomeVoice?.().catch(() => undefined);
    }

    if (autoDismissMs > 0) {
      dismissTimer.current = setTimeout(() => dismiss(), autoDismissMs);
    }
    return () => {
      clearTimeout(showT);
      if (dismissTimer.current) clearTimeout(dismissTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx, removed, autoDismissMs, silent]);

  const dismiss = useCallback(() => {
    if (dismissTimer.current) {
      clearTimeout(dismissTimer.current);
      dismissTimer.current = null;
    }
    setOpen(false);
    exitTimer.current = setTimeout(() => {
      setRemoved(true);
      onDismissed?.();
    }, SLIDE_MS + 20);
  }, [onDismissed]);

  useEffect(
    () => () => {
      if (exitTimer.current) clearTimeout(exitTimer.current);
    },
    [],
  );

  const message = useMemo(() => {
    if (!ctx) return null;
    const versionStr = `v${ctx.version || EVE_VERSION}`;
    switch (ctx.banner_type) {
      case 'first_boot':
        return (
          <span>
            Welcome, <strong>{ctx.user}</strong> — first boot of EVE {versionStr}.
            <button type="button" style={linkStyle} onClick={dismiss} data-testid="eve-welcome-tour">
              Quick tour?
            </button>
          </span>
        );
      case 'updated':
        return (
          <span>
            Welcome back, <strong>{ctx.user}</strong>. Updated from v
            {ctx.prev_version ?? '?'} &rarr; {versionStr} —{' '}
            {ctx.release_notes_url ? (
              <a
                href={ctx.release_notes_url}
                target="_blank"
                rel="noreferrer"
                style={linkStyle}
                onClick={dismiss}
                data-testid="eve-welcome-release-notes"
              >
                see what's new
              </a>
            ) : (
              <button type="button" style={linkStyle} onClick={dismiss}>
                see what's new
              </button>
            )}
          </span>
        );
      case 'returning':
      default: {
        const seen = relativeTime(ctx.last_seen);
        return (
          <span>
            Welcome back, <strong>{ctx.user}</strong>. {versionStr}
            {seen ? ` — last seen ${seen}` : ''}
          </span>
        );
      }
    }
  }, [ctx, dismiss]);

  if (removed || !ctx) return null;

  return (
    <div
      style={banner(open)}
      role="status"
      aria-live="polite"
      data-testid="eve-welcome-banner"
      data-banner-type={ctx.banner_type}
    >
      {message}
      <span style={{ display: 'inline-flex', alignItems: 'center' }}>
        <span style={versionBadgeStyle} data-testid="eve-welcome-version">
          {EVE_VERSION_BADGE}
        </span>
        <button
          type="button"
          aria-label="Dismiss welcome banner"
          style={closeBtn}
          onClick={dismiss}
          data-testid="eve-welcome-close"
        >
          x
        </button>
      </span>
    </div>
  );
};

export default WelcomeBanner;
