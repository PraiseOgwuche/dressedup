from app.fashion.knowledge import (
    archetype_rules,
    gap_priorities,
    knowledge_version,
    occasion_rules,
    silhouette_rules,
    trend_profiles,
)
from app.fashion.style_rules import score_archetype, score_silhouette
from types import SimpleNamespace


def test_knowledge_v4_sections():
    assert knowledge_version() >= 4
    assert len(silhouette_rules().get("balanced_pairs", [])) >= 2
    assert len(archetype_rules()) >= 3
    assert len(gap_priorities()) >= 3
    assert "dark-academia" in trend_profiles()
    assert "brunch" in occasion_rules()


def test_relaxed_top_slim_bottom_silhouette_bonus():
    top = SimpleNamespace(
        category="top",
        subcategory="hoodie",
        name="Oversized hoodie",
        product_name=None,
        pattern="solid",
        formality="casual",
    )
    bottom = SimpleNamespace(
        category="bottom",
        subcategory="jeans",
        name="Slim black jeans",
        product_name=None,
        pattern="solid",
        formality="casual",
    )
    score, highlights, _ = score_silhouette([top, bottom])
    assert score > 0.2
    assert highlights


def test_archetype_smart_separate_bonus():
    top = SimpleNamespace(
        category="top",
        subcategory="oxford",
        name="White oxford",
        product_name=None,
        pattern="solid",
        formality="business",
    )
    bottom = SimpleNamespace(
        category="bottom",
        subcategory="chinos",
        name="Khaki chinos",
        product_name=None,
        pattern="solid",
        formality="smart-casual",
    )
    shoes = SimpleNamespace(
        category="footwear",
        subcategory="loafers",
        name="Brown loafers",
        product_name=None,
        pattern="solid",
        formality="business",
    )
    score, highlights, _ = score_archetype([top, bottom, shoes])
    assert score > 0.2
    assert highlights
