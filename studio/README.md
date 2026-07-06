# OliveWolf Studio

Production-oriented customer workspace for OliveWolf.

This is the control plane customers use instead of installing model dependencies or editing YAML files.

## What Studio Provides

- Tenant/workspace management
- Project management
- Avatar registry
- Browser-based Studio console
- Avatar image upload API
- API key protection for non-health endpoints
- Knowledge source registry and ingestion hook
- Conversation test API
- Training job API for customer-facing avatar build tasks
- Render job API
- Object storage abstraction
- Queue abstraction for render workers
- Docker entrypoint
- Background worker that processes queued training/render jobs into deployable artifact manifests

The current implementation is a production skeleton: stable API shape, persistence models, and deployment entrypoints. Render workers are intentionally abstracted so deployments can plug in CPU/GPU workers separately.

## Local Run

```bash
cd studio
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Open:

```text
http://localhost:8080/
```

API docs:

```text
http://localhost:8080/docs
```

If `STUDIO_API_KEY` is set in `.env`, enter the same key in the Studio console or send it as `X-API-Key`.

## Docker Run

```bash
cd studio
cp .env.example .env
docker compose up --build
```

## Quick API Test

```bash
curl -X POST http://localhost:8080/api/v1/tenants \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: change-me-in-production' \
  -d '{"name":"Demo Company","slug":"demo"}'
```

## Customer Console

The built-in console is available at `/` and `/studio/`.

It supports the first customer workflow:

1. Create tenant.
2. Create project.
3. Create avatar.
4. Upload avatar image.
5. Add knowledge source.
6. Test conversation.
7. Queue render job.

This is intentionally plain HTML so it can be deployed anywhere and later replaced by a full React/Next.js console.

## Production Notes

- Use Postgres, not SQLite.
- Put all generated media in object storage (S3/MinIO/CDN).
- Use Redis/RQ or Celery for render jobs.
- Keep GPU workers separate from API containers.
- Store provider keys in a secret manager.
- Add authentication before exposing to customers.
- Add audit logs and usage metering for Enterprise.

## Worker Integration Plan

`app/workers/render_worker.py` is the integration boundary.

Render worker should:

1. Load `RenderJob`.
2. Resolve `Project` and `Avatar`.
3. Pull source media from object storage.
4. Call OliveWolf Core:
   - `LivePortraitBackend` for real-time/portrait tasks.
   - `LHMBackend` for offline/full-body tasks.
5. Store generated outputs.
6. Update job status.
