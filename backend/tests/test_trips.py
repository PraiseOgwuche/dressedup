from datetime import UTC, datetime, timedelta

from app.models.user import User


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
