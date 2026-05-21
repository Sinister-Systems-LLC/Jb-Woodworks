// RKOJ Mobile :: components/RkojHeader.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Top header bar -- mirrors tools/sinister-rkoj-qt/.../header.py:
//   - RKOJ logo + "RKOJ Mobile" title (tappable -> drawer toggle)
//   - 3 chip tabs: Agents (●) / Phones (#) / Workstation (⚙)
//   - 4 action icons: alerts (!) / inbox (⏰) / palette (⌕) / settings (⚙)

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "@/theme";
import { RkojLogo } from "./RkojLogo";

export type ChipKey = "agents" | "phones" | "workstation";
export type ActionKey = "alerts" | "inbox" | "palette" | "settings";

export const CHIPS: { key: ChipKey; label: string; glyph: string }[] = [
  { key: "agents",      label: "Agents",      glyph: "●" },
  { key: "phones",      label: "Phones",      glyph: "#" },
  { key: "workstation", label: "Workstation", glyph: "⚙" },
];

const ACTIONS: { key: ActionKey; glyph: string; tip: string }[] = [
  { key: "alerts",   glyph: "!",  tip: "Alerts" },
  { key: "inbox",    glyph: "⏰", tip: "Inbox" },
  { key: "palette",  glyph: "⌕",  tip: "Search" },
  { key: "settings", glyph: "⚙",  tip: "Settings" },
];

interface RkojHeaderProps {
  activeChip: ChipKey;
  onChipPress: (key: ChipKey) => void;
  onMenuPress: () => void;
  onActionPress: (key: ActionKey) => void;
  alertCount?: number;
  inboxCount?: number;
}

export function RkojHeader({
  activeChip,
  onChipPress,
  onMenuPress,
  onActionPress,
  alertCount = 0,
  inboxCount = 0,
}: RkojHeaderProps) {
  const { tokens, spacing, radii } = useTheme();

  const styles = StyleSheet.create({
    root: {
      backgroundColor: tokens.bgGlass,
      borderBottomWidth: 1,
      borderBottomColor: tokens.borderGlass,
    },
    inner: {
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
    },
    topRow: {
      flexDirection: "row",
      alignItems: "center",
    },
    titleBlock: {
      flex: 1,
      marginLeft: spacing.sm,
    },
    title: {
      color: tokens.purpleHalo,
      fontSize: 18,
      fontWeight: "700",
      letterSpacing: 1.5,
    },
    subtitle: {
      color: tokens.soft,
      fontSize: 10,
      letterSpacing: 1.5,
      marginTop: 1,
    },
    actionsRow: {
      flexDirection: "row",
      alignItems: "center",
    },
    actionBtn: {
      paddingHorizontal: spacing.sm,
      paddingVertical: 6,
      borderRadius: radii.md,
      marginLeft: 2,
      minWidth: 30,
      alignItems: "center",
      flexDirection: "row",
    },
    actionGlyph: {
      color: tokens.soft,
      fontSize: 14,
    },
    actionBadge: {
      backgroundColor: tokens.purpleDeep,
      color: tokens.lightPurple,
      fontSize: 9,
      fontWeight: "700",
      paddingHorizontal: 4,
      paddingVertical: 1,
      borderRadius: radii.pill,
      marginLeft: 2,
      overflow: "hidden",
    },
    chipsRow: {
      flexDirection: "row",
      marginTop: spacing.sm,
    },
    chip: {
      flex: 1,
      paddingVertical: 7,
      paddingHorizontal: spacing.md,
      borderRadius: radii.pill,
      borderWidth: 1,
      borderColor: tokens.borderGlass,
      backgroundColor: tokens.bgGlass2,
      marginRight: spacing.sm,
      flexDirection: "row",
      justifyContent: "center",
      alignItems: "center",
    },
    chipActive: {
      backgroundColor: tokens.bgGlow,
      borderColor: tokens.purpleAccent,
    },
    chipGlyph: {
      color: tokens.soft,
      fontSize: 12,
      marginRight: 6,
    },
    chipGlyphActive: { color: tokens.purpleHalo },
    chipLabel: {
      color: tokens.soft,
      fontSize: 12,
      fontWeight: "600",
      letterSpacing: 0.5,
    },
    chipLabelActive: { color: tokens.purpleHalo },
  });

  const badgeFor = (k: ActionKey): number =>
    k === "alerts" ? alertCount : k === "inbox" ? inboxCount : 0;

  return (
    <View style={styles.root}>
      <View style={styles.inner}>
        <View style={styles.topRow}>
          <Pressable onPress={onMenuPress} hitSlop={10}>
            <RkojLogo size={36} />
          </Pressable>
          <View style={styles.titleBlock}>
            <Text style={styles.title}>RKOJ Mobile</Text>
            <Text style={styles.subtitle}>EVE · Sanctum Fleet</Text>
          </View>
          <View style={styles.actionsRow}>
            {ACTIONS.map((a) => {
              const n = badgeFor(a.key);
              return (
                <Pressable
                  key={a.key}
                  onPress={() => onActionPress(a.key)}
                  style={styles.actionBtn}
                  hitSlop={8}
                >
                  <Text style={styles.actionGlyph}>{a.glyph}</Text>
                  {n > 0 && (
                    <Text style={styles.actionBadge}>{n > 99 ? "99+" : n}</Text>
                  )}
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={styles.chipsRow}>
          {CHIPS.map((c) => {
            const active = c.key === activeChip;
            return (
              <Pressable
                key={c.key}
                onPress={() => onChipPress(c.key)}
                style={[styles.chip, active && styles.chipActive]}
              >
                <Text style={[styles.chipGlyph, active && styles.chipGlyphActive]}>
                  {c.glyph}
                </Text>
                <Text style={[styles.chipLabel, active && styles.chipLabelActive]}>
                  {c.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>
    </View>
  );
}
