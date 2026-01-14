# UPDATED DOCUMENTATION — READ FIRST
This document updates the MVP docs and defines what is required to make **Splay** truly functional with **real product matching** and **live retailer links**.  
If you are an agent working on Splay, **you must read this file before implementing changes**.

---

# Splay — Real‑World Integration Plan
Version: 2026‑01‑14  
Status: REQUIRED FOR PRODUCTION‑LIKE FUNCTIONALITY  

## Summary (What Changes vs MVP)
The MVP uses stubbed vision + seeded catalog + mock affiliate links.  
This update replaces those with:
- Real image understanding (vision / detection)
- Real product catalog ingestion
- Real embeddings + similarity search
- Live retailer links (affiliate or direct)

## Goals
1. A user uploads a room photo and receives actual product matches.
2. Product cards link to live retailer URLs.
3. Results are reproducible, explainable, and updatable.

## Non‑Goals
- Payments / subscriptions
- Full web scraping at runtime (batch ingest instead)
- AR / 3D / virtual staging

---

# Architecture Updates
## New Services / Modules
1. **Catalog Ingestor**
   - Pulls product data from one or more real sources.
   - Normalizes categories, prices, images, availability.
   - Stores product embeddings and metadata.

2. **Embedding Pipeline**
   - Uses real multimodal embeddings (image + text).
   - Runs on ingestion (catalog) and on scan (cropped detection images).

3. **Vector Search**
   - Stores embeddings and supports nearest‑neighbor search.
   - Must support top‑K queries by category.

4. **Retail Link Resolver**
   - Maintains live retailer URLs (affiliate if available).
   - Handles link expiration or redirects.

---

# Required External Integrations
You must choose and document actual providers. Options:

## A) Vision / Detection
- Implemented options: **Gemini vision** (default) and **OpenAI vision**.
  - `VISION_PROVIDER=gemini` (recommended when OpenAI quota is exhausted)
  - `VISION_PROVIDER=openai`
- Returns bounding boxes + category labels + a short query phrase for search.

## B) Embeddings
- Implemented option: **OpenAI text embeddings** (see `EMBEDDING_PROVIDER=openai`).
- Generates vector embeddings for:
  - Product images
  - Product text (title + brand + category)
  - Detected item crops from scans

## C) Product Catalog Sources
Pick **at least one**:
- **Shopping search API** (implemented: SerpAPI or Serper)
- Retailer APIs (preferred if available)
- Affiliate networks (product feeds)
- Licensed catalogs

## D) Vector Store
Supported examples:
- Postgres + pgvector
- Pinecone / Weaviate / Qdrant

---

# Data Model Updates
Extend existing schema with:

## products (add or replace columns)
- external_id (text, unique)
- source (text)
- image_url (text)
- product_url (text, live retailer link)
- availability (text)
- last_seen_at (timestamp)
- embedding_image (vector or json)
- embedding_text (vector or json)

## product_images (new table)
- id, product_id, image_url, embedding (vector/json)

## scan_items (existing detected_items)
- add item_embedding (vector/json)
- add crop_image_path or crop_image_url

---

# API Updates
## POST /scans
Same input, but processing must:
1. Run vision detection on uploaded image.
2. For each detected item:
   - Crop image from original.
   - Generate embedding.
   - Query vector store for top‑K matches (filtered by category).
   - Add live product URLs in results.

## Optional: POST /catalog/ingest
For manual ingestion or updates. Accepts a feed URL or uploads CSV/JSON.

---

# Matching Logic Updates
Current: deterministic stub ranking.  
Required: real ranking.

## New ranking steps
1. Category filter
2. Vector similarity (cosine or dot)
3. Optional re‑rank using price / brand / popularity
4. Return:
   - Top match
   - Budget alternatives (lower price threshold)

---

# Compliance / Risk
If using retailer data:
- Confirm permitted usage for display and affiliate linking.
- Store and honor licensing terms.
- Respect robots.txt where scraping is used.

For images:
- Ensure user uploads are stored privately.
- Set retention policy (e.g., 30 days).

---

# Configuration (New Env Vars)
Define and document these for the chosen stack:
- VISION_PROVIDER=...
- VISION_API_KEY=...
- EMBEDDING_PROVIDER=...
- EMBEDDING_API_KEY=...
- VECTOR_DB_URL=...
- CATALOG_SOURCE=...
- AFFILIATE_ID=...
- PRODUCT_FEED_URL=...
 - PRODUCT_SEARCH_PROVIDER=serpapi|serper
 - SERPAPI_API_KEY=...
 - SERPER_API_KEY=...

---

# Implementation Steps (Agent Checklist)
1. Choose providers (vision, embeddings, catalog, vector DB) and update docs.
2. Implement catalog ingestion pipeline:
   - Fetch + normalize products
   - Generate embeddings
   - Store in DB + vector store
3. Replace `VisionProvider` and `EmbeddingProvider` with real implementations.
4. Implement vector search and ranking.
5. Update API responses to include live `product_url`.
6. Add basic monitoring/logging for ingestion and scan processing.
7. Update tests:
   - Integration tests for live provider mocks
   - Ensure API still meets contracts

---

# Deliverables
Any agent working on “real functionality” must deliver:
- Updated provider modules
- Ingestion pipeline
- Vector search integration
- Documentation updates
- Working demo with live product links

---

# Important Notes for Agents
- This is **not optional**. The MVP is intentionally stubbed.
- If you do not implement the above, the app will remain a demo.
- Record any chosen provider and its constraints in this file.
