// RKOJ Mobile :: components/RkojLogo.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Inline RKOJ mark -- uses the PNG bitmap shipped in assets/rkoj-logo.png.
// Size + tint are configurable so the mark can sit in the sidebar mascot
// block, top header, splash, and account screens.

import React from "react";
import { Image, ImageStyle, StyleProp, View, ViewStyle } from "react-native";

interface RkojLogoProps {
  size?: number;
  style?: StyleProp<ViewStyle>;
  imageStyle?: StyleProp<ImageStyle>;
}

export function RkojLogo({ size = 56, style, imageStyle }: RkojLogoProps) {
  return (
    <View style={[{ width: size, height: size, alignItems: "center", justifyContent: "center" }, style]}>
      <Image
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        source={require("../../assets/rkoj-logo.png")}
        style={[{ width: size, height: size, resizeMode: "contain" }, imageStyle]}
      />
    </View>
  );
}
