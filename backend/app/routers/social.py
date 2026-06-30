import mimetypes
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.social import SocialPostCreate, SocialPostLikeResponse, SocialPostResponse
from app.services.social_service import SocialService
from app.utils.dependencies import get_current_user, get_optional_current_user

router = APIRouter(prefix="/social", tags=["Social"])


async def _read_optional_photo(upload: Optional[UploadFile]) -> tuple[Optional[bytes], Optional[str]]:
    if upload is None:
        return None, None
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


@router.get("/posts", response_model=List[SocialPostResponse])
def list_posts(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    viewer_id = current_user.id if current_user else None
    return SocialService.list_posts(db, viewer_id)


@router.post("/posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    top_id: Optional[int] = Form(None),
    bottom_id: Optional[int] = Form(None),
    shoes_id: Optional[int] = Form(None),
    outerwear_id: Optional[int] = Form(None),
    caption: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = SocialPostCreate(
        caption=caption,
        top_id=top_id,
        bottom_id=bottom_id,
        shoes_id=shoes_id,
        outerwear_id=outerwear_id,
    )
    photo_bytes, photo_ext = await _read_optional_photo(photo)
    return SocialService.create_post(
        db,
        current_user.id,
        payload,
        photo_bytes=photo_bytes,
        photo_ext=photo_ext,
    )


@router.post("/posts/{post_id}/like", response_model=SocialPostLikeResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.toggle_like(db, current_user.id, post_id)
