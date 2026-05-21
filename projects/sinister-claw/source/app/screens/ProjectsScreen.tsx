// Sinister Claw :: screens/ProjectsScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Drill into one of the 12 Sinister projects. Lists the project roster from
// /api/sanctum/projects; tap one to open detail (PROGRESS top 5, latest
// resume-point, matched plan dirs).

import React, { useCallback, useEffect, useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, spacing, typography, projectAccents } from "@/theme";
import {
  getProjects,
  getProjectDetail,
  SanctumProject,
  ProjectDetail,
} from "@/api/sanctum";

export function ProjectsScreen() {
  const [projects, setProjects] = useState<SanctumProject[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<SanctumProject | null>(null);
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const openProject = useCallback(async (p: SanctumProject) => {
    setOpen(p);
    setDetail(null);
    setLoading(true);
    try {
      const d = await getProjectDetail(p.key);
      setDetail(d);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[typography.display, { color: colors.purpleBright }]}>
          ◈ PROJECTS
        </Text>
        <Text style={[typography.caption, { marginBottom: spacing.lg }]}>
          {projects.length} sinister projects
        </Text>

        {error && (
          <GlassPanel style={{ marginBottom: spacing.md }}>
            <Text style={{ color: colors.red }}>Bridge: {error}</Text>
          </GlassPanel>
        )}

        {projects.map((p) => {
          const accent = projectAccents[p.key] ?? colors.purpleBright;
          return (
            <Pressable key={p.key} onPress={() => openProject(p)}>
              <GlassPanel style={{ marginBottom: spacing.sm, borderColor: accent + "44" }}>
                <View style={styles.row}>
                  <View style={[styles.dot, { backgroundColor: accent }]} />
                  <Text style={[typography.h1, { color: accent, flex: 1 }]}>{p.display}</Text>
                </View>
                <Text style={[typography.body, { marginTop: spacing.xs }]} numberOfLines={2}>
                  {p.tag}
                </Text>
                <Text style={[typography.caption, { marginTop: spacing.xs }]} numberOfLines={1}>
                  {p.github}
                </Text>
              </GlassPanel>
            </Pressable>
          );
        })}
      </ScrollView>

      <DetailSheet
        project={open}
        detail={detail}
        loading={loading}
        onClose={() => { setOpen(null); setDetail(null); }}
      />
    </SafeAreaView>
  );
}

function DetailSheet({
  project, detail, loading, onClose,
}: {
  project: SanctumProject | null;
  detail: ProjectDetail | null;
  loading: boolean;
  onClose: () => void;
}) {
  if (!project) return null;
  const accent = projectAccents[project.key] ?? colors.purpleBright;
  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <SafeAreaView style={styles.detailContainer}>
        <View style={[styles.detailHeader, { borderColor: accent + "55" }]}>
          <View style={{ flex: 1 }}>
            <Text style={[typography.title, { color: accent }]}>{project.display}</Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]} numberOfLines={2}>
              {project.tag}
            </Text>
          </View>
          <Pressable onPress={onClose}>
            <Text style={[typography.h2, { color: colors.dim }]}>CLOSE</Text>
          </Pressable>
        </View>
        <ScrollView contentContainerStyle={{ padding: spacing.md }}>
          {loading && <Text style={typography.caption}>loading detail...</Text>}

          {detail?.resume_point && (
            <GlassPanel style={{ marginBottom: spacing.md, borderColor: accent + "55" }}>
              <Text style={[typography.h2, { color: accent }]}>RESUME POINT</Text>
              <Text style={[typography.body, { marginTop: spacing.xs }]}>
                {detail.resume_point.focus_intent || "(no focus_intent)"}
              </Text>
              <Text style={[typography.caption, { marginTop: spacing.sm }]}>
                {detail.resume_point.mode} · {detail.resume_point.agent_name}
              </Text>
              {detail.resume_point.git?.head_msg && (
                <Text style={[typography.caption, { marginTop: spacing.xs, color: colors.cyan }]} numberOfLines={2}>
                  HEAD: {detail.resume_point.git.head_msg}
                </Text>
              )}
            </GlassPanel>
          )}

          {detail && detail.progress_entries.length > 0 && (
            <GlassPanel style={{ marginBottom: spacing.md }}>
              <Text style={[typography.h2, { color: accent }]}>RECENT PROGRESS</Text>
              {detail.progress_entries.map((e, i) => (
                <View key={i} style={styles.progressRow}>
                  <Text style={[typography.caption, { color: colors.cyan }]}>{e.heading}</Text>
                  <Text style={[typography.body, { marginTop: spacing.xs }]} numberOfLines={4}>
                    {e.snippet}
                  </Text>
                </View>
              ))}
            </GlassPanel>
          )}

          {detail && detail.plans.length > 0 && (
            <GlassPanel style={{ marginBottom: spacing.md }}>
              <Text style={[typography.h2, { color: accent }]}>PLANS</Text>
              {detail.plans.map((p) => (
                <Text key={p.dir} style={[typography.body, { marginTop: spacing.xs }]}>
                  · {p.dir}
                </Text>
              ))}
            </GlassPanel>
          )}

          <GlassPanel>
            <Text style={[typography.h2, { color: accent }]}>METADATA</Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              key: {project.key}
            </Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              root: {project.root}
            </Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              github: {project.github}
            </Text>
          </GlassPanel>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  scroll: { padding: spacing.lg },
  row: { flexDirection: "row", alignItems: "center" },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: spacing.sm },
  detailContainer: {
    flex: 1,
    backgroundColor: colors.bgDeep,
  },
  detailHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: spacing.md,
    borderBottomWidth: 1,
  },
  progressRow: {
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderGlass,
  },
});
