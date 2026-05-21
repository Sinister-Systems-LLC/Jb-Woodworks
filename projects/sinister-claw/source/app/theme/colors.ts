// Sinister Claw :: theme/colors.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Sinister palette - iOS 18 purple liquid glass on dark void. Matches
// Sinister Mind's mind.css + Sinister Forge's theme.py.

export const colors = {
  bgDeep:        "#07070B",
  bg:            "#0E0A14",
  bgGlass:       "rgba(21, 19, 26, 0.55)",
  bgGlassThin:   "rgba(14, 10, 20, 0.65)",

  purple:        "#7A3DD4",
  purpleBright:  "#A06EFF",
  purpleGlow:    "rgba(160, 110, 255, 0.45)",
  purpleSoft:    "rgba(160, 110, 255, 0.12)",
  lightPurple:   "#E8D6FF",

  cyan:          "#6EE8FF",
  green:         "#6EFFA0",
  yellow:        "#FFD66E",
  red:           "#FF6E6E",
  magenta:       "#FF6EE8",

  white:         "#F5F5FA",
  dim:           "#6E6E84",
  soft:          "#999AB0",

  borderGlass:        "rgba(160, 110, 255, 0.22)",
  borderGlassStrong:  "rgba(160, 110, 255, 0.55)",
} as const;

export type ColorKey = keyof typeof colors;

// Per-project accent palette (mirrors Forge's PROJECT_BORDER_PALETTE)
export const projectAccents: Record<string, string> = {
  "sanctum":             "#A06EFF",
  "sinister-panel":      "#6EE8FF",
  "kernel-apk":          "#6EFFA0",
  "sinister-emulator":   "#FFD66E",
  "rkoj-workstation":    "#FF6EE8",
  "snap-emulator-api":   "#FF8C42",
  "tiktok-emulator-api": "#FF6E6E",
  "bumble-emulator-api": "#E8D6FF",
  "sinister-forge":      "#42E8FF",
  "sinister-mind":       "#B042FF",
  "sinister-term":       "#42FFB0",
  "sinister-claw":       "#FF42B0",
  _default:              "#A06EFF",
};
