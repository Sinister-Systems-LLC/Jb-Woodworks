// RKOJ Mobile :: theme/index.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Re-exports the Sanctum-canonical tokens + useTheme() hook + back-compat
// `colors` alias so the existing screens keep compiling during the rebrand.

export {
  tokens,
  spacing,
  radii,
  sizes,
  typography,
  shadows,
  projectAccents,
  useTheme,
} from "./tokens";
export type { ThemeTokens, TokenKey, UseThemeResult } from "./tokens";

// Legacy `colors.*` shim -- maps the prior names onto the new tokens.
// Screens written before the rebrand still reference colors.bgDeep / .purpleBright;
// new code should use `useTheme()` or import `tokens` directly.
export { colors } from "./colors";
