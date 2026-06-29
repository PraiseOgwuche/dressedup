from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trip_plan import TripPlan
from app.schemas.trips import TripPlanCreate, TripPlanUpdate


class TripService:
    @staticmethod
    def list_plans(db: Session, user_id: int):
        return (
            db.query(TripPlan)
            .filter(TripPlan.user_id == user_id)
            .order_by(TripPlan.created_at.desc())
            .all()
        )

    @staticmethod
    def create_plan(db: Session, user_id: int, payload: TripPlanCreate):
        plan = TripPlan(user_id=user_id, **payload.model_dump())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_plan(db: Session, user_id: int, plan_id: int, payload: TripPlanUpdate):
        plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == user_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip plan not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(plan, key, value)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

