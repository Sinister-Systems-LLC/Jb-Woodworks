// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
//
// Entry point for Sinister Chatbot (Eve Powered). Boots Express on PORT
// (default 5099). Mounts /health and /chatbot/* routes. Logs to stdout
// plus an audit.log file in this folder.

import express from "express";
import { appendFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chatbotRouter } from "./routes/chatbot.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const AUDIT_LOG = join(__dirname, "..", "audit.log");

const PORT = Number(process.env.PORT || 5099);

async function audit(line: object): Promise<void> {
  const row = JSON.stringify({ ts: new Date().toISOString(), ...line }) + "\n";
  try {
    await appendFile(AUDIT_LOG, row, "utf8");
  } catch {
    // best-effort; never let audit failure crash the server
  }
}

function log(...args: unknown[]): void {
  // eslint-disable-next-line no-console
  console.log("[sinister-chatbot]", ...args);
}

const app = express();
app.use(express.json({ limit: "2mb" }));

// Per-request audit + stdout line
app.use((req, _res, next) => {
  const line = { method: req.method, path: req.path };
  log(line);
  void audit({ kind: "request", ...line });
  next();
});

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "@sinister/chatbot",
    version: "0.1.0",
    sanctumInvention: 2,
    timestamp: new Date().toISOString(),
  });
});

app.use("/chatbot", chatbotRouter);

app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  log("error", err.message);
  void audit({ kind: "error", error: err.message });
  res.status(500).json({ error: err.message });
});

app.listen(PORT, () => {
  log(`listening on http://localhost:${PORT}`);
  log(`audit log: ${AUDIT_LOG}`);
  void audit({ kind: "boot", port: PORT });
});
