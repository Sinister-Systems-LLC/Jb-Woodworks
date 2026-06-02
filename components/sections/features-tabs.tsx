// Author: RKOJ-ELENO :: 2026-06-01
// v2: 5-tab features (decks, docks, pergolas, outdoor furniture, marine-grade restoration)
// Adapted from operator brief (Let's Text revamp) — wood-tone brand + coastal-blue accent.
"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { IconName } from "@/components/ui/icon";

type Feature = {
  key: string;
  label: string;
  icon: IconName;
  headline: string;
  body: string;
  bullets: string[];
};

const FEATURES: Feature[] = [
  {
    key: "decks",
    label: "Custom Decks",
    icon: "anvil",
    headline: "Decks engineered for the Florida sun.",
    body: "IPE, cedar, and composite — built to FBC, sealed for UV + salt, drawn to your lot's grade and sightlines. No cookie-cutter span tables.",
    bullets: ["Florida Building Code-compliant framing", "Stainless or coated marine-grade fasteners", "Hidden-fastener finish options", "10-yr structural workmanship"]
  },
  {
    key: "docks",
    label: "Docks & Boardwalks",
    icon: "compass",
    headline: "Docks that survive the season — and the storm.",
    body: "Through-bolted to IPE or pressure-treated southern yellow pine, marine hardware throughout. We file the permits; you keep the waterfront.",
    bullets: ["Permit + survey coordination", "Hurricane-tie + wind-uplift detailing", "T-head, U-head, finger pier layouts", "Composite or hardwood decking"]
  },
  {
    key: "pergolas",
    label: "Pergolas & Shade",
    icon: "ruler",
    headline: "Shade structures that read as architecture.",
    body: "Cedar, IPE, or powder-coated steel — anchored for hurricane season, detailed like furniture. Optional retractable canopy + integrated lighting.",
    bullets: ["Cedar / IPE / metal hybrids", "Engineered for FL wind zones", "Integrated low-voltage lighting", "Retractable shade options"]
  },
  {
    key: "furniture",
    label: "Outdoor Furniture",
    icon: "leaf",
    headline: "Heirloom outdoor furniture, built in-shop.",
    body: "Dining tables, lounge sets, planters, bars. Dovetailed where it counts, marine-finished where it must — designed around your space, not a SKU.",
    bullets: ["Solid hardwood + composite hybrids", "Marine-grade oil + UV finish", "Custom-sized to your patio", "Powder-coated steel hardware"]
  },
  {
    key: "restoration",
    label: "Marine-Grade Restoration",
    icon: "ruler",
    headline: "Bring saltwater wood back from the brink.",
    body: "Re-decking, re-sealing, fastener replacement, structural inspections on existing docks, decks, and outdoor structures. We diagnose first, quote second.",
    bullets: ["Structural + fastener audits", "Selective board + joist replacement", "Strip + re-seal + UV treatment", "Hurricane-prep tune-ups"]
  }
];

export function FeaturesTabs() {
  const [active, setActive] = useState(0);
  const f = FEATURES[active];

  return (
    <section id="features" aria-labelledby="features-heading" className="relative py-24 sm:py-32 bg-ink-2 overflow-hidden border-y border-line">
      {/* Coastal-blue radial — subtle, off-screen */}
      <div aria-hidden className="absolute -top-40 -left-40 w-[560px] h-[560px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(58,124,165,0.10), transparent 70%)" }} />
      <div aria-hidden className="absolute -bottom-40 -right-40 w-[520px] h-[520px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />

      <div className="container-site relative">
        <div className="text-center mb-12 max-w-[760px] mx-auto">
          <p className="font-mono text-[0.65rem] tracking-[0.42em] uppercase text-coastal-light mb-5">
            <span className="tabular-nums">05</span><span className="mx-3 text-cream-30">·</span>Five things we do, deeply
          </p>
          <h2 id="features-heading" className="font-display text-[clamp(2.2rem,5vw,3.8rem)] leading-[1.05] text-white m-0">
            What we build, <em className="text-gold">in detail.</em>
          </h2>
          <span aria-hidden className="block h-px w-20 mx-auto mt-6 bg-gradient-to-r from-transparent via-coastal to-transparent" />
        </div>

        {/* Tabs */}
        <div role="tablist" aria-label="Service categories" className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-12">
          {FEATURES.map((feat, i) => {
            const isActive = i === active;
            return (
              <button
                key={feat.key}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls={`feature-panel-${feat.key}`}
                id={`feature-tab-${feat.key}`}
                onClick={() => setActive(i)}
                className={[
                  "relative px-5 sm:px-6 py-3 text-[0.78rem] font-semibold tracking-[0.12em] uppercase rounded-md transition-all duration-300 border",
                  isActive
                    ? "bg-coastal/15 border-coastal text-white shadow-[0_0_24px_rgba(58,124,165,0.25)]"
                    : "bg-transparent border-line text-cream-50 hover:text-white hover:border-gold/40"
                ].join(" ")}
              >
                <Icon name={feat.icon} size={14} className="inline-block mr-2 -mt-0.5" />
                {feat.label}
              </button>
            );
          })}
        </div>

        {/* Panel */}
        <AnimatePresence mode="wait">
          <motion.div
            key={f.key}
            id={`feature-panel-${f.key}`}
            role="tabpanel"
            aria-labelledby={`feature-tab-${f.key}`}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="grid gap-10 lg:grid-cols-2 max-w-[1040px] mx-auto bg-ink-3/60 border border-line rounded-2xl p-8 sm:p-12"
          >
            <div>
              <span className="font-mono text-[0.62rem] tracking-[0.4em] uppercase text-gold mb-3 inline-block">{f.label}</span>
              <h3 className="font-display text-[clamp(1.6rem,3.4vw,2.6rem)] leading-[1.1] text-white m-0">{f.headline}</h3>
              <p className="mt-5 text-cream-50 text-[0.98rem] leading-[1.7]">{f.body}</p>
            </div>
            <ul className="grid gap-3.5 self-center">
              {f.bullets.map((b, i) => (
                <li key={i} className="flex items-start gap-3 text-cream-80 text-[0.92rem] leading-snug">
                  <span aria-hidden className="mt-2 h-1.5 w-1.5 rounded-full bg-coastal shrink-0" />
                  {b}
                </li>
              ))}
            </ul>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
