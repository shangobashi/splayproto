# API Contracts (MVP)

Base URL (dev): `http://localhost:8000`

## Auth (dev only)
### POST `/auth/dev-login`
Request JSON:
```json
{ "email": "you@example.com" }
```
Response:
```json
{ "token": "<jwt>", "user": { "id": "...", "email": "...", "is_premium": false } }
```

Use header:
`Authorization: Bearer <jwt>`

## Scans
### POST `/scans`
Multipart form:
- `image` (file)

Response:
```json
{ "scan_id": "uuid" }
```

### GET `/scans/{scan_id}`
Response (pending/processing):
```json
{ "id":"...", "status":"processing", "created_at":"...", "items":[] }
```

Response (done):
```json
{
  "id":"...",
  "status":"done",
  "created_at":"...",
  "items":[
    {
      "id":"...",
      "category":"sofa",
      "bbox":{"x":0.12,"y":0.22,"w":0.51,"h":0.36},
      "confidence":0.87,
      "matches":[
        {"rank":1,"is_budget":false,"product":{...}},
        {"rank":2,"is_budget":true,"product":{...}},
        {"rank":3,"is_budget":true,"product":{...}}
      ]
    }
  ]
}
```

## Errors
- 401 invalid/missing token (where required)
- 429 free-tier scan limit exceeded
- 415 unsupported image type
