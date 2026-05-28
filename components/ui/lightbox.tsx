// Author: RKOJ-ELENO :: 2026-05-28
"use client";
import { useEffect, useState } from "react";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

type Props = {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  sizes?: string;
  priority?: boolean;
  className?: string;
  thumbClassName?: string;
};

// Wraps a Next/Image in a <button> that, on click, mounts a full-screen overlay
// with the same image scaled up. ESC + click-outside close. Respects reduced motion.
export function LightboxImage({
  src,
  alt,
  width = 1600,
  height = 1200,
  sizes = "(max-width: 960px) 100vw, 960px",
  priority,
  className,
  thumbClassName
}: Props) {
  const [open, setOpen] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Open ${alt} full-size`}
        className={`block w-full bg-transparent border-0 p-0 cursor-zoom-in ${thumbClassName ?? ""}`}
      >
        <Image
          src={src}
          alt={alt}
          width={width}
          height={height}
          sizes={sizes}
          priority={priority}
          quality={92}
          style={{ width: "100%", height: "auto" }}
          className={`block cinematic-image ${className ?? ""}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            key="lightbox-overlay"
            role="dialog"
            aria-modal="true"
            aria-label={`${alt} expanded view`}
            onClick={() => setOpen(false)}
            initial={reduced ? { opacity: 1 } : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[120] grid place-items-center bg-ink/95 backdrop-blur-sm cursor-zoom-out p-6"
          >
            <motion.div
              initial={reduced ? false : { scale: 0.94, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={reduced ? { opacity: 0 } : { scale: 0.96, opacity: 0 }}
              transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
              className="relative max-w-[1600px] max-h-[92vh] w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Image
                src={src}
                alt={alt}
                width={width}
                height={height}
                sizes="100vw"
                quality={95}
                style={{ width: "auto", height: "auto", maxWidth: "100%", maxHeight: "92vh", margin: "0 auto", display: "block" }}
                className="rounded-lg shadow-2xl"
              />
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close expanded view"
                className="absolute top-3 right-3 w-10 h-10 grid place-items-center rounded-full bg-ink/80 border border-line text-white hover:bg-ink hover:border-gold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
