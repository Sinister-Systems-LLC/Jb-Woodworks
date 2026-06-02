// Author: RKOJ-ELENO :: 2026-05-23
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#080808",
          2: "#0f0f0f",
          3: "#141414",
          4: "#1a1a1a",
          5: "#222222"
        },
        gold: {
          DEFAULT: "#c9a84c",
          light: "#e2c47a",
          deep: "#a8842f",
          dim: "rgba(201, 168, 76, 0.10)",
          glow: "rgba(201, 168, 76, 0.25)"
        },
        cream: {
          DEFAULT: "#ffffff",
          80: "rgba(255,255,255,0.80)",
          50: "rgba(255,255,255,0.50)",
          30: "rgba(255,255,255,0.30)"
        },
        line: {
          DEFAULT: "rgba(255,255,255,0.07)",
          strong: "rgba(255,255,255,0.12)"
        },
        // v2 (2026-06-01): FL-coastal blue accent. Pairs with wood-tone gold —
        // gold stays primary brand, coastal-blue used for subtle flow/glow/contrast.
        coastal: {
          DEFAULT: "#3a7ca5",      // muted Atlantic blue
          light:   "#7aa9c7",      // sun-bleached seafoam-blue
          deep:    "#1f4f78",      // dock-shadow deep
          glow:    "rgba(58,124,165,0.25)",
          dim:     "rgba(58,124,165,0.10)"
        }
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "-apple-system", "Segoe UI", "sans-serif"]
      },
      maxWidth: {
        site: "1180px"
      },
      transitionTimingFunction: {
        "out-soft": "cubic-bezier(0.16, 1, 0.3, 1)"
      },
      keyframes: {
        "intro-rise": {
          "0%": { opacity: "0", transform: "translateY(28px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "intro-curtain": {
          "0%": { transform: "scaleY(1)" },
          "100%": { transform: "scaleY(0)" }
        },
        "intro-line": {
          "0%": { transform: "scaleX(0)", opacity: "0" },
          "100%": { transform: "scaleX(1)", opacity: "0.45" }
        },
        "scroll-bob": {
          "0%, 100%": { transform: "translateY(-100%)", opacity: "0" },
          "50%": { transform: "translateY(28px)", opacity: "1" }
        }
      },
      animation: {
        "intro-rise": "intro-rise 0.85s cubic-bezier(0.16,1,0.3,1) both",
        "intro-curtain": "intro-curtain 1s cubic-bezier(0.16,1,0.3,1) 0.1s both",
        "intro-line": "intro-line 1.4s cubic-bezier(0.16,1,0.3,1) 1.1s both",
        "scroll-bob": "scroll-bob 2.2s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

export default config;
