// Author: RKOJ-ELENO :: 2026-05-23
// Interactive before / after image comparison slider. Drag the gold divider to
// reveal the "after" build. Supports mouse, touch, and keyboard (focus + arrow
// keys / Home / End). Snaps to 50% on prefers-reduced-motion (no animation).
"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";

type Props = {
  before: string;
  after: string;
  alt: string;
  /** Label for the "before" pane (rendered top-left). Default "Before". */
  beforeLabel?: string;
  /** Label for the "after" pane (rendered top-right). Default "After". */
  afterLabel?: string;
  /** Where the divider starts (0-100). Default 50. */
  initialPercent?: number;
  /** Aspect ratio. Defaults to 4/3 to match the rest of the portfolio. */
  aspect?: `${number}/${number}`;
  /** Eager-load the images (above the fold). Default false. */
  eager?: boolean;
};

const STEP = 2;          // arrow-key step in percent
const STEP_LARGE = 10;   // shift+arrow-key step

function clamp(n: number) {
  if (n < 0) return 0;
  if (n > 100) return 100;
  return n;
}

export function BeforeAfter({
  before,
  after,
  alt,
  beforeLabel = "Before",
  afterLabel = "After",
  initialPercent = 50,
  aspect = "4/3",
  eager = false
}: Props) {
  const reduced = useReducedMotion();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [percent, setPercent] = useState(clamp(initialPercent));
  const [dragging, setDragging] = useState(false);

  const moveTo = useCallback((clientX: number) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    if (rect.width <= 0) return;
    const next = ((clientX - rect.left) / rect.width) * 100;
    setPercent(clamp(next));
  }, []);

  // Pointer-based interaction (one path covers mouse + touch + pen).
  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: PointerEvent) => moveTo(e.clientX);
    const onUp = () => setDragging(false);
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
    document.addEventListener("pointercancel", onUp);
    return () => {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      document.removeEventListener("pointercancel", onUp);
    };
  }, [dragging, moveTo]);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    moveTo(e.clientX);
    setDragging(true);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? STEP_LARGE : STEP;
    switch (e.key) {
      case "ArrowLeft":
      case "ArrowDown":
        e.preventDefault();
        setPercent((p) => clamp(p - step));
        return;
      case "ArrowRight":
      case "ArrowUp":
        e.preventDefault();
        setPercent((p) => clamp(p + step));
        return;
      case "Home":
        e.preventDefault();
        setPercent(0);
        return;
      case "End":
        e.preventDefault();
        setPercent(100);
        return;
    }
  };

  // Render path for users with prefers-reduced-motion: drop the slider, render
  // a side-by-side comparison instead (no animation, no drag).
  if (reduced) {
    return (
      <div className="grid sm:grid-cols-2 gap-3 bg-ink-3 border border-line rounded-xl p-3">
        <figure className="space-y-2">
          <div className="relative overflow-hidden rounded-md" style={{ aspectRatio: aspect }}>
            <Image src={before} alt={`${alt} - ${beforeLabel.toLowerCase()}`} fill sizes="(max-width: 960px) 50vw, 480px" className="object-cover" loading={eager ? undefined : "lazy"} />
          </div>
          <figcaption className="text-[0.65rem] tracking-[0.28em] uppercase font-bold text-gold">{beforeLabel}</figcaption>
        </figure>
        <figure className="space-y-2">
          <div className="relative overflow-hidden rounded-md" style={{ aspectRatio: aspect }}>
            <Image src={after} alt={`${alt} - ${afterLabel.toLowerCase()}`} fill sizes="(max-width: 960px) 50vw, 480px" className="object-cover" loading={eager ? undefined : "lazy"} />
          </div>
          <figcaption className="text-[0.65rem] tracking-[0.28em] uppercase font-bold text-gold">{afterLabel}</figcaption>
        </figure>
      </div>
    );
  }

  // Active slider. Container clips the "after" image; the "before" image sits
  // beneath it full-width.
  return (
    <div
      ref={containerRef}
      role="img"
      aria-label={`Before / after comparison: ${alt}. Use arrow keys to drag the divider.`}
      onPointerDown={onPointerDown}
      className={`relative w-full overflow-hidden rounded-xl bg-ink-5 border border-line ${dragging ? "cursor-grabbing select-none" : "cursor-ew-resize"}`}
      style={{ aspectRatio: aspect, touchAction: "none" }}
    >
      {/* After (bottom layer, full width) */}
      <Image
        src={after}
        alt={`${alt} - ${afterLabel.toLowerCase()}`}
        fill
        sizes="(max-width: 960px) 100vw, 960px"
        priority={eager}
        loading={eager ? undefined : "lazy"}
        className="object-cover object-center"
      />

      {/* Before (top layer, clipped to percent) */}
      <div
        className="absolute inset-0 overflow-hidden pointer-events-none"
        style={{ clipPath: `inset(0 ${100 - percent}% 0 0)` }}
      >
        <Image
          src={before}
          alt={`${alt} - ${beforeLabel.toLowerCase()}`}
          fill
          sizes="(max-width: 960px) 100vw, 960px"
          priority={eager}
          loading={eager ? undefined : "lazy"}
          className="object-cover object-center"
        />
      </div>

      {/* Corner labels */}
      <span className="lg-tag absolute top-3 left-3 px-2.5 py-1 text-[0.62rem] font-bold tracking-[0.22em] uppercase">
        {beforeLabel}
      </span>
      <span className="lg-tag absolute top-3 right-3 px-2.5 py-1 text-[0.62rem] font-bold tracking-[0.22em] uppercase">
        {afterLabel}
      </span>

      {/* Divider line + draggable thumb */}
      <div
        aria-hidden="true"
        className="absolute top-0 bottom-0 pointer-events-none"
        style={{ left: `${percent}%`, transform: "translateX(-50%)" }}
      >
        <div className="w-px h-full mx-auto bg-gradient-to-b from-gold/0 via-gold to-gold/0 shadow-[0_0_12px_rgba(var(--accent-rgb),0.55)]" />
      </div>
      <div
        role="slider"
        aria-valuenow={Math.round(percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Drag to reveal the after build"
        tabIndex={0}
        onKeyDown={onKeyDown}
        onFocus={() => { /* style only via :focus-visible */ }}
        className="lg-fab absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-11 h-11 flex items-center justify-center cursor-grab active:cursor-grabbing focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold/70 focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
        style={{ left: `${percent}%` }}
      >
        <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="7 5 3 10 7 15" />
          <polyline points="13 5 17 10 13 15" />
        </svg>
      </div>
    </div>
  );
}
