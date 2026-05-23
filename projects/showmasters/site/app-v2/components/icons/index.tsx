/* Author: RKOJ-ELENO :: 2026-05-23
 * Custom SVG icons for Showmasters. No lucide-react outside this folder.
 * All icons share the same prop interface: { size?, className?, strokeWidth? }.
 * Drawings mirror the bespoke set we put inline in the static index.html.
 */
import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement> & {
  size?: number | string;
  strokeWidth?: number;
};

function Icon({
  size = 24,
  strokeWidth = 1.6,
  children,
  className,
  ...rest
}: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  );
}

/* Service icons (match the inline ones on the static home) */

export const StagehandIcon = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="7" cy="4.5" r="2" />
    <path d="M7 6.5v4.5l-2 5" />
    <path d="M7 11l3.2 2.5" />
    <rect x="10.5" y="13" width="9.5" height="7.5" rx="1" />
    <path d="M14 13v-1.6h3V13" />
    <circle cx="12" cy="22" r="1.1" />
    <circle cx="18.5" cy="22" r="1.1" />
  </Icon>
);

export const RiggerIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M9 3h5.5a4.5 4.5 0 0 1 4.5 4.5v9A4.5 4.5 0 0 1 14.5 21H9" />
    <path d="M9 3v18" />
    <path d="M9 7c-2 0-3.5 1.5-3.5 3.5" />
    <path d="M5.5 10.5v3" />
    <path d="M5.5 13.5c0 2 1.5 3.5 3.5 3.5" />
    <path d="M11 3c-.8-1.6-2.5-1.8-4-1" />
    <path d="M11 21c-.8 1.6-2.5 1.8-4 1" />
  </Icon>
);

export const TechnicianIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <line x1="8" y1="6" x2="8" y2="18" />
    <line x1="12" y1="6" x2="12" y2="18" />
    <line x1="16" y1="6" x2="16" y2="18" />
    <rect x="6.4" y="9" width="3.2" height="2.2" rx="0.5" fill="currentColor" />
    <rect x="10.4" y="13" width="3.2" height="2.2" rx="0.5" fill="currentColor" />
    <rect x="14.4" y="10.5" width="3.2" height="2.2" rx="0.5" fill="currentColor" />
  </Icon>
);

export const LiftOpIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="18" width="18" height="2.4" rx="0.5" />
    <circle cx="6.5" cy="22" r="1.1" />
    <circle cx="17.5" cy="22" r="1.1" />
    <path d="M7 18 L17 8 M17 18 L7 8 M9.5 15.5 L14.5 10.5 M14.5 15.5 L9.5 10.5" />
    <rect x="4" y="4" width="16" height="2.4" rx="0.5" />
    <path d="M5.5 4v-2 M18.5 4v-2" />
  </Icon>
);

export const CrewLeadIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 13a8 8 0 0 1 16 0" />
    <rect x="3" y="13" width="4" height="6" rx="1" />
    <rect x="17" y="13" width="4" height="6" rx="1" />
    <path d="M19 19l-1.2 3" />
    <circle cx="17.6" cy="22.4" r="1" />
  </Icon>
);

export const LogisticsIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="5" y="4" width="14" height="18" rx="1.2" />
    <rect x="9" y="2.4" width="6" height="3.2" rx="0.6" />
    <line x1="8" y1="10.5" x2="16" y2="10.5" />
    <line x1="8" y1="13.5" x2="16" y2="13.5" />
    <line x1="8" y1="16.5" x2="14" y2="16.5" />
    <path d="M15.8 16.5l1.1 1.1l2-2.8" />
  </Icon>
);

/* UI icons */

export const CheckIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 12.5l5 5L20 6" />
  </Icon>
);

export const ChevronRightIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M9 6l6 6-6 6" />
  </Icon>
);

export const MenuIcon = (p: IconProps) => (
  <Icon {...p}>
    <line x1="4" y1="7" x2="20" y2="7" />
    <line x1="4" y1="12" x2="20" y2="12" />
    <line x1="4" y1="17" x2="20" y2="17" />
  </Icon>
);

export const XIcon = (p: IconProps) => (
  <Icon {...p}>
    <line x1="6" y1="6" x2="18" y2="18" />
    <line x1="18" y1="6" x2="6" y2="18" />
  </Icon>
);

export const PhoneIcon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" />
  </Icon>
);

export const MailIcon = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="M3 7l9 7 9-7" />
  </Icon>
);

/* SMPL mark (small, for nav fallback) */
export const SmplMonogram = ({
  size = 32,
  className,
}: { size?: number | string; className?: string }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    role="img"
    aria-label="SMPL"
    className={className}
  >
    <rect width="64" height="64" rx="14" fill="#0B0B0F" />
    <text
      x="32"
      y="46"
      textAnchor="middle"
      fontFamily="Inter, Arial, sans-serif"
      fontWeight="900"
      fontSize="44"
      letterSpacing="-1.5"
      fill="#FFFFFF"
    >
      S
    </text>
    <path d="M44 12 L56 12 L56 24 Z" fill="#D4A24A" />
  </svg>
);
