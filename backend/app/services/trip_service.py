"""Trip packing: one outfit per day + deduplicated suitcase list."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.clothing_item import ClothingItem
from app.models.trip_plan import TripPlan
from app.services.outfit_service import OutfitService
from app.services.weather_service import DailyWeather, WeatherService

logger = logging.getLogger(__name__)


class TripService:
    @staticmethod
    def _normalize_plan_dates(payload) -> dict:
        data = payload.model_dump()
        start = data.get("start_date")
        end = data.get("end_date")
        days = data.get("days") or 1

        if start and not end:
            data["end_date"] = start + timedelta(days=days - 1)
        elif start and end:
            data["days"] = (end - start).days + 1

        return data

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
        data = TripService._normalize_plan_dates(payload)
        plan = TripPlan(user_id=user_id, **data)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_plan(db: Session, user_id: int, plan_id: int, payload):
        plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == user_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip plan not found")
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(plan, key, value)
        if plan.start_date and plan.end_date and plan.end_date >= plan.start_date:
            plan.days = (plan.end_date - plan.start_date).days + 1
        elif plan.start_date and plan.days:
            plan.end_date = plan.start_date + timedelta(days=plan.days - 1)
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
    def delete_plan(db: Session, user_id: int, plan_id: int) -> None:
        plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == user_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip plan not found")
        db.delete(plan)
        db.commit()

    @staticmethod
    def _load_forecast(plan: TripPlan) -> tuple[list[DailyWeather], str, Optional[str]]:
        start, end = WeatherService.trip_date_range(plan.start_date, plan.end_date, plan.days)
        if not start or not end:
            note = None
            if plan.weather_tag:
                note = f"Using manual weather ({plan.weather_tag}) — add trip dates for a live forecast."
            return [], "manual", note

        if not settings.WEATHER_API_ENABLED:
            return [], "manual", "Weather API disabled — using default outfit rules."

        try:
            forecast = WeatherService.forecast_for_trip(plan.destination, start, end)
            return forecast, "open-meteo", None
        except Exception as exc:
            logger.warning("trip weather fetch failed for %s: %s", plan.destination, exc)
            fallback = plan.weather_tag or "mild"
            return [], "fallback", (
                f"Could not fetch live weather for {plan.destination} "
                f"({exc}). Using {fallback} for all days."
            )

    @staticmethod
    def packing_plan(
        db: Session,
        user_id: int,
        plan_id: int,
        reshuffle_day: int | None = None,
        locked_days: list | None = None,
    ) -> dict:
        plan = TripService.get_plan(db, user_id, plan_id)
        if reshuffle_day is not None and (reshuffle_day < 1 or reshuffle_day > plan.days):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"day must be between 1 and {plan.days}",
            )

        forecast, weather_source, weather_note = TripService._load_forecast(plan)

        locked_by_day: dict[int, object] = {}
        for lock in locked_days or []:
            locked_by_day[lock.day] = lock

        closet = {
            item.id: item
            for item in db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        }

        used_ids: set[int] = set()
        packed_by_id: dict[int, ClothingItem] = {}

        # Reserve pieces from locked days so reshuffled day cannot steal them.
        for day, lock in locked_by_day.items():
            if reshuffle_day is not None and day == reshuffle_day:
                continue
            for item_id in (
                getattr(lock, "top_id", None),
                getattr(lock, "bottom_id", None),
                getattr(lock, "shoes_id", None),
                getattr(lock, "outerwear_id", None),
            ):
                if item_id and item_id in closet:
                    used_ids.add(item_id)
                    packed_by_id[item_id] = closet[item_id]

        avoid_for_reshuffle: set[int] = set()
        if reshuffle_day is not None and reshuffle_day in locked_by_day:
            lock = locked_by_day[reshuffle_day]
            for item_id in (
                getattr(lock, "top_id", None),
                getattr(lock, "bottom_id", None),
                getattr(lock, "shoes_id", None),
                getattr(lock, "outerwear_id", None),
            ):
                if item_id:
                    avoid_for_reshuffle.add(item_id)

        days_outfits: list[dict] = []
        start, _ = WeatherService.trip_date_range(plan.start_date, plan.end_date, plan.days)

        for day in range(1, plan.days + 1):
            trip_date = start + timedelta(days=day - 1) if start else None
            day_weather: DailyWeather | None = forecast[day - 1] if day - 1 < len(forecast) else None

            if day_weather:
                weather_tag = day_weather.weather_tag
                weather_summary = day_weather.summary
                trip_date = day_weather.date
            else:
                weather_tag = plan.weather_tag or "mild"
                weather_summary = None

            use_lock = (
                day in locked_by_day
                and not (reshuffle_day is not None and day == reshuffle_day)
            )

            if use_lock:
                lock = locked_by_day[day]

                def _locked(slot: str):
                    item_id = getattr(lock, f"{slot}_id", None)
                    return closet.get(item_id) if item_id else None

                chosen_slots = {
                    "top": _locked("top"),
                    "bottom": _locked("bottom"),
                    "shoes": _locked("shoes"),
                    "outerwear": _locked("outerwear"),
                }
                rationale = None
            else:
                exclude = set(used_ids)
                if reshuffle_day is not None and day == reshuffle_day:
                    exclude |= avoid_for_reshuffle
                suggestion = OutfitService.get_suggestion(
                    db=db,
                    user_id=user_id,
                    weather_tag=weather_tag,
                    occasion="travel",
                    include_alternative=False,
                    exclude_ids=exclude,
                )
                chosen_slots = {
                    "top": suggestion.get("top"),
                    "bottom": suggestion.get("bottom"),
                    "shoes": suggestion.get("shoes"),
                    "outerwear": suggestion.get("outerwear"),
                }
                rationale = suggestion.get("rationale")

            for item in chosen_slots.values():
                if item is not None:
                    used_ids.add(item.id)
                    packed_by_id[item.id] = item

            date_label = trip_date.strftime("%b %d") if trip_date else f"Day {day}"
            title = f"{date_label} — {plan.destination}"
            if weather_tag and day_weather:
                title = f"{date_label} — {plan.destination} ({weather_tag})"

            if weather_summary:
                rationale = f"Forecast: {weather_summary}. {rationale or ''}".strip()

            days_outfits.append(
                {
                    "day": day,
                    "title": title,
                    "trip_date": trip_date,
                    "weather_tag": weather_tag,
                    "weather_summary": weather_summary,
                    "rationale": rationale,
                    "top": chosen_slots["top"],
                    "bottom": chosen_slots["bottom"],
                    "shoes": chosen_slots["shoes"],
                    "outerwear": chosen_slots["outerwear"],
                }
            )

        packing_list = list(packed_by_id.values())
        summary = (
            f"{len(packing_list)} piece{'s' if len(packing_list) != 1 else ''} "
            f"for {plan.days} day{'s' if plan.days != 1 else ''} in {plan.destination}"
        )
        if forecast:
            tags = ", ".join({d.weather_tag for d in forecast})
            summary += f" · forecast: {tags}"

        return {
            "trip": plan,
            "days": days_outfits,
            "packing_list": packing_list,
            "summary": summary,
            "weather_source": weather_source,
            "weather_note": weather_note,
        }
