# Dockerfile — Sinister Vault HTTP API
# Author: RKOJ-ELENO :: 2026-05-24
FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt server.py ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5078

CMD ["python", "-u", "server.py"]
