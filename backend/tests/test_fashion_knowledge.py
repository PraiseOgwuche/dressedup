from app.fashion.knowledge import (
    classic_color_pairings,
    knowledge_version,
    load_knowledge,
    occasion_color_palettes,
    texture_rules,
    trend_profiles,
)
from app.fashion.matcher import FashionMatcher
from app.fashion.context import MatchContext
from app.fashion.style_rules import score_textures
from app.fashion.trend_rules import available_trends, score_occasion_palette, score_trend_fit
from types import SimpleNamespace


def test_knowledge_yaml_loads():
    data = load_knowledge()
    assert data["meta"]["version"] >= 3
    assert knowledge_version() >= 3
    assert len(classic_color_pairings()) >= 20
    assert "quiet-luxury" in trend_profiles()
    assert "work" in occasion_color_palettes()


def test_work_palette_bonus_for_navy_charcoal():
    top = SimpleNamespace(color="navy", category="top")
    bottom = SimpleNamespace(color="charcoal", category="bottom")
    score, highlights, _ = score_occasion_palette([top, bottom], "work")
    assert score > 0
    assert any("work" in h for h in highlights)


def test_party_palette_warns_on_mismatch():
    top = SimpleNamespace(color="lime", category="top")
    bottom = SimpleNamespace(color="cyan", category="bottom")
    score, _, warnings = score_occasion_palette([top, bottom], "party")
    assert score < 0
    assert warnings


def test_quiet_luxury_trend_scores_neutral_tailoring():
    top = SimpleNamespace(
        color="camel",
        pattern="solid",
        formality="smart-casual",
        category="top",
        material="wool",
        subcategory="sweater",
        style_tags=[],
    )
    bottom = SimpleNamespace(
        color="charcoal",
        pattern="solid",
        formality="business",
        category="bottom",
        material="wool",
        subcategory="trousers",
        style_tags=[],
    )
    shoes = SimpleNamespace(
        color="black",
        pattern="solid",
        formality="business",
        category="footwear",
        subcategory="loafers",
        material="leather",
        style_tags=[],
    )
    score, highlights, _ = score_trend_fit([top, bottom, shoes], "quiet-luxury")
    assert score > 0.3
    assert any("quiet" in h.lower() for h in highlights)


def test_streetwear_scores_lower_than_quiet_luxury_for_formal_tailoring():
    top = SimpleNamespace(
        color="charcoal",
        pattern="solid",
        formality="business",
        category="top",
        material="wool",
        subcategory="shirt",
        style_tags=[],
    )
    bottom = SimpleNamespace(
        color="navy",
        pattern="solid",
        formality="business",
        category="bottom",
        material="wool",
        subcategory="trousers",
        style_tags=[],
    )
    shoes = SimpleNamespace(
        color="black",
        pattern="solid",
        formality="business",
        category="footwear",
        subcategory="loafers",
        material="leather",
        style_tags=[],
    )
    garments = [top, bottom, shoes]
    street_score, _, _ = score_trend_fit(garments, "streetwear")
    quiet_score, quiet_highlights, _ = score_trend_fit(garments, "quiet-luxury")
    assert quiet_score > street_score
    assert any("quiet" in h.lower() for h in quiet_highlights)
    assert street_score < 0.45


def test_available_trends_lists_profiles():
    trends = available_trends()
    ids = {t["id"] for t in trends}
    assert "quiet-luxury" in ids
    assert "streetwear" in ids
    assert all(t.get("label") for t in trends)


def test_matcher_applies_trend_and_palette():
    top = _item(category="top", color="navy", formality="business")
    bottom = _item(category="bottom", color="charcoal", formality="business")
    shoes = _item(category="footwear", subcategory="loafers", color="black", formality="business")

    with_trend = FashionMatcher.score_outfit(
        [top, bottom, shoes],
        MatchContext(occasion="work", trend="quiet-luxury"),
    )
    without = FashionMatcher.score_outfit(
        [top, bottom, shoes],
        MatchContext(occasion="work"),
    )
    assert with_trend.trend > 0
    assert with_trend.occasion_palette > 0
    assert with_trend.total >= without.total


def _item(**kwargs):
    defaults = {
        "color": None,
        "color_hex": None,
        "pattern": "solid",
        "formality": "casual",
        "category": "top",
        "subcategory": None,
        "material": None,
        "occasion": None,
        "seasons": None,
        "times_worn": 0,
        "style_tags": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_wool_leather_texture_harmony():
    top = SimpleNamespace(material="wool", category="top", pattern="solid", formality="casual")
    bottom = SimpleNamespace(material="leather", category="bottom", pattern="solid", formality="casual")
    score, highlights, warnings = score_textures([top, bottom])
    assert score > 0.2
    assert any("texture" in h for h in highlights)


def test_silk_nylon_texture_clash():
    top = SimpleNamespace(material="silk", category="top", pattern="solid", formality="business")
    bottom = SimpleNamespace(material="nylon", category="bottom", pattern="solid", formality="casual")
    score, _, warnings = score_textures([top, bottom])
    assert score < 0
    assert warnings


def test_texture_rules_present_in_yaml():
    rules = texture_rules()
    assert "harmonious" in rules
    assert len(rules.get("harmonious", [])) >= 5
