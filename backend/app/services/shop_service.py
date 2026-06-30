"""Shop v1 — curated catalog + virtual try-in-closet outfit counting."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.fashion import MatchContext
from app.fashion.style_rules import weather_seasons
from app.models.clothing_item import ClothingItem
from app.services.outfit_service import OutfitService
from app.shop.catalog import CatalogProduct, load_catalog

_MIN_OUTFIT_SCORE = 0.48
_SHOP_CONTEXT = MatchContext(
    occasion="everyday",
    weather_tag="mild",
    target_seasons=weather_seasons("mild"),
)


@dataclass
class VirtualGarment:
    """Looks like ClothingItem to the outfit scorer — not persisted."""

    id: int
    name: str
    brand: str | None
    category: str
    subcategory: str | None = None
    color: str | None = None
    color_hex: str | None = None
    pattern: str | None = "solid"
    material: str | None = None
    formality: str | None = None
    occasion: list | None = field(default_factory=lambda: ["everyday"])
    weather_tag: list | None = field(default_factory=lambda: ["mild", "warm"])
    seasons: list | None = field(default_factory=lambda: ["all-season"])
    is_clean: bool = True
    times_worn: int = 0
    image_url: str | None = None
    product_name: str | None = None
    source: str = "shop_catalog"


class ShopService:
    _SLOT_CATEGORY = {
        "top": OutfitService.TOP_CATEGORIES,
        "bottom": OutfitService.BOTTOM_CATEGORIES,
        "footwear": OutfitService.SHOE_CATEGORIES,
        "outerwear": OutfitService.OUTERWEAR_CATEGORIES,
    }

    @staticmethod
    def _virtual_id(product_id: str) -> int:
        return -(abs(hash(product_id)) % 2_000_000_000)

    @classmethod
    def _to_virtual(cls, product: CatalogProduct) -> VirtualGarment:
        return VirtualGarment(
            id=cls._virtual_id(product.id),
            name=product.name,
            brand=product.brand,
            product_name=product.name,
            category=product.category,
            subcategory=product.subcategory,
            color=product.color,
            color_hex=product.color_hex,
            pattern=product.pattern,
            formality=product.formality,
        )

    @classmethod
    def _slot_for_category(cls, category: str) -> str | None:
        cat = category.lower()
        if cat in cls._SLOT_CATEGORY["top"] or cat == "top":
            return "top"
        if cat in cls._SLOT_CATEGORY["bottom"] or cat == "bottom":
            return "bottom"
        if cat in cls._SLOT_CATEGORY["footwear"] or cat == "footwear":
            return "footwear"
        if cat in cls._SLOT_CATEGORY["outerwear"] or cat == "outerwear":
            return "outerwear"
        return None

    @classmethod
    def _build_pools(
        cls,
        items: list[ClothingItem],
        virtual: VirtualGarment,
        slot: str,
    ) -> tuple[list, list, list]:
        context_occasion = _SHOP_CONTEXT.occasion
        context_weather = _SHOP_CONTEXT.weather_tag

        tops = OutfitService._candidates(
            items,
            OutfitService.TOP_CATEGORIES,
            context_weather,
            context_occasion,
            subcategory_set=OutfitService.TOP_SUBCATEGORIES,
        )
        bottoms = OutfitService._candidates(
            items,
            OutfitService.BOTTOM_CATEGORIES,
            context_weather,
            context_occasion,
            subcategory_set=OutfitService.BOTTOM_SUBCATEGORIES,
        )
        shoes = OutfitService._candidates(
            items,
            OutfitService.SHOE_CATEGORIES,
            context_weather,
            context_occasion,
        )

        if slot == "top":
            tops = [virtual] + tops
        elif slot == "bottom":
            bottoms = [virtual] + bottoms
        elif slot == "footwear":
            shoes = [virtual] + shoes

        return tops, bottoms, shoes

    @classmethod
    def _count_outfits_with_item(
        cls,
        db: Session,
        user_id: int,
        tops: list,
        bottoms: list,
        shoes: list,
        required: VirtualGarment,
    ) -> int:
        count = 0
        top_opts = tops or [None]
        bottom_opts = bottoms or [None]
        shoe_opts = shoes or [None]

        for top in top_opts:
            for bottom in bottom_opts:
                if top is None and bottom is None:
                    continue
                for shoe in shoe_opts:
                    garments = [top, bottom, shoe]
                    if required not in garments:
                        continue
                    score = OutfitService._score(db, user_id, garments, _SHOP_CONTEXT)
                    if score >= _MIN_OUTFIT_SCORE:
                        count += 1
        return count

    @staticmethod
    def _user_has_near_duplicate(items: list[ClothingItem], product: CatalogProduct) -> bool:
        for item in items:
            if item.category.lower() != product.category:
                continue
            if item.color and product.color and item.color.lower() == product.color.lower():
                return True
            if item.brand and product.brand and item.brand.lower() == product.brand.lower():
                if item.name and product.name.lower() in item.name.lower():
                    return True
        return False

    @classmethod
    def _outfit_count_for_product(
        cls,
        db: Session,
        user_id: int,
        items: list[ClothingItem],
        product: CatalogProduct,
    ) -> int:
        slot = cls._slot_for_category(product.category)
        if slot is None:
            return 0
        virtual = cls._to_virtual(product)

        if slot == "outerwear":
            return cls._count_outerwear_outfits(db, user_id, items, virtual)

        tops, bottoms, shoes = cls._build_pools(items, virtual, slot)
        if not tops and not bottoms and not shoes:
            return 0
        return cls._count_outfits_with_item(db, user_id, tops, bottoms, shoes, virtual)

    @classmethod
    def _count_outerwear_outfits(
        cls,
        db: Session,
        user_id: int,
        items: list[ClothingItem],
        virtual: VirtualGarment,
    ) -> int:
        tops, bottoms, shoes = cls._build_pools(items, virtual, "top")
        count = 0
        for top in tops or [None]:
            for bottom in bottoms or [None]:
                if top is None and bottom is None:
                    continue
                for shoe in shoes or [None]:
                    trio = [top, bottom, shoe]
                    if OutfitService._score(db, user_id, trio, _SHOP_CONTEXT) < _MIN_OUTFIT_SCORE:
                        continue
                    anchor = top or bottom or shoe
                    if anchor is None:
                        continue
                    layer_score = OutfitService._score(db, user_id, [anchor, virtual], _SHOP_CONTEXT)
                    if layer_score >= _MIN_OUTFIT_SCORE:
                        count += 1
        return count

    @classmethod
    def get_recommendations(cls, db: Session, user_id: int) -> dict:
        items = (
            db.query(ClothingItem)
            .filter(ClothingItem.user_id == user_id, ClothingItem.is_clean.is_(True))
            .all()
        )
        catalog = load_catalog()

        if len(items) < 2:
            return {
                "summary": "Add a few more pieces to your closet — we'll show what to buy next.",
                "recommendations": [],
            }

        scored: list[dict] = []
        for product in catalog:
            if cls._user_has_near_duplicate(items, product):
                continue
            outfit_count = cls._outfit_count_for_product(db, user_id, items, product)
            if outfit_count < 1:
                continue

            priority = "high" if outfit_count >= 8 else ("medium" if outfit_count >= 4 else "low")
            scored.append(
                {
                    "product_id": product.id,
                    "brand": product.brand,
                    "name": product.name,
                    "category": product.category,
                    "color": product.color,
                    "price_usd": product.price_usd,
                    "product_url": product.product_url,
                    "pitch": product.pitch,
                    "outfit_count": outfit_count,
                    "reason": (
                        f"Works in {outfit_count} outfit{'s' if outfit_count != 1 else ''} "
                        f"with your closet. {product.pitch}"
                    ),
                    "priority": priority,
                }
            )

        scored.sort(key=lambda row: (-row["outfit_count"], row["price_usd"]))

        if not scored:
            summary = "Your closet is well covered — check back as we add more picks."
        else:
            top = scored[0]
            summary = (
                f"Top pick: {top['brand']} {top['name']} — "
                f"~{top['outfit_count']} new outfits from what you own."
            )

        return {
            "summary": summary,
            "recommendations": scored[:8],
        }
