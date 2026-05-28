// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import { type PortfolioItem, categorySlug, portfolioCategories } from "@/lib/content";
import { PortfolioCard } from "./portfolio-card";
import { cn } from "@/lib/utils";

export function PortfolioFilter({
  items,
  initialFilter = "all"
}: {
  items: PortfolioItem[];
  initialFilter?: string;
}) {
  const cats = useMemo(() => portfolioCategories(), []);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const validSlugs = useMemo(
    () => new Set(["all", ...cats.map((c) => categorySlug(c))]),
    [cats]
  );
  const [filter, setFilter] = useState<string>(
    validSlugs.has(initialFilter) ? initialFilter : "all"
  );
  const [query, setQuery] = useState<string>("");

  // Keep state in sync with the URL when the user nav's via back/forward or
  // when a service-card link drops them on /portfolio?category=docks.
  useEffect(() => {
    const fromUrl = searchParams.get("category") ?? "all";
    const next = validSlugs.has(fromUrl) ? fromUrl : "all";
    setFilter((prev) => (prev === next ? prev : next));
  }, [searchParams, validSlugs]);

  const selectFilter = (id: string) => {
    setFilter(id);
    // Persist in URL so the filter is shareable + back-button safe.
    const params = new URLSearchParams(searchParams.toString());
    if (id === "all") params.delete("category"); else params.set("category", id);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  const chips = [
    { id: "all", label: "All", count: items.length },
    ...cats.map((c) => ({
      id: categorySlug(c),
      label: c,
      count: items.filter((i) => i.category === c).length
    }))
  ];

  const q = query.trim().toLowerCase();
  const visible = items
    .filter((i) => filter === "all" || categorySlug(i.category) === filter)
    .filter((i) => {
      if (!q) return true;
      const hay = [i.title, i.category, i.blurb ?? "", i.meta?.location ?? "", i.meta?.materials ?? ""]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });

  return (
    <LayoutGroup>
      <div
        role="tablist"
        aria-label="Filter portfolio by project type"
        className="flex flex-wrap justify-center gap-2 mb-9 p-2 bg-ink-3 border border-line rounded-full max-w-max mx-auto"
      >
        {chips.map((chip, idx) => {
          const active = filter === chip.id;
          const onKey = (e: React.KeyboardEvent<HTMLButtonElement>) => {
            let next = -1;
            if (e.key === "ArrowRight") next = (idx + 1) % chips.length;
            else if (e.key === "ArrowLeft") next = (idx - 1 + chips.length) % chips.length;
            else if (e.key === "Home") next = 0;
            else if (e.key === "End") next = chips.length - 1;
            if (next === -1) return;
            e.preventDefault();
            selectFilter(chips[next]!.id);
            // Move focus to the new chip so keyboard users see the change.
            const el = document.getElementById(`pf-chip-${chips[next]!.id}`);
            el?.focus();
          };
          return (
            <button
              key={chip.id}
              id={`pf-chip-${chip.id}`}
              type="button"
              role="tab"
              aria-selected={active}
              tabIndex={active ? 0 : -1}
              onClick={() => selectFilter(chip.id)}
              onKeyDown={onKey}
              className={cn(
                "relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-full text-[0.78rem] font-semibold tracking-wide uppercase transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ink",
                active ? "text-ink" : "text-cream-50 hover:text-white"
              )}
            >
              {active && (
                <motion.span
                  layoutId="filter-pill"
                  className="absolute inset-0 bg-gold rounded-full"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className={cn("relative w-1.5 h-1.5 rounded-full transition-transform", active ? "bg-ink" : "bg-gold")} />
              <span className="relative">{chip.label}</span>
              <span className={cn("relative text-[0.72rem] font-medium", active ? "text-ink/65" : "text-cream-30")}>
                ({chip.count})
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex justify-center mb-7">
        <label className="relative block w-full max-w-md">
          <span className="sr-only">Search portfolio</span>
          <input
            type="search"
            inputMode="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects, materials, locations..."
            className="w-full bg-ink-3 border border-line rounded-full pl-12 pr-4 py-3 text-[0.92rem] text-white placeholder:text-cream-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
            aria-label="Search portfolio by title, material, or location"
          />
          <span aria-hidden className="absolute left-4 top-1/2 -translate-y-1/2 text-cream-30 select-none">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.5" y2="16.5" />
            </svg>
          </span>
        </label>
      </div>

      <motion.div
        layout
        className="grid gap-6 justify-center [grid-template-columns:repeat(auto-fill,minmax(320px,420px))]"
      >
        <AnimatePresence mode="popLayout">
          {visible.map((item, i) => (
            <motion.div
              key={item.slug}
              layout
              initial={{ opacity: 0, y: 20, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.94, transition: { duration: 0.25 } }}
              transition={{ duration: 0.55, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
            >
              <PortfolioCard item={item} index={i} />
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {visible.length === 0 && (
        <p className="text-center text-cream-30 py-16">
          No projects in this category yet. Try a different filter.
        </p>
      )}
    </LayoutGroup>
  );
}
