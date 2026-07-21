# DressedUp — product status

Digital closet with low-effort capture, outfit suggestions, laundry tracking, and daily planning.

## Design principles

- Vision and stylist providers are swappable (`stub` by default; cloud optional)
- Taxonomy and fashion rules live in code / YAML (`app/taxonomy.py`, `app/fashion/`)
- Users confirm AI drafts; low-confidence fields are highlighted
- Outfit suggestions never invent closet items that are not in the database

## Shipped

| Area | Status |
|------|--------|
| Auth, closet CRUD, confirm flows | Done |
| Ingestion: photo, batch, flat-lay, receipt, label, email | Done |
| Video frame scan (on-device thumbnails → batch ingest) | Done |
| Wear & laundry | Done |
| Outfit engine (rules, personalization, directions, ask) | Done |
| FashionCLIP embeddings + hybrid retrieval (feature-flagged) | Done |
| Daily plan, routines, push hooks | Done |
| Trips + weather-aware packing | Done |
| Shop catalog scoring | Done |
| Social feed | Done |
| Deploy path (Render/Neon/S3) | Done |
| 3D home mannequin (local mesh + color shells) | Done |

## In progress / next

| Area | Notes |
|------|--------|
| App Store / TestFlight | Waiting on Apple Developer Program enrollment |
| Personalized 3D avatars | Provider TBD (Ready Player Me discontinued; Avatar SDK trial deferred until after ship) |
| Production embedding rollout | See `backend/benchmarks/ROLLOUT.md` (coverage + blind review gates) |

## Parked

- Full garment draping / try-on on the 3D body
- On-device segmentation
- Trained recommender beyond current personalization
