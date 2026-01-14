# Architecture (MVP)

## Components
- **apps/api**: FastAPI
- **apps/worker**: RQ worker consuming Redis queue
- **apps/web**: Next.js client (upload + poll + render)
- **apps/ios**: SwiftUI client (upload + poll + render)
- **packages/matching_core**: deterministic ranking + budget selection

## Data flow
1. Client uploads image to API `POST /scans`
2. API stores image locally, creates Scan(status=pending), enqueues job
3. Worker processes job:
   - VisionProvider detects items (deterministic stub for tests)
   - Crops items, EmbeddingProvider generates embeddings (deterministic)
   - MatchingCore finds nearest products and budget alternatives
   - Writes results to DB, sets Scan(status=done)
4. Client polls `GET /scans/{id}` until done

## Provider interfaces (swap later)
- VisionProvider: `detect(image_path) -> list[DetectedItem]`
- EmbeddingProvider: `embed(image_bytes) -> list[float]`
- CatalogProvider: seed/ingest products and embeddings
