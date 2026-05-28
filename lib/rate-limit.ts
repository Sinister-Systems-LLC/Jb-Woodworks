// Author: RKOJ-ELENO :: 2026-05-28
// In-memory fixed-window rate limiter. Per-IP, per-bucket.
// Sufficient for a single Railway dyno; swap for Upstash if we horizontally
// scale. Resets when the process restarts (acceptable — limits abuse during
// a single deploy window, which is when spammers usually hit).

type Bucket = { count: number; resetAt: number };
const buckets = new Map<string, Bucket>();

export type RateLimitResult = {
  allowed: boolean;
  remaining: number;
  resetAt: number;
};

export function rateLimit(
  key: string,
  opts: { limit: number; windowMs: number }
): RateLimitResult {
  const now = Date.now();
  const existing = buckets.get(key);

  if (!existing || existing.resetAt <= now) {
    const resetAt = now + opts.windowMs;
    buckets.set(key, { count: 1, resetAt });
    return { allowed: true, remaining: opts.limit - 1, resetAt };
  }

  existing.count += 1;
  const allowed = existing.count <= opts.limit;
  return {
    allowed,
    remaining: Math.max(0, opts.limit - existing.count),
    resetAt: existing.resetAt
  };
}

// Sweep stale buckets occasionally so the map doesn't grow unbounded under
// sustained traffic. Cheap; runs once per ~10k limiter calls.
let calls = 0;
export function rateLimitWithSweep(
  key: string,
  opts: { limit: number; windowMs: number }
): RateLimitResult {
  calls += 1;
  if (calls % 10000 === 0) {
    const now = Date.now();
    for (const [k, b] of buckets) if (b.resetAt <= now) buckets.delete(k);
  }
  return rateLimit(key, opts);
}
