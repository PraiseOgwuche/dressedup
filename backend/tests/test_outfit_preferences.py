from app.config import settings
from app.services.preference_service import PreferenceService


def _add(client, auth_header, **fields):
    response = client.post(
        "/api/v1/closet/items", json={"is_clean": True, **fields}, headers=auth_header
    )
    assert response.status_code == 201
    return response.json()


def test_outfit_feedback_endpoint(client, auth_header):
    top = _add(client, auth_header, name="White tee", category="top")
    bottom = _add(client, auth_header, name="Jeans", category="bottom")
    shoes = _add(client, auth_header, name="Sneakers", category="footwear")

    response = client.post(
        "/api/v1/outfits/feedback",
        json={
            "top_id": top["id"],
            "bottom_id": bottom["id"],
            "shoes_id": shoes["id"],
            "signal": "like",
            "occasion": "everyday",
        },
        headers=auth_header,
    )
    assert response.status_code == 201
    assert response.json()["signal"] == PreferenceService.signal_value("like")


def test_preference_boosts_repeated_combo(client, auth_header, monkeypatch):
    monkeypatch.setattr(settings, "VISION_PROVIDER", "stub")

    top = _add(
        client,
        auth_header,
        name="Blue oxford",
        category="top",
        formality="business",
        color="blue",
        color_hex="#2244aa",
        occasion=["work"],
    )
    bottom = _add(
        client,
        auth_header,
        name="Gray slacks",
        category="bottom",
        formality="business",
        color="gray",
        color_hex="#888888",
        occasion=["work"],
    )
    shoes = _add(
        client,
        auth_header,
        name="Brown loafers",
        category="footwear",
        subcategory="loafers",
        formality="business",
        color="brown",
        occasion=["work"],
    )
    # Decoy pieces
    _add(
        client,
        auth_header,
        name="Neon hoodie",
        category="top",
        formality="loungewear",
        color="orange",
        color_hex="#ff5500",
        pattern="graphic",
    )

    for _ in range(3):
        client.post(
            "/api/v1/outfits/feedback",
            json={
                "top_id": top["id"],
                "bottom_id": bottom["id"],
                "shoes_id": shoes["id"],
                "signal": "wore",
                "occasion": "work",
            },
            headers=auth_header,
        )

    response = client.get(
        "/api/v1/outfits/suggestion",
        params={"occasion": "work"},
        headers=auth_header,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["top"]["id"] == top["id"]
    assert payload["bottom"]["id"] == bottom["id"]
