from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.style_profile import StyleProfileResponse
from app.schemas.style_signal import StyleSignalCreate, StyleSignalResponse
from app.services.style_profile_service import StyleProfileService
from app.services.style_signal_service import StyleSignalService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/style", tags=["Style"])


@router.get("/profile", response_model=StyleProfileResponse)
def get_style_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Visible summary of learned style preferences from closet + activity."""
    return StyleProfileService.get_profile(db, current_user.id)


@router.post("/signals", response_model=StyleSignalResponse, status_code=201)
def record_style_signal(
    payload: StyleSignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log shop taps, previews, and other client-side style activity."""
    return StyleSignalService.record(
        db,
        current_user.id,
        payload.event_type,
        top_id=payload.top_id,
        bottom_id=payload.bottom_id,
        shoes_id=payload.shoes_id,
        outerwear_id=payload.outerwear_id,
        swap_slot=payload.swap_slot,
        replaced_item_id=payload.replaced_item_id,
        product_id=payload.product_id,
        post_id=payload.post_id,
        occasion=payload.occasion,
        weather_tag=payload.weather_tag,
    )
