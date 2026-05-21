// RKOJ Mobile :: views/WorkstationTabView.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Grid of action tiles -- Vault / Brain / Watchdog Status / Backups / MCP Probe.
// Each tile calls the forge bridge and renders the result inline.

import React, { useCallback, useState } from "react";
import {
  ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import { useTheme } from "@/theme";
import {
  ActionResult, vaultStatus, brainProbe, watchdogStatus, backupsRun, mcpProbe,
} from "@/api/workstation";

interface Tile {
  key: string;
  glyph: string;
  label: string;
  caption: string;
  run: () => Promise<ActionResult>;
}

export function WorkstationTabView() {
  const { tokens, spacing, radii, typography } = useTheme();
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ActionResult>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const tiles: Tile[] = [
    { key: "vault",    glyph: "▣", label: "VAULT",    caption: "1 TB collaborative store",   run: vaultStatus },
    { key: "brain",    glyph: "✦", label: "BRAIN",    caption: "knowledge index probe",      run: brainProbe },
    { key: "watchdog", glyph: "◉", label: "WATCHDOG", caption: "heartbeat watcher status",   run: watchdogStatus },
    { key: "backups",  glyph: "↻", label: "BACKUPS",  caption: "trigger nightly snapshot",   run: backupsRun },
    { key: "mcp",      glyph: "⌬", label: "MCP",      caption: "probe MCP server health",    run: mcpProbe },
  ];

  const onPress = useCallback(async (t: Tile) => {
    setBusyKey(t.key);
    setErrors((e) => { const n = { ...e }; delete n[t.key]; return n; });
    try {
      const r = await t.run();
      setResults((s) => ({ ...s, [t.key]: r }));
    } catch (e: unknown) {
      setErrors((s) => ({ ...s, [t.key]: e instanceof Error ? e.message : String(e) }));
    } finally {
      setBusyKey(null);
    }
  }, []);

  const styles = StyleSheet.create({
    root: { flex: 1, backgroundColor: tokens.bg },
    grid: { padding: spacing.md },
    tile: {
      backgroundColor: tokens.bgGlass,
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.lg,
      padding: spacing.md,
      marginBottom: spacing.md,
    },
    tileTop: { flexDirection: "row", alignItems: "center" },
    glyph: {
      color: tokens.purpleAccent, fontSize: 22, fontWeight: "700",
      width: 36, textAlign: "center",
    },
    label: {
      color: tokens.purpleHalo, fontSize: 14, fontWeight: "700", letterSpacing: 1.5,
      marginLeft: spacing.sm,
    },
    caption: { color: tokens.soft, fontSize: 11, marginTop: 2, marginLeft: 44 },
    btnRow: { flexDirection: "row", marginTop: spacing.sm, marginLeft: 44 },
    btn: {
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
      backgroundColor: tokens.bgGlass2,
    },
    btnText: { color: tokens.lightPurple, fontSize: 11, fontWeight: "700", letterSpacing: 1 },
    result: {
      marginTop: spacing.sm, marginLeft: 44,
      backgroundColor: tokens.black,
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md,
      padding: spacing.sm,
    },
    resultLine: { color: tokens.lightPurple, fontFamily: "Menlo", fontSize: 11, lineHeight: 15 },
    errLine: { color: tokens.redAccent, fontFamily: "Menlo", fontSize: 11, lineHeight: 15 },
  });

  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.grid}>
        {tiles.map((t) => {
          const r = results[t.key];
          const err = errors[t.key];
          return (
            <View key={t.key} style={styles.tile}>
              <View style={styles.tileTop}>
                <Text style={styles.glyph}>{t.glyph}</Text>
                <Text style={styles.label}>{t.label}</Text>
              </View>
              <Text style={styles.caption}>{t.caption}</Text>
              <View style={styles.btnRow}>
                <Pressable onPress={() => onPress(t)} style={styles.btn}>
                  {busyKey === t.key ? (
                    <ActivityIndicator size="small" color={tokens.purpleAccent} />
                  ) : (
                    <Text style={styles.btnText}>RUN</Text>
                  )}
                </Pressable>
              </View>
              {err && (
                <View style={styles.result}>
                  <Text style={styles.errLine}>error: {err}</Text>
                </View>
              )}
              {r && (
                <View style={styles.result}>
                  <Text style={styles.resultLine}>
                    {r.ok ? "OK" : "FAIL"} · {r.action}
                  </Text>
                  {r.output && (
                    <Text style={[styles.resultLine, { marginTop: 4 }]}>{r.output}</Text>
                  )}
                </View>
              )}
            </View>
          );
        })}

        <Text style={[typography.caption, { textAlign: "center", marginTop: spacing.md }]}>
          all actions hit the forge bridge :5078 on the host
        </Text>
      </ScrollView>
    </View>
  );
}
