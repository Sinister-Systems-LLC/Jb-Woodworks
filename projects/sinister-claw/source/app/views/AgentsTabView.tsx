// RKOJ Mobile :: views/AgentsTabView.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Vertical list of agent cards. Each card:
//   - header  : project · "EVE on <project>" · mode pill · status dot · close
//   - log     : read-only ScrollView of streamed SSE lines
//   - input   : TextInput + Send button (POST /api/forge/agents/:id/input)
// "+ Spawn Agent" CTA at top opens a sheet that POSTs /api/forge/spawn.

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useTheme } from "@/theme";
import {
  ForgeAgent, listAgents, spawnAgent, terminateAgent, openAgentStream,
  getProjects, SanctumProject,
} from "@/api/forgeBridge";

const POLL_MS = 4000;
const TAIL_LIMIT = 250;

interface PaneState {
  agent: ForgeAgent;
  lines: string[];
  input: string;
  es?: EventSource;
}

export function AgentsTabView() {
  const { tokens, spacing, radii, typography, projectAccents } = useTheme();
  const [panes, setPanes] = useState<PaneState[]>([]);
  const [projects, setProjects] = useState<SanctumProject[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [spawnOpen, setSpawnOpen] = useState(false);
  const panesRef = useRef<PaneState[]>([]);
  panesRef.current = panes;

  const refresh = useCallback(async () => {
    try {
      const list = await listAgents();
      // Keep existing panes by id, add new ones, drop removed ones.
      setPanes((prev) => {
        const byId = new Map(prev.map((p) => [p.agent.id, p]));
        const next: PaneState[] = list.map((a) => {
          const existing = byId.get(a.id);
          return existing
            ? { ...existing, agent: a }
            : { agent: a, lines: [], input: "" };
        });
        return next;
      });
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

  // Auto-attach SSE streams for every pane that doesn't have one yet.
  useEffect(() => {
    panes.forEach((p, idx) => {
      if (p.es) return;
      openAgentStream(p.agent.id, (line) => {
        setPanes((prev) => prev.map((q, i) =>
          i === idx
            ? {
                ...q,
                lines: q.lines.concat(line).slice(-TAIL_LIMIT),
              }
            : q,
        ));
      })
        .then((es) => {
          setPanes((prev) => prev.map((q, i) => (i === idx ? { ...q, es } : q)));
        })
        .catch(() => { /* leave es undefined; will retry on next refresh */ });
    });
    return () => {
      // close streams on unmount
      panesRef.current.forEach((p) => {
        if (p.es) {
          try { (p.es as { close: () => void }).close(); } catch { /* ignore */ }
        }
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panes.length]);

  const onClose = useCallback((agentId: string) => {
    const pane = panes.find((p) => p.agent.id === agentId);
    Alert.alert(
      "Close agent",
      `Terminate ${pane?.agent.agent_name ?? agentId}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Kill", style: "destructive",
          onPress: async () => {
            try {
              await terminateAgent(agentId);
              await refresh();
            } catch (e: unknown) {
              Alert.alert("Terminate failed", e instanceof Error ? e.message : String(e));
            }
          },
        },
      ],
    );
  }, [panes, refresh]);

  const onSend = useCallback((agentId: string) => {
    // PROVISIONAL: bridge endpoint /api/forge/agents/:id/input is the
    // forge bridge's stdin write. We POST opportunistically; the bridge
    // is responsible for routing to the agent's stdin pipe.
    const pane = panesRef.current.find((p) => p.agent.id === agentId);
    if (!pane || !pane.input.trim()) return;
    const text = pane.input;
    setPanes((prev) => prev.map((q) =>
      q.agent.id === agentId ? { ...q, input: "" } : q,
    ));
    fetch(`/api/forge/agents/${agentId}/input`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).catch(() => { /* best-effort */ });
  }, []);

  const onSpawn = useCallback(async (params: {
    project: string; objective: string; agent_name: string;
    host: "claude" | "codex"; focus?: string;
  }) => {
    try {
      await spawnAgent({
        ...params,
        accent: projectAccents[params.project] ?? tokens.purpleAccent,
        token_mode: "compact",
        speed: "turbo",
      });
      setSpawnOpen(false);
      await refresh();
    } catch (e: unknown) {
      Alert.alert("Spawn failed", e instanceof Error ? e.message : String(e));
    }
  }, [projectAccents, tokens.purpleAccent, refresh]);

  const styles = StyleSheet.create({
    root: { flex: 1, backgroundColor: tokens.bg },
    list: { padding: spacing.md },
    spawnBtn: {
      backgroundColor: tokens.purpleDeep,
      paddingVertical: spacing.md,
      borderRadius: radii.lg,
      alignItems: "center",
      marginBottom: spacing.md,
    },
    spawnText: {
      color: tokens.white,
      fontSize: 13,
      fontWeight: "700",
      letterSpacing: 1,
    },
    errBox: {
      backgroundColor: tokens.bgGlass,
      borderColor: tokens.redAccent,
      borderWidth: 1,
      borderRadius: radii.md,
      padding: spacing.sm,
      marginBottom: spacing.md,
    },
    errText: { color: tokens.redAccent, fontSize: 12 },
    emptyBox: {
      padding: spacing.xl,
      alignItems: "center",
      backgroundColor: tokens.bgGlass,
      borderColor: tokens.borderGlass,
      borderWidth: 1,
      borderRadius: radii.lg,
    },
    emptyText: { color: tokens.dim, fontSize: 12, letterSpacing: 1 },

    card: {
      backgroundColor: tokens.bgGlass,
      borderWidth: 1,
      borderColor: tokens.borderGlass,
      borderRadius: radii.lg,
      padding: spacing.md,
      marginBottom: spacing.md,
    },
    cardHeader: { flexDirection: "row", alignItems: "center" },
    cardDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
    cardProject: {
      color: tokens.soft,
      fontSize: 10,
      letterSpacing: 1.5,
      fontWeight: "700",
    },
    cardName: {
      color: tokens.purpleHalo,
      fontSize: 14,
      fontWeight: "700",
      marginTop: 2,
    },
    cardMeta: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: spacing.xs,
    },
    pill: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: radii.pill,
      borderWidth: 1,
      borderColor: tokens.borderGlass,
      backgroundColor: tokens.bgGlass2,
      marginRight: 6,
    },
    pillText: { color: tokens.soft, fontSize: 10, letterSpacing: 1 },
    closeBtn: {
      paddingHorizontal: spacing.sm,
      paddingVertical: 4,
      borderWidth: 1,
      borderColor: tokens.borderGlass,
      borderRadius: radii.md,
    },
    closeText: { color: tokens.redAccent, fontSize: 10, fontWeight: "700", letterSpacing: 1 },

    log: {
      backgroundColor: tokens.black,
      borderColor: tokens.borderGlass,
      borderWidth: 1,
      borderRadius: radii.md,
      marginTop: spacing.sm,
      maxHeight: 240,
    },
    logInner: { padding: spacing.sm },
    logLine: {
      color: tokens.lightPurple,
      fontFamily: "Menlo",
      fontSize: 11,
      lineHeight: 15,
    },
    inputRow: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: spacing.sm,
    },
    input: {
      flex: 1,
      color: tokens.lightPurple,
      backgroundColor: tokens.bgGlass2,
      borderColor: tokens.borderGlass,
      borderWidth: 1,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      fontSize: 13,
      fontFamily: "Menlo",
    },
    sendBtn: {
      marginLeft: spacing.sm,
      backgroundColor: tokens.purpleDeep,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      borderRadius: radii.md,
    },
    sendText: { color: tokens.white, fontSize: 12, fontWeight: "700", letterSpacing: 1 },
  });

  const statusColor = (s: string): string => {
    switch (s) {
      case "running": return tokens.greenAccent;
      case "ready":   return tokens.cyan;
      case "exited":  return tokens.dim;
      case "error":   return tokens.redAccent;
      default:        return tokens.purpleAccent;
    }
  };

  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.list}>
        <Pressable onPress={() => setSpawnOpen(true)} style={styles.spawnBtn}>
          <Text style={styles.spawnText}>+ SPAWN AGENT</Text>
        </Pressable>

        {error && (
          <View style={styles.errBox}>
            <Text style={styles.errText}>Bridge unreachable: {error}</Text>
            <Text style={[typography.caption, { marginTop: 4 }]}>
              Start the Forge bridge on your PC: `python -m forge.bridge`
            </Text>
          </View>
        )}

        {panes.length === 0 && !error && (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>NO LIVE AGENTS</Text>
            <Text style={[typography.caption, { marginTop: 6 }]}>
              Tap SPAWN AGENT to start one.
            </Text>
          </View>
        )}

        {panes.map((p, idx) => {
          const accent = projectAccents[p.agent.project_key] ?? tokens.purpleAccent;
          return (
            <View key={p.agent.id} style={[styles.card, { borderColor: accent + "55" }]}>
              <View style={styles.cardHeader}>
                <View style={[styles.cardDot, { backgroundColor: statusColor(p.agent.status) }]} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardProject}>{p.agent.project_display.toUpperCase()}</Text>
                  <Text style={[styles.cardName, { color: accent }]}>
                    EVE on {p.agent.project_key}
                  </Text>
                </View>
                <Pressable onPress={() => onClose(p.agent.id)} style={styles.closeBtn}>
                  <Text style={styles.closeText}>×  KILL</Text>
                </Pressable>
              </View>
              <View style={styles.cardMeta}>
                <View style={styles.pill}>
                  <Text style={styles.pillText}>{p.agent.mode.toUpperCase()}</Text>
                </View>
                <View style={styles.pill}>
                  <Text style={styles.pillText}>{p.agent.host.toUpperCase()}</Text>
                </View>
                <Text style={[typography.caption, { marginLeft: "auto" }]}>
                  {p.agent.status}{p.agent.pid ? ` · pid ${p.agent.pid}` : ""}
                </Text>
              </View>

              <ScrollView
                style={styles.log}
                contentContainerStyle={styles.logInner}
                ref={(r) => {
                  if (r) (r as unknown as { scrollToEnd: (a?: object) => void })
                    .scrollToEnd({ animated: false });
                }}
              >
                {p.lines.length === 0 ? (
                  <Text style={[typography.caption, { fontFamily: "Menlo" }]}>
                    waiting for output...
                  </Text>
                ) : (
                  p.lines.map((l, i) => (
                    <Text key={i} style={styles.logLine}>{l}</Text>
                  ))
                )}
              </ScrollView>

              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  value={p.input}
                  placeholder="message agent..."
                  placeholderTextColor={tokens.dim}
                  onChangeText={(t) => setPanes((prev) =>
                    prev.map((q, i) => (i === idx ? { ...q, input: t } : q)),
                  )}
                  onSubmitEditing={() => onSend(p.agent.id)}
                  returnKeyType="send"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <Pressable onPress={() => onSend(p.agent.id)} style={styles.sendBtn}>
                  <Text style={styles.sendText}>SEND</Text>
                </Pressable>
              </View>
            </View>
          );
        })}
      </ScrollView>

      <SpawnSheet
        open={spawnOpen}
        onClose={() => setSpawnOpen(false)}
        onSpawn={onSpawn}
        projects={projects}
      />
    </View>
  );
}

// ---- SpawnSheet ----

interface SpawnSheetProps {
  open: boolean;
  onClose: () => void;
  onSpawn: (p: {
    project: string; objective: string; agent_name: string;
    host: "claude" | "codex"; focus?: string;
  }) => void;
  projects: SanctumProject[];
}

function SpawnSheet({ open, onClose, onSpawn, projects }: SpawnSheetProps) {
  const { tokens, spacing, radii, typography, projectAccents } = useTheme();
  const [project, setProject] = useState(projects[0]?.key ?? "sanctum");
  const [agentName, setAgentName] = useState("EVE");
  const [objective, setObjective] = useState("dev");
  const [host, setHost] = useState<"claude" | "codex">("claude");
  const [focus, setFocus] = useState("");

  useEffect(() => {
    if (!project && projects[0]) setProject(projects[0].key);
  }, [projects, project]);

  const styles = StyleSheet.create({
    backdrop: {
      flex: 1,
      backgroundColor: "rgba(7, 7, 11, 0.85)",
      justifyContent: "center",
      padding: spacing.lg,
    },
    card: {
      backgroundColor: tokens.bgGlass,
      borderColor: tokens.borderGlass,
      borderWidth: 1,
      borderRadius: radii.xl,
      padding: spacing.lg,
      maxHeight: "90%",
    },
    title: {
      color: tokens.purpleHalo,
      fontSize: 18,
      fontWeight: "700",
      letterSpacing: 1.5,
      marginBottom: spacing.md,
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
      borderColor: tokens.borderGlass,
      backgroundColor: tokens.bgGlass2,
      marginRight: spacing.sm,
      marginBottom: spacing.sm,
    },
    chipActive: {
      backgroundColor: tokens.bgGlow,
      borderColor: tokens.purpleAccent,
    },
    chipText: { color: tokens.soft, fontSize: 12 },
    chipTextActive: { color: tokens.purpleHalo, fontWeight: "600" },
    input: {
      color: tokens.lightPurple,
      backgroundColor: tokens.bgGlass2,
      borderColor: tokens.borderGlass,
      borderWidth: 1,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      fontSize: 13,
      marginBottom: spacing.sm,
    },
    btnRow: { flexDirection: "row", marginTop: spacing.md },
    cancelBtn: {
      flex: 1,
      paddingVertical: spacing.md,
      borderRadius: radii.lg,
      alignItems: "center",
      marginRight: spacing.xs,
      borderWidth: 1,
      borderColor: tokens.borderGlass,
    },
    goBtn: {
      flex: 1,
      paddingVertical: spacing.md,
      borderRadius: radii.lg,
      alignItems: "center",
      marginLeft: spacing.xs,
      backgroundColor: tokens.purpleDeep,
    },
    btnText: {
      fontSize: 13,
      fontWeight: "700",
      letterSpacing: 1,
      color: tokens.lightPurple,
    },
    btnTextGo: { color: tokens.white },
  });

  return (
    <Modal visible={open} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <ScrollView style={styles.card}>
          <Text style={styles.title}>SPAWN AGENT</Text>

          <Text style={typography.h2}>Project</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}
            style={{ marginVertical: spacing.sm }}>
            {projects.map((p) => {
              const accent = projectAccents[p.key] ?? tokens.purpleAccent;
              const active = p.key === project;
              return (
                <Pressable key={p.key} onPress={() => setProject(p.key)}
                  style={[styles.chip, active && { backgroundColor: accent + "33", borderColor: accent }]}>
                  <Text style={[styles.chipText, active && { color: accent }]}>{p.display}</Text>
                </Pressable>
              );
            })}
          </ScrollView>

          <Text style={typography.h2}>Agent name</Text>
          <TextInput value={agentName} onChangeText={setAgentName}
            style={styles.input} placeholderTextColor={tokens.dim} autoCapitalize="words" />

          <Text style={typography.h2}>Objective</Text>
          <View style={styles.row}>
            {(["dev", "resume", "audit", "expand", "smoketest"] as const).map((o) => (
              <Pressable key={o} onPress={() => setObjective(o)}
                style={[styles.chip, objective === o && styles.chipActive]}>
                <Text style={[styles.chipText, objective === o && styles.chipTextActive]}>{o}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={typography.h2}>Host</Text>
          <View style={styles.row}>
            {(["claude", "codex"] as const).map((h) => (
              <Pressable key={h} onPress={() => setHost(h)}
                style={[styles.chip, host === h && styles.chipActive]}>
                <Text style={[styles.chipText, host === h && styles.chipTextActive]}>{h}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={typography.h2}>Focus (optional)</Text>
          <TextInput value={focus} onChangeText={setFocus}
            style={[styles.input, { minHeight: 60 }]}
            placeholder="e.g. wire mobile spawn flow"
            placeholderTextColor={tokens.dim} multiline />

          <View style={styles.btnRow}>
            <Pressable onPress={onClose} style={styles.cancelBtn}>
              <Text style={styles.btnText}>CANCEL</Text>
            </Pressable>
            <Pressable
              onPress={() => onSpawn({
                project, objective, agent_name: agentName, host,
                focus: focus || undefined,
              })}
              style={styles.goBtn}
            >
              <Text style={[styles.btnText, styles.btnTextGo]}>SPAWN</Text>
            </Pressable>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
}
