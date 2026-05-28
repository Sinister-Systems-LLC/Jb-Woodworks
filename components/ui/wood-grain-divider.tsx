// Author: RKOJ-ELENO :: 2026-05-28
import { cn } from "@/lib/utils";

export function WoodGrainDivider({
  className,
  variant = "default",
  ariaLabel = "decorative wood-grain divider"
}: {
  className?: string;
  variant?: "default" | "thin" | "gold-tint";
  ariaLabel?: string;
}) {
  const height = variant === "thin" ? 14 : 28;
  const opacity = variant === "thin" ? 0.18 : 0.32;
  const stroke = variant === "gold-tint" ? "#c9a84c" : "#8a6b3a";

  return (
    <div
      role="separator"
      aria-label={ariaLabel}
      className={cn("w-full overflow-hidden select-none pointer-events-none", className)}
    >
      <svg
        viewBox={`0 0 1600 ${height}`}
        preserveAspectRatio="none"
        className="w-full block"
        style={{ height: `${height}px` }}
        aria-hidden
      >
        <defs>
          <filter id="wgd-turb" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.012 0.6" numOctaves="2" seed="7" />
            <feColorMatrix
              type="matrix"
              values="0 0 0 0 0.541
                      0 0 0 0 0.42
                      0 0 0 0 0.227
                      0 0 0 0.85 0"
            />
          </filter>
          <linearGradient id="wgd-fade" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#080808" stopOpacity="1" />
            <stop offset="10%" stopColor="#080808" stopOpacity="0" />
            <stop offset="90%" stopColor="#080808" stopOpacity="0" />
            <stop offset="100%" stopColor="#080808" stopOpacity="1" />
          </linearGradient>
        </defs>
        <rect width="1600" height={height} fill="#080808" />
        <rect width="1600" height={height} filter="url(#wgd-turb)" opacity={opacity} />
        <line
          x1="0"
          y1={height / 2}
          x2="1600"
          y2={height / 2}
          stroke={stroke}
          strokeOpacity="0.45"
          strokeWidth="0.7"
        />
        <rect width="1600" height={height} fill="url(#wgd-fade)" />
      </svg>
    </div>
  );
}
