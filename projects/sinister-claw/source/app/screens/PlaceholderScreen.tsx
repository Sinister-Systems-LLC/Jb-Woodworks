// Sinister Claw :: screens/PlaceholderScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, spacing, typography } from "@/theme";

interface PlaceholderProps {
  title: string;
  description: string;
  phase: string;
}

export function PlaceholderScreen({ title, description, phase }: PlaceholderProps) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.center}>
        <Text style={[typography.display, { color: colors.purpleBright, marginBottom: spacing.sm }]}>
          ◈ {title.toUpperCase()}
        </Text>
        <GlassPanel style={{ marginTop: spacing.lg, maxWidth: 360 }}>
          <Text style={typography.h1}>{title}</Text>
          <Text style={[typography.body, { marginTop: spacing.sm }]}>{description}</Text>
          <Text style={[typography.caption, { marginTop: spacing.md, color: colors.cyan }]}>
            Lands in {phase}
          </Text>
        </GlassPanel>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: spacing.lg },
});
