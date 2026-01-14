# PRD — Splay (MVP)

## Vision
“Shazam for furniture”: users upload/snap a room photo and get a breakdown of key furniture pieces with **exact-ish matches** when possible and **cheaper alternatives** when not. Revenue: affiliate commissions + **$29/month** premium for unlimited scans + advanced features (post-MVP).

## Target users
- Screenshot hoarders (Pinterest/Instagram inspiration folders)
- New homeowners furnishing fast
- Interior enthusiasts recreating vibes from hotels/Airbnbs

## MVP scope (P0)
### Supported item categories (MVP)
- sofa/couch
- coffee_table
- side_table
- dining_table
- chair
- floor_lamp
- table_lamp
- pendant_light

### P0 features
- Upload/capture photo (web + iOS)
- Async scan processing (job queue)
- Detected items returned with bbox + confidence
- Ranked matches per item:
  - 1 top match
  - 2 budget alternatives
- Affiliate link-outs
- Scan history (authed) + share link (public read)
- Free-tier scan limits + premium entitlement flag (stubbed)

## Out of scope (explicit)
- Rugs, art, decor, plants
- AR try-on
- Real payments (Stripe / StoreKit)
- Real scraping in MVP (CSV/seeded catalog only)

## Success metrics (MVP)
- Time-to-first-result: < 15s on local
- Scan-to-click rate (tracked event): baseline measurement
- >= 80% test coverage for backend/shared logic
