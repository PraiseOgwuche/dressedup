import base64
import io
from typing import Optional

import anthropic
from PIL import Image

from app.config import settings
from app.schemas.ingestion import BoundingBox, DraftItem, ReceiptExtract
from app.services.vision.base import VisionProvider
from app.taxonomy import (
    CATEGORIES,
    FORMALITY_LEVELS,
    OCCASIONS,
    PATTERNS,
    SEASONS,
    WEATHER_TAGS,
)

_ATTR_FIELDS = [
    "name",
    "category",
    "subcategory",
    "brand",
    "color",
    "material",
    "size",
    "occasion",
    "formality",
    "weather_tag",
    "pattern",
]

_SYSTEM_PROMPT = (
    "You are a wardrobe cataloging assistant. Classify the clothing or accessory in "
    "the photo into the provided taxonomy and return concise, normalized attributes via "
    "the save_clothing_item tool. Only set `brand`, `material`, or `size` when they are "
    "clearly visible (a printed logo, or a care-label/tag image) — never guess them from "
    "the fabric. List any fields you are unsure about in `uncertain_fields`."
)

_TOOL = {
    "name": "save_clothing_item",
    "description": "Record the catalogued attributes of the clothing item in the image.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Short human label, e.g. 'Black crewneck t-shirt'."},
            "category": {"type": "string", "enum": CATEGORIES},
            "subcategory": {"type": "string"},
            "brand": {"type": ["string", "null"]},
            "color": {"type": "string"},
            "color_hex": {"type": "string", "description": "Dominant color as #rrggbb."},
            "pattern": {"type": "string", "enum": PATTERNS},
            "material": {"type": ["string", "null"]},
            "size": {"type": ["string", "null"]},
            "occasion": {
                "type": "array",
                "items": {"type": "string", "enum": OCCASIONS},
                "description": "All occasions the item reasonably suits.",
            },
            "formality": {"type": "string", "enum": FORMALITY_LEVELS},
            "weather_tag": {
                "type": "array",
                "items": {"type": "string", "enum": WEATHER_TAGS},
                "description": "All weather conditions the item is comfortable in.",
            },
            "seasons": {"type": "array", "items": {"type": "string", "enum": SEASONS}},
            "uncertain_fields": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "category"],
    },
}

_MULTI_SYSTEM_PROMPT = (
    "You are a wardrobe cataloging assistant. The photo may show several distinct "
    "clothing items (flat-lay on a bed, outfit pile, closet shelf). Identify every "
    "separate garment or accessory and catalog each one. Do not merge multiple items "
    "into one entry. For each item, also return a tight bounding box (bbox) as "
    "normalized fractions of the full image (x,y = top-left; w,h = size; all 0–1). "
    "Boxes may lightly overlap but should not cover the whole photo unless only one "
    "item is present. Only set brand/material/size when clearly visible."
)

_BBOX_SCHEMA = {
    "type": "object",
    "description": "Normalized box around this garment in the source photo.",
    "properties": {
        "x": {"type": "number", "minimum": 0, "maximum": 1},
        "y": {"type": "number", "minimum": 0, "maximum": 1},
        "w": {"type": "number", "minimum": 0.05, "maximum": 1},
        "h": {"type": "number", "minimum": 0.05, "maximum": 1},
    },
    "required": ["x", "y", "w", "h"],
}

_MULTI_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        **_TOOL["input_schema"]["properties"],
        "bbox": _BBOX_SCHEMA,
    },
    "required": ["name", "category", "bbox"],
}

_MULTI_TOOL = {
    "name": "save_clothing_items",
    "description": "Record every distinct clothing item visible in the photo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": _MULTI_ITEM_SCHEMA,
                "description": "One entry per distinct garment or accessory in the image.",
            }
        },
        "required": ["items"],
    },
}

_RECEIPT_LINE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Short label for the line item."},
        "category": {"type": "string", "enum": CATEGORIES},
        "subcategory": {"type": "string"},
        "brand": {"type": ["string", "null"]},
        "product_name": {"type": ["string", "null"]},
        "size": {"type": ["string", "null"]},
        "color": {"type": ["string", "null"]},
        "sku": {"type": ["string", "null"], "description": "Style/SKU/product code when printed."},
        "price": {"type": ["number", "null"], "description": "Line-item price in USD."},
        "uncertain_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "category"],
}

_RECEIPT_SYSTEM_PROMPT = (
    "You are a wardrobe cataloging assistant. Parse the retail receipt photo and extract "
    "only clothing, footwear, and fashion accessories (bags, belts, hats, jewelry). "
    "Skip non-apparel lines (tax, gift cards, food, electronics). Use the merchant name "
    "from the receipt header when brand is not printed per line. Never invent SKUs or prices — "
    "only include them when clearly visible."
)

_RECEIPT_TOOL = {
    "name": "save_receipt_items",
    "description": "Record apparel line items from the receipt.",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchant": {"type": ["string", "null"]},
            "purchase_date": {
                "type": ["string", "null"],
                "description": "ISO date YYYY-MM-DD when visible on the receipt.",
            },
            "items": {
                "type": "array",
                "items": _RECEIPT_LINE_SCHEMA,
                "description": "One entry per apparel line on the receipt.",
            },
        },
        "required": ["items"],
    },
}

_LABEL_SYSTEM_PROMPT = (
    "You are a wardrobe cataloging assistant. Read the care label, hang tag, or sewn-in tag "
    "photo. Extract brand, product name, size, and material composition when printed. "
    "Infer category/subcategory only when obvious from the label (e.g. 'MEN'S TEE'). "
    "Do not guess color or pattern — leave visual attributes empty."
)

_LABEL_TOOL = {
    "name": "save_label_item",
    "description": "Record identity fields visible on the care label or tag.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Short human label from the tag."},
            "category": {"type": "string", "enum": CATEGORIES},
            "subcategory": {"type": "string"},
            "brand": {"type": ["string", "null"]},
            "product_name": {"type": ["string", "null"]},
            "size": {"type": ["string", "null"]},
            "material": {"type": ["string", "null"]},
            "uncertain_fields": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "category"],
    },
}


class AnthropicVisionProvider(VisionProvider):
    """Real extraction via Claude. Images are downscaled before upload and output is
    capped to keep per-scan cost minimal (~$0.002 on Haiku)."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    @staticmethod
    def _to_jpeg_b64(data: bytes) -> str:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.thumbnail((settings.VISION_MAX_IMAGE_PX, settings.VISION_MAX_IMAGE_PX))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @staticmethod
    def _image_block(b64: str) -> dict:
        return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}

    def extract_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> DraftItem:
        content: list[dict] = [
            {"type": "text", "text": "Garment photo:"},
            self._image_block(self._to_jpeg_b64(garment_image)),
        ]
        if label_image is not None:
            content.append({"type": "text", "text": "Care label / tag photo (use for brand, material, size):"})
            content.append(self._image_block(self._to_jpeg_b64(label_image)))
        content.append({"type": "text", "text": "Catalog this item using the save_clothing_item tool."})

        message = self._client.messages.create(
            model=settings.VISION_MODEL,
            max_tokens=settings.VISION_MAX_OUTPUT_TOKENS,
            system=_SYSTEM_PROMPT,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "save_clothing_item"},
            messages=[{"role": "user", "content": content}],
        )

        data = next((b.input for b in message.content if b.type == "tool_use"), None)
        if not data:
            raise RuntimeError("Vision model returned no structured item.")

        return self._to_draft(data, has_label=label_image is not None)

    def extract_multi_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> list[DraftItem]:
        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    "Flat-lay / multi-item photo — list every separate garment or accessory "
                    "you can see:"
                ),
            },
            self._image_block(self._to_jpeg_b64(garment_image)),
        ]
        if label_image is not None:
            content.append({"type": "text", "text": "Optional care label (identity hints only):"})
            content.append(self._image_block(self._to_jpeg_b64(label_image)))

        message = self._client.messages.create(
            model=settings.VISION_MODEL,
            max_tokens=settings.VISION_MAX_MULTI_OUTPUT_TOKENS,
            system=_MULTI_SYSTEM_PROMPT,
            tools=[_MULTI_TOOL],
            tool_choice={"type": "tool", "name": "save_clothing_items"},
            messages=[{"role": "user", "content": content}],
        )

        data = next((b.input for b in message.content if b.type == "tool_use"), None)
        if not data or not data.get("items"):
            raise RuntimeError("Vision model returned no items for multi scan.")

        has_label = label_image is not None
        drafts = [self._to_draft(item, has_label=has_label) for item in data["items"]]
        return drafts[: settings.MAX_MULTI_ITEMS_PER_PHOTO]

    def extract_from_receipt(self, receipt_image: bytes) -> ReceiptExtract:
        content: list[dict] = [
            {"type": "text", "text": "Retail receipt photo — extract apparel line items:"},
            self._image_block(self._to_jpeg_b64(receipt_image)),
            {"type": "text", "text": "Parse using the save_receipt_items tool."},
        ]

        message = self._client.messages.create(
            model=settings.VISION_MODEL,
            max_tokens=settings.VISION_MAX_RECEIPT_OUTPUT_TOKENS,
            system=_RECEIPT_SYSTEM_PROMPT,
            tools=[_RECEIPT_TOOL],
            tool_choice={"type": "tool", "name": "save_receipt_items"},
            messages=[{"role": "user", "content": content}],
        )

        data = next((b.input for b in message.content if b.type == "tool_use"), None)
        if not data or not data.get("items"):
            raise RuntimeError("Vision model returned no receipt line items.")

        purchase_date = data.get("purchase_date")
        drafts = [
            self._to_receipt_draft(item, purchase_date=purchase_date)
            for item in data["items"][: settings.MAX_RECEIPT_ITEMS]
        ]
        return ReceiptExtract(
            merchant=data.get("merchant"),
            purchase_date=purchase_date,
            items=drafts,
        )

    def extract_from_care_label(self, label_image: bytes) -> DraftItem:
        content: list[dict] = [
            {"type": "text", "text": "Care label / hang tag photo:"},
            self._image_block(self._to_jpeg_b64(label_image)),
            {"type": "text", "text": "Catalog identity fields using save_label_item."},
        ]

        message = self._client.messages.create(
            model=settings.VISION_MODEL,
            max_tokens=settings.VISION_MAX_OUTPUT_TOKENS,
            system=_LABEL_SYSTEM_PROMPT,
            tools=[_LABEL_TOOL],
            tool_choice={"type": "tool", "name": "save_label_item"},
            messages=[{"role": "user", "content": content}],
        )

        data = next((b.input for b in message.content if b.type == "tool_use"), None)
        if not data:
            raise RuntimeError("Vision model returned no label data.")

        return self._to_label_draft(data)

    @staticmethod
    def _parse_bbox(raw) -> Optional[BoundingBox]:
        if not isinstance(raw, dict):
            return None
        try:
            box = BoundingBox(
                x=float(raw["x"]),
                y=float(raw["y"]),
                w=float(raw["w"]),
                h=float(raw["h"]),
            )
        except (KeyError, TypeError, ValueError):
            return None
        # Reject boxes that cover almost the whole frame — useless for cropping.
        if box.w * box.h > 0.92:
            return None
        if box.x + box.w > 1.05 or box.y + box.h > 1.05:
            return None
        return box

    @staticmethod
    def _to_draft(data: dict, has_label: bool) -> DraftItem:
        uncertain = set(data.get("uncertain_fields") or [])
        confidence = {
            field: (0.5 if field in uncertain else 0.92)
            for field in _ATTR_FIELDS
            if data.get(field)
        }
        return DraftItem(
            name=data.get("name") or "Unnamed item",
            category=data.get("category") or "accessory",
            subcategory=data.get("subcategory"),
            brand=data.get("brand"),
            color=data.get("color"),
            color_hex=data.get("color_hex"),
            pattern=data.get("pattern"),
            material=data.get("material"),
            size=data.get("size"),
            occasion=data.get("occasion") or [],
            formality=data.get("formality"),
            weather_tag=data.get("weather_tag") or [],
            seasons=data.get("seasons") or [],
            source="label_ocr" if has_label else "photo",
            confidence=confidence,
            needs_review=bool(uncertain) or not data.get("brand"),
            bbox=AnthropicVisionProvider._parse_bbox(data.get("bbox")),
        )

    @staticmethod
    def _to_receipt_draft(data: dict, purchase_date: Optional[str]) -> DraftItem:
        uncertain = set(data.get("uncertain_fields") or [])
        identity_fields = ["brand", "product_name", "size", "sku", "price", "category", "name"]
        confidence = {
            field: (0.5 if field in uncertain else 0.93)
            for field in identity_fields
            if data.get(field) is not None
        }
        return DraftItem(
            name=data.get("name") or "Receipt item",
            category=data.get("category") or "accessory",
            subcategory=data.get("subcategory"),
            brand=data.get("brand"),
            product_name=data.get("product_name"),
            size=data.get("size"),
            color=data.get("color"),
            sku=data.get("sku"),
            price=data.get("price"),
            purchase_date=purchase_date,
            source="receipt",
            confidence=confidence,
            needs_review=bool(uncertain) or not data.get("brand"),
        )

    @staticmethod
    def _to_label_draft(data: dict) -> DraftItem:
        uncertain = set(data.get("uncertain_fields") or [])
        identity_fields = ["brand", "product_name", "size", "material", "category", "name"]
        confidence = {
            field: (0.5 if field in uncertain else 0.94)
            for field in identity_fields
            if data.get(field)
        }
        return DraftItem(
            name=data.get("name") or "Tagged item",
            category=data.get("category") or "top",
            subcategory=data.get("subcategory"),
            brand=data.get("brand"),
            product_name=data.get("product_name"),
            size=data.get("size"),
            material=data.get("material"),
            source="label_ocr",
            confidence=confidence,
            needs_review=bool(uncertain) or not data.get("brand"),
        )
