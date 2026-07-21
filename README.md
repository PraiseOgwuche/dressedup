# DressedUp

Digital closet + outfit assistant. **FastAPI / PostgreSQL** backend, **Expo** mobile app.

## What's built

- Auth, rich closet CRUD, AI ingestion (single / batch / flat-lay / receipt / care-label / **email** scan)
- Outfit engine v3: fashion knowledge (`backend/app/fashion/knowledge.yaml`) + learns from likes/wears
- Trend vibes (quiet-luxury, streetwear, …) and occasion color palettes in outfit scoring
- Ask DressedUp (natural language outfit requests) and trip packing lists with live weather forecasts
- Plan my day, saved routines, wear & laundry tracking
- Morning push infra (needs dev build; works in-app via “Send me my plan” in Expo Go)
- Social, shop, trips (stubs / premium hooks)

Roadmap: [`PLAN.md`](./PLAN.md)

## Local dev

**Backend** — Python 3.11 or 3.12:

```bash
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # DATABASE_URL, SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Mobile** — Expo Go:

```bash
cd mobile && npm install
cp .env.example .env          # EXPO_PUBLIC_API_BASE_URL=http://<your-mac-ip>:8000
npx expo start --clear
```

Phone and Mac on the same Wi‑Fi. IP: `ipconfig getifaddr en0`.

**AI scans** — free with `VISION_PROVIDER=stub` in `backend/.env`. Real Claude vision: set `VISION_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` (~$0.002/scan).

**Garment embeddings (Outfit Engine v4)** — free local FashionCLIP: `python scripts/download_fashionclip.py` (~336 MB, once), then set `EMBEDDING_PROVIDER=fashionclip` + `OUTFIT_EMBEDDINGS_ENABLED=true`. Defaults to a free stub otherwise.

**Tests:** `cd backend && pytest` · `cd mobile && npm test`

**Outfit benchmark:** `cd backend && python scripts/run_outfit_benchmark.py`.
The frozen v3 baseline and evaluation contract live in
[`backend/benchmarks/`](./backend/benchmarks/).

## Deploy (Render + Neon)

1. Push this repo to GitHub.
2. [Neon](https://neon.tech) → new project → copy Postgres connection string.
3. [Render](https://render.com) → Blueprint or Web Service → repo root `backend`, Docker, free tier.
4. Env vars: `DATABASE_URL`, `SECRET_KEY` (`openssl rand -hex 32`), `ENV=production`, `DEBUG=False`, `RUN_MIGRATIONS_ON_STARTUP=true`, `ALLOWED_ORIGINS=*`, `VISION_PROVIDER=stub`.
5. **Media (production):** create an S3 bucket, allow public `GetObject` on `items/*` (bucket policy), IAM user with `s3:PutObject`, then set `STORAGE_PROVIDER=s3`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`. Optional `S3_PUBLIC_BASE_URL` for CloudFront.
6. `curl https://<your-app>.onrender.com/health`
7. `mobile/.env` → `EXPO_PUBLIC_API_BASE_URL=https://<your-app>.onrender.com` → `npx expo start --clear`

Without S3, closet **images** on Render disk are ephemeral (lost on redeploy). Local dev uses `STORAGE_PROVIDER=local` (default).

`railway.json` is an alternative host with the same env vars.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Postgres `role "postgres" does not exist` | Use your macOS user in `DATABASE_URL`, `createdb dressedup` |
| Alembic revision error | `python scripts/repair_alembic_version.py` then `alembic upgrade head` |
| Expo can't reach API | Same Wi‑Fi, `--host 0.0.0.0`, correct IP in `mobile/.env` |
| Push notifications | Need EAS dev build (`eas-cli`); Expo Go uses in-app plan only |
