// server.js — Sinister Panel PLACEHOLDER stub
// Author: RKOJ-ELENO :: 2026-05-24
//
// This is a stub planted by the ISO builder when the real Panel
// Next.js standalone bundle (produced by bake-panel.sh) is not yet
// available. It exists ONLY so the build.sh staging-check passes and
// the ISO can be produced for early VM boot-tests.
//
// On a first-boot of the ISO, sinister-panel-kiosk.sh launches
// chromium pointing at http://localhost:3000. This stub serves a
// minimal "Sinister OS — Panel bundle not yet baked" page so the
// kiosk session is informative rather than broken.
//
// REPLACE THIS FILE by running: bash bake-panel.sh

const http = require('http');

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOSTNAME || '0.0.0.0';

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sinister OS — Panel Stub</title>
  <style>
    body {
      background: #0a0a14;
      color: #c9b3ff;
      font-family: ui-monospace, "JetBrains Mono", monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }
    .card {
      max-width: 640px;
      padding: 2rem 3rem;
      border: 1px solid #4a2e8a;
      border-radius: 12px;
      background: #14102a;
      box-shadow: 0 0 40px rgba(138, 80, 230, 0.25);
    }
    h1 { color: #b794f6; margin-top: 0; }
    code { color: #f0e8ff; background: #1f1840; padding: 2px 6px; border-radius: 4px; }
    .accent { color: #d6bcfa; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Sinister OS — Panel stub</h1>
    <p>The Sinister Panel Next.js bundle was not baked into this ISO.</p>
    <p>To replace this stub with the real Panel:</p>
    <pre><code>cd projects/sinister-os/source/iso-build
bash bake-panel.sh
bash build.sh</code></pre>
    <p class="accent">Author: RKOJ-ELENO :: 2026-05-24</p>
  </div>
</body>
</html>`;

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});

server.listen(PORT, HOST, () => {
  console.log(`Sinister Panel stub listening on http://${HOST}:${PORT}`);
});
