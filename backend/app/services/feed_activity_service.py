"""In-app feed activity — likes, comments, follows, new posts, streak nudges."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.social_post import SocialPost
from app.models.social_post_comment import SocialPostComment
from app.models.social_post_like import SocialPostLike
from app.models.user import User
from app.models.user_feed_state import UserFeedState
from app.models.user_follow import UserFollow
from app.services.social_service import SocialService
from app.services.streak_service import StreakService

_ACTIVITY_LOOKBACK_DAYS = 14
_MAX_ITEMS = 30


@dataclass
class _ActivityEvent:
    key: str
    type: str
    actor_user_id: Optional[int]
    actor_name: str
    message: str
    post_id: Optional[int]
    created_at: datetime


def _post_label(post: SocialPost) -> str:
    if post.look_name:
        return post.look_name
    if post.caption:
        return post.caption[:60]
    return "your fit"


def _is_unread(created_at: datetime, last_seen_at: Optional[datetime]) -> bool:
    if last_seen_at is None:
        return True
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    seen = last_seen_at if last_seen_at.tzinfo else last_seen_at.replace(tzinfo=UTC)
    return created_at > seen


class FeedActivityService:
    @staticmethod
    def _cutoff() -> datetime:
        return datetime.now(UTC) - timedelta(days=_ACTIVITY_LOOKBACK_DAYS)

    @staticmethod
    def _last_seen(db: Session, user_id: int) -> Optional[datetime]:
        row = db.query(UserFeedState).filter(UserFeedState.user_id == user_id).first()
        return row.last_seen_at if row else None

    @staticmethod
    def _collect_events(db: Session, user_id: int) -> list[_ActivityEvent]:
        cutoff = FeedActivityService._cutoff()
        events: list[_ActivityEvent] = []

        likes = (
            db.query(SocialPostLike)
            .join(SocialPost, SocialPost.id == SocialPostLike.post_id)
            .options(joinedload(SocialPostLike.user), joinedload(SocialPostLike.post))
            .filter(
                SocialPost.user_id == user_id,
                SocialPostLike.user_id != user_id,
                SocialPostLike.created_at >= cutoff,
            )
            .order_by(SocialPostLike.created_at.desc())
            .limit(_MAX_ITEMS)
            .all()
        )
        for like in likes:
            actor = like.user.full_name if like.user else "Someone"
            label = _post_label(like.post) if like.post else "your fit"
            events.append(
                _ActivityEvent(
                    key=f"like:{like.id}",
                    type="like",
                    actor_user_id=like.user_id,
                    actor_name=actor,
                    message=f"liked {label}",
                    post_id=like.post_id,
                    created_at=like.created_at,
                )
            )

        comments = (
            db.query(SocialPostComment)
            .join(SocialPost, SocialPost.id == SocialPostComment.post_id)
            .options(joinedload(SocialPostComment.user), joinedload(SocialPostComment.post))
            .filter(
                SocialPost.user_id == user_id,
                SocialPostComment.user_id != user_id,
                SocialPostComment.created_at >= cutoff,
            )
            .order_by(SocialPostComment.created_at.desc())
            .limit(_MAX_ITEMS)
            .all()
        )
        for comment in comments:
            actor = comment.user.full_name if comment.user else "Someone"
            preview = comment.body.strip()
            if len(preview) > 80:
                preview = preview[:77] + "..."
            events.append(
                _ActivityEvent(
                    key=f"comment:{comment.id}",
                    type="comment",
                    actor_user_id=comment.user_id,
                    actor_name=actor,
                    message=f'commented: "{preview}"',
                    post_id=comment.post_id,
                    created_at=comment.created_at,
                )
            )

        follows = (
            db.query(UserFollow)
            .options(joinedload(UserFollow.follower))
            .filter(
                UserFollow.following_id == user_id,
                UserFollow.created_at >= cutoff,
            )
            .order_by(UserFollow.created_at.desc())
            .limit(_MAX_ITEMS)
            .all()
        )
        for follow in follows:
            actor = follow.follower.full_name if follow.follower else "Someone"
            events.append(
                _ActivityEvent(
                    key=f"follow:{follow.id}",
                    type="follow",
                    actor_user_id=follow.follower_id,
                    actor_name=actor,
                    message="started following you",
                    post_id=None,
                    created_at=follow.created_at,
                )
            )

        following_ids = SocialService._following_ids(db, user_id)
        if following_ids:
            new_posts = (
                db.query(SocialPost)
                .options(joinedload(SocialPost.user))
                .filter(
                    SocialPost.user_id.in_(following_ids),
                    SocialPost.user_id != user_id,
                    SocialPost.created_at >= cutoff,
                )
                .order_by(SocialPost.created_at.desc())
                .limit(_MAX_ITEMS)
                .all()
            )
            for post in new_posts:
                actor = post.user.full_name if post.user else "Someone"
                label = _post_label(post)
                events.append(
                    _ActivityEvent(
                        key=f"post:{post.id}",
                        type="new_post",
                        actor_user_id=post.user_id,
                        actor_name=actor,
                        message=f"shared {label}",
                        post_id=post.id,
                        created_at=post.created_at,
                    )
                )

        streak = StreakService.get_streak(db, user_id)
        today = datetime.now(UTC).date()
        if streak.current_streak > 0 and streak.last_active_date != today:
            events.append(
                _ActivityEvent(
                    key="streak:nudge",
                    type="streak_nudge",
                    actor_user_id=None,
                    actor_name="DressedUp",
                    message=(
                        f"Don't break your {streak.current_streak}-day streak — "
                        "log today's fit on Home."
                    ),
                    post_id=None,
                    created_at=datetime.now(UTC),
                )
            )

        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:_MAX_ITEMS]

    @classmethod
    def get_activity(cls, db: Session, user_id: int) -> dict:
        last_seen = cls._last_seen(db, user_id)
        events = cls._collect_events(db, user_id)
        items = []
        unread_count = 0
        for event in events:
            is_unread = _is_unread(event.created_at, last_seen)
            if is_unread:
                unread_count += 1
            items.append(
                {
                    "id": event.key,
                    "type": event.type,
                    "actor_user_id": event.actor_user_id,
                    "actor_name": event.actor_name,
                    "message": event.message,
                    "post_id": event.post_id,
                    "created_at": event.created_at,
                    "is_unread": is_unread,
                }
            )
        return {
            "items": items,
            "unread_count": unread_count,
            "last_seen_at": last_seen,
        }

    @staticmethod
    def mark_seen(db: Session, user_id: int) -> dict:
        now = datetime.now(UTC)
        row = db.query(UserFeedState).filter(UserFeedState.user_id == user_id).first()
        if row:
            row.last_seen_at = now
        else:
            db.add(UserFeedState(user_id=user_id, last_seen_at=now))
        db.commit()
        return {"last_seen_at": now, "unread_count": 0}
