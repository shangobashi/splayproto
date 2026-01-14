# Test Strategy

## Goals
- Deterministic tests (no network calls, no nondeterministic ML)
- Coverage gate: **>=80%** on `apps/api` + `packages/matching_core`

## What we test
- MatchingCore:
  - cosine similarity
  - ranking stability
  - budget alternative selection
- API:
  - dev-login
  - create scan (queues job)
  - poll scan (pending→done)
  - free-tier rate limiting

## What we do NOT test in MVP
- Real ML model correctness
- Real payments (Stripe/StoreKit)
- Real scraping (seed only)

## Running
```bash
cd apps/api
pytest --cov=app --cov=matching_core --cov-fail-under=80
```
