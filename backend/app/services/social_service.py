from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.clothing_item import ClothingItem
from app.models.social_post import SocialPost
from app.models.social_post_comment import SocialPostComment
from app.models.social_post_like import SocialPostLike
from app.models.user import User
from app.models.user_follow import UserFollow
from app.schemas.closet import ClothingItemResponse
from app.schemas.social import (
    FeedScope,
    SocialCommentCreate,
    SocialCommentResponse,
    SocialFollowResponse,
    SocialPostCreate,
    SocialPostLikeResponse,
    SocialPostResponse,
    SocialUserSummary,
)
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
    def _following_ids(db: Session, viewer_id: int) -> set[int]:
        rows = db.query(UserFollow.following_id).filter(UserFollow.follower_id == viewer_id).all()
        return {row[0] for row in rows}

    @staticmethod
    def _serialize_post(
        post: SocialPost,
        *,
        liked_by_me: bool = False,
        viewer_id: Optional[int] = None,
        following_author: bool = False,
    ) -> SocialPostResponse:
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
            is_mine=viewer_id is not None and post.user_id == viewer_id,
            following_author=following_author,
            created_at=post.created_at,
        )

    @staticmethod
    def _post_query(db: Session):
        return db.query(SocialPost).options(
            joinedload(SocialPost.user),
            joinedload(SocialPost.top),
            joinedload(SocialPost.bottom),
            joinedload(SocialPost.shoes),
            joinedload(SocialPost.outerwear),
        )

    @staticmethod
    def _liked_post_ids(db: Session, viewer_id: int, post_ids: list[int]) -> set[int]:
        if not post_ids:
            return set()
        rows = (
            db.query(SocialPostLike.post_id)
            .filter(SocialPostLike.user_id == viewer_id, SocialPostLike.post_id.in_(post_ids))
            .all()
        )
        return {row[0] for row in rows}

    @staticmethod
    def list_posts(
        db: Session,
        viewer_id: Optional[int] = None,
        *,
        scope: FeedScope = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> list[SocialPostResponse]:
        limit = max(1, min(limit, 50))
        offset = max(0, offset)

        query = SocialService._post_query(db)

        if scope == "mine":
            if viewer_id is None:
                return []
            query = query.filter(SocialPost.user_id == viewer_id)
        elif scope == "following":
            if viewer_id is None:
                return []
            following = SocialService._following_ids(db, viewer_id)
            allowed = following | {viewer_id}
            query = query.filter(SocialPost.user_id.in_(allowed))

        posts = query.order_by(SocialPost.created_at.desc()).offset(offset).limit(limit).all()

        liked_ids: set[int] = set()
        following_ids: set[int] = set()
        if viewer_id is not None and posts:
            liked_ids = SocialService._liked_post_ids(db, viewer_id, [p.id for p in posts])
            following_ids = SocialService._following_ids(db, viewer_id)

        return [
            SocialService._serialize_post(
                p,
                liked_by_me=p.id in liked_ids,
                viewer_id=viewer_id,
                following_author=p.user_id in following_ids,
            )
            for p in posts
        ]

    @staticmethod
    def get_post(db: Session, post_id: int, viewer_id: Optional[int] = None) -> SocialPostResponse:
        post = SocialService._post_query(db).filter(SocialPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

        liked = False
        following_author = False
        if viewer_id is not None:
            liked = (
                db.query(SocialPostLike)
                .filter(SocialPostLike.post_id == post_id, SocialPostLike.user_id == viewer_id)
                .first()
                is not None
            )
            following_author = (
                db.query(UserFollow)
                .filter(UserFollow.follower_id == viewer_id, UserFollow.following_id == post.user_id)
                .first()
                is not None
            )

        return SocialService._serialize_post(
            post,
            liked_by_me=liked,
            viewer_id=viewer_id,
            following_author=following_author,
        )

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
        look_name = (payload.look_name or "").strip() or None
        occasion = (payload.occasion or "").strip() or None

        post = SocialPost(
            user_id=user_id,
            caption=caption,
            look_name=look_name,
            occasion=occasion,
            top_id=payload.top_id,
            bottom_id=payload.bottom_id,
            shoes_id=payload.shoes_id,
            outerwear_id=payload.outerwear_id,
            photo_url=photo_url,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        post = SocialService._post_query(db).filter(SocialPost.id == post.id).one()
        return SocialService._serialize_post(post, viewer_id=user_id)

    @staticmethod
    def delete_post(db: Session, user_id: int, post_id: int) -> None:
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post.")
        db.delete(post)
        db.commit()

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

    @staticmethod
    def list_comments(
        db: Session,
        post_id: int,
        viewer_id: Optional[int] = None,
    ) -> list[SocialCommentResponse]:
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

        comments = (
            db.query(SocialPostComment)
            .options(joinedload(SocialPostComment.user))
            .filter(SocialPostComment.post_id == post_id)
            .order_by(SocialPostComment.created_at.asc())
            .all()
        )
        return [
            SocialCommentResponse(
                id=c.id,
                post_id=c.post_id,
                user_id=c.user_id,
                user_name=c.user.full_name if c.user else "User",
                body=c.body,
                is_mine=viewer_id is not None and c.user_id == viewer_id,
                created_at=c.created_at,
            )
            for c in comments
        ]

    @staticmethod
    def add_comment(
        db: Session,
        user_id: int,
        post_id: int,
        payload: SocialCommentCreate,
    ) -> SocialCommentResponse:
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

        body = payload.body.strip()
        comment = SocialPostComment(post_id=post_id, user_id=user_id, body=body)
        db.add(comment)
        post.comments_count = (post.comments_count or 0) + 1
        db.commit()
        db.refresh(comment)
        comment = (
            db.query(SocialPostComment)
            .options(joinedload(SocialPostComment.user))
            .filter(SocialPostComment.id == comment.id)
            .one()
        )
        return SocialCommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            user_name=comment.user.full_name if comment.user else "User",
            body=comment.body,
            is_mine=True,
            created_at=comment.created_at,
        )

    @staticmethod
    def delete_comment(db: Session, user_id: int, comment_id: int) -> None:
        comment = db.query(SocialPostComment).filter(SocialPostComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment.")

        post = db.query(SocialPost).filter(SocialPost.id == comment.post_id).first()
        if post:
            post.comments_count = max((post.comments_count or 0) - 1, 0)

        db.delete(comment)
        db.commit()

    @staticmethod
    def list_people(db: Session, viewer_id: int) -> list[SocialUserSummary]:
        following_ids = SocialService._following_ids(db, viewer_id)

        post_counts = dict(
            db.query(SocialPost.user_id, func.count(SocialPost.id))
            .group_by(SocialPost.user_id)
            .all()
        )
        follower_counts = dict(
            db.query(UserFollow.following_id, func.count(UserFollow.id))
            .group_by(UserFollow.following_id)
            .all()
        )

        users = db.query(User).filter(User.is_active.is_(True)).order_by(User.full_name.asc()).all()
        summaries: list[SocialUserSummary] = []
        for user in users:
            summaries.append(
                SocialUserSummary(
                    id=user.id,
                    full_name=user.full_name,
                    post_count=post_counts.get(user.id, 0),
                    follower_count=follower_counts.get(user.id, 0),
                    is_following=user.id in following_ids,
                    is_self=user.id == viewer_id,
                )
            )
        return summaries

    @staticmethod
    def toggle_follow(db: Session, viewer_id: int, target_user_id: int) -> SocialFollowResponse:
        if viewer_id == target_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself.")

        target = db.query(User).filter(User.id == target_user_id, User.is_active.is_(True)).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        existing = (
            db.query(UserFollow)
            .filter(UserFollow.follower_id == viewer_id, UserFollow.following_id == target_user_id)
            .first()
        )
        if existing:
            db.delete(existing)
            following = False
        else:
            db.add(UserFollow(follower_id=viewer_id, following_id=target_user_id))
            following = True

        db.commit()
        follower_count = (
            db.query(func.count(UserFollow.id))
            .filter(UserFollow.following_id == target_user_id)
            .scalar()
            or 0
        )
        return SocialFollowResponse(following=following, follower_count=follower_count)
