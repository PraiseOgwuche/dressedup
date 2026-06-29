from sqlalchemy.orm import Session

from app.models.social_post import SocialPost
from app.schemas.social import SocialPostCreate


class SocialService:
    @staticmethod
    def list_posts(db: Session):
        return db.query(SocialPost).order_by(SocialPost.created_at.desc()).all()

    @staticmethod
    def create_post(db: Session, user_id: int, payload: SocialPostCreate):
        post = SocialPost(user_id=user_id, **payload.model_dump())
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

