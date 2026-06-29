from datetime import date

from app.services.routine_service import RoutineService


def test_get_routine_returns_defaults(client, auth_header):
    response = client.get("/api/v1/outfits/routine", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["wake_time"] == "07:00"
    assert data["weekday_activities"] == ["work"]
    assert data["weekend_activities"] == ["everyday"]
    assert data["notifications_enabled"] is False


def test_update_routine(client, auth_header):
    response = client.put(
        "/api/v1/outfits/routine",
        json={
            "wake_time": "06:30",
            "weekday_activities": ["work", "gym"],
            "gym_days": ["mon", "wed", "fri"],
            "default_weather_tag": "mild",
            "notifications_enabled": True,
        },
        headers=auth_header,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["wake_time"] == "06:30"
    assert data["weekday_activities"] == ["work", "gym"]
    assert data["gym_days"] == ["mon", "wed", "fri"]
    assert data["default_weather_tag"] == "mild"
    assert data["notifications_enabled"] is True


def test_plan_today_from_routine(client, auth_header):
    client.post(
        "/api/v1/closet/items",
        json={"name": "Shirt", "category": "top", "occasion": ["work"], "is_clean": True},
        headers=auth_header,
    )
    client.post(
        "/api/v1/closet/items",
        json={"name": "Pants", "category": "bottom", "occasion": ["work"], "is_clean": True},
        headers=auth_header,
    )
    client.put(
        "/api/v1/outfits/routine",
        json={"weekday_activities": ["work"], "default_weather_tag": "mild"},
        headers=auth_header,
    )

    response = client.get("/api/v1/outfits/plan/today", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "routine"
    assert len(data["activities"]) >= 1
    assert data["activities"][0]["activity"] == "work"


def test_activities_for_today_appends_gym_on_gym_day():
    from app.models.daily_routine import DailyRoutine

    routine = DailyRoutine(
        user_id=1,
        weekday_activities=["work"],
        weekend_activities=["everyday"],
        gym_days=["mon"],
    )
    monday = date(2026, 6, 29)
    assert RoutineService.activities_for_today(routine, today=monday) == ["work", "gym"]

    tuesday = date(2026, 6, 30)
    assert RoutineService.activities_for_today(routine, today=tuesday) == ["work"]

    saturday = date(2026, 7, 4)
    assert RoutineService.activities_for_today(routine, today=saturday) == ["everyday"]
