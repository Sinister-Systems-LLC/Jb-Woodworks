/* Author: RKOJ-ELENO :: 2026-05-23
 * Class-merge helper. Standard shadcn/ui pattern.
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import { createHash } from 'node:crypto';
/* SHA-256 hash for IP storage — never store raw IP. */
export function hashIp(ip: string | null | undefined, salt = 'smpl'): string | null {
  if (!ip) return null;
  return createHash('sha256').update(`${salt}:${ip}`).digest('hex');
}
