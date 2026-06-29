from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.social import SocialPostCreate, SocialPostResponse
from app.services.social_service import SocialService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/social", tags=["Social"])


@router.get("/posts", response_model=List[SocialPostResponse])
def list_posts(db: Session = Depends(get_db)):
    return SocialService.list_posts(db)


@router.post("/posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: SocialPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SocialService.create_post(db, current_user.id, payload)

