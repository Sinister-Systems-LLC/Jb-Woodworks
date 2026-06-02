// Author: RKOJ-ELENO :: 2026-05-23 (D-series D11 mirror 2026-05-31 — saw-blade)
import Link from "next/link";

// D-series D11 mirror: tiny spinning saw-blade pixel animation. Brand gold #c9a84c.
function SawBlade() {
  return (
    <div className="mb-8 inline-flex items-center justify-center" aria-hidden>
      <svg
        width="64"
        height="64"
        viewBox="0 0 64 64"
        fill="none"
        className="animate-[spin_3.5s_linear_infinite] drop-shadow-[0_0_14px_rgba(201,168,76,0.45)]"
      >
        <g stroke="#c9a84c" strokeWidth="1.4" fill="none">
          <circle cx="32" cy="32" r="22" strokeOpacity="0.85" />
          <circle cx="32" cy="32" r="6" fill="#c9a84c" fillOpacity="0.9" stroke="none" />
          {Array.from({ length: 12 }).map((_, i) => {
            const a = (i * Math.PI) / 6;
            const x1 = 32 + Math.cos(a) * 22;
            const y1 = 32 + Math.sin(a) * 22;
            const x2 = 32 + Math.cos(a) * 30;
            const y2 = 32 + Math.sin(a) * 30;
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#c9a84c"
                strokeWidth="2"
                strokeLinecap="square"
              />
            );
          })}
        </g>
      </svg>
    </div>
  );
}

export default function NotFound() {
  return (
    <section className="pt-40 pb-32 bg-gradient-to-b from-ink-2 to-ink relative overflow-hidden min-h-[80vh] flex items-center">
      {/* In-theme atmospheric backdrop (Nano Banana, 2026-05-23). Lone wood shaving on dark floor. */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none bg-cover bg-center"
        style={{ backgroundImage: "url(/img/generated/error-quiet-shop.png)", opacity: 0.32 }}
      />
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at center, rgba(8,8,8,0.55) 0%, rgba(8,8,8,0.95) 70%, #080808 100%)" }} />
      <div aria-hidden className="absolute -top-24 -right-24 w-[500px] h-[500px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />

      <div className="container-site relative">
        <SawBlade />
        <span className="section-tag">404 / Not Found</span>
        <h1 className="mb-5">That page doesn&apos;t<br /><em>exist.</em></h1>
        <p className="section-subheadline">
          Got lost in the lumber &mdash; a shaving on the shop floor where a link used to be. Try the main floor:
        </p>
        <div className="flex gap-3.5 flex-wrap">
          <Link href="/" className="btn btn-primary btn-large">Go home</Link>
          <Link href="/portfolio" className="btn btn-ghost btn-large">See the work</Link>
          <Link href="/contact" className="btn btn-ghost btn-large">Get a quote</Link>
        </div>
      </div>
    </section>
  );
}
