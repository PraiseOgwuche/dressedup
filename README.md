# DressedUp

Digital closet and outfit assistant.

| Layer | Stack |
|-------|--------|
| API | FastAPI, PostgreSQL, Alembic |
| Mobile | Expo (React Native) |
| Media | Local disk (dev) or S3 (production) |

## Features

- Authentication and closet CRUD with wear / laundry tracking
- Photo ingestion: single, batch, flat-lay, video frames, receipt, care label, email
- Outfit engine with fashion rules, personalization, directions, and natural-language ask
- Daily plans, routines, push notification hooks
- Trips, shop catalog, and social feed
- Optional vision (Anthropic) and garment embeddings (FashionCLIP)

Product status: [`PLAN.md`](./PLAN.md)

## Local development

### Backend (Python 3.11+)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL, SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mobile (Expo Go)

```bash
cd mobile
npm install
cp .env.example .env   # EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
npx expo start --clear
```

Use the same Wi‑Fi for phone and Mac. Current IP: `ipconfig getifaddr en0`.

### Optional services

| Capability | Config |
|------------|--------|
| Stub vision (no cost) | `VISION_PROVIDER=stub` |
| Cloud vision | `VISION_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` |
| FashionCLIP embeddings | `python scripts/download_fashionclip.py`, then `EMBEDDING_PROVIDER=fashionclip` and `OUTFIT_EMBEDDINGS_ENABLED=true` |
| Backfill embeddings | `python scripts/backfill_embeddings.py` |

### Tests and benchmarks

```bash
cd backend && pytest
cd mobile && npm test
cd backend && python scripts/run_outfit_benchmark.py
```

Benchmark contract and rollout notes: [`backend/benchmarks/`](./backend/benchmarks/).

## Production (Render + Neon)

1. Create a Neon Postgres database and copy `DATABASE_URL`.
2. Deploy the `backend` service from this repo (Docker / Render Blueprint).
3. Set at least: `DATABASE_URL`, `SECRET_KEY`, `ENV=production`, `DEBUG=False`, `RUN_MIGRATIONS_ON_STARTUP=true`, `ALLOWED_ORIGINS`, `VISION_PROVIDER`.
4. For durable images: S3 bucket + `STORAGE_PROVIDER=s3`, `S3_BUCKET`, AWS credentials, `AWS_REGION` (optional `S3_PUBLIC_BASE_URL`).
5. Point `EXPO_PUBLIC_API_BASE_URL` at the deployed API and rebuild / restart Expo.

`railway.json` is an alternate host using the same environment variables.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Postgres role missing | Use your macOS username in `DATABASE_URL`, run `createdb dressedup` |
| Alembic revision mismatch | `python scripts/repair_alembic_version.py` then `alembic upgrade head` |
| App cannot reach API | Same Wi‑Fi, API bound to `0.0.0.0`, fresh IP in `mobile/.env` |
| Push notifications | Requires an EAS development build; Expo Go supports in-app plan actions only |
