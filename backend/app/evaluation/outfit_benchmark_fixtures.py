"""Versioned Phase 0 fixtures for the Outfit Engine v3 baseline.

The automated suite measures constraints, ranking, context coverage, diversity,
and latency. It deliberately does not claim to measure subjective style quality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ItemSpec:
    name: str
    category: str
    subcategory: str | None = None
    color: str | None = None
    color_hex: str | None = None
    pattern: str | None = "solid"
    material: str | None = None
    formality: str | None = "casual"
    occasion: list[str] | None = None
    weather_tag: list[str] | None = None
    seasons: list[str] | None = None
    is_clean: bool = True
    times_worn: int = 0


@dataclass(frozen=True)
class RankingProbe:
    preferred: tuple[str, ...]
    alternative: tuple[str, ...]
    label: str


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    description: str
    items: tuple[ItemSpec, ...]
    weather_tag: str | None = None
    occasion: str | None = None
    trend: str | None = None
    required_slots: tuple[str, ...] = ()
    forbidden_names: tuple[str, ...] = ()
    required_names: tuple[str, ...] = ()
    outerwear: Literal["required", "forbidden", "optional"] = "optional"
    ranking_probes: tuple[RankingProbe, ...] = ()
    known_debts: tuple[str, ...] = ()
    tags: tuple[str, ...] = field(default_factory=tuple)


FIXTURES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        case_id="tiny-casual-complete",
        description="Minimum complete closet returns its only clean outfit.",
        items=(
            ItemSpec("White Cotton Tee", "top", color="white", color_hex="#FFFFFF"),
            ItemSpec("Indigo Straight Jeans", "bottom", color="navy", color_hex="#203A5F"),
            ItemSpec("White Leather Sneakers", "footwear", "sneakers", color="white"),
        ),
        weather_tag="mild",
        occasion="everyday",
        required_slots=("top", "bottom", "shoes"),
        required_names=(
            "White Cotton Tee",
            "Indigo Straight Jeans",
            "White Leather Sneakers",
        ),
        tags=("smoke", "tiny-closet"),
    ),
    BenchmarkCase(
        case_id="work-formality-ranking",
        description="Business-coherent pieces should outrank lounge and athletic alternatives.",
        items=(
            ItemSpec(
                "White Oxford Shirt",
                "top",
                color="white",
                color_hex="#FFFFFF",
                material="cotton",
                formality="business",
                occasion=["work"],
                seasons=["spring", "fall"],
            ),
            ItemSpec(
                "Orange Graphic Hoodie",
                "top",
                "hoodie",
                color="orange",
                color_hex="#F05A28",
                pattern="graphic",
                material="fleece",
                formality="loungewear",
                occasion=["loungewear"],
            ),
            ItemSpec(
                "Navy Wool Trousers",
                "bottom",
                color="navy",
                color_hex="#172A46",
                material="wool",
                formality="business",
                occasion=["work"],
            ),
            ItemSpec(
                "Black Leather Loafers",
                "footwear",
                "loafers",
                color="black",
                color_hex="#151515",
                material="leather",
                formality="business",
                occasion=["work"],
            ),
            ItemSpec(
                "Neon Running Shoes",
                "footwear",
                "sneakers",
                color="green",
                color_hex="#8BE000",
                material="mesh",
                formality="casual",
                occasion=["workout"],
            ),
        ),
        weather_tag="mild",
        occasion="work",
        required_slots=("top", "bottom", "shoes"),
        required_names=(
            "White Oxford Shirt",
            "Navy Wool Trousers",
            "Black Leather Loafers",
        ),
        ranking_probes=(
            RankingProbe(
                preferred=(
                    "White Oxford Shirt",
                    "Navy Wool Trousers",
                    "Black Leather Loafers",
                ),
                alternative=(
                    "Orange Graphic Hoodie",
                    "Navy Wool Trousers",
                    "Neon Running Shoes",
                ),
                label="business coherence",
            ),
        ),
        tags=("occasion", "formality", "footwear"),
    ),
    BenchmarkCase(
        case_id="cold-requires-layer",
        description="Cold context selects an available clean coat.",
        items=(
            ItemSpec(
                "Cream Merino Sweater",
                "top",
                "sweater",
                color="cream",
                material="wool",
                weather_tag=["cold"],
                seasons=["winter"],
            ),
            ItemSpec(
                "Charcoal Wool Trousers",
                "bottom",
                color="charcoal",
                material="wool",
                weather_tag=["cold"],
                seasons=["winter"],
            ),
            ItemSpec(
                "Black Weatherproof Boots",
                "footwear",
                "boots",
                color="black",
                material="leather",
                weather_tag=["cold", "rainy"],
                seasons=["winter"],
            ),
            ItemSpec(
                "Navy Wool Overcoat",
                "outerwear",
                "coat",
                color="navy",
                material="wool",
                formality="smart-casual",
                weather_tag=["cold"],
                seasons=["winter"],
            ),
        ),
        weather_tag="cold",
        occasion="everyday",
        required_slots=("top", "bottom", "shoes"),
        outerwear="required",
        tags=("weather", "outerwear"),
    ),
    BenchmarkCase(
        case_id="warm-skips-layer",
        description="Warm context must not add outerwear.",
        items=(
            ItemSpec("Linen Camp Shirt", "top", "shirt", material="linen", weather_tag=["hot", "warm"]),
            ItemSpec("Cotton Chino Shorts", "bottom", "shorts", material="cotton", weather_tag=["hot", "warm"]),
            ItemSpec("Canvas Low Tops", "footwear", "sneakers", material="canvas", weather_tag=["warm"]),
            ItemSpec("Heavy Parka", "outerwear", "parka", material="wool", weather_tag=["cold"]),
        ),
        weather_tag="warm",
        occasion="everyday",
        required_slots=("top", "bottom", "shoes"),
        outerwear="forbidden",
        tags=("weather", "outerwear"),
    ),
    BenchmarkCase(
        case_id="dirty-best-item-excluded",
        description="A dirty high-quality item never leaks into a suggestion.",
        items=(
            ItemSpec(
                "Dirty White Oxford",
                "top",
                "shirt",
                color="white",
                formality="business",
                occasion=["work"],
                is_clean=False,
            ),
            ItemSpec(
                "Clean Blue Oxford",
                "top",
                "shirt",
                color="blue",
                formality="business",
                occasion=["work"],
            ),
            ItemSpec("Grey Trousers", "bottom", color="grey", formality="business", occasion=["work"]),
            ItemSpec("Brown Derby Shoes", "footwear", "loafers", color="brown", formality="business", occasion=["work"]),
        ),
        weather_tag="mild",
        occasion="work",
        required_slots=("top", "bottom", "shoes"),
        forbidden_names=("Dirty White Oxford",),
        required_names=("Clean Blue Oxford",),
        tags=("cleanliness", "hard-constraint"),
    ),
    BenchmarkCase(
        case_id="workout-activewear-ranking",
        description="Workout-specific activewear should outrank casual street clothes.",
        items=(
            ItemSpec(
                "Moisture Wick Training Tee",
                "activewear",
                "athletic-top",
                material="polyester",
                occasion=["workout"],
                weather_tag=["warm"],
            ),
            ItemSpec(
                "Training Shorts",
                "activewear",
                "athletic-shorts",
                material="polyester",
                occasion=["workout"],
                weather_tag=["warm"],
            ),
            ItemSpec(
                "Cross Trainers",
                "footwear",
                "sneakers",
                material="mesh",
                occasion=["workout"],
                weather_tag=["warm"],
            ),
            ItemSpec("Casual Polo", "top", "polo", occasion=["everyday"], weather_tag=["warm"]),
            ItemSpec("Rigid Denim Jeans", "bottom", "jeans", material="denim", occasion=["everyday"]),
            ItemSpec("Leather Loafers", "footwear", "loafers", material="leather", occasion=["work"]),
        ),
        weather_tag="warm",
        occasion="workout",
        required_slots=("top", "bottom", "shoes"),
        required_names=(
            "Moisture Wick Training Tee",
            "Training Shorts",
            "Cross Trainers",
        ),
        ranking_probes=(
            RankingProbe(
                preferred=("Moisture Wick Training Tee", "Training Shorts", "Cross Trainers"),
                alternative=("Casual Polo", "Rigid Denim Jeans", "Leather Loafers"),
                label="workout context",
            ),
        ),
        tags=("occasion", "activewear"),
    ),
    BenchmarkCase(
        case_id="pattern-color-ranking",
        description="A restrained classic combination should outrank a strong pattern/color clash.",
        items=(
            ItemSpec("White Poplin Shirt", "top", color="white", color_hex="#FFFFFF", pattern="solid"),
            ItemSpec("Red Striped Shirt", "top", color="red", color_hex="#D92332", pattern="striped"),
            ItemSpec("Navy Chinos", "bottom", color="navy", color_hex="#152A46", pattern="solid"),
            ItemSpec("Green Plaid Trousers", "bottom", color="green", color_hex="#11823B", pattern="plaid"),
            ItemSpec("Black Minimal Sneakers", "footwear", "sneakers", color="black", pattern="solid"),
        ),
        weather_tag="mild",
        occasion="everyday",
        required_slots=("top", "bottom", "shoes"),
        ranking_probes=(
            RankingProbe(
                preferred=("White Poplin Shirt", "Navy Chinos", "Black Minimal Sneakers"),
                alternative=("Red Striped Shirt", "Green Plaid Trousers", "Black Minimal Sneakers"),
                label="color and pattern coherence",
            ),
        ),
        tags=("color", "pattern"),
    ),
    BenchmarkCase(
        case_id="soft-context-fallback",
        description="Records when v3 silently falls back after no item matches the requested context.",
        items=(
            ItemSpec("Beach Linen Shirt", "top", weather_tag=["hot"], occasion=["vacation"]),
            ItemSpec("Beach Shorts", "bottom", weather_tag=["hot"], occasion=["vacation"]),
            ItemSpec("Beach Sandals", "footwear", "sandals", weather_tag=["hot"], occasion=["vacation"]),
        ),
        weather_tag="cold",
        occasion="formal-event",
        required_slots=("top", "bottom", "shoes"),
        known_debts=("soft_weather_fallback", "soft_occasion_fallback"),
        tags=("known-debt", "context-fallback"),
    ),
    BenchmarkCase(
        case_id="dress-only-unsupported",
        description="Records the current v3 full-body garment coverage gap.",
        items=(
            ItemSpec(
                "Black Midi Dress",
                "dress",
                "midi",
                color="black",
                formality="formal",
                occasion=["date", "formal-event"],
            ),
            ItemSpec("Black Slingback Heels", "footwear", "heels", color="black", formality="formal"),
        ),
        weather_tag="mild",
        occasion="date",
        known_debts=("full_body_garment_not_generated",),
        tags=("known-debt", "dress", "slot-coverage"),
    ),
)


def fixture_manifest() -> list[dict[str, Any]]:
    """Small serializable manifest for reports and tests."""
    return [
        {
            "case_id": case.case_id,
            "description": case.description,
            "item_count": len(case.items),
            "tags": list(case.tags),
            "known_debts": list(case.known_debts),
        }
        for case in FIXTURES
    ]
