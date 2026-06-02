// Author: RKOJ-ELENO :: 2026-06-01
// v2: FL-coastal section separators (driftwood / wave-line / seafoam-glow / sun-fade / marine-rope).
// Pure SVG/CSS — no images required, no layout shift.

type Variant = "driftwood" | "wave-line" | "seafoam-glow" | "sun-fade" | "marine-rope";

export function CoastalSeparator({ variant = "wave-line", className = "" }: { variant?: Variant; className?: string }) {
  return (
    <div aria-hidden className={`relative w-full overflow-hidden ${className}`}>
      {variant === "driftwood" && <Driftwood />}
      {variant === "wave-line" && <WaveLine />}
      {variant === "seafoam-glow" && <SeafoamGlow />}
      {variant === "sun-fade" && <SunFade />}
      {variant === "marine-rope" && <MarineRope />}
    </div>
  );
}

function Driftwood() {
  return (
    <div className="h-10 flex items-center justify-center bg-ink">
      <svg viewBox="0 0 1200 40" preserveAspectRatio="none" className="w-full h-full opacity-60">
        <defs>
          <linearGradient id="dw" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="50%" stopColor="#c9a84c" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path d="M0 20 Q 200 12, 400 22 T 800 18 T 1200 20" stroke="url(#dw)" strokeWidth="1.5" fill="none" />
        <path d="M0 24 Q 250 30, 500 22 T 1000 26 T 1200 22" stroke="url(#dw)" strokeWidth="0.8" fill="none" opacity="0.5" />
      </svg>
    </div>
  );
}

function WaveLine() {
  return (
    <div className="h-12 flex items-center justify-center bg-ink-2">
      <svg viewBox="0 0 1200 48" preserveAspectRatio="none" className="w-full h-full">
        <defs>
          <linearGradient id="wl" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="50%" stopColor="#3a7ca5" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path d="M0 24 Q 150 8, 300 24 T 600 24 T 900 24 T 1200 24" stroke="url(#wl)" strokeWidth="1.2" fill="none" opacity="0.7" />
        <path d="M0 32 Q 150 16, 300 32 T 600 32 T 900 32 T 1200 32" stroke="url(#wl)" strokeWidth="0.8" fill="none" opacity="0.4" />
      </svg>
    </div>
  );
}

function SeafoamGlow() {
  return (
    <div className="h-16 relative bg-ink">
      <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at center, rgba(122,169,199,0.18), transparent 60%)" }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-px w-2/3 bg-gradient-to-r from-transparent via-coastal-light to-transparent" />
    </div>
  );
}

function SunFade() {
  return (
    <div className="h-14 relative" style={{ background: "linear-gradient(180deg, #0f0f0f 0%, rgba(201,168,76,0.06) 50%, #080808 100%)" }}>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-px w-1/2 bg-gradient-to-r from-transparent via-gold to-transparent" />
    </div>
  );
}

function MarineRope() {
  return (
    <div className="h-10 flex items-center bg-ink-2">
      <svg viewBox="0 0 1200 24" preserveAspectRatio="none" className="w-full h-full opacity-70">
        <defs>
          <pattern id="rope" x="0" y="0" width="24" height="12" patternUnits="userSpaceOnUse">
            <path d="M0 6 Q 6 0, 12 6 T 24 6" stroke="#c9a84c" strokeWidth="1" fill="none" />
            <path d="M0 6 Q 6 12, 12 6 T 24 6" stroke="#3a7ca5" strokeWidth="0.7" fill="none" opacity="0.6" />
          </pattern>
        </defs>
        <rect width="1200" height="24" fill="url(#rope)" />
      </svg>
    </div>
  );
}
