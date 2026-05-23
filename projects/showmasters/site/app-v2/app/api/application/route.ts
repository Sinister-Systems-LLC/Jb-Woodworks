/* Author: RKOJ-ELENO :: 2026-05-23
 * POST /api/application — careers application endpoint.
 */
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { applicationSchema } from '@/lib/validations';
import { hashIp } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }
  const parsed = applicationSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { ok: false, error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 },
    );
  }
  const d = parsed.data;
  const ip =
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    req.headers.get('x-real-ip') ??
    null;

  const row = await prisma.application.create({
    data: {
      name:     d.name,
      email:    d.email,
      phone:    d.phone || null,
      city:     d.city || null,
      state:    d.state || null,
      role:     d.role,
      yearsExp: d.yearsExp ?? null,
      skills:   d.skills ?? [],
      notes:    d.notes || null,
      ipHash:   hashIp(ip),
      userAgent: req.headers.get('user-agent') ?? null,
    },
    select: { id: true, createdAt: true },
  });

  return NextResponse.json({ ok: true, id: row.id, createdAt: row.createdAt });
}
