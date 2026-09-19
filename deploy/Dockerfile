# StudentUp bot container (cron-only bot — ports/servers levu).
# Build: docker build -f deploy/Dockerfile -t studentup-bot .
# Run:   docker run -d --env-file .env -v studentup-data:/data --name studentup-bot studentup-bot
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# bot state + logs /data volume lo (container delete ayina safe)
ENV STATE_PATH=/data/state.db
VOLUME ["/data"]

# health: state.db 3 gantallo touch ayyinda (bot run avutunda?)
HEALTHCHECK --interval=5m --timeout=10s --start-period=10m --retries=3 \
  CMD python -c "import os,time,sys; p='/data/state.db'; sys.exit(0 if (os.path.exists(p) and time.time()-os.path.getmtime(p)<10800) else 1)"

CMD ["bash", "deploy/bot-loop.sh"]
