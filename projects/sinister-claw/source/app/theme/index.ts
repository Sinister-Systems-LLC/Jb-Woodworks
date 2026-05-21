// Sinister Claw :: theme/index.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later

export { colors, projectAccents } from "./colors";

import { colors } from "./colors";

export const spacing = {
  xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32,
} as const;

export const radii = {
  sm: 8, md: 12, lg: 18, xl: 24, pill: 999,
} as const;

export const typography = {
  fontFamily: "System",
  display: { fontSize: 28, fontWeight: "700" as const, letterSpacing: -0.5 },
  title:   { fontSize: 22, fontWeight: "700" as const, letterSpacing: -0.3 },
  h1:      { fontSize: 18, fontWeight: "600" as const },
  h2:      { fontSize: 15, fontWeight: "600" as const, letterSpacing: 1, textTransform: "uppercase" as const },
  body:    { fontSize: 14, fontWeight: "400" as const, lineHeight: 20 },
  caption: { fontSize: 11, fontWeight: "500" as const, color: colors.dim, letterSpacing: 0.5 },
  mono:    { fontSize: 12, fontFamily: "Menlo" },
} as const;

export const shadows = {
  glass: {
    shadowColor: colors.purple,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 24,
    elevation: 8,
  },
  inset: {
    shadowColor: colors.white,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 0,
  },
} as const;
