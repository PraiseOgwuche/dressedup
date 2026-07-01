from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CATALOG_PATH = Path(__file__).resolve().parent / "catalog.yaml"


@dataclass(frozen=True)
class CatalogProduct:
    id: str
    brand: str
    name: str
    category: str
    subcategory: str | None
    color: str | None
    color_hex: str | None
    formality: str | None
    pattern: str | None
    price_usd: float
    product_url: str
    pitch: str
    image_url: str | None = None
    affiliate_url: str | None = None
    retailer: str | None = None


def _parse_product(raw: dict[str, Any]) -> CatalogProduct:
    return CatalogProduct(
        id=str(raw["id"]),
        brand=str(raw["brand"]),
        name=str(raw["name"]),
        category=str(raw["category"]).lower(),
        subcategory=(str(raw["subcategory"]).lower() if raw.get("subcategory") else None),
        color=raw.get("color"),
        color_hex=raw.get("color_hex"),
        formality=raw.get("formality"),
        pattern=raw.get("pattern"),
        price_usd=float(raw.get("price_usd", 0)),
        product_url=str(raw.get("product_url", "")),
        pitch=str(raw.get("pitch", "")),
        image_url=raw.get("image_url"),
        affiliate_url=raw.get("affiliate_url"),
        retailer=raw.get("retailer") or raw.get("brand"),
    )


@lru_cache
def load_catalog() -> list[CatalogProduct]:
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return [_parse_product(entry) for entry in data.get("products", [])]
