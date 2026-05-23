/* Author: RKOJ-ELENO :: 2026-05-23
 * Home placeholder. Phase 2 will port the full static-site index.html
 * into proper Next.js components (Navbar, HeroVideoSlider, ServicesGrid,
 * LocationsPreview, EstimateForm).
 */
export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-24">
      <div className="lg-card max-w-2xl p-10 text-center">
        <p className="text-[0.7rem] font-bold tracking-[6px] text-[var(--gold)]">
          SMPL · APP-V2 SCAFFOLD
        </p>
        <h1 className="mt-4 text-4xl md:text-5xl font-display">
          Show Masters Production Logistics
        </h1>
        <p className="mt-6 text-[var(--text-2)] leading-relaxed">
          Next.js 15 + React 19 + Prisma + Postgres + Tailwind + shadcn/ui — stack
          aligned with LetsText. This is the v2 application shell. Pages port
          from the static site one-by-one in the migration phases described in
          <code className="mx-1 px-1.5 py-0.5 rounded bg-white/10 text-[var(--gold-300)]">
            STACK.md
          </code>.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-3 text-sm">
          <span className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
            Next.js 15.5
          </span>
          <span className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
            React 19.2
          </span>
          <span className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
            Tailwind 4.1
          </span>
          <span className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
            Prisma + Postgres
          </span>
          <span className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5">
            shadcn/ui
          </span>
        </div>
        <p className="mt-10 text-xs text-[var(--text-3)]">
          Live public site is at <code>../index.html</code> until cutover.
        </p>
      </div>
    </main>
  );
}
