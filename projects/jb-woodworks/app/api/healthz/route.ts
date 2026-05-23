// Author: RKOJ-ELENO :: 2026-05-23
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ ok: true, ts: new Date().toISOString() });
}
