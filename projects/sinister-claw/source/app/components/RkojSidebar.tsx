// RKOJ Mobile :: components/RkojSidebar.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Drawer body -- mirrors tools/sinister-rkoj-qt/.../sidebar.py and the
// Sinister Panel sidebar.tsx 4-section layout:
//   WORKSPACE   Overview / Agents / Projects
//   OPERATIONS  Phones / Vault / Watchdog
//   AI          Brain / MCP / Skills
//   SYSTEM      Settings / Account

import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "@/theme";
import { RkojLogo } from "./RkojLogo";

export type SidebarKey =
  | "overview" | "agents" | "projects"
  | "phones" | "vault" | "watchdog"
  | "brain" | "mcp" | "skills"
  | "settings" | "account";

export interface SidebarSection {
  label: string;
  items: { key: SidebarKey; label: string; glyph?: string }[];
}

export const SIDEBAR_SECTIONS: SidebarSection[] = [
  { label: "WORKSPACE", items: [
    { key: "overview", label: "Overview", glyph: "◈" },
    { key: "agents",   label: "Agents",   glyph: "●" },
    { key: "projects", label: "Projects", glyph: "◆" },
  ]},
  { label: "OPERATIONS", items: [
    { key: "phones",   label: "Phones",   glyph: "#" },
    { key: "vault",    label: "Vault",    glyph: "▣" },
    { key: "watchdog", label: "Watchdog", glyph: "◉" },
  ]},
  { label: "AI", items: [
    { key: "brain",  label: "Brain",  glyph: "✦" },
    { key: "mcp",    label: "MCP",    glyph: "⌬" },
    { key: "skills", label: "Skills", glyph: "▲" },
  ]},
  { label: "SYSTEM", items: [
    { key: "settings", label: "Settings", glyph: "⚙" },
    { key: "account",  label: "Account",  glyph: "◐" },
  ]},
];

interface RkojSidebarProps {
  activeKey: SidebarKey;
  onSelect: (key: SidebarKey) => void;
}

export function RkojSidebar({ activeKey, onSelect }: RkojSidebarProps) {
  const { tokens, spacing, radii, typography } = useTheme();

  const styles = StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: tokens.bgGlass,
      borderRightWidth: 1,
      borderRightColor: tokens.borderGlass,
    },
    mascot: {
      alignItems: "center",
      paddingTop: spacing.lg,
      paddingBottom: spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: tokens.bgGlass2,
    },
    eve: {
      color: tokens.purpleHalo,
      fontSize: 14,
      fontWeight: "700",
      letterSpacing: 4,
      marginTop: spacing.sm,
    },
    rkoj: {
      color: tokens.purpleAccent,
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 3,
      marginTop: 2,
    },
    section: {
      color: tokens.dim,
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 2,
      paddingHorizontal: spacing.lg,
      paddingTop: spacing.lg,
      paddingBottom: spacing.xs,
    },
    item: {
      paddingHorizontal: spacing.md,
      paddingVertical: 9,
      marginHorizontal: spacing.sm,
      borderRadius: radii.lg,
      flexDirection: "row",
      alignItems: "center",
      borderWidth: 1,
      borderColor: "transparent",
    },
    itemActive: {
      backgroundColor: tokens.bgGlow,
      borderColor: tokens.borderGlass,
    },
    itemGlyph: {
      color: tokens.purpleAccent,
      width: 20,
      textAlign: "center",
      fontSize: 13,
    },
    itemLabel: {
      color: tokens.soft,
      fontSize: 13,
      marginLeft: spacing.sm,
    },
    itemLabelActive: {
      color: tokens.purpleHalo,
      fontWeight: "600",
    },
  });

  return (
    <SafeAreaView style={styles.root} edges={["top", "left", "bottom"]}>
      <View style={styles.mascot}>
        <RkojLogo size={48} />
        <Text style={styles.eve}>E V E</Text>
        <Text style={styles.rkoj}>R K O J</Text>
      </View>
      <ScrollView showsVerticalScrollIndicator={false}>
        {SIDEBAR_SECTIONS.map((sec) => (
          <View key={sec.label}>
            <Text style={styles.section}>{sec.label}</Text>
            {sec.items.map((it) => {
              const active = it.key === activeKey;
              return (
                <Pressable
                  key={it.key}
                  onPress={() => onSelect(it.key)}
                  style={[styles.item, active && styles.itemActive]}
                >
                  <Text style={styles.itemGlyph}>{it.glyph ?? "·"}</Text>
                  <Text style={[styles.itemLabel, active && styles.itemLabelActive]}>
                    {it.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        ))}
        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}
