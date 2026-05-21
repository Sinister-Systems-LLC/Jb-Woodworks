// Sinister Claw :: screens/MindScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Mind tab - WebView pointing at the operator's Sinister Mind Flask server
// over Tailscale. The full D3 graph + sidebar work on mobile.

import React, { useEffect, useState } from "react";
import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, spacing, typography } from "@/theme";
import { getBaseUrl } from "@/api/sanctum";

export function MindScreen() {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const base = await getBaseUrl();
      // Mind defaults to port 5079 on operator's PC
      const mindUrl = base.replace(/:\d+$/, "") + ":5079/";
      setUrl(mindUrl);
    })();
  }, []);

  if (!url) {
    return (
      <SafeAreaView style={styles.container}>
        <GlassPanel style={{ margin: spacing.lg }}>
          <Text style={typography.body}>Loading Mind...</Text>
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
            <Text style={{ color: colors.red }}>Failed to load: {e}</Text>
            <Text style={[typography.caption, { marginTop: spacing.sm }]}>
              Is Sinister Mind running on the operator's PC? Settings tab → check Tailscale base URL.
            </Text>
          </GlassPanel>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  web: { flex: 1, backgroundColor: colors.bgDeep },
});
