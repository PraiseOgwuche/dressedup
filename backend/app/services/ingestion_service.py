import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from app.config import settings
from app.schemas.ingestion import BatchIngestEntry, IngestResult, MultiIngestEntry, MultiIngestResult, ReceiptIngestResult
from app.services.image_processing import remove_background
from app.services.storage import get_storage_provider
from app.services.vision import get_vision_provider

logger = logging.getLogger(__name__)

# (filename, image_bytes, ext, read_error) — read_error set means skip vision.
BatchPayload = Tuple[Optional[str], Optional[bytes], Optional[str], Optional[str]]


class IngestionService:
    """Orchestrates closet ingestion: store the image(s), run the vision
    provider, and return a confirmable draft. The provider is stubbed until
    the AI bridge, so this whole flow runs with zero token spend."""

    @staticmethod
    def _save_cutout(garment_bytes: bytes, storage, fallback_url: str) -> str:
        """Background-removed transparent PNG for thumbnail_url; falls back to
        the original photo URL whenever the cutout can't be produced."""
        cutout = remove_background(garment_bytes)
        if cutout is None:
            return fallback_url
        return storage.save(cutout, ext="png", subdir="cutouts")

    @staticmethod
    def ingest(
        garment_bytes: bytes,
        garment_ext: str,
        label_bytes: Optional[bytes] = None,
    ) -> IngestResult:
        storage = get_storage_provider()
        image_url = storage.save(garment_bytes, ext=garment_ext, subdir="items")
        thumbnail_url = IngestionService._save_cutout(garment_bytes, storage, image_url)

        draft = get_vision_provider().extract_attributes(
            garment_image=garment_bytes,
            label_image=label_bytes,
        )

        return IngestResult(draft=draft, image_url=image_url, thumbnail_url=thumbnail_url)

    @staticmethod
    def ingest_multi(
        garment_bytes: bytes,
        garment_ext: str,
        label_bytes: Optional[bytes] = None,
    ) -> MultiIngestResult:
        storage = get_storage_provider()
        image_url = storage.save(garment_bytes, ext=garment_ext, subdir="items")
        thumbnail_url = IngestionService._save_cutout(garment_bytes, storage, image_url)

        drafts = get_vision_provider().extract_multi_attributes(
            garment_image=garment_bytes,
            label_image=label_bytes,
        )
        if not drafts:
            drafts = [get_vision_provider().extract_attributes(garment_bytes, label_bytes)]

        entries = [
            MultiIngestEntry(
                index=i,
                draft=draft,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
            )
            for i, draft in enumerate(drafts[: settings.MAX_MULTI_ITEMS_PER_PHOTO])
        ]
        return MultiIngestResult(source_image_url=image_url, entries=entries)

    @staticmethod
    def ingest_many(payloads: List[BatchPayload]) -> List[BatchIngestEntry]:
        """Process a bulk scan: one item per image, run concurrently to cut latency.
        A failure on any single image is captured as an entry error, not raised."""

        def process(payload: BatchPayload) -> BatchIngestEntry:
            filename, data, ext, read_error = payload
            if read_error is not None:
                return BatchIngestEntry(filename=filename, error=read_error)
            try:
                result = IngestionService.ingest(data, ext)
                return BatchIngestEntry(filename=filename, result=result)
            except Exception as exc:  # noqa: BLE001 - surface as per-item error
                logger.exception("Batch ingest failed for %s", filename)
                return BatchIngestEntry(filename=filename, error=str(exc) or "Analysis failed.")

        if not payloads:
            return []

        workers = max(1, min(settings.INGEST_CONCURRENCY, len(payloads)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # executor.map preserves input order, which keeps results aligned to uploads.
            return list(executor.map(process, payloads))

    @staticmethod
    def ingest_receipt(receipt_bytes: bytes, receipt_ext: str) -> ReceiptIngestResult:
        storage = get_storage_provider()
        image_url = storage.save(receipt_bytes, ext=receipt_ext, subdir="receipts")

        extracted = get_vision_provider().extract_from_receipt(receipt_image=receipt_bytes)
        entries = [
            MultiIngestEntry(
                index=i,
                draft=draft,
                image_url=image_url,
                thumbnail_url=image_url,
            )
            for i, draft in enumerate(extracted.items)
        ]
        return ReceiptIngestResult(
            source_image_url=image_url,
            merchant=extracted.merchant,
            purchase_date=extracted.purchase_date,
            entries=entries,
        )

    @staticmethod
    def ingest_label(label_bytes: bytes, label_ext: str) -> IngestResult:
        storage = get_storage_provider()
        image_url = storage.save(label_bytes, ext=label_ext, subdir="labels")

        draft = get_vision_provider().extract_from_care_label(label_image=label_bytes)
        return IngestResult(draft=draft, image_url=image_url, thumbnail_url=image_url)
