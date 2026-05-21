// RKOJ Mobile :: theme/colors.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// LEGACY shim. New code should import `tokens` / `useTheme()` from
// `./tokens`. This file remains so existing screens (SanctumScreen,
// ForgeScreen, etc) keep compiling -- the field names map onto the
// canonical Sanctum tokens (no more hex divergence).

import { tokens, projectAccents as canonicalAccents } from "./tokens";

export const colors = {
  bgDeep:        tokens.bgDeep,
  bg:            tokens.bg,
  bgGlass:       tokens.bgGlassAlpha,
  bgGlassThin:   tokens.bgGlassThin,

  purple:        tokens.purpleDeep,
  purpleBright:  tokens.purpleAccent,
  purpleGlow:    tokens.purpleGlow,
  purpleSoft:    tokens.purpleSoft,
  lightPurple:   tokens.lightPurple,
  purpleHalo:    tokens.purpleHalo,

  cyan:          tokens.cyan,
  green:         tokens.greenAccent,
  yellow:        tokens.yellow,
  red:           tokens.redAccent,
  magenta:       tokens.magenta,

  white:         tokens.white,
  dim:           tokens.dim,
  soft:          tokens.soft,

  borderGlass:        tokens.borderGlassAlpha,
  borderGlassStrong:  tokens.borderGlassStrong,
  borderGlassSolid:   tokens.borderGlass,
} as const;

export type ColorKey = keyof typeof colors;

export const projectAccents = canonicalAccents;
