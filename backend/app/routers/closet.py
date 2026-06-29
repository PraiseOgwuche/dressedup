import mimetypes
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.closet import (
    ClothingItemCreate,
    ClothingItemResponse,
    ClothingItemUpdate,
    LaundrySummary,
    WashAllRequest,
)
from app.schemas.ingestion import BatchIngestResult, IngestResult, MultiIngestResult
from app.services.closet_service import ClosetService
from app.services.ingestion_service import IngestionService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/closet", tags=["Closet"])


async def _read_image(upload: UploadFile) -> tuple[bytes, str]:
    if not (upload.content_type or "").startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload must be an image.",
        )
    data = await upload.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.MAX_UPLOAD_MB} MB.",
        )
    ext = (mimetypes.guess_extension(upload.content_type) or ".jpg").lstrip(".")
    return data, ext


@router.get("/items", response_model=List[ClothingItemResponse])
def list_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.list_items(db, current_user.id)


@router.post("/items", response_model=ClothingItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ClothingItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.create_item(db, current_user.id, payload)


@router.post("/ingest", response_model=IngestResult)
async def ingest_item(
    garment: UploadFile = File(...),
    label: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
):
    """Store the image(s), run AI extraction, and return a confirmable draft.
    The client edits/confirms, then saves the result via POST /closet/items."""
    garment_bytes, garment_ext = await _read_image(garment)
    label_bytes = (await _read_image(label))[0] if label is not None else None
    return IngestionService.ingest(garment_bytes, garment_ext, label_bytes)


@router.post("/ingest/batch", response_model=BatchIngestResult)
async def ingest_batch(
    garments: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """Bulk scan: one item per image. Each image becomes a confirmable draft; a bad
    image yields a per-item error instead of failing the batch."""
    if len(garments) > settings.MAX_BATCH_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Up to {settings.MAX_BATCH_ITEMS} items per batch.",
        )

    payloads = []
    for upload in garments:
        try:
            data, ext = await _read_image(upload)
            payloads.append((upload.filename, data, ext, None))
        except HTTPException as exc:
            payloads.append((upload.filename, None, None, str(exc.detail)))

    return BatchIngestResult(entries=IngestionService.ingest_many(payloads))


@router.post("/ingest/multi", response_model=MultiIngestResult)
async def ingest_multi_item_photo(
    garment: UploadFile = File(...),
    label: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
):
    """Flat-lay scan: one photo with several garments → multiple confirmable drafts."""
    garment_bytes, garment_ext = await _read_image(garment)
    label_bytes = (await _read_image(label))[0] if label is not None else None
    return IngestionService.ingest_multi(garment_bytes, garment_ext, label_bytes)


@router.put("/items/{item_id}", response_model=ClothingItemResponse)
def update_item(
    item_id: int,
    payload: ClothingItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.update_item(db, current_user.id, item_id, payload)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ClosetService.delete_item(db, current_user.id, item_id)


@router.get("/laundry/summary", response_model=LaundrySummary)
def laundry_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.laundry_summary(db, current_user.id)


@router.post("/laundry/wash-all", response_model=LaundrySummary)
def wash_all(
    payload: WashAllRequest = WashAllRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ClosetService.do_laundry(db, current_user.id, payload.item_ids)
    return ClosetService.laundry_summary(db, current_user.id)


@router.post("/items/{item_id}/wear", response_model=ClothingItemResponse)
def wear_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.mark_worn(db, current_user.id, item_id)


@router.post("/items/{item_id}/wash", response_model=ClothingItemResponse)
def wash_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.mark_washed(db, current_user.id, item_id)


@router.post("/items/{item_id}/soil", response_model=ClothingItemResponse)
def soil_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ClosetService.mark_dirty(db, current_user.id, item_id)

