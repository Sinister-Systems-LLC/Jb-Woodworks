/* Author: RKOJ-ELENO :: 2026-05-23
 * Tailwind 4 config. Tokens mirror the existing static-site style.css so the
 * Next.js port renders pixel-equivalent.
 */
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        // Surface ramp (dark)
        bg:     '#0A0A0F',
        bg1:    '#13131A',
        bg2:    '#1C1C24',
        bg3:    '#2A2A33',

        // Brand gold (the SMPL primary)
        gold: {
          50:   '#FBF1DC',
          100:  '#F4DFB1',
          300:  '#E8C078',
          DEFAULT: '#D4A24A',
          700:  '#B88736',
          900:  '#5C4319',
        },

        // Text levels
        text:   '#FFFFFF',
        text2:  '#C7C7CF',
        text3:  '#8E8E98',
        text4:  '#5C5C66',

        // Semantic
        danger:  '#E5484D',
        success: '#34C759',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
      },
      borderRadius: {
        sm: '8px',
        DEFAULT: '14px',
        lg: '20px',
      },
      boxShadow: {
        'gold-glow': '0 0 40px 0 color-mix(in oklab, #D4A24A 35%, transparent)',
        'lg-card': 'inset 0 1px 0 0 color-mix(in oklab, white 14%, transparent), inset 0 0 50px -30px color-mix(in oklab, #D4A24A 10%, transparent), 0 10px 32px -12px color-mix(in oklab, #D4A24A 18%, rgba(0,0,0,0.55))',
      },
      transitionTimingFunction: {
        smpl: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      transitionDuration: {
        fast: '150ms',
        med:  '300ms',
        slow: '600ms',
      },
      backdropBlur: {
        glass: '24px',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
