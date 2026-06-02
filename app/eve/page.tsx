// Author: RKOJ-ELENO :: 2026-05-31
// D-series D12 mirror: stub route for "Powered by Eve" footer link.
import Link from "next/link";

export const metadata = {
  title: "Powered by Eve — JB Woodworks",
  description: "JB Woodworks runs on Eve, our in-house operating layer.",
};

export default function EvePage() {
  return (
    <section className="pt-40 pb-32 bg-ink min-h-[70vh]">
      <div className="container-site text-center">
        <p className="font-mono text-[0.65rem] tracking-[0.42em] uppercase text-gold mb-4">Powered by Eve</p>
        <h1 className="font-display text-[clamp(2rem,5vw,3.4rem)] text-white mb-6">A quiet little operating layer.</h1>
        <p className="max-w-xl mx-auto text-cream-50 mb-8">JB Woodworks runs on <em className="text-gold">Eve</em>, our in-house operating layer for the shop, the website, and the build pipeline. More soon.</p>
        <Link href="/" className="text-[0.78rem] tracking-[0.3em] uppercase text-cream-50 hover:text-gold transition-colors">Back to the shop &rarr;</Link>
      </div>
    </section>
  );
}
