/* Author: RKOJ-ELENO :: 2026-05-23
 * Prisma client singleton. Pattern lifted from LetsText backend.
 * In dev (HMR) we cache on globalThis so we don't open a new pool every reload.
 */
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
