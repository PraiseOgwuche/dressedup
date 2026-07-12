from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from app.models.user import User
from app.services.weather_service import DailyWeather


def test_trip_packing_plan(client, auth_header):
    create = client.post(
        "/api/v1/trips/plans",
        headers=auth_header,
        json={"destination": "Paris", "days": 2, "weather_tag": "mild"},
    )
    assert create.status_code == 201
    plan_id = create.json()["id"]

    packing = client.get(f"/api/v1/trips/plans/{plan_id}/packing", headers=auth_header)
    assert packing.status_code == 200
    body = packing.json()
    assert len(body["days"]) == 2
    assert body["days"][0]["day"] == 1
    assert "packing_list" in body
    assert body["trip"]["destination"] == "Paris"


@patch("app.services.trip_service.WeatherService.forecast_for_trip")
def test_trip_packing_uses_forecast_per_day(mock_forecast, client, auth_header):
    mock_forecast.return_value = [
        DailyWeather(
            date=date(2026, 7, 24),
            weather_tag="hot",
            summary="clear, high 88°F / low 74°F",
            temp_high_c=31.0,
            temp_low_c=23.0,
        ),
        DailyWeather(
            date=date(2026, 7, 25),
            weather_tag="rainy",
            summary="rain showers, high 82°F / low 72°F · 8mm precip",
            temp_high_c=28.0,
            temp_low_c=22.0,
            precipitation_mm=8.0,
        ),
        DailyWeather(
            date=date(2026, 7, 26),
            weather_tag="hot",
            summary="mostly clear, high 90°F / low 76°F",
            temp_high_c=32.0,
            temp_low_c=24.0,
        ),
    ]

    create = client.post(
        "/api/v1/trips/plans",
        headers=auth_header,
        json={
            "destination": "Honolulu, Hawaii",
            "start_date": "2026-07-24",
            "end_date": "2026-07-26",
        },
    )
    assert create.status_code == 201
    assert create.json()["days"] == 3

    packing = client.get(
        f"/api/v1/trips/plans/{create.json()['id']}/packing",
        headers=auth_header,
    )
    assert packing.status_code == 200
    body = packing.json()
    assert body["weather_source"] == "open-meteo"
    assert len(body["days"]) == 3
    assert body["days"][0]["weather_tag"] == "hot"
    assert body["days"][1]["weather_tag"] == "rainy"
    assert body["days"][0]["trip_date"] == "2026-07-24"
    assert "forecast" in body["summary"].lower() or "hot" in body["summary"]
    mock_forecast.assert_called_once()


def test_trip_requires_premium_without_trial(client, db_session):
    email = "nopremium@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Free User", "password": "password123"},
    )
    user = db_session.query(User).filter(User.email == email).first()
    user.premium_trial_ends_at = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    header = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.get("/api/v1/trips/plans", headers=header)
    assert response.status_code == 403


def test_delete_trip_plan(client, auth_header):
    create = client.post(
        "/api/v1/trips/plans",
        headers=auth_header,
        json={"destination": "Tokyo", "days": 2},
    )
    plan_id = create.json()["id"]

    delete = client.delete(f"/api/v1/trips/plans/{plan_id}", headers=auth_header)
    assert delete.status_code == 204

    plans = client.get("/api/v1/trips/plans", headers=auth_header)
    assert all(p["id"] != plan_id for p in plans.json())


def test_update_trip_plan_dates(client, auth_header):
    create = client.post(
        "/api/v1/trips/plans",
        headers=auth_header,
        json={"destination": "Berlin", "days": 2},
    )
    plan_id = create.json()["id"]

    update = client.put(
        f"/api/v1/trips/plans/{plan_id}",
        headers=auth_header,
        json={
            "destination": "Munich",
            "start_date": "2026-09-01",
            "end_date": "2026-09-04",
            "notes": "Oktoberfest",
        },
    )
    assert update.status_code == 200
    body = update.json()
    assert body["destination"] == "Munich"
    assert body["days"] == 4
    assert body["start_date"] == "2026-09-01"
    assert body["notes"] == "Oktoberfest"


def test_reshuffle_trip_day_keeps_other_days(client, auth_header):
    create = client.post(
        "/api/v1/trips/plans",
        headers=auth_header,
        json={"destination": "Seoul", "days": 2, "weather_tag": "mild"},
    )
    plan_id = create.json()["id"]

    packing = client.get(f"/api/v1/trips/plans/{plan_id}/packing", headers=auth_header)
    assert packing.status_code == 200
    original = packing.json()
    day1 = original["days"][0]

    locked = []
    for day in original["days"]:
        locked.append(
            {
                "day": day["day"],
                "top_id": day["top"]["id"] if day.get("top") else None,
                "bottom_id": day["bottom"]["id"] if day.get("bottom") else None,
                "shoes_id": day["shoes"]["id"] if day.get("shoes") else None,
                "outerwear_id": day["outerwear"]["id"] if day.get("outerwear") else None,
            }
        )

    reshuffle = client.post(
        f"/api/v1/trips/plans/{plan_id}/packing/reshuffle",
        headers=auth_header,
        json={"day": 2, "locked_days": locked},
    )
    assert reshuffle.status_code == 200
    body = reshuffle.json()
    assert body["days"][0]["day"] == 1
    if day1.get("top"):
        assert body["days"][0]["top"]["id"] == day1["top"]["id"]
    assert len(body["days"]) == 2