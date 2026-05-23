// Author: RKOJ-ELENO :: 2026-05-23
// Short, elegant loading state used during App Router streaming transitions.
// The long brand splash (components/ui/splash.tsx) is reserved for cold load /
// hard refresh; this is the quick "we are pulling the next page" indicator
// that appears between routes.
export default function Loading() {
  return (
    <div role="status" aria-label="Loading" className="pt-40 pb-24 min-h-[60vh]">
      <div className="container-site relative">
        {/* Quick centered emblem: gold rule + tiny wordmark + pulse dots. No
            long skeleton bars; that read as "broken page" between routes. */}
        <div className="flex flex-col items-center justify-center gap-5 mt-12">
          <div className="text-center select-none">
            <div className="font-sans text-[1.5rem] font-black tracking-[0.22em] text-white/90 leading-none">JB</div>
            <div className="mt-1.5 text-[0.55rem] tracking-[0.55em] text-gold font-bold uppercase">Woodworks</div>
          </div>

          {/* Shimmer rule */}
          <div className="relative h-px w-32 bg-gold-dim overflow-hidden rounded-full">
            <div
              aria-hidden
              className="absolute inset-y-0 w-1/2 jbw-loading-shimmer"
              style={{ background: "linear-gradient(90deg, transparent, #e2c47a, transparent)" }}
            />
          </div>

          {/* Three pulse dots */}
          <div aria-hidden className="flex gap-1.5">
            <span className="w-1 h-1 rounded-full bg-gold/70 jbw-loading-dot" style={{ animationDelay: "0ms" }} />
            <span className="w-1 h-1 rounded-full bg-gold/70 jbw-loading-dot" style={{ animationDelay: "180ms" }} />
            <span className="w-1 h-1 rounded-full bg-gold/70 jbw-loading-dot" style={{ animationDelay: "360ms" }} />
          </div>

          <p className="text-cream-30 text-[0.6rem] tracking-[0.36em] uppercase font-semibold">Loading</p>
        </div>

        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.06), transparent 70%)" }} />
      </div>
    </div>
  );
}
