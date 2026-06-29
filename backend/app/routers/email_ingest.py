import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.email_ingest import EmailIngestLogResponse, EmailIngestResult, EmailIngestSettings
from app.services.email_ingest_service import EmailIngestService
from app.utils.dependencies import get_current_user
from app.utils.mailgun import parse_mailgun_form, verify_mailgun_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/closet/email-ingest", tags=["Email ingest"])


@router.get("", response_model=EmailIngestSettings)
def get_email_ingest_settings(
    current_user: User = Depends(get_current_user),
):
    return EmailIngestService.get_settings(current_user)


@router.get("/logs", response_model=list[EmailIngestLogResponse])
def list_email_ingest_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EmailIngestService.list_recent_logs(db, current_user.id)


@router.post("/webhook", response_model=EmailIngestResult)
async def mailgun_inbound_webhook(request: Request, db: Session = Depends(get_db)):
    """Mailgun inbound route: forward emails to u-{token}@your-ingest-domain."""
    if not settings.EMAIL_INGEST_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email ingest disabled.")

    form = await request.form()
    timestamp = str(form.get("timestamp") or "")
    token = str(form.get("token") or "")
    signature = str(form.get("signature") or "")

    if settings.MAILGUN_WEBHOOK_SIGNING_KEY:
        if not verify_mailgun_signature(
            settings.MAILGUN_WEBHOOK_SIGNING_KEY,
            timestamp,
            token,
            signature,
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Mailgun signature.")
    elif settings.ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mailgun signing key is not configured.",
        )
    else:
        logger.warning("Accepting Mailgun webhook without signature verification (non-production).")

    email = parse_mailgun_form(form)
    user = EmailIngestService.resolve_user(db, email.recipient)
    return EmailIngestService.process_inbound_email(db, user, email)


@router.post("/simulate", response_model=EmailIngestResult)
async def simulate_email_ingest(
    attachment: UploadFile = File(...),
    subject: str = Form("Simulated receipt email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authenticated dev helper: process an image as if it arrived by email."""
    if settings.ENV == "production" and not settings.EMAIL_INGEST_ALLOW_SIMULATE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    if not (attachment.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload must be an image.")

    data = await attachment.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.MAX_UPLOAD_MB} MB.",
        )
    ext = (attachment.filename or "receipt.jpg").rsplit(".", 1)[-1].lower()
    return EmailIngestService.simulate_attachment(db, current_user, data, ext, subject=subject)
