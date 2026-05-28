/**
 * Lane MX-LEO-WELCOME-BANNER :: renderer root
 *
 * NOTE: MX-EVE-FULL has not shipped its own App.tsx yet. This file is the
 * scaffold root the welcome lane needs in order to mount its banner. When
 * MX-EVE-FULL lands, it should EITHER:
 *
 *   (a) merge the TopBannerSlot component below into its own root, OR
 *   (b) keep this file as the canonical root and import its tab tree as
 *       <AppTabs /> inside the marked slot.
 *
 * Why TopBannerSlot exists
 * ------------------------
 * Two lanes want the top strip of the window:
 *   - MX-EVE-UPDATER       -> UpdateBanner (UPDATE_READY + welcome-back hack)
 *   - MX-LEO-WELCOME-BANNER -> WelcomeBanner (proper per-boot welcome)
 *
 * Without coordination they would stack and Leo would see two pink bars.
 * TopBannerSlot enforces a single-slot policy:
 *
 *   1. If UPDATE_READY has fired AND we have a pending version -> show
 *      UpdateBanner exclusively (operator must decide before anything else).
 *   2. Otherwise -> show WelcomeBanner until it auto-dismisses or the user
 *      closes it.
 *
 * The slot is mounted BEFORE the tab tree so it sits visually above tabs but
 * doesn't push them around (banner is position: fixed).
 */

import React, { useEffect, useState } from 'react';
import { WelcomeBanner } from './components/WelcomeBanner';
import { UpdateBanner } from './components/UpdateBanner';
import { VersionCornerBadge } from './components/VersionBadge';

/**
 * Single coordinator for the top banner slot. UpdateBanner takes priority
 * when an update is pending; otherwise WelcomeBanner owns the slot.
 *
 * UpdateBanner is rendered unconditionally (it subscribes to UPDATE_READY
 * internally and returns null until something is pending) — we just need
 * to suppress the welcome banner when an update is in-flight.
 */
export const TopBannerSlot: React.FC = () => {
  const [updatePending, setUpdatePending] = useState(false);
  const [welcomeDismissed, setWelcomeDismissed] = useState(false);

  useEffect(() => {
    const off = window.electron?.onUpdateReady?.(() => setUpdatePending(true));
    return () => {
      try {
        off?.();
      } catch {
        /* preload may not implement an unsubscribe — ignore */
      }
    };
  }, []);

  return (
    <>
      {/* UpdateBanner always renders; it self-hides until UPDATE_READY arrives. */}
      <UpdateBanner />
      {/* WelcomeBanner only renders when no update is pending and it hasn't been dismissed. */}
      {!updatePending && !welcomeDismissed ? (
        <WelcomeBanner onDismissed={() => setWelcomeDismissed(true)} />
      ) : null}
    </>
  );
};

/**
 * Root component. MX-EVE-FULL's tab tree should be mounted in <AppTabs />.
 * Until then we render a quiet placeholder so dev sessions still launch.
 */
const App: React.FC = () => {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0d0612',
        color: '#f5e8ff',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
    >
      <TopBannerSlot />

      {/* === SLOT: MX-EVE-FULL tab tree mounts here === */}
      <main style={{ paddingTop: 56 /* leave room for the fixed banner */ }}>
        {/* Placeholder content — MX-EVE-FULL replaces with <AppTabs /> */}
        <div style={{ padding: 24, opacity: 0.65 }}>
          EVE renderer scaffold (MX-LEO-WELCOME-BANNER). Tab tree will mount here
          when MX-EVE-FULL ships its renderer.
        </div>
      </main>

      <VersionCornerBadge />
    </div>
  );
};

export default App;
