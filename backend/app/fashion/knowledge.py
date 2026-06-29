"""Load and cache the YAML fashion knowledge base."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_KNOWLEDGE_PATH = Path(__file__).parent / "knowledge.yaml"


def _pair_set(pairs: list[list[str]]) -> set[frozenset[str]]:
    return {frozenset(p) for p in pairs}


def _normalize_occasion_rules(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {name: dict(values) for name, values in (raw or {}).items()}


@lru_cache
def load_knowledge() -> dict[str, Any]:
    with _KNOWLEDGE_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("knowledge.yaml must be a mapping at the root.")
    return data


@lru_cache
def color_vocabulary() -> dict[str, set[str]]:
    colors = load_knowledge().get("colors", {})
    return {
        "warm": set(colors.get("warm", [])),
        "cool": set(colors.get("cool", [])),
        "neutral": set(colors.get("neutral", [])),
    }


@lru_cache
def classic_color_pairings() -> set[frozenset[str]]:
    pairs = load_knowledge().get("colors", {}).get("classic_pairings", [])
    return _pair_set(pairs)


@lru_cache
def clashing_color_pairings() -> set[frozenset[str]]:
    pairs = load_knowledge().get("colors", {}).get("clashing_pairings", [])
    return _pair_set(pairs)


@lru_cache
def occasion_rules() -> dict[str, dict[str, Any]]:
    return _normalize_occasion_rules(load_knowledge().get("occasions"))


@lru_cache
def pattern_clashes() -> set[frozenset[str]]:
    pairs = load_knowledge().get("patterns", {}).get("clashes", [])
    return _pair_set(pairs)


@lru_cache
def statement_patterns() -> set[str]:
    return set(load_knowledge().get("patterns", {}).get("statement", []))


@lru_cache
def footwear_rules() -> dict[str, set[str]]:
    foot = load_knowledge().get("footwear", {})
    return {
        "casual_only": set(foot.get("casual_only", [])),
        "formal_types": set(foot.get("formal_types", [])),
    }


@lru_cache
def texture_rules() -> dict[str, Any]:
    return dict(load_knowledge().get("textures", {}))


@lru_cache
def weather_season_map() -> dict[str, set[str]]:
    raw = load_knowledge().get("weather_seasons", {})
    return {key: set(values) for key, values in raw.items()}


@lru_cache
def cold_weather_tags() -> set[str]:
    return set(load_knowledge().get("cold_weather_tags", []))


@lru_cache
def category_rules() -> list[dict[str, Any]]:
    return list(load_knowledge().get("category_rules", []))


@lru_cache
def occasion_color_palettes() -> dict[str, set[str]]:
    rules = occasion_rules()
    return {
        name: set(config.get("color_palette", []))
        for name, config in rules.items()
        if config.get("color_palette")
    }


@lru_cache
def trend_profiles() -> dict[str, dict[str, Any]]:
    raw = load_knowledge().get("trends", {})
    return {name: dict(profile) for name, profile in (raw or {}).items()}


def knowledge_version() -> int:
    return int(load_knowledge().get("meta", {}).get("version", 1))
