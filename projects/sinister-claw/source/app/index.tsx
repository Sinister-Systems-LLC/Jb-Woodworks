// RKOJ Mobile :: app/index.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Root component -- RKOJ branding shell:
//   - Drawer left  (RkojSidebar)   :: WORKSPACE / OPERATIONS / AI / SYSTEM
//   - Top header   (RkojHeader)    :: logo + title + 3 chip tabs + actions
//   - Body         (chip switch)   :: AgentsTabView / PhonesTabView / WorkstationTabView
//   - Splash       (SplashOverlay) :: Sanctum purple gradient + RKOJ logo
//
// The drawer slides in over the body via Modal. Sidebar selections that
// don't map to one of the three chip tabs (e.g. Vault, Brain) jump to
// the Workstation chip so the relevant tile is one tap away.

import React, { useEffect, useState } from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

import { useTheme } from "./theme";
import { RkojHeader, ChipKey } from "./components/RkojHeader";
import { RkojSidebar, SidebarKey } from "./components/RkojSidebar";
import { SplashOverlay } from "./components/SplashOverlay";
import { AgentsTabView } from "./views/AgentsTabView";
import { PhonesTabView } from "./views/PhonesTabView";
import { WorkstationTabView } from "./views/WorkstationTabView";

const SIDEBAR_TO_CHIP: Record<SidebarKey, ChipKey> = {
  overview:   "workstation",
  agents:     "agents",
  projects:   "workstation",
  phones:     "phones",
  vault:      "workstation",
  watchdog:   "workstation",
  brain:      "workstation",
  mcp:        "workstation",
  skills:     "workstation",
  settings:   "workstation",
  account:    "workstation",
};

export default function App() {
  const { tokens } = useTheme();
  const [chip, setChip] = useState<ChipKey>("agents");
  const [nav, setNav] = useState<SidebarKey>("agents");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [splash, setSplash] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setSplash(false), 1200);
    return () => clearTimeout(t);
  }, []);

  const onSidebarSelect = (key: SidebarKey) => {
    setNav(key);
    setChip(SIDEBAR_TO_CHIP[key]);
    setDrawerOpen(false);
  };

  const styles = StyleSheet.create({
    root: { flex: 1, backgroundColor: tokens.bg },
    body: { flex: 1, backgroundColor: tokens.bg },

    drawerBackdrop: {
      flex: 1,
      backgroundColor: "rgba(7, 7, 11, 0.6)",
      flexDirection: "row",
    },
    drawerPanel: {
      width: 280,
      backgroundColor: tokens.bgGlass,
      borderRightWidth: 1,
      borderRightColor: tokens.borderGlass,
    },
    drawerSpacer: { flex: 1 },
  });

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <SafeAreaView style={styles.root} edges={["top"]}>
        <RkojHeader
          activeChip={chip}
          onChipPress={setChip}
          onMenuPress={() => setDrawerOpen(true)}
          onActionPress={(k) => {
            if (k === "settings") { onSidebarSelect("settings"); }
            else if (k === "inbox")   { onSidebarSelect("overview"); }
            // alerts / palette: no-op for now (placeholder for v0.3)
          }}
        />
        <View style={styles.body}>
          {chip === "agents"      && <AgentsTabView />}
          {chip === "phones"      && <PhonesTabView />}
          {chip === "workstation" && <WorkstationTabView />}
        </View>
      </SafeAreaView>

      <Modal
        visible={drawerOpen}
        animationType="fade"
        transparent
        onRequestClose={() => setDrawerOpen(false)}
      >
        <View style={styles.drawerBackdrop}>
          <View style={styles.drawerPanel}>
            <RkojSidebar activeKey={nav} onSelect={onSidebarSelect} />
          </View>
          <Pressable style={styles.drawerSpacer} onPress={() => setDrawerOpen(false)} />
        </View>
      </Modal>

      <SplashOverlay visible={splash} />
    </SafeAreaProvider>
  );
}
