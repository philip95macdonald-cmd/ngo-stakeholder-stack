# impact-story-builder

Erzeugt Stories nach der **Proof-Chain-Methode** (Sopact): jede Story
verbindet Output → Outcome → Impact, jedes Glied mit quantitativem
Wert + qualitativer Stimme + Verifikationsquelle.

**Wichtig — ethische Grenze:** Dieses Tool **strukturiert** Stories aus
echten Daten. Es erzeugt keine generierten Quotes. Beneficiary-Stimmen
müssen vom Menschen kommen, dürfen nicht von einem LLM erfunden werden.

## CLI

```bash
# Beispiel-Story aus YAML rendern
python builder.py render examples/baeume-story.yaml --format markdown

# HTML-Render für Newsletter / Web-Embed
python builder.py render examples/baeume-story.yaml --format html

# Self-Test (rendert die Beispiel-Story und prüft Struktur)
python builder.py --self-test
```

## YAML-Format

```yaml
headline: "1.873 Bäume — und ein Wald, der zurückkommt"
output:
  metric: "1.873 Bäume gepflanzt im Jahr 2026"
  qualitative: |
    "Ich war 12 Jahre alt, als der Wald gerodet wurde. Heute pflanze
    ich mit meinen eigenen Kindern dort wieder Bäume."
    — Sarah K., Helferin im Aufforstungs-Projekt
  source: "Forstamt-Bestätigung 2026-03-15, Az. 442-2026"
outcome:
  metric: "Bodenfeuchtigkeit auf 38 % gestiegen (Mai 2025: 22 %)"
  qualitative: "..."
  source: "Messdaten Sensor-Station 7B, Universität Freiburg"
impact:
  metric: "Erste Rückkehr von 4 Reh-Familien dokumentiert"
  qualitative: "..."
  source: "Wildtier-Monitoring Frühling 2026, Naturschutzbund"
cta: "Hilf dem Wald wachsen — eine Spende von 5 € pflanzt einen weiteren Baum."
```

## Output-Formate

| Format | Verwendung |
|---|---|
| `markdown` | Internes Briefing, Newsletter-Texte für CMS |
| `html` | Web-Embed (eingebettetes CSS, Standalone) |
| `brevo-template` | Direkt in Brevo Drag&Drop-Editor importierbar |
