from types import SimpleNamespace

from app.fashion.color_harmony import pair_color_score_names
from app.fashion.matcher import FashionMatcher
from app.fashion.context import MatchContext


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
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_classic_navy_white_scores_high():
    assert pair_color_score_names("navy", "white") >= 0.8


def test_red_green_clash_scores_low():
    assert pair_color_score_names("red", "green") <= -0.5


def test_sneakers_with_business_suit_penalized():
    top = _item(category="top", formality="business", color="white", color_hex="#ffffff")
    bottom = _item(category="bottom", formality="business", color="charcoal", color_hex="#333333")
    shoes = _item(category="footwear", subcategory="sneakers", formality="casual", color="white")

    breakdown = FashionMatcher.score_outfit([top, bottom, shoes], MatchContext(occasion="work"))
    assert breakdown.footwear < 0
    assert any("sneakers" in w.lower() or "casual" in w.lower() for w in breakdown.warnings)


def test_pattern_clash_stripes_and_plaid():
    top = _item(category="top", pattern="striped", color="blue")
    bottom = _item(category="bottom", pattern="plaid", color="navy")

    breakdown = FashionMatcher.score_outfit([top, bottom], MatchContext())
    assert breakdown.pattern < 0
    assert any("striped" in w for w in breakdown.warnings)


def test_formality_coherent_outfit_scores_higher():
    coherent_top = _item(category="top", formality="business", color="white", color_hex="#ffffff")
    coherent_bottom = _item(category="bottom", formality="business", color="navy", color_hex="#001f3f")
    coherent_shoes = _item(category="footwear", subcategory="loafers", formality="business", color="black")

    loud_top = _item(category="top", formality="loungewear", pattern="graphic", color="orange", color_hex="#ff5a00")
    same_bottom = coherent_bottom
    same_shoes = coherent_shoes

    coherent = FashionMatcher.score_outfit(
        [coherent_top, coherent_bottom, coherent_shoes],
        MatchContext(occasion="work"),
    )
    incoherent = FashionMatcher.score_outfit(
        [loud_top, same_bottom, same_shoes],
        MatchContext(occasion="work"),
    )
    assert coherent.total > incoherent.total
