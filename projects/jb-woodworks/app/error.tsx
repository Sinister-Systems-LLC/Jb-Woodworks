// Author: RKOJ-ELENO :: 2026-05-23
// App-router error boundary. Themed to match 404 + brand voice.
"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // Surface for ops/dev consoles. Wired to whatever logger Sanctum prefers.
    // eslint-disable-next-line no-console
    console.error("[jbw] runtime error:", error);
  }, [error]);

  return (
    <section className="pt-40 pb-32 bg-gradient-to-b from-ink-2 to-ink relative overflow-hidden min-h-[80vh] flex items-center">
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none bg-cover bg-center"
        style={{ backgroundImage: "url(/img/generated/error-quiet-shop.png)", opacity: 0.28 }}
      />
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at center, rgba(8,8,8,0.55) 0%, rgba(8,8,8,0.95) 70%, #080808 100%)" }} />
      <div aria-hidden className="absolute -top-24 -right-24 w-[500px] h-[500px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />

      <div className="container-site relative">
        <span className="section-tag">Something broke</span>
        <h1 className="mb-5">A board slipped<br /><em>off the bench.</em></h1>
        <p className="section-subheadline">
          An unexpected error knocked the page off. Try again, or take one of the routes below. If it keeps happening, call (407) 561-1453 and we will sort it out.
        </p>
        <div className="flex gap-3.5 flex-wrap">
          <button type="button" onClick={() => reset()} className="btn btn-primary btn-large">Try again</button>
          <Link href="/" className="btn btn-ghost btn-large">Go home</Link>
          <Link href="/contact" className="btn btn-ghost btn-large">Contact us</Link>
        </div>
        {error?.digest && (
          <p className="mt-8 text-cream-30 text-[0.7rem] tracking-[0.18em] uppercase">Ref: {error.digest}</p>
        )}
      </div>
    </section>
  );
}
