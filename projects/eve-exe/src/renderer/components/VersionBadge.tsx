/**
 * Lane MX-EVE-UPDATER :: version surfacing helpers
 *
 * Three small components the renderer can drop anywhere version info is
 * required by the "version-everywhere" directive:
 *
 *   - <VersionCornerBadge />  — always-on tiny corner badge (bottom-right)
 *   - <VersionFooter />       — full-width tab footer
 *   - <AboutModal />          — stub About modal (until MX-EVE-FULL ships one)
 *
 * Plus `setWindowTitleWithVersion()` for main-process callers that own
 * BrowserWindow lifecycles (used only when not frameless).
 */

import React from 'react';
import { EVE_VERSION, EVE_VERSION_BADGE, EVE_VERSION_LABEL } from '../../shared/version';

const SANCTUM_GRADIENT = 'linear-gradient(90deg, #ff4fb3 0%, #8a2be2 100%)';

export const VersionCornerBadge: React.FC = () => (
  <div
    data-testid="eve-version-corner-badge"
    style={{
      position: 'fixed',
      bottom: 6,
      right: 8,
      fontSize: 10,
      fontFamily: 'ui-monospace, SFMono-Regular, monospace',
      padding: '2px 6px',
      borderRadius: 4,
      background: 'rgba(0,0,0,0.45)',
      color: '#ffd8f1',
      letterSpacing: 0.4,
      zIndex: 9998,
      pointerEvents: 'none',
      userSelect: 'none',
    }}
  >
    {EVE_VERSION_BADGE}
  </div>
);

export const VersionFooter: React.FC<{ tabId?: string }> = ({ tabId }) => (
  <footer
    data-testid="eve-version-footer"
    style={{
      borderTop: '1px solid rgba(255,255,255,0.08)',
      padding: '6px 12px',
      fontSize: 11,
      color: '#aaa',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}
  >
    <span>{EVE_VERSION_LABEL}</span>
    {tabId ? <span style={{ opacity: 0.7 }}>{tabId}</span> : null}
  </footer>
);

export const AboutModal: React.FC<{ open: boolean; onClose: () => void }> = ({
  open,
  onClose,
}) => {
  if (!open) return null;
  return (
    <div
      data-testid="eve-about-modal"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#1a0d1f',
          border: '1px solid rgba(255,79,179,0.4)',
          borderRadius: 10,
          padding: 24,
          minWidth: 320,
          color: '#fff',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div
          style={{
            background: SANCTUM_GRADIENT,
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            color: 'transparent',
            fontSize: 22,
            fontWeight: 700,
            marginBottom: 8,
          }}
        >
          EVE — Sinister Sanctum
        </div>
        <div style={{ fontSize: 14, marginBottom: 4 }}>Version: {EVE_VERSION}</div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>Auto-update channel: generic / sinister-vault</div>
        <button
          type="button"
          onClick={onClose}
          style={{
            marginTop: 16,
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid rgba(255,255,255,0.35)',
            background: 'transparent',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
};

/**
 * Main-process helper. Call from BrowserWindow setup ONLY when the window
 * is not frameless. Frameless windows hide the OS title bar — use the
 * corner badge there instead.
 */
export function buildWindowTitle(base = 'EVE'): string {
  return `${base} ${EVE_VERSION_BADGE}`;
}
