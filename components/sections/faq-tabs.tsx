// Author: RKOJ-ELENO :: 2026-05-24
// Tabbed FAQ section. Pill bar of categories across the top, accordion list
// below. Each tab swap resets which item is open. Keyboard a11y: arrow keys
// cycle tabs (role=tablist), Tab → focuses questions, Enter/Space toggles,
// reduced-motion users get instant open/close.
"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import type { FaqCategory } from "@/lib/content/faq-categorized";

export function FaqTabs({
  categories,
  initialTab,
  initialOpen = 0
}: {
  categories: readonly FaqCategory[];
  /** Pass the id of the category to default to. Falls back to the first. */
  initialTab?: string;
  /** Index within the chosen tab's items that opens on mount. -1 = all closed. */
  initialOpen?: number;
}) {
  const reduced = useReducedMotion();
  const [activeId, setActiveId] = useState<string>(
    initialTab && categories.some((c) => c.id === initialTab) ? initialTab : categories[0]!.id
  );
  const [openIdx, setOpenIdx] = useState<number>(initialOpen);

  const active = categories.find((c) => c.id === activeId) ?? categories[0]!;

  function selectTab(id: string) {
    if (id === activeId) return;
    setActiveId(id);
    setOpenIdx(0);
  }

  function onTabKey(e: React.KeyboardEvent<HTMLButtonElement>, idx: number) {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const dir = e.key === "ArrowRight" ? 1 : -1;
      const next = (idx + dir + categories.length) % categories.length;
      selectTab(categories[next]!.id);
      // Move focus to the new tab button so keyboard users see the change
      const btn = document.getElementById(`faq-tab-${categories[next]!.id}`);
      btn?.focus();
    }
  }

  return (
    <div>
      {/* ── Pill bar ── */}
      <div
        role="tablist"
        aria-label="FAQ categories"
        className="flex justify-center mb-10"
      >
        <div className="inline-flex gap-1 rounded-2xl p-1.5 border border-line bg-ink-3/60 backdrop-blur-sm shrink-0 max-w-full overflow-x-auto">
          {categories.map((tab, idx) => {
            const isActive = tab.id === activeId;
            return (
              <button
                key={tab.id}
                id={`faq-tab-${tab.id}`}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls={`faq-panel-${tab.id}`}
                tabIndex={isActive ? 0 : -1}
                onClick={() => selectTab(tab.id)}
                onKeyDown={(e) => onTabKey(e, idx)}
                className={[
                  "relative inline-flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2.5 text-[0.78rem] font-bold tracking-[0.06em] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ink",
                  isActive
                    ? "text-ink"
                    : "text-cream-50 hover:text-white"
                ].join(" ")}
              >
                {isActive && (
                  <motion.span
                    layoutId="faq-pill"
                    className="absolute inset-0 bg-gold rounded-xl shadow-[0_0_18px_rgba(201,168,76,0.22)]"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                <svg
                  aria-hidden
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={isActive ? 2 : 1.6}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="relative shrink-0"
                >
                  <path d={tab.iconPath} />
                </svg>
                <span className="relative">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Accordion list ── */}
      <ul
        id={`faq-panel-${active.id}`}
        role="tabpanel"
        aria-labelledby={`faq-tab-${active.id}`}
        className="flex flex-col gap-2.5 list-none p-0 m-0"
      >
        {active.items.map((item, i) => {
          const isOpen = i === openIdx;
          return (
            <li key={`${active.id}-${i}`}>
              <article
                className={[
                  "rounded-xl border overflow-hidden transition-colors",
                  isOpen
                    ? "border-gold/40 bg-ink-3/80"
                    : "border-line bg-ink-3/40 hover:border-gold-dim hover:bg-ink-3/60"
                ].join(" ")}
              >
                <button
                  type="button"
                  onClick={() => setOpenIdx(isOpen ? -1 : i)}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${active.id}-${i}`}
                  className="w-full flex items-center justify-between gap-4 text-left px-5 sm:px-6 py-4 sm:py-5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
                >
                  <span className="font-display text-[1.02rem] sm:text-[1.08rem] text-white leading-snug italic">
                    {item.q}
                  </span>
                  <span
                    aria-hidden
                    className={[
                      "shrink-0 w-7 h-7 grid place-items-center rounded-full border transition-all duration-300",
                      isOpen
                        ? "border-gold text-ink bg-gold rotate-45"
                        : "border-gold/40 text-gold bg-transparent"
                    ].join(" ")}
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M6 1.5v9M1.5 6h9" />
                    </svg>
                  </span>
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      key="content"
                      id={`faq-answer-${active.id}-${i}`}
                      initial={reduced ? { opacity: 1 } : { height: 0, opacity: 0 }}
                      animate={reduced ? { opacity: 1 } : { height: "auto", opacity: 1 }}
                      exit={reduced ? { opacity: 0 } : { height: 0, opacity: 0 }}
                      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="px-5 sm:px-6 pb-5 sm:pb-6 pt-1">
                        <div className="h-px bg-gold/20 mb-4" aria-hidden />
                        <p className="text-cream-50 text-[0.95rem] leading-[1.75] m-0">
                          {item.a}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </article>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
