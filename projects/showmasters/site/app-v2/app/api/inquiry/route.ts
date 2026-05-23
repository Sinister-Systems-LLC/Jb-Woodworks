/* Author: RKOJ-ELENO :: 2026-05-23
 * POST /api/inquiry — public estimate-request endpoint.
 * Pattern from LetsText: zod-validate, write via Prisma, return JSON.
 */
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { inquirySchema } from '@/lib/validations';
import { hashIp } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = inquirySchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { ok: false, error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 },
    );
  }
  const data = parsed.data;

  // Turnstile verification — only if a secret + token are present.
  let turnstileOk = true;
  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (secret && data.turnstileToken) {
    try {
      const verifyRes = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'content-type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ secret, response: data.turnstileToken }),
      });
      const json = (await verifyRes.json()) as { success: boolean };
      turnstileOk = !!json.success;
    } catch {
      turnstileOk = false;
    }
    if (!turnstileOk) {
      return NextResponse.json({ ok: false, error: 'Captcha failed' }, { status: 400 });
    }
  }

  const ip =
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    req.headers.get('x-real-ip') ??
    null;
  const userAgent = req.headers.get('user-agent') ?? null;

  const row = await prisma.inquiry.create({
    data: {
      name:    data.name,
      email:   data.email,
      phone:   data.phone || null,
      company: data.company || null,
      location: data.location || null,
      dates:    data.dates || null,
      brief:    data.brief,
      source:   data.source || null,
      ipHash:   hashIp(ip),
      userAgent,
      turnstileOk,
    },
    select: { id: true, createdAt: true },
  });

  // TODO: queue a notification email to INQUIRY_NOTIFY_EMAIL via SMTP_*.

  return NextResponse.json({ ok: true, id: row.id, createdAt: row.createdAt });
}
