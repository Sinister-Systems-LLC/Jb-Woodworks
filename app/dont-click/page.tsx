// Author: RKOJ-ELENO :: 2026-06-01
// v2: /dont-click — 404-style dino-game easter egg. Chrome-style endless runner,
// JBW-themed (jumping over sawhorses, ducking under planks). No external assets.
import type { Metadata } from "next";
import { DinoGame } from "@/components/sections/dino-game";

export const metadata: Metadata = {
  title: "DO NOT CLICK · JB Woodworks",
  description: "An easter egg. You weren't supposed to find this.",
  robots: { index: false, follow: false }
};

export default function DontClick() {
  return (
    <section className="pt-28 pb-20 bg-ink min-h-[80vh] relative overflow-hidden">
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at top, rgba(58,124,165,0.10), transparent 60%)" }} />
      <div className="container-site relative">
        <p className="font-mono text-[0.62rem] tracking-[0.42em] uppercase text-coastal-light mb-3">
          You weren&apos;t supposed to click that
        </p>
        <h1 className="font-display text-[clamp(2rem,4.8vw,3.6rem)] leading-[1.05] text-white m-0 mb-6">
          So now you&apos;re a <em className="text-gold">dino</em>.
        </h1>
        <p className="text-cream-50 max-w-[560px] leading-[1.7] mb-10">
          Press space or tap to jump. Down-arrow to duck. Don&apos;t hit the sawhorses. Don&apos;t hit the swinging planks. There&apos;s no high-score server &mdash; this is just for you.
        </p>
        <DinoGame />
      </div>
    </section>
  );
}
