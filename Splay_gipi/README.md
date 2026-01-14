# Splay — MVP (AI-Agent-Ready Monorepo)

**One room photo → key furniture detected → shoppable matches + cheaper alternatives.**

This repo is intentionally **deterministic and runnable** end-to-end with stubbed vision/embeddings so an AI-agent team can ship the golden path first, then swap real providers later.

## What you get (MVP)
- Web app (Next.js) upload → poll → results with overlays + product cards
- iOS app (SwiftUI) upload → poll → results
- FastAPI backend with:
  - `/auth/dev-login` (dev token)
  - `/scans` create scan (image upload)
  - `/scans/{id}` poll scan + results
- Worker (RQ) that processes scans asynchronously via Redis
- Seeded product catalog (100 items) with deterministic embeddings
- **>=80%** backend + shared library coverage gate (pytest)

## Repo layout
```
apps/
  api/        FastAPI backend
  worker/     RQ worker
  web/        Next.js web app
  ios/        SwiftUI app + Xcode project
packages/
  matching_core/  Shared matching/ranking logic (Python)
infra/docker/     docker-compose (Postgres optional) + Redis
docs/             PRD / Architecture / API Contracts / Data Models / Test Strategy
```

## Quickstart (local)
### 0) Requirements
- Python 3.12+
- Node 20+
- Docker Desktop (for Redis)

### 1) Start Redis
```bash
cd infra/docker
docker compose up -d
```

### 2) Backend API
```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python -m app.scripts.init_db
python -m app.scripts.seed_products

uvicorn app.main:app --reload
```

Open API docs: http://localhost:8000/docs

### 3) Worker
```bash
cd apps/worker
source ../api/.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m worker.main
```

### 4) Web app
```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Open web: http://localhost:3000

### 5) Run tests (coverage gate)
```bash
cd apps/api
source .venv/bin/activate
pytest --cov=app --cov=matching_core --cov-fail-under=80
```

## Notes
- Storage is local by default (`apps/api/.data/uploads`). Swap to S3/MinIO later.
- Vision/embeddings are deterministic stubs. Swap providers behind interfaces in `app/providers/`.

## Real integrations (non‑MVP)
To enable real product matching + live retailer links, see `docs/REAL_WORLD_INTEGRATION.md`.

See `docs/` for the full doc system.
