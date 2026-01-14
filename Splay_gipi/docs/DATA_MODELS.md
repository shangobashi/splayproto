# Data Models (MVP)

## Tables
### users
- id (uuid)
- email (text, unique)
- is_premium (bool)
- created_at (timestamp)

### scans
- id (uuid)
- user_id (uuid nullable)
- image_path (text)
- status (text: pending|processing|done|failed)
- created_at (timestamp)

### detected_items
- id (uuid)
- scan_id (uuid)
- category (text)
- bbox_x, bbox_y, bbox_w, bbox_h (real; normalized 0..1)
- confidence (real 0..1)

### matches
- id (uuid)
- detected_item_id (uuid)
- product_id (uuid)
- rank (int)
- is_budget (bool)

### products
- id (uuid)
- name (text)
- brand (text)
- category (text)
- price (real)
- affiliate_url (text)
- product_url (text)
- image_url (text)
- external_id (text)
- source (text)
- availability (text)
- last_seen_at (timestamp)
- embedding_json (text)  # JSON list[float]
