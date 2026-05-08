"""
impact-story-builder — Stories nach der Proof-Chain-Methode.

Voll funktionsfaehig: rendert Markdown + HTML aus YAML-Input.
Brevo-Template-Output ist Skeleton fuer Phase 4.5.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import click
import yaml


@dataclass
class ProofPoint:
    metric: str
    qualitative: str
    source: str


@dataclass
class ImpactStory:
    headline: str
    output: ProofPoint
    outcome: ProofPoint
    impact: ProofPoint
    cta: str

    @classmethod
    def from_dict(cls, d: dict) -> "ImpactStory":
        return cls(
            headline=d["headline"],
            output=ProofPoint(**d["output"]),
            outcome=ProofPoint(**d["outcome"]),
            impact=ProofPoint(**d["impact"]),
            cta=d["cta"],
        )


def load_story(path: str) -> ImpactStory:
    with open(path, encoding="utf-8") as fh:
        return ImpactStory.from_dict(yaml.safe_load(fh))


def render_markdown(s: ImpactStory) -> str:
    return f"""# {s.headline}

## Was wir getan haben — Output

**{s.output.metric}**

> {s.output.qualitative}

*Verifikation: {s.output.source}*

## Was sich verändert hat — Outcome

**{s.outcome.metric}**

> {s.outcome.qualitative}

*Verifikation: {s.outcome.source}*

## Warum es zählt — Impact

**{s.impact.metric}**

> {s.impact.qualitative}

*Verifikation: {s.impact.source}*

---

{s.cta}
"""


def render_html(s: ImpactStory) -> str:
    css = (
        "body{font-family:system-ui,sans-serif;max-width:720px;margin:48px auto;padding:0 24px;"
        "line-height:1.65;color:#1a1d21}"
        "h1{font-size:2rem;line-height:1.15}"
        "h2{margin-top:32px;font-size:1.2rem;color:#00a86b}"
        "blockquote{border-left:3px solid #00a86b;background:#f6fdf9;padding:14px 20px;"
        "border-radius:6px;margin:14px 0;font-style:italic}"
        ".verif{color:#666;font-size:0.85em}"
        ".cta{margin-top:48px;padding:24px;background:#00a86b;color:white;border-radius:12px;text-align:center;font-weight:600}"
    )
    blocks = []
    for label, p in (("Was wir getan haben — Output", s.output),
                     ("Was sich verändert hat — Outcome", s.outcome),
                     ("Warum es zählt — Impact", s.impact)):
        blocks.append(
            f"<section><h2>{label}</h2>"
            f"<p><strong>{p.metric}</strong></p>"
            f"<blockquote>{p.qualitative}</blockquote>"
            f"<p class='verif'>Verifikation: {p.source}</p></section>"
        )
    return (
        f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>"
        f"<title>{s.headline}</title><style>{css}</style></head>"
        f"<body><h1>{s.headline}</h1>"
        + "".join(blocks)
        + f"<div class='cta'>{s.cta}</div></body></html>"
    )


def validate(s: ImpactStory) -> list[str]:
    """Strukturelle Validierung: Proof Chain ist nur intakt wenn alle Glieder gefuellt sind."""
    issues = []
    for label, p in (("output", s.output), ("outcome", s.outcome), ("impact", s.impact)):
        if not p.metric.strip():
            issues.append(f"{label}.metric ist leer")
        if not p.qualitative.strip():
            issues.append(f"{label}.qualitative ist leer — Beneficiary-Stimme fehlt")
        if not p.source.strip():
            issues.append(f"{label}.source ist leer — keine Verifikation")
    if not s.cta.strip():
        issues.append("cta ist leer")
    return issues


@click.command()
@click.argument("yaml_path", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option("--format", "fmt", type=click.Choice(["markdown", "html"]), default="markdown")
@click.option("--self-test", is_flag=True)
def main(yaml_path: str, fmt: str, self_test: bool) -> None:
    if self_test:
        sample_path = Path(__file__).resolve().parent / "examples" / "baeume-story.yaml"
        if not sample_path.exists():
            click.echo(f"✗ Self-Test: {sample_path} fehlt.", err=True)
            sys.exit(2)
        story = load_story(str(sample_path))
        issues = validate(story)
        if issues:
            click.echo("✗ Validierung schlug fehl:", err=True)
            for i in issues:
                click.echo(f"  - {i}", err=True)
            sys.exit(1)
        click.echo("✓ impact-story-builder: Self-Test OK")
        return

    if not yaml_path:
        click.echo("Bitte YAML-Pfad angeben oder --self-test.", err=True)
        sys.exit(2)

    story = load_story(yaml_path)
    issues = validate(story)
    if issues:
        click.echo("✗ Story unvollstaendig:", err=True)
        for i in issues:
            click.echo(f"  - {i}", err=True)
        sys.exit(1)

    if fmt == "markdown":
        click.echo(render_markdown(story))
    elif fmt == "html":
        click.echo(render_html(story))


if __name__ == "__main__":
    main()
