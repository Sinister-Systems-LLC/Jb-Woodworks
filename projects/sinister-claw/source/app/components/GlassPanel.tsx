// Sinister Claw :: components/GlassPanel.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Liquid-glass surface - BlurView wrapped with a thin purple border + inner
// shadow. iOS 18 aesthetic translated to React Native via expo-blur.

import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { BlurView } from "expo-blur";
import { colors, radii, shadows } from "@/theme";

interface GlassPanelProps {
  children: React.ReactNode;
  style?: ViewStyle;
  intensity?: number;
  variant?: "thick" | "thin";
}

export function GlassPanel({
  children,
  style,
  intensity = 24,
  variant = "thick",
}: GlassPanelProps) {
  return (
    <View style={[styles.wrapper, shadows.glass, style]}>
      <BlurView
        intensity={variant === "thin" ? 16 : intensity}
        tint="dark"
        style={styles.blur}
      >
        <View style={styles.content}>{children}</View>
      </BlurView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    borderRadius: radii.lg,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.borderGlass,
    backgroundColor: colors.bgGlass,
  },
  blur: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 16,
  },
});
