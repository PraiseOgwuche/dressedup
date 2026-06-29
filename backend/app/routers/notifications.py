from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.notifications import NotificationTestResult, PushTokenRegister, PushTokenUnregister
from app.services.notification_service import NotificationService, plan_notification_text
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
def register_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    NotificationService.register_token(
        db,
        current_user.id,
        payload.token,
        platform=payload.platform,
        timezone_name=payload.timezone,
    )


@router.delete("/register", status_code=status.HTTP_204_NO_CONTENT)
def unregister_push_token(
    payload: PushTokenUnregister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    NotificationService.unregister_token(db, current_user.id, payload.token)


@router.post("/test", response_model=NotificationTestResult)
def send_test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send today's routine plan as a push now (for dev build testing)."""
    result = NotificationService.send_today_plan_to_user(db, current_user.id)
    plan = result["plan"]
    title, body = plan_notification_text(plan)
    return NotificationTestResult(
        title=title,
        body=body,
        tokens_sent=result["tokens_sent"],
        push_result=result["push_result"],
    )
