# Dockerfile — Yjs CRDT websocket relay
# Author: RKOJ-ELENO :: 2026-05-24
FROM node:22-alpine

WORKDIR /app

COPY package.json server.js ./
RUN npm install --omit=dev --no-audit --no-fund

EXPOSE 1234

CMD ["node", "server.js"]
