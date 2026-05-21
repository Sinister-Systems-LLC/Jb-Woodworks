// Sinister Claw :: screens/SanctumScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later

import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, spacing, typography, projectAccents } from "@/theme";
import { getHeartbeats, getProjects, getRecentCommits, SanctumHeartbeat, SanctumProject, RecentCommit } from "@/api/sanctum";

export function SanctumScreen() {
  const [heartbeats, setHeartbeats] = useState<SanctumHeartbeat[]>([]);
  const [projects, setProjects] = useState<SanctumProject[]>([]);
  const [commits, setCommits] = useState<RecentCommit[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [hb, p, c] = await Promise.all([
          getHeartbeats().catch(() => ({ agents: [] })),
          getProjects().catch(() => []),
          getRecentCommits(20).catch(() => []),
        ]);
        setHeartbeats(hb.agents);
        setProjects(p);
        setCommits(c);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[typography.display, { color: colors.purpleBright }]}>
          ◈ SANCTUM
        </Text>
        <Text style={[typography.caption, { marginBottom: spacing.lg }]}>
          fleet overview
        </Text>

        {error && (
          <GlassPanel style={{ marginBottom: spacing.md }}>
            <Text style={{ color: colors.red }}>Connection error: {error}</Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              Settings tab → set Tailscale base URL + auth token.
            </Text>
          </GlassPanel>
        )}

        <GlassPanel style={{ marginBottom: spacing.md }}>
          <Text style={typography.h2}>Heartbeats</Text>
          {heartbeats.length === 0 ? (
            <Text style={typography.body}>No live agents (or backend not reachable).</Text>
          ) : (
            heartbeats.map((h) => (
              <View key={h.agent} style={styles.row}>
                <View style={[styles.dot, { backgroundColor: h.alive ? colors.green : colors.dim }]} />
                <Text style={[typography.body, { flex: 1 }]}>{h.agent}</Text>
                <Text style={typography.caption}>{h.ago_min}m ago</Text>
              </View>
            ))
          )}
        </GlassPanel>

        <GlassPanel style={{ marginBottom: spacing.md }}>
          <Text style={typography.h2}>Projects ({projects.length})</Text>
          {projects.map((p) => (
            <View key={p.key} style={styles.row}>
              <View style={[styles.dot, { backgroundColor: projectAccents[p.key] ?? colors.purpleBright }]} />
              <Text style={[typography.body, { flex: 1 }]}>{p.display}</Text>
              <Text style={typography.caption} numberOfLines={1}>
                {p.tag.slice(0, 30)}
              </Text>
            </View>
          ))}
        </GlassPanel>

        <GlassPanel>
          <Text style={typography.h2}>Recent Commits</Text>
          {commits.map((c) => (
            <View key={c.hash} style={[styles.row, { flexDirection: "column", alignItems: "flex-start" }]}>
              <Text style={[typography.body, { color: colors.cyan }]}>
                {c.hash.slice(0, 7)} {c.branch}
              </Text>
              <Text style={[typography.caption, { marginTop: spacing.xs }]} numberOfLines={2}>
                {c.message}
              </Text>
            </View>
          ))}
        </GlassPanel>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  scroll: { padding: spacing.lg },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderGlass,
  },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: spacing.sm },
});
