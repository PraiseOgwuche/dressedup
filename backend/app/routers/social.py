import mimetypes
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.social import (
    FeedScope,
    FeedActivityResponse,
    FeedActivitySeenResponse,
    SocialCommentCreate,
    SocialCommentResponse,
    SocialFollowResponse,
    SocialPostCreate,
    SocialPostLikeResponse,
    SocialPostResponse,
    SocialUserSummary,
    StreakResponse,
)
from app.services.feed_activity_service import FeedActivityService
from app.services.social_service import SocialService
from app.services.streak_service import StreakService
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
    scope: FeedScope = "all",
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    viewer_id = current_user.id if current_user else None
    return SocialService.list_posts(db, viewer_id, scope=scope, limit=limit, offset=offset)


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    viewer_id = current_user.id if current_user else None
    return SocialService.get_post(db, post_id, viewer_id)


@router.post("/posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    top_id: Optional[int] = Form(None),
    bottom_id: Optional[int] = Form(None),
    shoes_id: Optional[int] = Form(None),
    outerwear_id: Optional[int] = Form(None),
    caption: Optional[str] = Form(None),
    look_name: Optional[str] = Form(None),
    occasion: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = SocialPostCreate(
        caption=caption,
        look_name=look_name,
        occasion=occasion,
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


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    SocialService.delete_post(db, current_user.id, post_id)


@router.post("/posts/{post_id}/like", response_model=SocialPostLikeResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.toggle_like(db, current_user.id, post_id)


@router.get("/posts/{post_id}/comments", response_model=List[SocialCommentResponse])
def list_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    viewer_id = current_user.id if current_user else None
    return SocialService.list_comments(db, post_id, viewer_id)


@router.post("/posts/{post_id}/comments", response_model=SocialCommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    payload: SocialCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.add_comment(db, current_user.id, post_id, payload)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    SocialService.delete_comment(db, current_user.id, comment_id)


@router.get("/people", response_model=List[SocialUserSummary])
def list_people(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.list_people(db, current_user.id)


@router.post("/users/{user_id}/follow", response_model=SocialFollowResponse)
def toggle_follow(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.toggle_follow(db, current_user.id, user_id)


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    timezone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StreakService.get_streak(db, current_user.id, timezone=timezone)


@router.get("/activity", response_model=FeedActivityResponse)
def get_feed_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """In-app activity feed: likes, comments, follows, new posts, streak nudges."""
    return FeedActivityService.get_activity(db, current_user.id)


@router.post("/activity/seen", response_model=FeedActivitySeenResponse)
def mark_feed_activity_seen(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FeedActivityService.mark_seen(db, current_user.id)
