from app.fashion.knowledge import (
    classic_color_pairings,
    knowledge_version,
    load_knowledge,
    texture_rules,
)
from app.fashion.matcher import FashionMatcher
from app.fashion.context import MatchContext
from app.fashion.style_rules import score_textures
from types import SimpleNamespace


def test_knowledge_yaml_loads():
    data = load_knowledge()
    assert data["meta"]["version"] >= 2
    assert knowledge_version() >= 2
    assert len(classic_color_pairings()) >= 20


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
