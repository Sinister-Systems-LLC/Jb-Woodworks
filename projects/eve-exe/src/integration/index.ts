/**
 * Lane MX-EVE-INTEGRATE :: barrel + bootstrap helper
 *
 * Single entry-point the EVE Electron main process calls to wire ALL five
 * integrations from one canonical config file.
 *
 * Usage (electron/main.ts):
 *   import { bootstrapEveIntegration } from '../src/integration';
 *   const integration = await bootstrapEveIntegration(ipcMain, 'D:/Sinister Sanctum/projects/eve-exe/config/runtime-integration.json');
 *   app.on('before-quit', () => integration.shutdown());
 */

import { promises as fs } from 'node:fs';
import type { IpcMain } from 'electron';
import { createClaudeAuth, ClaudeAuth, ClaudeAuthConfig } from './claude-auth';
import { createMcpManager, McpManager, McpConfig } from './mcp';
import { createMeshClient, MeshClient, MeshConfig } from './mesh';
import { createSwarmConsole, SwarmConsole, SwarmConfig } from './swarm';

export interface RuntimeIntegrationConfig {
  claude_auth: ClaudeAuthConfig;
  mcp: McpConfig;
  mesh: MeshConfig;
  swarm: SwarmConfig;
}

export interface EveIntegration {
  claudeAuth: ClaudeAuth;
  mcp: McpManager;
  mesh: MeshClient;
  swarm: SwarmConsole;
  config: RuntimeIntegrationConfig;
  shutdown: () => Promise<void>;
}

export async function loadRuntimeConfig(file: string): Promise<RuntimeIntegrationConfig> {
  const raw = await fs.readFile(file, 'utf8');
  return JSON.parse(raw) as RuntimeIntegrationConfig;
}

export async function bootstrapEveIntegration(
  ipcMain: IpcMain,
  configFile: string,
): Promise<EveIntegration> {
  const cfg = await loadRuntimeConfig(configFile);

  const claudeAuth = createClaudeAuth(cfg.claude_auth);
  const mcp = createMcpManager(cfg.mcp);
  const mesh = createMeshClient(cfg.mesh);
  const swarm = createSwarmConsole(cfg.swarm);

  await Promise.allSettled([
    claudeAuth.start(ipcMain),
    mcp.start(ipcMain),
    mesh.start(ipcMain),
    swarm.start(ipcMain),
  ]);

  return {
    claudeAuth,
    mcp,
    mesh,
    swarm,
    config: cfg,
    shutdown: async () => {
      claudeAuth.stop();
      swarm.stop();
      await Promise.allSettled([mcp.shutdown(), mesh.shutdown()]);
    },
  };
}

export {
  createClaudeAuth,
  createMcpManager,
  createMeshClient,
  createSwarmConsole,
};
