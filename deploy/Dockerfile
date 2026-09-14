# Simplest deploy (college VM / any Docker host). Build: docker build -f deploy/Dockerfile -t studentup-exam .
# Run: docker run -d -p 8080:8080 -v studentup-data:/data -e EXAM_PORTAL_ADMIN_KEY="$(openssl rand -hex 8)" studentup-exam
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# exam DB + admin key repo root lo untayi — /data volume ki point chesam
ENV EXAM_PORTAL_DB=/data/exam_portal.db
VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=4).status==200 else 1)"

CMD ["python", "run.py", "--exam-portal", "--exam-host", "0.0.0.0", "--exam-port", "8080", \
     "--exam-db", "/data/exam_portal.db"]
