// Author: RKOJ-ELENO :: 2026-05-23
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const ts = new Date().toISOString();

  // DB probe — degrades gracefully when DATABASE_URL is absent (Railway pre-DB
  // boot, local dev without Postgres). Railway healthcheck reports real
  // liveness when Prisma is wired.
  let db: "ok" | "skip" | "fail" = "skip";
  if (process.env.DATABASE_URL) {
    try {
      const { prisma } = await import("@/lib/db");
      await prisma.$queryRaw`SELECT 1`;
      db = "ok";
    } catch {
      db = "fail";
    }
  }

  const ok = db !== "fail";
  return NextResponse.json({ ok, ts, db }, { status: ok ? 200 : 503 });
}
