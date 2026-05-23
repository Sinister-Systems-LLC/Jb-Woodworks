// Author: RKOJ-ELENO :: 2026-05-23
// Thin gold progress bar at the top of the viewport during App Router
// navigations. Started by internal-link clicks, completed when pathname
// changes.
"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export function RouteProgress() {
  const pathname = usePathname();
  const [active, setActive] = useState(false);
  const firstRenderRef = useRef(true);

  // Detect internal-link clicks to fire the bar early (before pathname swap).
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as HTMLElement | null)?.closest?.("a");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href) return;
      // Skip external + anchors + special schemes + new-tab links.
      if (a.target === "_blank") return;
      if (/^(https?:|mailto:|tel:|javascript:|sms:)/i.test(href)) return;
      if (href.startsWith("#")) return;
      // Same-path navigation? Skip.
      const targetPath = href.split("#")[0].split("?")[0] || "/";
      if (targetPath === pathname) return;
      setActive(true);
    };
    document.addEventListener("click", onClick, { capture: true });
    return () => document.removeEventListener("click", onClick, { capture: true } as EventListenerOptions);
  }, [pathname]);

  // On pathname change, finish + hide.
  useEffect(() => {
    if (firstRenderRef.current) {
      firstRenderRef.current = false;
      return;
    }
    // Pathname just changed; wait one tick so the bar reaches 100% visibly.
    const t = setTimeout(() => setActive(false), 250);
    return () => clearTimeout(t);
  }, [pathname]);

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          key="route-progress"
          aria-hidden
          className="fixed top-0 left-0 right-0 z-[10000] pointer-events-none"
          initial={{ opacity: 1 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        >
          <motion.div
            className="h-[2px] origin-left"
            style={{ background: "linear-gradient(90deg, transparent, #c9a84c 25%, #e2c47a 50%, #c9a84c 75%, transparent)" }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 0.92 }}
            exit={{ scaleX: 1 }}
            transition={{
              scaleX: { duration: 0.55, ease: [0.16, 1, 0.3, 1] }
            }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
