import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import SessionLocal
from app.routers import auth, closet, notifications, outfit, social, shop, trips
from app.utils.exceptions import register_exception_handlers
from app.utils.migrations import run_migrations
from app.utils.responses import success_response

logger = logging.getLogger(__name__)


async def _notification_scheduler(stop_event: asyncio.Event) -> None:
    from app.services.notification_service import NotificationService

    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                sent = NotificationService.process_morning_notifications(db)
                if sent:
                    logger.info("morning push sent to %s user(s)", sent)
            finally:
                db.close()
        except Exception:
            logger.exception("morning notification tick failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    if settings.RUN_MIGRATIONS_ON_STARTUP:
        run_migrations()

    stop_event = asyncio.Event()
    scheduler_task = None
    if settings.NOTIFICATION_SCHEDULER_ENABLED:
        scheduler_task = asyncio.create_task(_notification_scheduler(stop_event))

    yield

    if scheduler_task:
        stop_event.set()
        await scheduler_task

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(closet.router, prefix=settings.API_V1_PREFIX)
app.include_router(outfit.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(social.router, prefix=settings.API_V1_PREFIX)
app.include_router(shop.router, prefix=settings.API_V1_PREFIX)
app.include_router(trips.router, prefix=settings.API_V1_PREFIX)

# Serve locally stored media (uploaded closet images) when using local storage.
if settings.STORAGE_PROVIDER == "local":
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_DIR), name="media")

register_exception_handlers(app)

@app.get("/")
def root():
    return success_response(
        data={"service": settings.APP_NAME, "env": settings.ENV},
        message="API is running",
    )

@app.get("/health")
def health_check():
    return success_response(data={"status": "healthy"})
