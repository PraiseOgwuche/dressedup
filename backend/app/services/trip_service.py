"""Trip packing: one outfit per day + deduplicated suitcase list."""

from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.clothing_item import ClothingItem
from app.models.trip_plan import TripPlan
from app.services.outfit_service import OutfitService


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
    def create_plan(db: Session, user_id: int, payload):
        plan = TripPlan(user_id=user_id, **payload.model_dump())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_plan(db: Session, user_id: int, plan_id: int, payload):
        plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == user_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip plan not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(plan, key, value)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def get_plan(db: Session, user_id: int, plan_id: int) -> TripPlan:
        plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == user_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip plan not found")
        return plan

    @staticmethod
    def packing_plan(db: Session, user_id: int, plan_id: int) -> dict:
        plan = TripService.get_plan(db, user_id, plan_id)
        used_ids: set[int] = set()
        days_outfits: list[dict] = []
        packed_by_id: dict[int, ClothingItem] = {}

        for day in range(1, plan.days + 1):
            suggestion = OutfitService.get_suggestion(
                db=db,
                user_id=user_id,
                weather_tag=plan.weather_tag,
                occasion="travel",
                include_alternative=False,
                exclude_ids=used_ids,
            )
            chosen = [
                suggestion[slot]
                for slot in ("top", "bottom", "shoes", "outerwear")
                if suggestion.get(slot) is not None
            ]
            for item in chosen:
                used_ids.add(item.id)
                packed_by_id[item.id] = item

            days_outfits.append(
                {
                    "day": day,
                    "title": f"Day {day} — {plan.destination}",
                    "rationale": suggestion.get("rationale"),
                    "top": suggestion.get("top"),
                    "bottom": suggestion.get("bottom"),
                    "shoes": suggestion.get("shoes"),
                    "outerwear": suggestion.get("outerwear"),
                }
            )

        packing_list = list(packed_by_id.values())
        return {
            "trip": plan,
            "days": days_outfits,
            "packing_list": packing_list,
            "summary": (
                f"{len(packing_list)} piece{'s' if len(packing_list) != 1 else ''} "
                f"for {plan.days} day{'s' if plan.days != 1 else ''} in {plan.destination}"
            ),
        }
