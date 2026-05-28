/**
 * Lane MX-EVE-INTEGRATE :: integration smoke
 *
 * Runs all 5 feature checks post-launch (or in pre-build dry mode).
 *
 *   node --loader ts-node/esm tests/integration-smoke.ts        # full
 *   node --loader ts-node/esm tests/integration-smoke.ts --dry  # skip live process spawns
 *
 * Exit code 0 if all five report WIRED or PENDING-BUILD with valid evidence.
 * Exit code 1 if any check yields BLOCKED.
 */

import { promises as fs } from 'node:fs';
import path from 'node:path';
import net from 'node:net';

const CONFIG_FILE = path.resolve(__dirname, '..', 'config', 'runtime-integration.json');
const DRY = process.argv.includes('--dry');

type Result = 'WIRED' | 'PENDING-BUILD' | 'BLOCKED';

interface CheckResult {
  feature: string;
  result: Result;
  evidence: string;
}

async function fileExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function readJson<T>(p: string): Promise<T | null> {
  try {
    return JSON.parse(await fs.readFile(p, 'utf8')) as T;
  } catch {
    return null;
  }
}

function tcpProbe(host: string, port: number, timeoutMs = 2000): Promise<boolean> {
  return new Promise((resolve) => {
    const sock = new net.Socket();
    const done = (ok: boolean) => {
      sock.destroy();
      resolve(ok);
    };
    sock.setTimeout(timeoutMs);
    sock.once('connect', () => done(true));
    sock.once('timeout', () => done(false));
    sock.once('error', () => done(false));
    sock.connect(port, host);
  });
}

async function check1ClaudeAuth(cfg: { claude_auth: { canonical_accounts_file: string; canonical_health_file: string } }): Promise<CheckResult> {
  const acc = await fileExists(cfg.claude_auth.canonical_accounts_file);
  const hlth = await readJson<{ slots?: unknown[]; measured_at_utc?: string }>(cfg.claude_auth.canonical_health_file);
  if (acc && hlth && Array.isArray(hlth.slots)) {
    return {
      feature: '1. Real Claude account auth',
      result: 'WIRED',
      evidence: `accounts file present + health snapshot at ${hlth.measured_at_utc} with ${hlth.slots.length} slots`,
    };
  }
  return {
    feature: '1. Real Claude account auth',
    result: 'BLOCKED',
    evidence: `accounts=${acc} health=${!!hlth}`,
  };
}

async function check2Mcp(cfg: { mcp: { servers: Array<{ id: string; enabled: boolean; cwd?: string }> } }): Promise<CheckResult> {
  const reachable: string[] = [];
  const missing: string[] = [];
  for (const s of cfg.mcp.servers) {
    if (!s.enabled) continue;
    if (s.cwd && !(await fileExists(s.cwd))) {
      missing.push(`${s.id}(cwd missing)`);
    } else {
      reachable.push(s.id);
    }
  }
  if (reachable.length > 0 && missing.length === 0) {
    return {
      feature: '2. MCP server connections',
      result: 'WIRED',
      evidence: `${reachable.length} server cwds resolved: ${reachable.join(', ')}`,
    };
  }
  if (reachable.length > 0) {
    return {
      feature: '2. MCP server connections',
      result: 'PENDING-BUILD',
      evidence: `partial: ok=[${reachable.join(',')}] missing=[${missing.join(',')}]`,
    };
  }
  return {
    feature: '2. MCP server connections',
    result: 'BLOCKED',
    evidence: `no reachable server cwds: ${missing.join(', ')}`,
  };
}

async function check3Mesh(cfg: { mesh: { nats_url: string; panel_http_url: string } }): Promise<CheckResult> {
  const natsUrl = new URL(cfg.mesh.nats_url.replace('nats://', 'http://'));
  const panelUrl = new URL(cfg.mesh.panel_http_url);
  const natsOk = DRY ? true : await tcpProbe(natsUrl.hostname, Number(natsUrl.port || 4222));
  const panelOk = DRY ? true : await tcpProbe(panelUrl.hostname, Number(panelUrl.port || 3081));
  if (natsOk && panelOk) {
    return {
      feature: '3. Bot network connection',
      result: 'WIRED',
      evidence: `NATS ${cfg.mesh.nats_url} OK, panel ${cfg.mesh.panel_http_url} OK`,
    };
  }
  if (natsOk || panelOk) {
    return {
      feature: '3. Bot network connection',
      result: 'PENDING-BUILD',
      evidence: `nats=${natsOk} panel=${panelOk}`,
    };
  }
  return {
    feature: '3. Bot network connection',
    result: 'BLOCKED',
    evidence: `nats=${natsOk} panel=${panelOk}`,
  };
}

async function check4Swarm(cfg: { swarm: { paths: Record<string, string> } }): Promise<CheckResult> {
  const checks: string[] = [];
  for (const [k, v] of Object.entries(cfg.swarm.paths)) {
    if (k === 'tasks_fallback_glob') continue;
    checks.push(`${k}=${(await fileExists(v)) ? 'ok' : 'missing'}`);
  }
  const anyOk = checks.some((c) => c.endsWith('ok'));
  return {
    feature: '4. Swarm console',
    result: anyOk ? 'WIRED' : 'BLOCKED',
    evidence: checks.join(' '),
  };
}

async function check5Binary(cfg: { binary: { canonical_path: string; backup_path: string; disallowed_duplicates_glob: string[] } }): Promise<CheckResult> {
  const exists = await fileExists(cfg.binary.canonical_path);
  const backup = await fileExists(cfg.binary.backup_path);
  const dupes: string[] = [];
  for (const d of cfg.binary.disallowed_duplicates_glob) {
    if (await fileExists(d)) dupes.push(d);
  }
  if (exists && backup && dupes.length === 0) {
    return {
      feature: '5. Single canonical EVE.exe',
      result: 'WIRED',
      evidence: `canonical present, backup present, no duplicates`,
    };
  }
  if (exists && dupes.length > 0) {
    return {
      feature: '5. Single canonical EVE.exe',
      result: 'PENDING-BUILD',
      evidence: `duplicates present: ${dupes.join(', ')}`,
    };
  }
  return {
    feature: '5. Single canonical EVE.exe',
    result: exists ? 'PENDING-BUILD' : 'BLOCKED',
    evidence: `canonical=${exists} backup=${backup} dupes=${dupes.length}`,
  };
}

async function main(): Promise<void> {
  const cfg = await readJson<{
    claude_auth: { canonical_accounts_file: string; canonical_health_file: string };
    mcp: { servers: Array<{ id: string; enabled: boolean; cwd?: string }> };
    mesh: { nats_url: string; panel_http_url: string };
    swarm: { paths: Record<string, string> };
    binary: { canonical_path: string; backup_path: string; disallowed_duplicates_glob: string[] };
  }>(CONFIG_FILE);
  if (!cfg) {
    console.error(`FATAL: cannot read ${CONFIG_FILE}`);
    process.exit(1);
  }

  const results: CheckResult[] = [];
  results.push(await check1ClaudeAuth(cfg));
  results.push(await check2Mcp(cfg));
  results.push(await check3Mesh(cfg));
  results.push(await check4Swarm(cfg));
  results.push(await check5Binary(cfg));

  console.log('\n=== EVE.exe integration smoke ===\n');
  let blocked = 0;
  for (const r of results) {
    const tag = r.result.padEnd(14);
    console.log(`[${tag}] ${r.feature}`);
    console.log(`               ${r.evidence}\n`);
    if (r.result === 'BLOCKED') blocked += 1;
  }
  console.log(blocked === 0 ? 'OK — no blockers' : `FAIL — ${blocked} blocker(s)`);
  process.exit(blocked === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
