// Author: RKOJ-ELENO :: 2026-06-02
// D-series JP-aesthetic section separators — asanoha (hemp leaf) and torii (gate).
// Server component — no client runtime needed.

type SeparatorVariant = "asanoha" | "torii";

interface SectionSeparatorProps {
  variant: SeparatorVariant;
  label: string;
}

// Asanoha (麻の葉) — traditional Japanese hemp-leaf geometric motif.
// Simplified: six-pointed interlocking star with radiating arms.
function AsanohaIcon() {
  const R = 20; // outer radius
  const r = 8;  // inner hub radius
  const cx = 24;
  const cy = 24;
  const arms = Array.from({ length: 6 }, (_, i) => {
    const a0 = (i * Math.PI) / 3 - Math.PI / 6;
    const a1 = ((i + 1) * Math.PI) / 3 - Math.PI / 6;
    const aMid = a0 + Math.PI / 6;
    const x0 = cx + Math.cos(a0) * r;
    const y0 = cy + Math.sin(a0) * r;
    const xM = cx + Math.cos(aMid) * R;
    const yM = cy + Math.sin(aMid) * R;
    const x1 = cx + Math.cos(a1) * r;
    const y1 = cy + Math.sin(a1) * r;
    return `M ${x0} ${y0} L ${xM} ${yM} L ${x1} ${y1}`;
  });
  const spokes = Array.from({ length: 6 }, (_, i) => {
    const a = (i * Math.PI) / 3;
    const x = cx + Math.cos(a) * R;
    const y = cy + Math.sin(a) * R;
    return `M ${cx} ${cy} L ${x} ${y}`;
  });
  return (
    <svg
      width="48"
      height="48"
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
      className="text-gold"
    >
      {/* Outer ring */}
      <circle cx={cx} cy={cy} r={R} stroke="currentColor" strokeOpacity="0.35" strokeWidth="0.8" />
      {/* Spoke lines */}
      {spokes.map((d, i) => (
        <path key={`s${i}`} d={d} stroke="currentColor" strokeOpacity="0.5" strokeWidth="0.7" />
      ))}
      {/* Petal arms */}
      {arms.map((d, i) => (
        <path key={`a${i}`} d={d} stroke="currentColor" strokeWidth="1.1" fill="none" />
      ))}
      {/* Center dot */}
      <circle cx={cx} cy={cy} r="2.5" fill="currentColor" fillOpacity="0.9" />
    </svg>
  );
}

// Torii (鳥居) — traditional Japanese gate silhouette.
function ToriiIcon() {
  return (
    <svg
      width="48"
      height="48"
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
      className="text-gold"
    >
      {/* Two vertical posts */}
      <line x1="13" y1="16" x2="13" y2="40" stroke="currentColor" strokeWidth="2.2" strokeLinecap="square" />
      <line x1="35" y1="16" x2="35" y2="40" stroke="currentColor" strokeWidth="2.2" strokeLinecap="square" />
      {/* Lower crossbar (straight) */}
      <line x1="10" y1="26" x2="38" y2="26" stroke="currentColor" strokeWidth="1.8" strokeLinecap="square" />
      {/* Upper crossbar (extends + slight upward sweep at ends) */}
      <path
        d="M 6 18.5 Q 7 17 13 17 L 35 17 Q 41 17 42 18.5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        fill="none"
      />
      {/* Cap beam above upper crossbar */}
      <path
        d="M 5 14 Q 7 12.5 24 12 Q 41 12.5 43 14"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
        strokeOpacity="0.8"
      />
    </svg>
  );
}

export function SectionSeparator({ variant, label }: SectionSeparatorProps) {
  const Icon = variant === "asanoha" ? AsanohaIcon : ToriiIcon;

  return (
    <div className="relative py-10 overflow-hidden" aria-hidden="true">
      {/* Faint horizontal center line behind motif */}
      <div className="absolute inset-y-0 left-0 right-0 flex items-center pointer-events-none">
        <div className="w-full h-px bg-gradient-to-r from-transparent via-gold/20 to-transparent" />
      </div>

      <div className="container-site relative flex flex-col items-center gap-3">
        {/* Left rule */}
        <div className="absolute top-1/2 left-0 right-1/2 -translate-y-1/2 pr-[72px] pointer-events-none hidden md:block">
          <div className="h-px bg-gradient-to-r from-transparent via-gold/25 to-gold/40" />
        </div>

        {/* Motif */}
        <div className="relative z-10 flex flex-col items-center gap-2.5">
          <Icon />
          <span className="font-mono text-[0.52rem] tracking-[0.45em] uppercase text-gold/60 font-bold">
            {label}
          </span>
        </div>

        {/* Right rule */}
        <div className="absolute top-1/2 left-1/2 right-0 -translate-y-1/2 pl-[72px] pointer-events-none hidden md:block">
          <div className="h-px bg-gradient-to-l from-transparent via-gold/25 to-gold/40" />
        </div>
      </div>
    </div>
  );
}
