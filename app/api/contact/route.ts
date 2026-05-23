// Author: RKOJ-ELENO :: 2026-05-23
// POST /api/contact - persist to Postgres (if DATABASE_URL set), forward to
// Resend (if RESEND_API_KEY set), and/or relay to FormSubmit as a fallback.
// Mirrors the LetsText pattern of layered email + DB.
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

export const runtime = "nodejs";

const schema = z.object({
  name: z.string().min(1).max(200),
  email: z.string().email().max(300),
  phone: z.string().max(50).optional().or(z.literal("")),
  service: z.string().max(80).optional().or(z.literal("")),
  message: z.string().min(1).max(5000),
  _honey: z.string().optional()
});

export async function POST(req: NextRequest) {
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

  const ip = req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || null;
  const userAgent = req.headers.get("user-agent") || null;

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

  // ---- 3) Fallback: forward to FormSubmit (v1 behavior) ----
  if (!emailSent && process.env.CONTACT_FORMSUBMIT_URL) {
    try {
      const fwd = new URLSearchParams();
      fwd.set("Name", name);
      fwd.set("Email", email);
      if (phone) fwd.set("Phone", phone);
      if (service) fwd.set("Service", service);
      fwd.set("Project Details", message);
      fwd.set("_subject", `New project inquiry - JB Woodworks (${name})`);
      fwd.set("_captcha", "false");
      await fetch(process.env.CONTACT_FORMSUBMIT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: fwd.toString()
      });
      emailSent = true;
    } catch (err) {
      console.error("[contact] FormSubmit fallback failed:", err);
    }
  }

  // ---- 4) Always log to stdout for ops visibility ----
  console.log(`[contact] received name=${name} email=${email} dbId=${dbId} emailSent=${emailSent}`);

  return NextResponse.json({ ok: true, dbId, emailSent });
}
