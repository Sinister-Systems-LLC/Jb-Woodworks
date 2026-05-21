// Sinister Claw :: screens/PanelScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Mobile view of Sinister Panel. v1 is a WebView pointed at the configured
// Panel URL (default https://snap.sinijkr.com). The Panel team owns the
// mobile-responsive treatment; this screen is the transport.
//
// PH-mirror-2 will replace this with native Claw screens hitting Panel's REST
// API directly so we own the mobile UI. Same pattern as Mind eventually goes
// native too.

import React, { useEffect, useState } from "react";
import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import * as SecureStore from "expo-secure-store";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, spacing, typography } from "@/theme";

const STORE_KEY_PANEL_URL = "claw.panel.url";
const DEFAULT_PANEL_URL = "https://snap.sinijkr.com";

export function PanelScreen() {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const saved = await SecureStore.getItemAsync(STORE_KEY_PANEL_URL);
      setUrl((saved && saved.trim()) || DEFAULT_PANEL_URL);
    })();
  }, []);

  if (!url) {
    return (
      <SafeAreaView style={styles.container}>
        <GlassPanel style={{ margin: spacing.lg }}>
          <Text style={typography.body}>Loading Panel...</Text>
        </GlassPanel>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <WebView
        source={{ uri: url }}
        style={styles.web}
        startInLoadingState
        renderLoading={() => (
          <GlassPanel style={{ margin: spacing.lg }}>
            <Text style={typography.body}>Connecting to {url}...</Text>
          </GlassPanel>
        )}
        renderError={(e) => (
          <GlassPanel style={{ margin: spacing.lg }}>
            <Text style={{ color: colors.red }}>Failed to load Panel: {e}</Text>
            <Text style={[typography.caption, { marginTop: spacing.sm }]}>
              Settings tab → set Panel URL. Default: {DEFAULT_PANEL_URL}
            </Text>
          </GlassPanel>
        )}
        // Allow third-party cookies so Panel session sticks
        sharedCookiesEnabled
        thirdPartyCookiesEnabled
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  web: { flex: 1, backgroundColor: colors.bgDeep },
});
