from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.clothing_item import ClothingItem
from app.models.social_post import SocialPost
from app.models.social_post_like import SocialPostLike
from app.schemas.closet import ClothingItemResponse
from app.schemas.social import SocialPostCreate, SocialPostLikeResponse, SocialPostResponse
from app.services.storage import get_storage_provider


class SocialService:
    @staticmethod
    def _validate_outfit_items(
        db: Session,
        user_id: int,
        *,
        top_id: Optional[int],
        bottom_id: Optional[int],
        shoes_id: Optional[int],
        outerwear_id: Optional[int],
    ) -> None:
        ids = [i for i in [top_id, bottom_id, shoes_id, outerwear_id] if i is not None]
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one outfit item is required.",
            )
        owned = (
            db.query(ClothingItem.id)
            .filter(ClothingItem.user_id == user_id, ClothingItem.id.in_(ids))
            .count()
        )
        if owned != len(ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more outfit items are invalid.",
            )

    @staticmethod
    def _serialize_post(post: SocialPost, *, liked_by_me: bool = False) -> SocialPostResponse:
        return SocialPostResponse(
            id=post.id,
            user_id=post.user_id,
            user_name=post.user.full_name if post.user else "User",
            caption=post.caption,
            look_name=post.look_name,
            occasion=post.occasion,
            photo_url=post.photo_url,
            top=ClothingItemResponse.model_validate(post.top) if post.top else None,
            bottom=ClothingItemResponse.model_validate(post.bottom) if post.bottom else None,
            shoes=ClothingItemResponse.model_validate(post.shoes) if post.shoes else None,
            outerwear=ClothingItemResponse.model_validate(post.outerwear) if post.outerwear else None,
            reactions_count=post.reactions_count or 0,
            comments_count=post.comments_count or 0,
            liked_by_me=liked_by_me,
            created_at=post.created_at,
        )

    @staticmethod
    def list_posts(db: Session, viewer_id: Optional[int] = None) -> list[SocialPostResponse]:
        posts = (
            db.query(SocialPost)
            .options(
                joinedload(SocialPost.user),
                joinedload(SocialPost.top),
                joinedload(SocialPost.bottom),
                joinedload(SocialPost.shoes),
                joinedload(SocialPost.outerwear),
            )
            .order_by(SocialPost.created_at.desc())
            .all()
        )
        liked_ids: set[int] = set()
        if viewer_id is not None and posts:
            rows = (
                db.query(SocialPostLike.post_id)
                .filter(
                    SocialPostLike.user_id == viewer_id,
                    SocialPostLike.post_id.in_([p.id for p in posts]),
                )
                .all()
            )
            liked_ids = {row[0] for row in rows}
        return [SocialService._serialize_post(p, liked_by_me=p.id in liked_ids) for p in posts]

    @staticmethod
    def create_post(
        db: Session,
        user_id: int,
        payload: SocialPostCreate,
        *,
        photo_bytes: Optional[bytes] = None,
        photo_ext: Optional[str] = None,
    ) -> SocialPostResponse:
        SocialService._validate_outfit_items(
            db,
            user_id,
            top_id=payload.top_id,
            bottom_id=payload.bottom_id,
            shoes_id=payload.shoes_id,
            outerwear_id=payload.outerwear_id,
        )
        photo_url = None
        if photo_bytes:
            storage = get_storage_provider()
            photo_url = storage.save(photo_bytes, ext=photo_ext or "jpg", subdir="feed")

        caption = (payload.caption or "").strip() or None
        post = SocialPost(
            user_id=user_id,
            caption=caption,
            top_id=payload.top_id,
            bottom_id=payload.bottom_id,
            shoes_id=payload.shoes_id,
            outerwear_id=payload.outerwear_id,
            photo_url=photo_url,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        post = (
            db.query(SocialPost)
            .options(
                joinedload(SocialPost.user),
                joinedload(SocialPost.top),
                joinedload(SocialPost.bottom),
                joinedload(SocialPost.shoes),
                joinedload(SocialPost.outerwear),
            )
            .filter(SocialPost.id == post.id)
            .one()
        )
        return SocialService._serialize_post(post)

    @staticmethod
    def toggle_like(db: Session, user_id: int, post_id: int) -> SocialPostLikeResponse:
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

        existing = (
            db.query(SocialPostLike)
            .filter(SocialPostLike.post_id == post_id, SocialPostLike.user_id == user_id)
            .first()
        )
        if existing:
            db.delete(existing)
            post.reactions_count = max((post.reactions_count or 0) - 1, 0)
            liked = False
        else:
            db.add(SocialPostLike(post_id=post_id, user_id=user_id))
            post.reactions_count = (post.reactions_count or 0) + 1
            liked = True

        db.commit()
        db.refresh(post)
        return SocialPostLikeResponse(liked=liked, reactions_count=post.reactions_count or 0)
