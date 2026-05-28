// Author: RKOJ-ELENO :: 2026-05-28
"use client";
import Script from "next/script";
import { useEffect, useRef } from "react";

// Cloudflare Turnstile widget — invisible spam shield for the contact form.
// Renders only when NEXT_PUBLIC_TURNSTILE_SITE_KEY is configured; otherwise no-op.
// On verification the widget injects a hidden input `cf-turnstile-response` into
// the surrounding form, which the /api/contact handler can validate server-side.
declare global {
  interface Window {
    turnstile?: {
      render: (
        el: HTMLElement | string,
        opts: { sitekey: string; size?: "normal" | "compact" | "invisible"; theme?: "dark" | "light" | "auto" }
      ) => string;
      reset: (widgetId?: string) => void;
    };
  }
}

export function Turnstile({ size = "invisible" }: { size?: "normal" | "compact" | "invisible" }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

  useEffect(() => {
    if (!siteKey || !containerRef.current) return;
    const id = window.setInterval(() => {
      if (window.turnstile && containerRef.current && !widgetId.current) {
        widgetId.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          size,
          theme: "dark"
        });
        window.clearInterval(id);
      }
    }, 200);
    return () => window.clearInterval(id);
  }, [siteKey, size]);

  if (!siteKey) return null;

  return (
    <>
      <Script
        src="https://challenges.cloudflare.com/turnstile/v0/api.js"
        strategy="afterInteractive"
        async
        defer
      />
      <div ref={containerRef} className="cf-turnstile-mount" aria-hidden />
    </>
  );
}
