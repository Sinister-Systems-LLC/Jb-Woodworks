// Author: RKOJ-ELENO :: 2026-05-23
import Link from "next/link";

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
      <div aria-hidden className="absolute -top-24 -right-24 w-[500px] h-[500px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(var(--accent-rgb),0.10), transparent 70%)" }} />

      <div className="container-site relative">
        <span className="section-tag">404 / Not Found</span>
        <h1 className="mb-5">That page doesn&apos;t<br /><em>exist.</em></h1>
        <p className="section-subheadline">
          A shaving on the shop floor where a link used to be. Try the main floor:
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
