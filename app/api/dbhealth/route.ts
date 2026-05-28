// Author: RKOJ-ELENO :: 2026-05-28
// Database-specific probe distinct from /api/healthz (which Railway uses for app
// liveness and must never fail on transient DB issues). Returns 200 with `db: "ok"`
// when Prisma can reach Postgres, 503 with `db: "down"` otherwise. Use this for
// dashboards/alerting, not for orchestrator healthchecks.
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  if (!process.env.DATABASE_URL) {
    return NextResponse.json({ ok: true, db: "unconfigured", ts: new Date().toISOString() });
  }
  try {
    const { prisma } = await import("@/lib/db");
    await prisma.$queryRaw`SELECT 1`;
    return NextResponse.json({ ok: true, db: "ok", ts: new Date().toISOString() });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, db: "down", error: msg, ts: new Date().toISOString() },
      { status: 503 }
    );
  }
}
