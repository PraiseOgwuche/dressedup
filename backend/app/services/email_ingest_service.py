import logging
import mimetypes
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.email_ingest_log import EmailIngestLog
from app.models.user import User
from app.schemas.closet import ClothingItemCreate
from app.schemas.email_ingest import EmailIngestResult, EmailIngestSettings
from app.schemas.ingestion import DraftItem
from app.services.closet_service import ClosetService
from app.services.ingestion_service import IngestionService
from app.utils.mailgun import InboundEmail, MailgunAttachment, extract_ingest_token

logger = logging.getLogger(__name__)

_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif"}


class EmailIngestService:
    @staticmethod
    def build_address(user: User) -> Optional[str]:
        if not settings.EMAIL_INGEST_DOMAIN:
            return None
        return f"u-{user.ingest_token}@{settings.EMAIL_INGEST_DOMAIN}"

    @staticmethod
    def get_settings(user: User) -> EmailIngestSettings:
        address = EmailIngestService.build_address(user)
        enabled = bool(settings.EMAIL_INGEST_ENABLED and address)
        if enabled:
            instructions = (
                "Forward order confirmations or receipt emails to your address below. "
                "We'll pull apparel line items into your closet for review."
            )
        elif not settings.EMAIL_INGEST_DOMAIN:
            instructions = "Email import is not configured on this server yet."
        else:
            instructions = "Email import is temporarily disabled on this server."
        return EmailIngestSettings(enabled=enabled, address=address, instructions=instructions)

    @staticmethod
    def list_recent_logs(db: Session, user_id: int, limit: int = 10) -> list[EmailIngestLog]:
        return (
            db.query(EmailIngestLog)
            .filter(EmailIngestLog.user_id == user_id)
            .order_by(EmailIngestLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def resolve_user(db: Session, recipient_field: str) -> User:
        token = extract_ingest_token(recipient_field)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ingest address found in recipient.",
            )
        user = db.query(User).filter(User.ingest_token == token).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown ingest address.")
        return user

    @staticmethod
    def process_inbound_email(db: Session, user: User, email: InboundEmail) -> EmailIngestResult:
        if not settings.EMAIL_INGEST_ENABLED:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email ingest disabled.")

        items_created = 0
        attachments_processed = 0
        errors: list[str] = []
        email_meta = {
            "email_sender": email.sender,
            "email_subject": email.subject,
        }

        for attachment in email.attachments:
            if not EmailIngestService._is_image(attachment.content_type, attachment.filename):
                continue
            attachments_processed += 1
            ext = EmailIngestService._extension_for(attachment.content_type, attachment.filename)
            try:
                items_created += EmailIngestService._ingest_attachment(
                    db,
                    user.id,
                    attachment.data,
                    ext,
                    email_meta,
                )
            except Exception as exc:  # noqa: BLE001 - log per attachment, keep processing
                logger.exception("Email attachment ingest failed for user %s", user.id)
                errors.append(f"{attachment.filename}: {exc}")

        log = EmailIngestLog(
            user_id=user.id,
            sender=email.sender,
            subject=email.subject,
            items_created=items_created,
            attachments_processed=attachments_processed,
            errors=errors or None,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return EmailIngestResult(
            items_created=items_created,
            attachments_processed=attachments_processed,
            errors=errors,
            log_id=log.id,
        )

    @staticmethod
    def simulate_attachment(
        db: Session,
        user: User,
        image_bytes: bytes,
        ext: str,
        subject: str = "Simulated receipt email",
    ) -> EmailIngestResult:
        email = InboundEmail(
            recipient=EmailIngestService.build_address(user) or "",
            sender=user.email,
            subject=subject,
            attachments=[
                MailgunAttachment(
                    filename=f"receipt.{ext}",
                    content_type=mimetypes.guess_type(f"x.{ext}")[0] or "image/jpeg",
                    data=image_bytes,
                )
            ],
        )
        return EmailIngestService.process_inbound_email(db, user, email)

    @staticmethod
    def _ingest_attachment(
        db: Session,
        user_id: int,
        image_bytes: bytes,
        ext: str,
        email_meta: dict,
    ) -> int:
        created = 0

        receipt = IngestionService.ingest_receipt(image_bytes, ext)
        if receipt.entries:
            merchant_meta = {**email_meta}
            if receipt.merchant:
                merchant_meta["merchant"] = receipt.merchant
            if receipt.purchase_date:
                merchant_meta["purchase_date"] = receipt.purchase_date
            for entry in receipt.entries:
                ClosetService.create_item(
                    db,
                    user_id,
                    EmailIngestService._draft_to_create(
                        entry.draft,
                        entry.image_url,
                        entry.thumbnail_url,
                        merchant_meta,
                    ),
                )
                created += 1
            return created

        garment = IngestionService.ingest(image_bytes, ext)
        ClosetService.create_item(
            db,
            user_id,
            EmailIngestService._draft_to_create(
                garment.draft,
                garment.image_url,
                garment.thumbnail_url,
                email_meta,
            ),
        )
        return 1

    @staticmethod
    def _draft_to_create(
        draft: DraftItem,
        image_url: str,
        thumbnail_url: str,
        email_meta: dict,
    ) -> ClothingItemCreate:
        ai_metadata = dict(email_meta)
        if draft.sku:
            ai_metadata["sku"] = draft.sku
        if draft.price is not None:
            ai_metadata["price"] = draft.price
        if draft.purchase_date:
            ai_metadata["purchase_date"] = draft.purchase_date

        return ClothingItemCreate(
            name=draft.name,
            category=draft.category,
            subcategory=draft.subcategory,
            brand=draft.brand,
            product_name=draft.product_name,
            size=draft.size,
            color=draft.color,
            color_hex=draft.color_hex,
            pattern=draft.pattern,
            material=draft.material,
            occasion=draft.occasion or None,
            formality=draft.formality,
            weather_tag=draft.weather_tag or None,
            seasons=draft.seasons or None,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            source="email",
            confidence=draft.confidence or None,
            needs_review=True,
            ai_metadata=ai_metadata or None,
        )

    @staticmethod
    def _is_image(content_type: str, filename: str) -> bool:
        normalized = (content_type or "").split(";")[0].strip().lower()
        if normalized in _IMAGE_TYPES or normalized.startswith("image/"):
            return True
        guessed, _ = mimetypes.guess_type(filename)
        return bool(guessed and guessed.startswith("image/"))

    @staticmethod
    def _extension_for(content_type: str, filename: str) -> str:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            ext = mimetypes.guess_extension(guessed) or ".jpg"
            return ext.lstrip(".")
        if "png" in content_type:
            return "png"
        if "webp" in content_type:
            return "webp"
        return "jpg"
