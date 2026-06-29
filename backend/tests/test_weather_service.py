from datetime import date

from app.services.weather_service import daily_weather_tag


def test_daily_weather_tag_hot():
    assert daily_weather_tag(32.0, 0.0, 0) == "hot"


def test_daily_weather_tag_rain_overrides_warm():
    assert daily_weather_tag(24.0, 5.0, 61) == "rainy"


def test_daily_weather_tag_snow():
    assert daily_weather_tag(-2.0, 1.0, 73) == "snow"


def test_daily_weather_tag_cold():
    assert daily_weather_tag(10.0, 0.0, 3) == "cold"
