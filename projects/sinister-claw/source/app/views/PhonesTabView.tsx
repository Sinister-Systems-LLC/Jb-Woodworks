// RKOJ Mobile :: views/PhonesTabView.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Device list backed by `adb devices` from the Forge bridge. Tap a device
// to open the bottom-sheet detail panel (Identity / Heartbeat / RKA /
// Kill-switch / Open scrcpy on host / ADB shell / Logcat tail SSE).

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useTheme } from "@/theme";
import {
  AdbDevice, listDevices, getDeviceDetail, adbShell, openScrcpy,
  rkaArm, rkaKill, openLogcatStream,
} from "@/api/devices";

const POLL_MS = 6000;
const LOGCAT_LIMIT = 300;

export function PhonesTabView() {
  const { tokens, spacing, radii, typography } = useTheme();
  const [devices, setDevices] = useState<AdbDevice[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AdbDevice | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listDevices();
      setDevices(list);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const styles = StyleSheet.create({
    root: { flex: 1, backgroundColor: tokens.bg },
    list: { padding: spacing.md },
    errBox: {
      backgroundColor: tokens.bgGlass, borderColor: tokens.redAccent,
      borderWidth: 1, borderRadius: radii.md, padding: spacing.sm,
      marginBottom: spacing.md,
    },
    errText: { color: tokens.redAccent, fontSize: 12 },
    emptyBox: {
      padding: spacing.xl, alignItems: "center",
      backgroundColor: tokens.bgGlass, borderColor: tokens.borderGlass,
      borderWidth: 1, borderRadius: radii.lg,
    },
    emptyText: { color: tokens.dim, fontSize: 12, letterSpacing: 1 },

    card: {
      backgroundColor: tokens.bgGlass,
      borderWidth: 1, borderColor: tokens.borderGlass,
      borderRadius: radii.lg, padding: spacing.md,
      marginBottom: spacing.md,
    },
    cardRow: { flexDirection: "row", alignItems: "center" },
    dot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
    model: {
      color: tokens.purpleHalo, fontSize: 15, fontWeight: "700",
    },
    serial: {
      color: tokens.soft, fontFamily: "Menlo",
      fontSize: 11, marginTop: 2,
    },
    badge: {
      paddingHorizontal: 8, paddingVertical: 2,
      borderRadius: radii.pill, borderWidth: 1,
      borderColor: tokens.borderGlass, backgroundColor: tokens.bgGlass2,
      marginLeft: 6,
    },
    badgeText: { color: tokens.soft, fontSize: 10, letterSpacing: 1 },
  });

  const stateColor = (s: string): string => {
    switch (s) {
      case "device": return tokens.greenAccent;
      case "offline": return tokens.dim;
      case "unauthorized": return tokens.amberAccent;
      default: return tokens.purpleAccent;
    }
  };

  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.list}>
        {error && (
          <View style={styles.errBox}>
            <Text style={styles.errText}>Devices bridge unreachable: {error}</Text>
          </View>
        )}

        {devices.length === 0 && !error && (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>NO DEVICES ATTACHED</Text>
            <Text style={[typography.caption, { marginTop: 6 }]}>
              Run `adb devices` on the host to verify.
            </Text>
          </View>
        )}

        {devices.map((d) => (
          <Pressable key={d.serial} onPress={() => setSelected(d)} style={styles.card}>
            <View style={styles.cardRow}>
              <View style={[styles.dot, { backgroundColor: stateColor(d.state) }]} />
              <View style={{ flex: 1 }}>
                <Text style={styles.model}>{d.model ?? d.product ?? d.serial}</Text>
                <Text style={styles.serial}>{d.serial}</Text>
              </View>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{d.state.toUpperCase()}</Text>
              </View>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{(d.transport || "?").toUpperCase()}</Text>
              </View>
            </View>
          </Pressable>
        ))}
      </ScrollView>

      <DeviceSheet
        device={selected}
        onClose={() => setSelected(null)}
        onChanged={refresh}
      />
    </View>
  );
}

// ---- DeviceSheet ----

interface DeviceSheetProps {
  device: AdbDevice | null;
  onClose: () => void;
  onChanged: () => void;
}

function DeviceSheet({ device, onClose, onChanged }: DeviceSheetProps) {
  const { tokens, spacing, radii, typography } = useTheme();
  const [detail, setDetail] = useState<AdbDevice | null>(null);
  const [shellCmd, setShellCmd] = useState("getprop ro.build.version.release");
  const [shellOut, setShellOut] = useState("");
  const [logcatOn, setLogcatOn] = useState(false);
  const [logLines, setLogLines] = useState<string[]>([]);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!device) {
      setDetail(null); setShellOut(""); setLogLines([]); setLogcatOn(false);
      if (esRef.current) {
        try { (esRef.current as { close: () => void }).close(); } catch { /* ignore */ }
        esRef.current = null;
      }
      return;
    }
    getDeviceDetail(device.serial).then(setDetail).catch(() => setDetail(device));
  }, [device]);

  const toggleLogcat = useCallback(async () => {
    if (!device) return;
    if (logcatOn) {
      if (esRef.current) {
        try { (esRef.current as { close: () => void }).close(); } catch { /* ignore */ }
        esRef.current = null;
      }
      setLogcatOn(false);
      return;
    }
    setLogLines([]);
    try {
      const es = await openLogcatStream(device.serial, (line) => {
        setLogLines((prev) => prev.concat(line).slice(-LOGCAT_LIMIT));
      });
      esRef.current = es;
      setLogcatOn(true);
    } catch (e: unknown) {
      Alert.alert("Logcat failed", e instanceof Error ? e.message : String(e));
    }
  }, [device, logcatOn]);

  const runShell = useCallback(async () => {
    if (!device || !shellCmd.trim()) return;
    try {
      const r = await adbShell(device.serial, shellCmd);
      setShellOut(`exit ${r.exit_code}\n${r.stdout}${r.stderr ? "\n[stderr]\n" + r.stderr : ""}`);
    } catch (e: unknown) {
      setShellOut(`error: ${e instanceof Error ? e.message : String(e)}`);
    }
  }, [device, shellCmd]);

  const onScrcpy = useCallback(async () => {
    if (!device) return;
    try {
      await openScrcpy(device.serial);
      Alert.alert("scrcpy", "Opened on host.");
    } catch (e: unknown) {
      Alert.alert("scrcpy failed", e instanceof Error ? e.message : String(e));
    }
  }, [device]);

  const onArm = useCallback(async () => {
    if (!device) return;
    try { await rkaArm(device.serial); onChanged(); }
    catch (e: unknown) { Alert.alert("RKA arm failed", e instanceof Error ? e.message : String(e)); }
  }, [device, onChanged]);

  const onKill = useCallback(async () => {
    if (!device) return;
    Alert.alert("Kill-switch", `Trigger RKA kill on ${device.serial}?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Kill", style: "destructive",
        onPress: async () => {
          try { await rkaKill(device.serial); onChanged(); }
          catch (e: unknown) { Alert.alert("RKA kill failed", e instanceof Error ? e.message : String(e)); }
        },
      },
    ]);
  }, [device, onChanged]);

  if (!device) return null;
  const d = detail ?? device;

  const styles = StyleSheet.create({
    backdrop: {
      flex: 1, backgroundColor: "rgba(7, 7, 11, 0.85)",
      justifyContent: "flex-end",
    },
    sheet: {
      backgroundColor: tokens.bg,
      borderTopLeftRadius: radii.xxl, borderTopRightRadius: radii.xxl,
      borderColor: tokens.borderGlass, borderWidth: 1,
      maxHeight: "90%", padding: spacing.lg,
    },
    headerRow: { flexDirection: "row", alignItems: "center" },
    title: {
      flex: 1, color: tokens.purpleHalo,
      fontSize: 18, fontWeight: "700", letterSpacing: 1.5,
    },
    close: {
      paddingHorizontal: spacing.sm, paddingVertical: 4,
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md,
    },
    closeText: { color: tokens.soft, fontSize: 11, letterSpacing: 1 },

    section: { marginTop: spacing.md },
    kv: { flexDirection: "row", paddingVertical: 4 },
    k: { color: tokens.dim, fontSize: 11, letterSpacing: 1, width: 110 },
    v: { color: tokens.lightPurple, fontSize: 12, flex: 1 },

    btnRow: {
      flexDirection: "row", flexWrap: "wrap",
      marginTop: spacing.sm,
    },
    btn: {
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
      marginRight: spacing.sm, marginBottom: spacing.sm,
      backgroundColor: tokens.bgGlass,
    },
    btnText: { color: tokens.lightPurple, fontSize: 11, fontWeight: "700", letterSpacing: 1 },
    btnDanger: { borderColor: tokens.redAccent },
    btnDangerText: { color: tokens.redAccent },

    input: {
      color: tokens.lightPurple,
      backgroundColor: tokens.bgGlass2,
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
      fontSize: 12, fontFamily: "Menlo",
    },
    log: {
      backgroundColor: tokens.black,
      borderColor: tokens.borderGlass, borderWidth: 1,
      borderRadius: radii.md, marginTop: spacing.sm,
      maxHeight: 220,
    },
    logLine: { color: tokens.lightPurple, fontFamily: "Menlo", fontSize: 10, lineHeight: 14 },
  });

  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <ScrollView style={styles.sheet}>
          <View style={styles.headerRow}>
            <Text style={styles.title}>{d.model ?? d.serial}</Text>
            <Pressable onPress={onClose} style={styles.close}>
              <Text style={styles.closeText}>CLOSE</Text>
            </Pressable>
          </View>

          <View style={styles.section}>
            <Text style={typography.h2}>Identity</Text>
            <View style={styles.kv}><Text style={styles.k}>SERIAL</Text><Text style={styles.v}>{d.serial}</Text></View>
            <View style={styles.kv}><Text style={styles.k}>MODEL</Text><Text style={styles.v}>{d.model ?? "—"}</Text></View>
            <View style={styles.kv}><Text style={styles.k}>PRODUCT</Text><Text style={styles.v}>{d.product ?? "—"}</Text></View>
            <View style={styles.kv}><Text style={styles.k}>ANDROID</Text><Text style={styles.v}>{d.android_version ?? "—"}</Text></View>
            <View style={styles.kv}><Text style={styles.k}>TRANSPORT</Text><Text style={styles.v}>{d.transport ?? "—"}</Text></View>
          </View>

          <View style={styles.section}>
            <Text style={typography.h2}>Heartbeat</Text>
            <View style={styles.kv}><Text style={styles.k}>STATE</Text><Text style={styles.v}>{d.state}</Text></View>
            <View style={styles.kv}><Text style={styles.k}>AGE</Text>
              <Text style={styles.v}>{d.heartbeat_age_s != null ? `${d.heartbeat_age_s}s` : "—"}</Text>
            </View>
            <View style={styles.kv}><Text style={styles.k}>IDENTITY</Text><Text style={styles.v}>{d.identity ?? "—"}</Text></View>
          </View>

          <View style={styles.section}>
            <Text style={typography.h2}>RKA</Text>
            <View style={styles.kv}><Text style={styles.k}>RKA STATE</Text><Text style={styles.v}>{d.rka_state ?? "—"}</Text></View>
            <View style={styles.btnRow}>
              <Pressable onPress={onArm} style={styles.btn}>
                <Text style={styles.btnText}>ARM</Text>
              </Pressable>
              <Pressable onPress={onKill} style={[styles.btn, styles.btnDanger]}>
                <Text style={[styles.btnText, styles.btnDangerText]}>KILL-SWITCH</Text>
              </Pressable>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={typography.h2}>Host actions</Text>
            <View style={styles.btnRow}>
              <Pressable onPress={onScrcpy} style={styles.btn}>
                <Text style={styles.btnText}>OPEN SCRCPY</Text>
              </Pressable>
              <Pressable onPress={toggleLogcat} style={styles.btn}>
                <Text style={styles.btnText}>{logcatOn ? "STOP LOGCAT" : "TAIL LOGCAT"}</Text>
              </Pressable>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={typography.h2}>ADB shell</Text>
            <TextInput
              value={shellCmd} onChangeText={setShellCmd}
              style={styles.input} autoCapitalize="none" autoCorrect={false}
              placeholder="adb shell command" placeholderTextColor={tokens.dim}
            />
            <View style={styles.btnRow}>
              <Pressable onPress={runShell} style={styles.btn}>
                <Text style={styles.btnText}>RUN</Text>
              </Pressable>
            </View>
            {!!shellOut && (
              <ScrollView style={styles.log}>
                <Text style={[styles.logLine, { padding: spacing.sm }]}>{shellOut}</Text>
              </ScrollView>
            )}
          </View>

          {logcatOn && (
            <View style={styles.section}>
              <Text style={typography.h2}>Logcat (live)</Text>
              <ScrollView style={styles.log}
                ref={(r) => { if (r) (r as unknown as { scrollToEnd: (a?: object) => void }).scrollToEnd({ animated: false }); }}
              >
                <View style={{ padding: spacing.sm }}>
                  {logLines.map((l, i) => (
                    <Text key={i} style={styles.logLine}>{l}</Text>
                  ))}
                </View>
              </ScrollView>
            </View>
          )}
          <View style={{ height: spacing.xl }} />
        </ScrollView>
      </View>
    </Modal>
  );
}
