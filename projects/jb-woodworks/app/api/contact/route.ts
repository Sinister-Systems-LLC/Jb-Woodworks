// Author: RKOJ-ELENO :: 2026-05-23
// POST /api/contact - persist to Postgres (if DATABASE_URL set), forward to
// Resend (if RESEND_API_KEY set), and/or relay to FormSubmit as a fallback.
// Mirrors the LetsText pattern of layered email + DB.
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { rateLimitWithSweep } from "@/lib/rate-limit";

export const runtime = "nodejs";

// 5 submissions per IP per hour. Same shape as the LetsText limiter so ops
// muscle-memory carries between the two sites.
const CONTACT_LIMIT = 5;
const CONTACT_WINDOW_MS = 60 * 60 * 1000;

const schema = z.object({
  name: z.string().min(1).max(200),
  email: z.string().email().max(300),
  phone: z.string().max(50).optional().or(z.literal("")),
  service: z.string().max(80).optional().or(z.literal("")),
  message: z.string().min(1).max(5000),
  _honey: z.string().optional()
});

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || null;
  const userAgent = req.headers.get("user-agent") || null;

  const limiterKey = `contact:${(ip || "unknown").split(",")[0]!.trim()}`;
  const rl = rateLimitWithSweep(limiterKey, {
    limit: CONTACT_LIMIT,
    windowMs: CONTACT_WINDOW_MS
  });
  if (!rl.allowed) {
    const retryAfter = Math.max(1, Math.ceil((rl.resetAt - Date.now()) / 1000));
    return NextResponse.json(
      { ok: false, error: "Too many submissions. Please try again later." },
      {
        status: 429,
        headers: {
          "Retry-After": String(retryAfter),
          "X-RateLimit-Limit": String(CONTACT_LIMIT),
          "X-RateLimit-Remaining": "0",
          "X-RateLimit-Reset": String(Math.ceil(rl.resetAt / 1000))
        }
      }
    );
  }

  const form = await req.formData();
  const raw = Object.fromEntries(form.entries());
  const parsed = schema.safeParse(raw);

  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "Invalid form fields." }, { status: 400 });
  }

  const { name, email, phone, service, message, _honey } = parsed.data;
  if (_honey) {
    // honeypot tripped - silently accept
    return NextResponse.json({ ok: true, accepted: false });
  }

  // ---- 1) Persist to Postgres if Prisma is wired ----
  let dbId: string | null = null;
  if (process.env.DATABASE_URL) {
    try {
      const { prisma } = await import("@/lib/db");
      const row = await prisma.contactInquiry.create({
        data: {
          name,
          email,
          phone: phone || null,
          service: service || null,
          message,
          ip,
          userAgent
        }
      });
      dbId = row.id;
    } catch (err) {
      console.error("[contact] DB persist failed:", err);
    }
  }

  // ---- 2) Send email via Resend if configured ----
  let emailSent = false;
  if (process.env.RESEND_API_KEY && process.env.CONTACT_TO_EMAIL) {
    try {
      const { Resend } = await import("resend");
      const resend = new Resend(process.env.RESEND_API_KEY);
      const r = await resend.emails.send({
        from: process.env.CONTACT_FROM_EMAIL || "JB Woodworks <noreply@jbwoodworks.example>",
        to: [process.env.CONTACT_TO_EMAIL],
        replyTo: email,
        subject: `New project inquiry from ${name}`,
        text: [
          `Name:    ${name}`,
          `Email:   ${email}`,
          `Phone:   ${phone || "-"}`,
          `Service: ${service || "-"}`,
          `IP:      ${ip || "-"}`,
          `UA:      ${userAgent || "-"}`,
          "",
          "Message:",
          message
        ].join("\n")
      });
      emailSent = !r.error;
      if (r.error) console.error("[contact] Resend error:", r.error);
    } catch (err) {
      console.error("[contact] Resend send failed:", err);
    }
  }

  // ---- 3) Fallback: forward to FormSubmit (operator-owned default) ----
  // Hardcoded fallback so inquiries flow even when no env vars are set.
  // Operator-owned email: jbwoodworks8@gmail.com (matches lib/site.ts SITE.email).
  // Bounded to 8s so a slow third-party never hangs the form response.
  const formSubmitUrl =
    process.env.CONTACT_FORMSUBMIT_URL || "https://formsubmit.co/jbwoodworks8@gmail.com";
  if (!emailSent && formSubmitUrl) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const fwd = new URLSearchParams();
      fwd.set("Name", name);
      fwd.set("Email", email);
      if (phone) fwd.set("Phone", phone);
      if (service) fwd.set("Service", service);
      fwd.set("Project Details", message);
      fwd.set("_subject", `New project inquiry - JB Woodworks (${name})`);
      fwd.set("_captcha", "false");
      fwd.set("_template", "table");
      const res = await fetch(formSubmitUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Accept": "application/json",
          "User-Agent": "JB-Woodworks-Site/0.3.0"
        },
        body: fwd.toString(),
        redirect: "manual",
        signal: controller.signal
      });
      // 200, 302, and 303 are all "delivered" from FormSubmit.
      emailSent = res.status < 400;
      if (!emailSent) {
        console.warn(`[contact] FormSubmit returned ${res.status}`);
      }
    } catch (err) {
      // AbortError or network failure - log but do not block the user.
      console.error("[contact] FormSubmit fallback failed:", err);
    } finally {
      clearTimeout(timer);
    }
  }

  // ---- 4) Always log to stdout for ops visibility ----
  console.log(`[contact] received name=${name} email=${email} dbId=${dbId} emailSent=${emailSent}`);

  return NextResponse.json({ ok: true, dbId, emailSent });
}
