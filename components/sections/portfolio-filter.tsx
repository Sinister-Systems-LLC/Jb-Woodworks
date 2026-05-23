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

  const visible = items.filter((i) => filter === "all" || categorySlug(i.category) === filter);

  return (
    <LayoutGroup>
      <div
        role="tablist"
        aria-label="Filter portfolio by project type"
        className="flex flex-wrap gap-2 mb-9 p-2 bg-ink-3 border border-line rounded-full max-w-max"
      >
        {chips.map((chip) => {
          const active = filter === chip.id;
          return (
            <button
              key={chip.id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => selectFilter(chip.id)}
              className={cn(
                "relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-full text-[0.78rem] font-semibold tracking-wide uppercase transition-colors duration-200",
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

      <motion.div
        layout
        className="grid gap-6 [grid-template-columns:repeat(auto-fit,minmax(320px,1fr))]"
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
