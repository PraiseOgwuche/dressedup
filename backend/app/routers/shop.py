from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.shop import ShopRecommendationResponse
from app.services.shop_service import ShopService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/shop", tags=["Shop"])


@router.get("/recommendations", response_model=ShopRecommendationResponse)
def get_shop_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ShopService.get_recommendations(db, current_user.id)

