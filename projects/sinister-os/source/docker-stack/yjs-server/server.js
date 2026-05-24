// server.js — Sinister Mesh OS Yjs CRDT relay
// Author: RKOJ-ELENO :: 2026-05-24
//
// Listens on :1234. Browsers / editors connect via WebSocket; Yjs handles
// concurrent edits at character resolution. State persists to LevelDB at
// /app/data/yjs.level so doc state survives container restart.
//
// Health: GET /healthz returns 200 OK.
// Docs:   any path becomes a doc id; e.g. ws://host:1234/sanctum/progress.md
//         maps to doc 'sanctum/progress.md'.

import http from 'http';
import { WebSocketServer } from 'ws';
import { setupWSConnection } from 'y-websocket/bin/utils';
import { LeveldbPersistence } from 'y-leveldb';

const PORT = parseInt(process.env.YJS_PORT || '1234', 10);
const DB_PATH = process.env.YJS_DB || '/app/data/yjs.level';

const ldb = new LeveldbPersistence(DB_PATH);

const server = http.createServer((req, res) => {
  if (req.url === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'sinister-yjs', port: PORT }));
    return;
  }
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found. WebSocket endpoint: ws://host:' + PORT + '/<doc-id>');
});

const wss = new WebSocketServer({ noServer: true });

wss.on('connection', (conn, req) => {
  const docName = req.url.slice(1) || 'default';
  setupWSConnection(conn, req, { docName, gc: true });
});

server.on('upgrade', (req, socket, head) => {
  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit('connection', ws, req);
  });
});

server.listen(PORT, () => {
  console.log(`[sinister-yjs] listening on :${PORT}`);
  console.log(`[sinister-yjs] persistence at ${DB_PATH}`);
});

process.on('SIGTERM', () => {
  console.log('[sinister-yjs] SIGTERM; shutting down');
  server.close(() => process.exit(0));
});
