// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { PortfolioItem } from "@/lib/content";

export function PortfolioCard({
  item,
  index,
  hidden = false
}: {
  item: PortfolioItem;
  index: number;
  hidden?: boolean;
}) {
  const reduced = useReducedMotion();
  const src = item.is_raw_cover ? `/img/projects/${item.cover}` : `/media/${item.cover}`;
  // index < 3 = visible on first paint of the listing; preload those, lazy the rest.
  const eager = index < 3;

  // First video in item.media[], if any — enables hover-to-play preview on the
  // card without leaving the listing.
  const firstVideo = item.media.find((m) => m.type === "video") as
    | { type: "video"; src: string; poster: string }
    | undefined;
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoReady, setVideoReady] = useState(false);
  const [isHover, setIsHover] = useState(false);

  // Touch / focus parity: tap-to-toggle on touch devices.
  const startVideo = () => {
    if (!firstVideo || !videoRef.current || reduced) return;
    setIsHover(true);
    if (videoRef.current.preload !== "auto") {
      videoRef.current.preload = "auto";
      videoRef.current.load();
    }
    try {
      videoRef.current.currentTime = 0;
      const p = videoRef.current.play();
      if (p && typeof p.catch === "function") p.catch(() => {});
    } catch {
      /* ignore — some browsers block autoplay on first interaction */
    }
  };
  const stopVideo = () => {
    setIsHover(false);
    if (!videoRef.current) return;
    try {
      videoRef.current.pause();
    } catch {
      /* ignore */
    }
  };

  // Cleanup if the card unmounts while playing
  useEffect(() => {
    return () => {
      if (videoRef.current) {
        try { videoRef.current.pause(); } catch { /* noop */ }
      }
    };
  }, []);

  return (
    <motion.div
      layout
      initial={reduced ? false : { opacity: 0, y: 28 }}
      animate={
        hidden
          ? { opacity: 0, scale: 0.95, y: 20 }
          : { opacity: 1, scale: 1, y: 0 }
      }
      transition={{ duration: 0.55, delay: hidden ? 0 : index * 0.07, ease: [0.16, 1, 0.3, 1] }}
      className={hidden ? "pointer-events-none absolute" : ""}
      aria-hidden={hidden}
    >
      <Link
        href={`/portfolio/${item.slug}`}
        className="group block bg-ink-3 border border-line rounded-xl overflow-hidden transition-all duration-500 ease-out hover:border-gold hover:-translate-y-1.5 hover:shadow-[0_4px_32px_rgba(0,0,0,0.6)]"
        onMouseEnter={startVideo}
        onMouseLeave={stopVideo}
        onFocus={startVideo}
        onBlur={stopVideo}
      >
        <div className="relative aspect-[4/3] bg-ink-5 overflow-hidden">
          {/* Poster (always rendered, fades out when video plays) */}
          <Image
            src={src}
            alt={item.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            priority={eager}
            loading={eager ? undefined : "lazy"}
            quality={88}
            className={[
              "object-cover object-center transition-all duration-1000 ease-out cinematic-image",
              "group-hover:scale-105",
              isHover && videoReady ? "opacity-0" : "opacity-100"
            ].join(" ")}
          />

          {/* Hover-to-play video preview (only rendered if item has a video) */}
          {firstVideo && !reduced && (
            <video
              ref={videoRef}
              className={[
                "absolute inset-0 w-full h-full object-cover transition-opacity duration-500",
                isHover && videoReady ? "opacity-100" : "opacity-0"
              ].join(" ")}
              muted
              loop
              playsInline
              preload="none"
              poster={`/media/${firstVideo.poster}`}
              onCanPlay={() => setVideoReady(true)}
              onLoadedData={() => setVideoReady(true)}
              aria-hidden="true"
            >
              <source src={`/media/${firstVideo.src}`} type="video/mp4" />
            </video>
          )}

          {/* Editorial bottom-gradient so card title never fights for contrast */}
          <span aria-hidden className="absolute inset-x-0 bottom-0 h-2/3 pointer-events-none" style={{ background: "linear-gradient(180deg, transparent 0%, rgba(8,8,8,0.55) 100%)" }} />

          {/* Tiny "VIDEO" pill in the corner if this item has a video */}
          {firstVideo && (
            <span className="absolute top-3 right-3 inline-flex items-center gap-1.5 px-2.5 py-1 bg-ink/75 backdrop-blur-md border border-gold/40 rounded-full text-[0.55rem] tracking-[0.22em] uppercase font-bold text-gold opacity-90 group-hover:opacity-100 transition-opacity">
              <svg aria-hidden width="9" height="9" viewBox="0 0 9 9" fill="currentColor">
                <path d="M2 1.5v6l5-3z" />
              </svg>
              {isHover && videoReady ? "Playing" : "Video"}
            </span>
          )}
        </div>
        <div className="px-6 pt-6 pb-7">
          <span className="block text-[0.62rem] font-bold tracking-[0.22em] uppercase text-gold mb-2">
            {item.category}
            {item.subcategory && (
              <>
                <span aria-hidden className="mx-2 text-cream-30">·</span>
                <span className="text-cream-50">{item.subcategory}</span>
              </>
            )}
          </span>
          <h3 className="font-display text-[1.4rem] mb-2">{item.title}</h3>
          <p className="text-cream-50 text-[0.92rem] leading-[1.6] mb-3.5">{item.blurb}</p>
          <span className="inline-flex items-center gap-1.5 text-gold text-[0.72rem] font-bold tracking-[0.14em] uppercase">
            View project
            <Icon name="arrow-right" size={14} className="transition-transform duration-300 group-hover:translate-x-1" />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
