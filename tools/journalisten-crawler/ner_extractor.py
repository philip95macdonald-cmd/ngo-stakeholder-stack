"""
Kontakt-Extraktion aus HTML-Seiten.

Strategie (Reihenfolge der Verlaesslichkeit):
  1. E-Mail-Regex — sehr zuverlässig
  2. Heuristische Name-Erkennung (Vor + Nachname in Naehe der E-Mail)
  3. Rollen-Erkennung via Keyword-Liste (DE + EN)
  4. Optionaler spaCy-NER-Fallback (nur wenn Package installiert)

Keine externen ML-Calls — laeuft offline.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex-Patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Obfuscation patterns: vorname [at] medium [dot] de
_EMAIL_OBFUSCATED_RE = re.compile(
    r"([a-zA-Z0-9._%+\-]+)\s*[\[\(]?\s*(?:at|@)\s*[\]\)]?\s*"
    r"([a-zA-Z0-9.\-]+)\s*[\[\(]?\s*(?:dot|\.)\s*[\]\)]?\s*([a-zA-Z]{2,})",
    re.IGNORECASE,
)

# Single capitalised word
_CAP_WORD_RE = re.compile(
    r"\b([A-ZÄÖÜ][a-zäöüß]{1,25}(?:-[A-ZÄÖÜ][a-zäöüß]{1,25})?)\b"
)

# Roles — DE and EN, ordered by specificity
_ROLE_KEYWORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"chefredakteur(?:in)?", re.I), "Chefredakteur:in"),
    (re.compile(r"stellvertretende[rs]?\s+chefredakteur(?:in)?", re.I), "Stv. Chefredakteur:in"),
    (re.compile(r"pressesprecher(?:in)?", re.I), "Pressesprecher:in"),
    (re.compile(r"pressekontakt", re.I), "Pressekontakt"),
    (re.compile(r"mediensprechere?(?:in)?", re.I), "Mediensprecher:in"),
    (re.compile(r"kommunikation(?:sleiter(?:in)?)?", re.I), "Kommunikation"),
    (re.compile(r"redaktionsleiter(?:in)?", re.I), "Redaktionsleiter:in"),
    (re.compile(r"ressortleiter(?:in)?", re.I), "Ressortleiter:in"),
    (re.compile(r"leitende[rs]?\s+redakteur(?:in)?", re.I), "Leitende:r Redakteur:in"),
    (re.compile(r"redakteur(?:in)?", re.I), "Redakteur:in"),
    (re.compile(r"editor.?in.?chief", re.I), "Editor-in-chief"),
    (re.compile(r"editor", re.I), "Editor"),
    (re.compile(r"journalist(?:in)?", re.I), "Journalist:in"),
    (re.compile(r"freie[rs]?\s+(?:journalist(?:in)?|mitarbeiter(?:in)?)", re.I), "Freie:r"),
    (re.compile(r"volontär(?:in)?", re.I), "Volontär:in"),
    (re.compile(r"korrespondent(?:in)?", re.I), "Korrespondent:in"),
    (re.compile(r"head\s+of\s+(?:communications?|pr|press)", re.I), "Head of Comms"),
    (re.compile(r"press\s+contact", re.I), "Press Contact"),
    (re.compile(r"public\s+relations", re.I), "PR"),
]

# HTML elements typically used for contact sections
_CONTACT_SECTION_SELECTORS = [
    "section.presse", "section.press", "section.kontakt", "section.contact",
    "div.presse", "div.press", "div.kontakt", "div.contact",
    "div.redaktion", "div.editorial", "div.impressum",
    "#presse", "#press", "#kontakt", "#contact", "#redaktion",
    ".presse-kontakt", ".press-contact", ".redaktion",
]


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ContactCandidate:
    email: str
    first_name: str = ""
    last_name: str = ""
    role: str = ""
    source_url: str = ""
    context: str = ""  # raw text snippet for debugging

    def confidence(self, domain: str = "") -> float:
        score = 0.4  # base for having an email
        if self.first_name and self.last_name:
            score += 0.25
        elif self.first_name or self.last_name:
            score += 0.10
        if self.role:
            score += 0.20
        if domain and domain in self.email:
            score += 0.15
        return min(score, 1.0)


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def extract_contacts(
    html: str,
    source_url: str = "",
    domain: str = "",
    cap: int = 50,
) -> list[ContactCandidate]:
    """
    Extrahiert Kontaktkandidaten aus HTML. Gibt maximal `cap` Eintraege zurueck.
    """
    soup = BeautifulSoup(html, "lxml")
    _remove_noise(soup)
    text = soup.get_text(separator="\n")
    candidates: list[ContactCandidate] = []

    # Deduplicate emails
    seen_emails: set[str] = set()

    # Try targeted contact sections first
    section_candidates = _extract_from_sections(soup, source_url, domain)
    for c in section_candidates:
        key = c.email.lower()
        if key not in seen_emails:
            seen_emails.add(key)
            candidates.append(c)

    # Fall back to full-text extraction
    if len(candidates) < cap:
        full_text_candidates = _extract_from_text(text, source_url, domain)
        for c in full_text_candidates:
            key = c.email.lower()
            if key not in seen_emails and len(candidates) < cap:
                seen_emails.add(key)
                candidates.append(c)

    # spaCy NER enhancement (optional, silently skipped if not installed)
    if len(candidates) < 2:
        _try_spacy_enhance(candidates, text)

    return candidates[:cap]


def _remove_noise(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                               "noscript", "iframe", "aside"]):
        tag.decompose()
    # Expand mailto: links so the email appears in plain text
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and _EMAIL_RE.match(email):
                tag.string = email


def _extract_from_sections(
    soup: BeautifulSoup, source_url: str, domain: str
) -> list[ContactCandidate]:
    candidates: list[ContactCandidate] = []
    for sel in _CONTACT_SECTION_SELECTORS:
        for elem in soup.select(sel):
            text = elem.get_text(separator="\n")
            candidates.extend(_parse_contacts_from_text(text, source_url, domain))
        if candidates:
            break
    return candidates


def _extract_from_text(text: str, source_url: str, domain: str) -> list[ContactCandidate]:
    return _parse_contacts_from_text(text, source_url, domain)


def _parse_contacts_from_text(
    text: str, source_url: str, domain: str
) -> list[ContactCandidate]:
    candidates: list[ContactCandidate] = []

    # Normalise obfuscated emails first
    text = _deobfuscate_emails(text)

    for m in _EMAIL_RE.finditer(text):
        email = m.group(0).lower()
        # Skip obvious non-persons
        if _is_generic_address(email):
            continue

        # Context window (200 chars before + 200 after)
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        context = text[start:end]

        first, last = _find_name(context, email)
        role = _find_role(context)

        candidates.append(
            ContactCandidate(
                email=email,
                first_name=first,
                last_name=last,
                role=role,
                source_url=source_url,
                context=context[:150],
            )
        )

    return candidates


def _deobfuscate_emails(text: str) -> str:
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        return f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
    return _EMAIL_OBFUSCATED_RE.sub(_replace, text)


def _is_generic_address(email: str) -> bool:
    generic_prefixes = {
        "info", "kontakt", "contact", "noreply", "no-reply",
        "office", "mail", "post", "support", "feedback",
        "newsletter", "webmaster", "admin", "service",
        "hallo", "hello", "impressum", "datenschutz",
    }
    prefix = email.split("@")[0].lower()
    return prefix in generic_prefixes


def _find_name(context: str, email: str) -> tuple[str, str]:
    # Try to infer from email first (vorname.nachname@...)
    local = email.split("@")[0]
    parts = re.split(r"[.\-_]", local)
    if len(parts) == 2 and all(len(p) >= 2 for p in parts):
        first = parts[0].capitalize()
        last = parts[1].capitalize()
        if _looks_like_name(first) and _looks_like_name(last):
            return first, last

    # Find consecutive non-noise capitalised word pairs
    matches = [(m.group(1), m.start(), m.end()) for m in _CAP_WORD_RE.finditer(context)]
    for i in range(len(matches) - 1):
        first, _, end1 = matches[i]
        last, start2, _ = matches[i + 1]
        # Words must be directly adjacent (at most one space/hyphen between them)
        gap = context[end1:start2]
        if len(gap) > 2:
            continue
        if _is_noise_word(first) or _is_noise_word(last):
            continue
        return first, last
    return "", ""


_NOISE_WORDS = {
    "Die", "Der", "Das", "Für", "Mit", "Und", "Oder", "Bei", "Auf",
    "Dem", "Den", "Des", "Ein", "Eine", "Einen", "Einer", "Eines",
    "Kontakt", "Presse", "Mail", "Email", "Tel", "Fax", "Bitte",
    "Redaktion", "Redakteur", "Redakteurin", "Chefredakteur", "Chefredakteurin",
    "Pressesprecher", "Pressesprecherin", "Kommunikation",
    "Impressum", "More", "Read", "Click", "Here",
    "Newsletter", "Anmeldung", "Abonnieren", "Download", "Mehr",
    "Von", "Alle", "Über", "Zum", "Zur", "This", "That",
    "Journalist", "Journalistin", "Korrespondent", "Korrespondentin",
}


def _is_noise_word(word: str) -> bool:
    return word in _NOISE_WORDS or len(word) < 2


def _looks_like_name(s: str) -> bool:
    return bool(re.match(r"^[A-ZÄÖÜ][a-zäöüß]{1,}$", s))


def _find_role(context: str) -> str:
    for pattern, label in _ROLE_KEYWORDS:
        if pattern.search(context):
            return label
    return ""


def _try_spacy_enhance(candidates: list[ContactCandidate], text: str) -> None:
    try:
        import spacy  # type: ignore[import-not-found]
    except ImportError:
        return
    try:
        nlp = spacy.load("de_core_news_sm")
        doc = nlp(text[:100_000])
        person_names = [
            ent.text for ent in doc.ents
            if ent.label_ == "PER" and " " in ent.text
        ]
        for c in candidates:
            if not c.first_name and person_names:
                name_parts = person_names[0].split(None, 1)
                if len(name_parts) == 2:
                    c.first_name, c.last_name = name_parts
    except Exception as exc:
        log.debug("spaCy NER failed (non-fatal): %s", exc)
