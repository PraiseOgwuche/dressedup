from app.services.outfit_ask_service import parse_outfit_query


def test_parse_work_cold_quiet_luxury():
    parsed = parse_outfit_query("Dress me for a cold work day with quiet luxury vibes")
    assert parsed.occasion == "work"
    assert parsed.weather_tag == "cold"
    assert parsed.trend == "quiet-luxury"
    assert "work" in parsed.interpretation.lower()


def test_parse_date_night_streetwear():
    parsed = parse_outfit_query("Outfit for date night, streetwear")
    assert parsed.occasion == "date"
    assert parsed.trend == "streetwear"


def test_parse_rainy_party():
    parsed = parse_outfit_query("Going to a party and it might rain")
    assert parsed.occasion == "party"
    assert parsed.weather_tag == "rainy"


def test_parse_empty_defaults():
    parsed = parse_outfit_query("   ")
    assert parsed.occasion is None
    assert "tell me" in parsed.interpretation.lower()


def test_parse_gym_hot():
    parsed = parse_outfit_query("Gym session, hot weather")
    assert parsed.occasion == "workout"
    assert parsed.weather_tag == "hot"


def test_outfit_ask_endpoint(client, auth_header):
    response = client.post(
        "/api/v1/outfits/ask",
        headers=auth_header,
        json={"query": "Dress me for work on a cold day, quiet luxury"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parsed"]["occasion"] == "work"
    assert body["parsed"]["weather_tag"] == "cold"
    assert body["parsed"]["trend"] == "quiet-luxury"
    assert "suggestion" in body
    assert body["suggestion"]["title"]
