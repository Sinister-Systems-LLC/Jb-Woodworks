// Sinister Claw :: screens/ForgeScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Live multi-agent harness. List existing Forge agents on the operator's PC,
// spawn new ones with a 3-field sheet, tail one's stdout, and terminate.
//
// Requires the Forge bridge running on the operator's PC (:5078).
// `python -m forge.bridge` from projects/sinister-forge/source/.

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, radii, spacing, typography, projectAccents } from "@/theme";
import {
  ForgeAgent,
  listAgents,
  spawnAgent,
  terminateAgent,
  openAgentStream,
} from "@/api/forge";
import { getProjects, SanctumProject } from "@/api/sanctum";

const POLL_MS = 4000;
const TAIL_LIMIT = 200;

export function ForgeScreen() {
  const [agents, setAgents] = useState<ForgeAgent[]>([]);
  const [projects, setProjects] = useState<SanctumProject[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [spawnOpen, setSpawnOpen] = useState(false);
  const [tailAgent, setTailAgent] = useState<ForgeAgent | null>(null);
  const [tailLines, setTailLines] = useState<string[]>([]);
  const esRef = useRef<EventSource | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listAgents();
      setAgents(list);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    getProjects().then(setProjects).catch(() => setProjects([]));
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const onSpawn = useCallback(async (params: SpawnParams) => {
    try {
      await spawnAgent(params);
      setSpawnOpen(false);
      await refresh();
    } catch (e: unknown) {
      Alert.alert("Spawn failed", e instanceof Error ? e.message : String(e));
    }
  }, [refresh]);

  const onTerminate = useCallback(async (a: ForgeAgent) => {
    Alert.alert(
      "Terminate agent",
      `Kill ${a.agent_name} (${a.project_key})?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Kill",
          style: "destructive",
          onPress: async () => {
            try {
              await terminateAgent(a.id);
              await refresh();
            } catch (e: unknown) {
              Alert.alert("Terminate failed", e instanceof Error ? e.message : String(e));
            }
          },
        },
      ],
    );
  }, [refresh]);

  const onOpenTail = useCallback(async (a: ForgeAgent) => {
    setTailAgent(a);
    setTailLines([]);
    try {
      const es = await openAgentStream(a.id, (line) => {
        setTailLines((prev) => {
          const next = [...prev, line];
          return next.length > TAIL_LIMIT ? next.slice(-TAIL_LIMIT) : next;
        });
      });
      esRef.current = es;
    } catch (e: unknown) {
      Alert.alert("Stream failed", e instanceof Error ? e.message : String(e));
    }
  }, []);

  const onCloseTail = useCallback(() => {
    if (esRef.current) {
      try {
        // @ts-expect-error polyfill exposes close()
        esRef.current.close();
      } catch {
        // ignore
      }
      esRef.current = null;
    }
    setTailAgent(null);
    setTailLines([]);
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[typography.display, { color: colors.purpleBright }]}>
          ◈ FORGE
        </Text>
        <Text style={[typography.caption, { marginBottom: spacing.lg }]}>
          {agents.length === 0 ? "no live agents" : `${agents.length} live agent${agents.length === 1 ? "" : "s"}`}
        </Text>

        {error && (
          <GlassPanel style={{ marginBottom: spacing.md }}>
            <Text style={{ color: colors.red }}>Bridge unreachable: {error}</Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              Start the Forge bridge on your PC: `python -m forge.bridge`
            </Text>
          </GlassPanel>
        )}

        <Pressable onPress={() => setSpawnOpen(true)} style={styles.spawnBtn}>
          <Text style={styles.spawnBtnText}>＋ SPAWN AGENT</Text>
        </Pressable>

        {agents.map((a) => {
          const accent = projectAccents[a.project_key] ?? colors.purpleBright;
          return (
            <GlassPanel
              key={a.id}
              style={{ marginBottom: spacing.md, borderColor: accent + "55" }}
            >
              <View style={styles.agentHeader}>
                <View style={[styles.dot, { backgroundColor: statusDotColor(a.status) }]} />
                <Text style={[typography.h1, { flex: 1, color: accent }]}>
                  {a.agent_name}
                </Text>
                <Text style={typography.caption}>{a.host}</Text>
              </View>
              <Text style={typography.body}>{a.project_display}</Text>
              <Text style={[typography.caption, { marginTop: spacing.xs }]}>
                {a.mode} · {a.status} {a.pid ? `· pid ${a.pid}` : ""}
              </Text>
              <View style={styles.actions}>
                <Pressable onPress={() => onOpenTail(a)} style={styles.actionBtn}>
                  <Text style={styles.actionText}>TAIL</Text>
                </Pressable>
                <Pressable onPress={() => onTerminate(a)} style={[styles.actionBtn, styles.actionKill]}>
                  <Text style={[styles.actionText, { color: colors.red }]}>KILL</Text>
                </Pressable>
              </View>
            </GlassPanel>
          );
        })}
      </ScrollView>

      <SpawnSheet
        open={spawnOpen}
        onClose={() => setSpawnOpen(false)}
        onSpawn={onSpawn}
        projects={projects}
      />

      <TailSheet
        agent={tailAgent}
        lines={tailLines}
        onClose={onCloseTail}
      />
    </SafeAreaView>
  );
}

// ---- SpawnSheet ----

interface SpawnParams {
  project: string;
  objective: string;
  agent_name: string;
  accent: string;
  host: "claude" | "codex";
  token_mode: "compact" | "full";
  speed: "max" | "turbo" | "fast" | "normal";
  focus?: string;
}

function SpawnSheet({
  open, onClose, onSpawn, projects,
}: {
  open: boolean;
  onClose: () => void;
  onSpawn: (p: SpawnParams) => void;
  projects: SanctumProject[];
}) {
  const [project, setProject] = useState(projects[0]?.key ?? "sanctum");
  const [agentName, setAgentName] = useState("Forge Agent");
  const [objective, setObjective] = useState("dev");
  const [host, setHost] = useState<"claude" | "codex">("claude");
  const [focus, setFocus] = useState("");

  useEffect(() => {
    if (!project && projects[0]) setProject(projects[0].key);
  }, [projects, project]);

  return (
    <Modal visible={open} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <GlassPanel style={styles.modalCard}>
          <Text style={[typography.title, { color: colors.purpleBright, marginBottom: spacing.md }]}>
            spawn agent
          </Text>

          <Text style={typography.h2}>Project</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginVertical: spacing.sm }}>
            {projects.map((p) => {
              const accent = projectAccents[p.key] ?? colors.purpleBright;
              const active = p.key === project;
              return (
                <Pressable
                  key={p.key}
                  onPress={() => setProject(p.key)}
                  style={[
                    styles.chip,
                    active && { backgroundColor: accent + "33", borderColor: accent },
                  ]}
                >
                  <Text style={[styles.chipText, active && { color: accent }]}>{p.display}</Text>
                </Pressable>
              );
            })}
          </ScrollView>

          <Text style={typography.h2}>Agent name</Text>
          <TextInput
            value={agentName}
            onChangeText={setAgentName}
            style={styles.input}
            placeholderTextColor={colors.dim}
            autoCapitalize="words"
          />

          <Text style={typography.h2}>Objective</Text>
          <View style={styles.row}>
            {(["dev", "resume", "audit", "expand", "smoketest"] as const).map((o) => (
              <Pressable key={o} onPress={() => setObjective(o)} style={[styles.chip, objective === o && styles.chipActive]}>
                <Text style={[styles.chipText, objective === o && styles.chipTextActive]}>{o}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={typography.h2}>Host</Text>
          <View style={styles.row}>
            {(["claude", "codex"] as const).map((h) => (
              <Pressable key={h} onPress={() => setHost(h)} style={[styles.chip, host === h && styles.chipActive]}>
                <Text style={[styles.chipText, host === h && styles.chipTextActive]}>{h}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={typography.h2}>Focus (optional)</Text>
          <TextInput
            value={focus}
            onChangeText={setFocus}
            style={[styles.input, { minHeight: 60 }]}
            placeholder="e.g. wire PH3 picker to bridge"
            placeholderTextColor={colors.dim}
            multiline
          />

          <View style={[styles.row, { marginTop: spacing.lg }]}>
            <Pressable onPress={onClose} style={[styles.modalBtn, styles.modalBtnCancel]}>
              <Text style={styles.modalBtnText}>CANCEL</Text>
            </Pressable>
            <Pressable
              onPress={() => onSpawn({
                project,
                objective,
                agent_name: agentName,
                accent: projectAccents[project] ?? colors.purpleBright,
                host,
                token_mode: "compact",
                speed: "turbo",
                focus: focus || undefined,
              })}
              style={[styles.modalBtn, styles.modalBtnGo]}
            >
              <Text style={[styles.modalBtnText, { color: colors.bgDeep }]}>SPAWN</Text>
            </Pressable>
          </View>
        </GlassPanel>
      </View>
    </Modal>
  );
}

// ---- TailSheet ----

function TailSheet({
  agent, lines, onClose,
}: {
  agent: ForgeAgent | null;
  lines: string[];
  onClose: () => void;
}) {
  if (!agent) return null;
  const accent = projectAccents[agent.project_key] ?? colors.purpleBright;
  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <SafeAreaView style={styles.tailContainer}>
        <View style={[styles.tailHeader, { borderColor: accent + "55" }]}>
          <Text style={[typography.h1, { flex: 1, color: accent }]}>{agent.agent_name}</Text>
          <Pressable onPress={onClose}>
            <Text style={[typography.h2, { color: colors.dim }]}>CLOSE</Text>
          </Pressable>
        </View>
        <ScrollView
          contentContainerStyle={{ padding: spacing.md }}
          ref={(r) => {
            // auto-scroll to bottom on new line
            if (r) (r as unknown as { scrollToEnd: (a?: object) => void }).scrollToEnd({ animated: true });
          }}
        >
          {lines.length === 0 && (
            <Text style={typography.caption}>waiting for output...</Text>
          )}
          {lines.map((l, i) => (
            <Text key={i} style={styles.tailLine}>{l}</Text>
          ))}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

// ---- helpers ----

function statusDotColor(status: string): string {
  switch (status) {
    case "running": return colors.green;
    case "ready":   return colors.cyan;
    case "exited":  return colors.dim;
    case "error":   return colors.red;
    default:        return colors.purpleBright;
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  scroll: { padding: spacing.lg },
  spawnBtn: {
    backgroundColor: colors.purpleBright,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.lg,
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  spawnBtnText: {
    color: colors.bgDeep,
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 1,
  },
  agentHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: spacing.sm },
  actions: {
    flexDirection: "row",
    marginTop: spacing.md,
  },
  actionBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.borderGlass,
    marginRight: spacing.sm,
  },
  actionKill: { borderColor: "rgba(255,110,110,0.4)" },
  actionText: {
    color: colors.lightPurple,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(7, 7, 11, 0.85)",
    justifyContent: "center",
    padding: spacing.lg,
  },
  modalCard: {
    maxHeight: "90%",
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginVertical: spacing.sm,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.borderGlass,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  chipActive: {
    backgroundColor: colors.purpleSoft,
    borderColor: colors.purpleBright,
  },
  chipText: {
    color: colors.soft,
    fontSize: 12,
    fontWeight: "500",
  },
  chipTextActive: {
    color: colors.purpleBright,
  },
  input: {
    color: colors.lightPurple,
    backgroundColor: "rgba(14, 10, 20, 0.7)",
    borderWidth: 1,
    borderColor: colors.borderGlass,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 14,
    marginBottom: spacing.sm,
  },
  modalBtn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: radii.lg,
    alignItems: "center",
    marginHorizontal: spacing.xs,
  },
  modalBtnCancel: {
    borderWidth: 1,
    borderColor: colors.borderGlass,
  },
  modalBtnGo: {
    backgroundColor: colors.purpleBright,
  },
  modalBtnText: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1,
    color: colors.lightPurple,
  },
  tailContainer: {
    flex: 1,
    backgroundColor: colors.bgDeep,
  },
  tailHeader: {
    flexDirection: "row",
    alignItems: "center",
    padding: spacing.md,
    borderBottomWidth: 1,
  },
  tailLine: {
    color: colors.lightPurple,
    fontFamily: "Menlo",
    fontSize: 11,
    lineHeight: 16,
  },
});
