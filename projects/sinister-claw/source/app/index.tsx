// Sinister Claw :: app/index.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Root component - bottom-tab nav with the 7 tabs from the README plan.
// Sinister theme applied to NavigationContainer + tab bar.

import React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { colors } from "./theme";
import { SanctumScreen } from "./screens/SanctumScreen";
import { MindScreen } from "./screens/MindScreen";
import { ForgeScreen } from "./screens/ForgeScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { PlaceholderScreen } from "./screens/PlaceholderScreen";

const Tab = createBottomTabNavigator();

const SinisterNavTheme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.purpleBright,
    background: colors.bgDeep,
    card: colors.bg,
    text: colors.lightPurple,
    border: colors.borderGlass,
    notification: colors.cyan,
  },
};

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer theme={SinisterNavTheme}>
        <Tab.Navigator
          screenOptions={{
            headerShown: false,
            tabBarStyle: {
              backgroundColor: colors.bg,
              borderTopColor: colors.borderGlass,
            },
            tabBarActiveTintColor: colors.purpleBright,
            tabBarInactiveTintColor: colors.dim,
            tabBarLabelStyle: { fontSize: 10, letterSpacing: 0.5 },
          }}
        >
          <Tab.Screen name="Sanctum" component={SanctumScreen} />
          <Tab.Screen name="Forge" component={ForgeScreen} />
          <Tab.Screen name="Mind" component={MindScreen} />
          <Tab.Screen name="Panel">
            {() => (
              <PlaceholderScreen
                title="Panel"
                description="Mirror of Sinister Panel (snap.sinijkr.com) optimized for mobile. Accounts / Videos / Devices / Phones / Dispatches."
                phase="PH5 (Panel mirror)"
              />
            )}
          </Tab.Screen>
          <Tab.Screen name="Projects">
            {() => (
              <PlaceholderScreen
                title="Projects"
                description="Drill into one of the 11 Sinister projects. Plans, PROGRESS, resume-points, brain entries scoped to that lane."
                phase="PH6 (Projects detail)"
              />
            )}
          </Tab.Screen>
          <Tab.Screen name="Inbox">
            {() => (
              <PlaceholderScreen
                title="Inbox"
                description="Cross-agent messages addressed to the operator. Acknowledge from your phone."
                phase="PH7 (Inbox + ack)"
              />
            )}
          </Tab.Screen>
          <Tab.Screen name="Settings" component={SettingsScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
