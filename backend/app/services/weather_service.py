"""Destination weather via Open-Meteo (free, no API key).

Geocodes the destination, fetches daily forecast for trip dates, and maps
conditions to DressedUp weather_tags for the outfit engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes (Open-Meteo).
_RAIN_CODES = frozenset(range(51, 68)) | frozenset(range(80, 83)) | frozenset(range(95, 100))
_SNOW_CODES = frozenset(range(71, 78)) | frozenset({85, 86})


@dataclass
class DailyWeather:
    date: date
    weather_tag: str
    summary: str
    temp_high_c: Optional[float] = None
    temp_low_c: Optional[float] = None
    precipitation_mm: Optional[float] = None


def _temp_weather_tag(max_c: float) -> str:
    if max_c >= 28:
        return "hot"
    if max_c >= 22:
        return "warm"
    if max_c >= 15:
        return "mild"
    return "cold"


def _wmo_label(code: int) -> str:
    labels = {
        0: "clear",
        1: "mostly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "foggy",
        48: "foggy",
        51: "light drizzle",
        61: "rain",
        63: "rain",
        65: "heavy rain",
        71: "snow",
        73: "snow",
        75: "heavy snow",
        80: "rain showers",
        81: "rain showers",
        82: "heavy showers",
        95: "thunderstorms",
    }
    return labels.get(code, "mixed conditions")


def daily_weather_tag(max_c: float, precip_mm: float, wmo_code: int) -> str:
    """Map forecast numbers to a single outfit-engine weather_tag."""
    if wmo_code in _SNOW_CODES:
        return "snow"
    if precip_mm >= 2.0 or wmo_code in _RAIN_CODES:
        return "rainy"
    return _temp_weather_tag(max_c)


def _format_summary(max_c: float, min_c: float, precip_mm: float, wmo_code: int) -> str:
    label = _wmo_label(wmo_code)
    high_f = round(max_c * 9 / 5 + 32)
    low_f = round(min_c * 9 / 5 + 32)
    parts = [f"{label}, high {high_f}°F / low {low_f}°F"]
    if precip_mm >= 0.5:
        parts.append(f"{precip_mm:.0f}mm precip")
    return " · ".join(parts)


class WeatherService:
    @staticmethod
    def geocode(destination: str) -> tuple[float, float, str]:
        if not settings.WEATHER_API_ENABLED:
            raise RuntimeError("Weather API is disabled")

        params = {"name": destination.strip(), "count": 5, "language": "en", "format": "json"}
        with httpx.Client(timeout=settings.WEATHER_API_TIMEOUT_SEC) as client:
            response = client.get(_GEOCODE_URL, params=params)
            response.raise_for_status()
            results = response.json().get("results") or []

        if not results:
            raise ValueError(f"Could not find weather location for “{destination}”")

        best = results[0]
        label = ", ".join(
            part for part in (best.get("name"), best.get("admin1"), best.get("country")) if part
        )
        return float(best["latitude"]), float(best["longitude"]), label

    @staticmethod
    def forecast_for_trip(destination: str, start: date, end: date) -> list[DailyWeather]:
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        if not settings.WEATHER_API_ENABLED:
            raise RuntimeError("Weather API is disabled")

        lat, lon, place_label = WeatherService.geocode(destination)
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        with httpx.Client(timeout=settings.WEATHER_API_TIMEOUT_SEC) as client:
            response = client.get(_FORECAST_URL, params=params)
            response.raise_for_status()
            daily = response.json().get("daily") or {}

        dates_raw = daily.get("time") or []
        highs = daily.get("temperature_2m_max") or []
        lows = daily.get("temperature_2m_min") or []
        precips = daily.get("precipitation_sum") or []
        codes = daily.get("weathercode") or []

        if not dates_raw:
            raise ValueError(f"No forecast available for {place_label}")

        forecast: list[DailyWeather] = []
        for i, date_str in enumerate(dates_raw):
            trip_date = date.fromisoformat(date_str)
            max_c = float(highs[i]) if i < len(highs) and highs[i] is not None else 20.0
            min_c = float(lows[i]) if i < len(lows) and lows[i] is not None else max_c - 5
            precip = float(precips[i]) if i < len(precips) and precips[i] is not None else 0.0
            code = int(codes[i]) if i < len(codes) and codes[i] is not None else 0
            tag = daily_weather_tag(max_c, precip, code)
            forecast.append(
                DailyWeather(
                    date=trip_date,
                    weather_tag=tag,
                    summary=_format_summary(max_c, min_c, precip, code),
                    temp_high_c=max_c,
                    temp_low_c=min_c,
                    precipitation_mm=precip,
                )
            )

        expected_days = (end - start).days + 1
        if len(forecast) < expected_days:
            logger.warning(
                "forecast shorter than trip for %s: got %s days, expected %s",
                destination,
                len(forecast),
                expected_days,
            )

        return forecast

    @staticmethod
    def trip_date_range(start: Optional[date], end: Optional[date], days: int) -> tuple[Optional[date], Optional[date]]:
        if start and end:
            return start, end
        if start and days >= 1:
            return start, start + timedelta(days=days - 1)
        return start, end
