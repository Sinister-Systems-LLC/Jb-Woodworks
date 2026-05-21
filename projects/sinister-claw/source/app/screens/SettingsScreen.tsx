// Sinister Claw :: screens/SettingsScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Operator-side configuration. Tailscale base URL + Forge bridge token.
// Token is persisted via expo-secure-store (iOS Keychain / Android Keystore).
// Also has a "Test connection" button that hits /api/health unauthenticated.

import React, { useEffect, useState } from "react";
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, radii, spacing, typography } from "@/theme";
import * as SecureStore from "expo-secure-store";
import {
  getBaseUrl,
  setBaseUrl,
  getAuthToken,
  setAuthToken,
} from "@/api/sanctum";

const STORE_KEY_PANEL_URL = "claw.panel.url";
const DEFAULT_PANEL_URL = "https://snap.sinijkr.com";

export function SettingsScreen() {
  const [baseUrl, setBaseUrlState] = useState("");
  const [token, setTokenState] = useState("");
  const [panelUrl, setPanelUrlState] = useState("");
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [healthMsg, setHealthMsg] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setBaseUrlState(await getBaseUrl());
      setTokenState((await getAuthToken()) ?? "");
      setPanelUrlState((await SecureStore.getItemAsync(STORE_KEY_PANEL_URL)) ?? DEFAULT_PANEL_URL);
    })();
  }, []);

  const onSave = async () => {
    await setBaseUrl(baseUrl.trim());
    await setAuthToken(token.trim());
    await SecureStore.setItemAsync(STORE_KEY_PANEL_URL, panelUrl.trim() || DEFAULT_PANEL_URL);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const onTest = async () => {
    setTesting(true);
    setHealthMsg(null);
    try {
      const resp = await fetch(`${baseUrl.trim()}/api/health`);
      if (resp.ok) {
        const data = await resp.json();
        setHealthMsg(`✓ ${data.name ?? "ok"} v${data.version ?? "?"} (${data.agents_active ?? 0} live)`);
      } else {
        setHealthMsg(`✗ HTTP ${resp.status}`);
      }
    } catch (e: unknown) {
      setHealthMsg(`✗ ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[typography.display, { color: colors.purpleBright }]}>
          ◈ SETTINGS
        </Text>
        <Text style={[typography.caption, { marginBottom: spacing.lg }]}>
          tailscale + bridge auth
        </Text>

        <GlassPanel style={{ marginBottom: spacing.md }}>
          <Text style={typography.h2}>Tailscale base URL</Text>
          <Text style={[typography.caption, { marginTop: spacing.xs }]}>
            Your PC on the tailnet. Forge bridge defaults to :5078.
          </Text>
          <TextInput
            value={baseUrl}
            onChangeText={setBaseUrlState}
            style={styles.input}
            placeholder="http://sanctum-pc:5078"
            placeholderTextColor={colors.dim}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
        </GlassPanel>

        <GlassPanel style={{ marginBottom: spacing.md }}>
          <Text style={typography.h2}>Panel URL</Text>
          <Text style={[typography.caption, { marginTop: spacing.xs }]}>
            Sinister Panel (deployed at snap.sinijkr.com or a local dev URL).
          </Text>
          <TextInput
            value={panelUrl}
            onChangeText={setPanelUrlState}
            style={styles.input}
            placeholder={DEFAULT_PANEL_URL}
            placeholderTextColor={colors.dim}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
        </GlassPanel>

        <GlassPanel style={{ marginBottom: spacing.md }}>
          <Text style={typography.h2}>Bridge auth token</Text>
          <Text style={[typography.caption, { marginTop: spacing.xs }]}>
            Find at: D:\Sinister Sanctum\_shared-memory\forge-bridge-token.txt
            {"\n"}
            Stored in iOS Keychain / Android Keystore via expo-secure-store.
          </Text>
          <TextInput
            value={token}
            onChangeText={setTokenState}
            style={styles.input}
            placeholder="paste token here"
            placeholderTextColor={colors.dim}
            autoCapitalize="none"
            autoCorrect={false}
            secureTextEntry
          />
        </GlassPanel>

        <View style={styles.row}>
          <Pressable onPress={onSave} style={[styles.btn, styles.btnPrimary]}>
            <Text style={[styles.btnText, { color: colors.bgDeep }]}>
              {saved ? "✓ SAVED" : "SAVE"}
            </Text>
          </Pressable>
          <Pressable onPress={onTest} style={[styles.btn, styles.btnSecondary]} disabled={testing}>
            <Text style={styles.btnText}>{testing ? "TESTING..." : "TEST"}</Text>
          </Pressable>
        </View>

        {healthMsg && (
          <GlassPanel style={{ marginTop: spacing.md }}>
            <Text style={[typography.body, { color: healthMsg.startsWith("✓") ? colors.green : colors.red }]}>
              {healthMsg}
            </Text>
          </GlassPanel>
        )}

        <GlassPanel style={{ marginTop: spacing.lg }}>
          <Text style={typography.h2}>How to bring the bridge up</Text>
          <Text style={[typography.body, { marginTop: spacing.sm }]}>
            On the operator's PC:{"\n"}
            <Text style={typography.mono}>
              cd "D:\Sinister Sanctum\projects\sinister-forge\source"{"\n"}
              python -m forge.bridge
            </Text>
          </Text>
          <Text style={[typography.caption, { marginTop: spacing.md }]}>
            The bridge prints the auth token at startup. Paste it above and tap TEST.
            If TEST passes, every tab in this app can drive your fleet over Tailscale.
          </Text>
        </GlassPanel>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  scroll: { padding: spacing.lg },
  input: {
    color: colors.lightPurple,
    backgroundColor: "rgba(14, 10, 20, 0.7)",
    borderWidth: 1,
    borderColor: colors.borderGlass,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 14,
    marginTop: spacing.sm,
  },
  row: { flexDirection: "row" },
  btn: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: radii.lg,
    alignItems: "center",
    marginHorizontal: spacing.xs,
  },
  btnPrimary: {
    backgroundColor: colors.purpleBright,
  },
  btnSecondary: {
    borderWidth: 1,
    borderColor: colors.borderGlass,
  },
  btnText: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1,
    color: colors.lightPurple,
  },
});
