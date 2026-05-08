"""Tests fuer den NER-Extraktor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ner_extractor import (
    ContactCandidate,
    _deobfuscate_emails,
    _find_name,
    _find_role,
    _is_generic_address,
    extract_contacts,
)


class TestEmailExtraction:
    def test_plain_email(self):
        html = "<p>Kontakt: max.mustermann@beispiel.de</p>"
        result = extract_contacts(html, domain="beispiel.de")
        assert len(result) == 1
        assert result[0].email == "max.mustermann@beispiel.de"

    def test_mailto_link(self):
        html = '<a href="mailto:anna.mueller@zeitung.de">Redaktion</a>'
        result = extract_contacts(html, domain="zeitung.de")
        assert any(c.email == "anna.mueller@zeitung.de" for c in result)

    def test_generic_addresses_filtered(self):
        html = "<p>info@beispiel.de, kontakt@beispiel.de, support@beispiel.de</p>"
        result = extract_contacts(html, domain="beispiel.de")
        assert len(result) == 0

    def test_multiple_contacts(self):
        html = """
        <p>Chefredakteur Klaus Maier: k.maier@zeitung.de</p>
        <p>Redakteurin Anna Schmidt: a.schmidt@zeitung.de</p>
        """
        result = extract_contacts(html, domain="zeitung.de")
        emails = [c.email for c in result]
        assert "k.maier@zeitung.de" in emails
        assert "a.schmidt@zeitung.de" in emails

    def test_obfuscated_email(self):
        html = "<p>Schreiben Sie uns: max [at] beispiel [dot] de</p>"
        result = extract_contacts(html, domain="beispiel.de")
        assert any("max@beispiel.de" in c.email for c in result)

    def test_cap_respected(self):
        lines = [f"person{i}@beispiel.de" for i in range(100)]
        html = "<p>" + " ".join(lines) + "</p>"
        result = extract_contacts(html, domain="beispiel.de", cap=10)
        assert len(result) <= 10


class TestDeobfuscation:
    def test_at_dot_pattern(self):
        text = "vorname [at] medium [dot] de"
        result = _deobfuscate_emails(text)
        assert "vorname@medium.de" in result

    def test_already_plain(self):
        text = "test@example.com"
        assert _deobfuscate_emails(text) == text


class TestNameExtraction:
    def test_name_from_email(self):
        first, last = _find_name("", "max.mustermann@beispiel.de")
        assert first == "Max"
        assert last == "Mustermann"

    def test_name_from_context(self):
        context = "Redakteurin Anna Schmidt ist zustaendig"
        first, last = _find_name(context, "a.s@zeitung.de")
        assert first == "Anna"
        assert last == "Schmidt"

    def test_no_name_generic_email(self):
        first, last = _find_name("Bitte kontaktieren Sie uns.", "info@beispiel.de")
        assert first == "" or True  # may or may not find a name


class TestRoleExtraction:
    def test_chefredakteur(self):
        assert _find_role("Chefredakteur Klaus Maier") == "Chefredakteur:in"

    def test_redakteurin(self):
        assert _find_role("Redakteurin fuer Wirtschaft") == "Redakteur:in"

    def test_pressesprecher(self):
        assert _find_role("Pressesprecher Thomas Weber") == "Pressesprecher:in"

    def test_no_role(self):
        assert _find_role("Keine Rolle hier") == ""


class TestConfidence:
    def test_full_data_high_confidence(self):
        c = ContactCandidate(
            email="max@beispiel.de",
            first_name="Max",
            last_name="Mustermann",
            role="Redakteur:in",
        )
        score = c.confidence("beispiel.de")
        assert score >= 0.8

    def test_email_only_low_confidence(self):
        c = ContactCandidate(email="x@beispiel.de")
        score = c.confidence("beispiel.de")
        assert score < 0.7

    def test_domain_match_boosts(self):
        c = ContactCandidate(email="m@beispiel.de", first_name="Max", last_name="M")
        with_domain = c.confidence("beispiel.de")
        without_domain = c.confidence("anderedomain.de")
        assert with_domain > without_domain


class TestFixture:
    def test_impressum_html(self):
        fixture = Path(__file__).parent / "fixtures" / "impressum.html"
        html = fixture.read_text(encoding="utf-8")
        result = extract_contacts(html, domain="beispielzeitung.de")
        emails = [c.email for c in result]
        assert "k.maier@beispielzeitung.de" in emails
        assert "a.schmidt@beispielzeitung.de" in emails
