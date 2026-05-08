"""Tests fuer den impact-story-builder."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import builder  # noqa: E402


def _good_story() -> builder.ImpactStory:
    return builder.ImpactStory(
        headline="Test",
        output=builder.ProofPoint(metric="100 Beispiele", qualitative="Quote", source="Q1"),
        outcome=builder.ProofPoint(metric="50% besser", qualitative="Quote", source="Q2"),
        impact=builder.ProofPoint(metric="System verändert", qualitative="Quote", source="Q3"),
        cta="Spende!",
    )


def test_validate_accepts_complete_story() -> None:
    assert builder.validate(_good_story()) == []


def test_validate_flags_missing_qualitative() -> None:
    s = _good_story()
    s.outcome = builder.ProofPoint(metric="X", qualitative="", source="Y")
    issues = builder.validate(s)
    assert any("qualitative" in i for i in issues)


def test_render_markdown_includes_proof_chain() -> None:
    md = builder.render_markdown(_good_story())
    assert "Output" in md
    assert "Outcome" in md
    assert "Impact" in md
    assert "Spende!" in md


def test_render_html_self_contained() -> None:
    html = builder.render_html(_good_story())
    assert "<html" in html
    assert "<style>" in html
    assert "</html>" in html


def test_load_story_from_example() -> None:
    sample = HERE.parents[1] / "examples" / "baeume-story.yaml"
    s = builder.load_story(str(sample))
    assert "Bäume" in s.headline
    assert builder.validate(s) == []
