// RKOJ Mobile :: theme/tokens.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Sanctum purple design tokens -- the SINGLE source of truth for branding.
// Mirrors tools/sinister-rkoj-qt/sinister_rkoj_qt/theme.py + Sinister Panel
// CSS variables. Every screen should consume `useTheme()` rather than hex.
//
// Operator-canonical 2026-05-21 hex tokens (verbatim):
//   --purple-accent #A06EFF
//   --purple-deep   #7A3DD4
//   --purple-halo   #C39DFF
//   --light-purple  #E8D6FF
//   --bg            #0E0A14
//   --bg-glass      #15131A
//   --bg-glow       #2A1F3D
//   --border-glass  #3A2A55
//   --soft          #999AB0
//   --dim           #6E6E84
//   --green-accent  #85C86E

import { useMemo } from "react";

export const tokens = {
  // ---- Backgrounds ----
  bg:            "#0E0A14",
  bgDeep:        "#07070B",
  bgGlass:       "#15131A",
  bgGlass2:      "#1B1722",
  bgGlow:        "#2A1F3D",
  bgGlassThin:   "rgba(14, 10, 20, 0.65)",
  bgGlassAlpha:  "rgba(21, 19, 26, 0.55)",

  // ---- Purple palette ----
  purpleAccent:  "#A06EFF",
  purpleDeep:    "#7A3DD4",
  purpleHalo:    "#C39DFF",
  lightPurple:   "#E8D6FF",
  purpleGlow:    "rgba(160, 110, 255, 0.45)",
  purpleSoft:    "rgba(160, 110, 255, 0.12)",

  // ---- Status accents ----
  greenAccent:   "#85C86E",
  redAccent:     "#E06464",
  amberAccent:   "#E0B464",
  cyan:          "#6EE8FF",
  yellow:        "#FFD66E",
  magenta:       "#FF6EE8",

  // ---- Neutrals ----
  white:         "#F5F5FA",
  soft:          "#999AB0",
  dim:           "#6E6E84",
  black:         "#000000",

  // ---- Borders ----
  borderGlass:        "#3A2A55",
  borderGlassAlpha:   "rgba(160, 110, 255, 0.22)",
  borderGlassStrong:  "rgba(160, 110, 255, 0.55)",
} as const;

export type ThemeTokens = typeof tokens;
export type TokenKey = keyof ThemeTokens;

export const spacing = {
  xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32,
} as const;

export const radii = {
  sm: 6, md: 8, lg: 12, xl: 18, xxl: 24, pill: 999,
} as const;

export const sizes = {
  sidebarWidth:  240,
  headerHeight:  96,
  ribbonHeight:  110,
  kpiHeight:     100,
  windowRadius:  18,
} as const;

export const typography = {
  fontFamily: "System",
  monoFamily: "Menlo",
  display: { fontSize: 28, fontWeight: "700" as const, letterSpacing: -0.5 },
  title:   { fontSize: 22, fontWeight: "700" as const, letterSpacing: -0.3 },
  h1:      { fontSize: 18, fontWeight: "600" as const },
  h2:      { fontSize: 15, fontWeight: "600" as const, letterSpacing: 1, textTransform: "uppercase" as const },
  body:    { fontSize: 14, fontWeight: "400" as const, lineHeight: 20 },
  caption: { fontSize: 11, fontWeight: "500" as const, color: tokens.dim, letterSpacing: 0.5 },
  mono:    { fontSize: 12, fontFamily: "Menlo" },
} as const;

export const shadows = {
  glass: {
    shadowColor: tokens.purpleDeep,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 24,
    elevation: 8,
  },
  inset: {
    shadowColor: tokens.white,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 0,
  },
} as const;

// Per-project accent palette (mirrors Forge PROJECT_BORDER_PALETTE).
export const projectAccents: Record<string, string> = {
  "sanctum":             "#A06EFF",
  "sinister-panel":      "#6EE8FF",
  "kernel-apk":          "#6EFFA0",
  "sinister-emulator":   "#FFD66E",
  "rkoj-workstation":    "#FF6EE8",
  "rkoj":                "#A06EFF",
  "snap-emulator-api":   "#FF8C42",
  "tiktok-emulator-api": "#FF6E6E",
  "bumble-emulator-api": "#E8D6FF",
  "sinister-forge":      "#42E8FF",
  "sinister-mind":       "#B042FF",
  "sinister-term":       "#42FFB0",
  "sinister-claw":       "#FF42B0",
  _default:              "#A06EFF",
};

export interface UseThemeResult {
  tokens: ThemeTokens;
  spacing: typeof spacing;
  radii: typeof radii;
  sizes: typeof sizes;
  typography: typeof typography;
  shadows: typeof shadows;
  projectAccents: typeof projectAccents;
}

/**
 * Single global theme hook -- there is only one theme (Sanctum purple).
 * Always returns the same memoised object so consumers can put it in
 * dependency arrays without re-renders.
 */
export function useTheme(): UseThemeResult {
  return useMemo(
    () => ({ tokens, spacing, radii, sizes, typography, shadows, projectAccents }),
    [],
  );
}
