// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
//
// Server-side port of the Eve observation derivation rules from
// `C:\Users\Zonia\Desktop\dashboard-skeleton\components\eve\eve-observations-card.tsx`.
//
// The .tsx file derives observations client-side from a fan profile and
// renders them under a read-only "EVE THINKS…" card in the inbox
// right-rail. The chatEngine on the server side needs the SAME
// observation set so it can fold them into the system prompt — i.e. the
// AI tone shifts in step with what the operator already sees in the UI.
//
// This module exports:
//   - Tone, Observation, FanProfile types
//   - deriveEveObservations(fan) — returns the top-3 observations sorted
//     by tone priority (accent > success > warning > info), identical
//     priority + cap behavior to the React `deriveObservations()`.
//
// Wiring status: chatEngine.ts has a TODO(eve) comment above
// `buildSystemPrompt` flagging the eventual call site. Until wired, this
// module is exported but unused — by design (see INTEGRATION.md).

export type Tone = "accent" | "success" | "warning" | "info";

export interface Observation {
  id: string;
  text: string;        // monolithic fallback string (matches Panel/skeleton shape)
  tone: Tone;
  label?: string;
  amount?: number;
  trailing?: string;
}

/**
 * Inputs to the derivation. Mirrors the `Inputs` interface in
 * `eve-observations-card.tsx` 1:1, renamed `FanProfile` to read better on
 * the server side where there is no concept of "card inputs".
 */
export interface FanProfile {
  totalSpent: number;
  completedPaymentsCount: number;
  highestPurchase: number;
  buyRate: number;                   // percent 0-100
  lastMessageAtMs: number | null;    // epoch ms or null
  fanSinceMs: number | null;         // epoch ms or null
  fanBirthday: string | null;        // 'YYYY-MM-DD' or null/empty
  isSubscribed: boolean;
}

function daysBetween(a: number, b: number): number {
  return Math.floor((a - b) / (24 * 60 * 60 * 1000));
}

function daysUntilBirthday(birthday: string): number | null {
  // birthday is YYYY-MM-DD. Compute days until next occurrence ignoring year.
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthday);
  if (!m) return null;
  const month = Number(m[2]);
  const day = Number(m[3]);
  if (!month || !day) return null;
  const now = new Date();
  const thisYear = new Date(now.getFullYear(), month - 1, day);
  const next = thisYear.getTime() >= now.getTime()
    ? thisYear
    : new Date(now.getFullYear() + 1, month - 1, day);
  return Math.ceil((next.getTime() - now.getTime()) / (24 * 60 * 60 * 1000));
}

/**
 * Returns the top 3 most relevant observations for this fan.
 * Priority: accent > success > warning > info — identical to the
 * dashboard-skeleton React implementation so the server-side prompt and
 * the client-side card stay in lockstep.
 */
export function deriveEveObservations(fan: FanProfile): Observation[] {
  const out: Observation[] = [];
  const now = Date.now();

  // Top-spender — large lifetime spend
  if (fan.totalSpent >= 1000) {
    out.push({
      id: "top-spender",
      tone: "accent",
      label: "Top spender",
      amount: Math.round(fan.totalSpent),
      trailing: "lifetime",
      text: `Top spender · $${Math.round(fan.totalSpent).toLocaleString()} lifetime`,
    });
  }

  // Premium tier — high single-buy ceiling
  if (fan.highestPurchase >= 50) {
    out.push({
      id: "premium-tier",
      tone: "success",
      label: "Premium tier",
      amount: Math.round(fan.highestPurchase),
      trailing: "top buy",
      text: `Premium tier · $${Math.round(fan.highestPurchase)} top buy`,
    });
  }

  // High intent — strong buy-rate with enough sample size
  if (fan.buyRate >= 70 && fan.completedPaymentsCount >= 3) {
    out.push({
      id: "high-intent",
      tone: "success",
      label: "High intent",
      trailing: `${fan.buyRate}% buy rate over ${fan.completedPaymentsCount} buys`,
      text: `High intent · ${fan.buyRate}% buy rate over ${fan.completedPaymentsCount} buys`,
    });
  }

  // First-purchase window — exactly one purchase = momentum opportunity
  if (fan.completedPaymentsCount === 1) {
    out.push({
      id: "first-buy-momentum",
      tone: "info",
      label: "First-purchase window",
      trailing: "follow up within 24h boosts repeat buy",
      text: "First-purchase window · follow up within 24h boosts repeat buy",
    });
  }

  // Dormant — no message activity 7+ days
  if (fan.lastMessageAtMs) {
    const dormantDays = daysBetween(now, fan.lastMessageAtMs);
    if (dormantDays >= 7) {
      out.push({
        id: "dormant",
        tone: "warning",
        label: `Dormant ${dormantDays}d`,
        trailing: "reactivation play is open",
        text: `Dormant ${dormantDays}d · reactivation play is open`,
      });
    }
  }

  // Birthday window — within next 7 days
  if (fan.fanBirthday) {
    const d = daysUntilBirthday(fan.fanBirthday);
    if (d !== null && d >= 0 && d <= 7) {
      out.push({
        id: "birthday",
        tone: "warning",
        label: d === 0 ? "Birthday today" : `Birthday in ${d}d`,
        text: d === 0 ? "Birthday today" : `Birthday in ${d}d`,
      });
    }
  }

  // Sub but no buys — paying subscriber that hasn't unlocked PPV yet
  if (fan.isSubscribed && fan.completedPaymentsCount === 0) {
    out.push({
      id: "sub-no-buys",
      tone: "info",
      label: "Subscriber",
      trailing: "no PPV unlocks yet",
      text: "Subscriber · no PPV unlocks yet",
    });
  }

  // Cap at top 3 most relevant — tone priority: accent > success > warning > info
  const priority: Record<Tone, number> = { accent: 0, success: 1, warning: 2, info: 3 };
  out.sort((a, b) => priority[a.tone] - priority[b.tone]);
  return out.slice(0, 3);
}

/**
 * Render a Observation[] as a compact bullet block suitable for injection
 * into a system prompt. The chatEngine will eventually use this when the
 * TODO(eve) wiring lands. Format example:
 *
 *   EVE THINKS (read-only signal — adapt tone, do NOT mention this to the fan):
 *   - Top spender · $1,240 lifetime
 *   - Premium tier · $99 top buy
 *   - First-purchase window · follow up within 24h boosts repeat buy
 */
export function renderObservationsForPrompt(observations: Observation[]): string {
  if (observations.length === 0) return "";
  const lines = observations.map((o) => {
    if (o.label && typeof o.amount === "number" && o.trailing) {
      return `- ${o.label} · $${o.amount.toLocaleString()} ${o.trailing}`;
    }
    if (o.label && o.trailing) {
      return `- ${o.label} · ${o.trailing}`;
    }
    return `- ${o.label ?? o.text}`;
  });
  return [
    "EVE THINKS (read-only signal — adapt tone, do NOT mention this to the fan):",
    ...lines,
  ].join("\n");
}
