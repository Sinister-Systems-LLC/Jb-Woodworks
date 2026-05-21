// RKOJ Mobile :: components/SplashOverlay.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Animated splash -- Sanctum purple gradient backdrop, RKOJ logo center,
// "Sinister Sanctum" subtitle. Caller dismisses it via `visible={false}`
// after first paint. Uses expo-linear-gradient (already in deps).

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useTheme } from "@/theme";
import { RkojLogo } from "./RkojLogo";

interface SplashOverlayProps {
  visible: boolean;
}

export function SplashOverlay({ visible }: SplashOverlayProps) {
  const { tokens, spacing } = useTheme();
  if (!visible) return null;

  const styles = StyleSheet.create({
    root: {
      ...StyleSheet.absoluteFillObject,
      alignItems: "center",
      justifyContent: "center",
      zIndex: 999,
    },
    title: {
      color: tokens.purpleHalo,
      fontSize: 28,
      fontWeight: "700",
      letterSpacing: 6,
      marginTop: spacing.xl,
    },
    subtitle: {
      color: tokens.soft,
      fontSize: 12,
      fontWeight: "500",
      letterSpacing: 3,
      marginTop: spacing.sm,
    },
    eve: {
      color: tokens.purpleAccent,
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 4,
      marginTop: spacing.lg,
    },
  });

  return (
    <View style={styles.root}>
      <LinearGradient
        colors={[tokens.bg, tokens.bgGlow, tokens.bg]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.0, y: 0.0 }}
        end={{ x: 1.0, y: 1.0 }}
      />
      <RkojLogo size={120} />
      <Text style={styles.title}>R K O J</Text>
      <Text style={styles.subtitle}>SINISTER · SANCTUM</Text>
      <Text style={styles.eve}>E V E</Text>
    </View>
  );
}
