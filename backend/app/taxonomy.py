"""Controlled vocabulary for closet items.

Single source of truth so AI-extracted attributes are normalized and queryable.
Kept intentionally small; extend as the product grows.
"""

# High-level item categories (drives outfit slotting and filtering).
CATEGORIES: list[str] = [
    "top",
    "bottom",
    "dress",
    "outerwear",
    "footwear",
    "activewear",
    "swimwear",
    "underwear",
    "headwear",
    "bag",
    "accessory",
    "jewelry",
]

# Representative subcategories per category (not exhaustive).
SUBCATEGORIES: dict[str, list[str]] = {
    "top": ["t-shirt", "shirt", "blouse", "sweater", "tank", "hoodie", "polo"],
    "bottom": ["jeans", "trousers", "shorts", "skirt", "leggings", "joggers"],
    "dress": ["mini", "midi", "maxi", "gown", "jumpsuit"],
    "outerwear": ["jacket", "coat", "blazer", "cardigan", "parka", "vest"],
    "footwear": ["sneakers", "boots", "heels", "flats", "sandals", "loafers"],
    "activewear": ["sports-bra", "athletic-top", "athletic-shorts", "tracksuit"],
    "swimwear": ["bikini", "one-piece", "trunks", "board-shorts"],
    "underwear": ["bra", "briefs", "boxers", "socks", "undershirt"],
    "headwear": ["cap", "beanie", "hat", "headband"],
    "bag": ["tote", "backpack", "crossbody", "clutch", "duffel"],
    "accessory": ["belt", "scarf", "sunglasses", "watch", "gloves", "tie"],
    "jewelry": ["ring", "necklace", "earrings", "bracelet", "anklet", "brooch"],
}

# Material composition vocabulary (fabrics + jewelry metals/stones).
MATERIALS: list[str] = [
    "cotton",
    "linen",
    "wool",
    "cashmere",
    "silk",
    "denim",
    "leather",
    "suede",
    "polyester",
    "nylon",
    "viscose",
    "elastane",
    "acrylic",
    "down",
    "gold",
    "silver",
    "platinum",
    "stainless-steel",
    "gemstone",
    "pearl",
]

PATTERNS: list[str] = [
    "solid",
    "striped",
    "plaid",
    "checked",
    "floral",
    "polka-dot",
    "graphic",
    "animal-print",
    "camo",
]

# Ordered least -> most formal.
FORMALITY_LEVELS: list[str] = [
    "loungewear",
    "casual",
    "smart-casual",
    "business",
    "formal",
]

SEASONS: list[str] = ["spring", "summer", "fall", "winter", "all-season"]

# Occasions an item suits / an outfit targets.
OCCASIONS: list[str] = [
    "everyday",
    "work",
    "date",
    "party",
    "formal-event",
    "workout",
    "travel",
    "loungewear",
    "outdoor",
]

# Coarse weather buckets used by the outfit engine.
WEATHER_TAGS: list[str] = ["hot", "warm", "mild", "cold", "rainy", "snow"]

# How an item entered the closet (provenance).
SOURCES: list[str] = ["manual", "photo", "label_ocr", "receipt"]


def is_valid(value: str | None, vocabulary: list[str]) -> bool:
    return value is None or value in vocabulary


# How many wears a category typically tolerates before it should be laundered.
# None => the item is not laundered by wear (jewelry, bags, accessories), so it
# never becomes "dirty" automatically. These are sensible defaults; a user can
# override per item via ClothingItem.wear_limit.
DEFAULT_WEAR_LIMITS: dict[str, int | None] = {
    "underwear": 1,
    "activewear": 1,
    "swimwear": 1,
    "top": 2,
    "dress": 2,
    "headwear": 5,
    "bottom": 4,
    "outerwear": 6,
    "footwear": 20,
    "bag": None,
    "accessory": None,
    "jewelry": None,
}

# Fallback when a category isn't listed above.
_FALLBACK_WEAR_LIMIT = 2


def wear_limit_for(category: str | None) -> int | None:
    """Default wears-before-wash for a category. None means 'not laundered'."""
    if category is None:
        return _FALLBACK_WEAR_LIMIT
    return DEFAULT_WEAR_LIMITS.get(category.lower(), _FALLBACK_WEAR_LIMIT)
