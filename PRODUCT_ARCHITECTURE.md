# OliveWolf Studio — Production Architecture

OliveWolf is split into three product layers:

- **OliveWolf Core**: open-source engine and render abstraction.
- **OliveWolf Studio**: customer-facing workspace for teams.
- **OliveWolf Enterprise**: private deployment, governance, SLA, and integrations.

This repository now includes a production-oriented Studio backend skeleton under `studio/`.

---

## Product Goal

Customers should not install CUDA, Python packages, model weights, or edit YAML files.

The customer workflow is:

1. Create workspace / project.
2. Upload avatar source image.
3. Select voice.
4. Upload knowledge files or paste text.
5. Choose scene template.
6. Test chat.
7. Publish as web widget, API, video task, or live stream.

The system hides all model complexity behind managed services.

---

## Production Services

```text
Browser / Customer Console
        |
        v
olivewolf-api              FastAPI control plane
        |
        +--> Postgres       tenants, users, projects, avatars, jobs
        +--> Redis          task queue, realtime session state
        +--> Object Store   avatar images, audio, generated videos
        +--> Render Workers
              |-- live worker: ASR -> LLM -> TTS -> LivePortrait
              |-- 3D worker: LHM offline rendering
        |
        v
CDN / WebRTC / RTMP / API outputs
```

---

## Studio Backend Modules

```text
studio/
├── app/
│   ├── main.py              FastAPI app entry
│   ├── core/                config, logging, security
│   ├── db/                  SQLAlchemy engine and base models
│   ├── models/              tenant/project/avatar/knowledge/job models
│   ├── schemas/             Pydantic request/response schemas
│   ├── api/v1/              REST API routes
│   ├── services/            business logic
│   └── workers/             queue task definitions
├── alembic/                 database migrations placeholder
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Surface

### Tenant / Workspace
- `GET /api/v1/health`
- `POST /api/v1/tenants`
- `GET /api/v1/tenants/{tenant_id}`

### Projects
- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`

### Avatars
- `POST /api/v1/avatars`
- `GET /api/v1/avatars`
- `POST /api/v1/avatars/{avatar_id}/assets`

### Knowledge
- `POST /api/v1/knowledge-sources`
- `GET /api/v1/knowledge-sources`
- `POST /api/v1/knowledge-sources/{source_id}/ingest`

### Conversations
- `POST /api/v1/conversations/test`
- future: `WS /api/v1/conversations/realtime`

### Training Jobs
- `POST /api/v1/training-jobs`
- `GET /api/v1/training-jobs/{job_id}`

### Render Jobs
- `POST /api/v1/render-jobs`
- `GET /api/v1/render-jobs/{job_id}`

---

## Deployment Principles

- API service is stateless.
- Rendering is worker-based, not done inside request lifecycle.
- All large files go through object storage.
- API keys are stored as secrets, never committed.
- Tenant isolation is explicit in every model.
- Enterprise deployments can swap OpenAI/ElevenLabs with private LLM/TTS.

---

## Near-Term Roadmap

1. Complete Studio API and local Postgres persistence.
2. Add minimal web console.
3. Add object storage adapter: local filesystem first, S3/MinIO later.
4. Add Redis queue worker and job state transitions.
5. Connect live render worker to existing OliveWolf Core.
6. Add WebRTC streaming endpoint.
7. Add admin dashboard, audit logs, usage metering.
