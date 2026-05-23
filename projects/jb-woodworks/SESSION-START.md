# SESSION-START.md - jb-woodworks

> **Author:** RKOJ-ELENO :: 2026-05-23

Steps to resume this project in a new EVE session:

1. Read `CLAUDE.md` (this folder).
2. Read top 5 entries of `D:\Sinister Sanctum\_shared-memory\PROGRESS\jb-woodworks.md`.
3. Read most-recent resume-point at `D:\Sinister Sanctum\_shared-memory\resume-points\Jb Woodworks\<latest>.json`.
4. First time: `bats\jb-install.bat` (npm install + prisma generate). Copy `.env.example` to `.env.local` and set DATABASE_URL.
5. Daily: `bats\jb-dev.bat` then open <http://127.0.0.1:3000>.
6. Work on branch `agent/jb-woodworks/<short-topic>`.
7. Drop heartbeat to `_shared-memory/heartbeats/jb-woodworks.json` each turn.

Stack: **Next.js 15 + Tailwind + framer-motion + Prisma + Postgres + Resend**.
Deploys to **Railway** (never Vercel).
