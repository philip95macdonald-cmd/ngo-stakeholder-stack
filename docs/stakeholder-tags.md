# Stakeholder-Tag-Konvention

Eine zentrale Stelle, wo wir die Tag-Sprache festschreiben — damit alle
Tools, alle Brevo-Templates und alle Reports konsistent mit denselben
Tags arbeiten.

## Format

`<präfix>:<wert>` — kleinbuchstaben, Bindestrich-getrennt für Mehrwort,
kein Leerzeichen, ASCII-only.

Beispiele:
```
stakeholder:journalist
stakeholder:politiker
stakeholder:spender:major
party:buendnis-90-die-gruenen
parliament:bundestag
parliament:landtag-bw
parliament:eu
region:de
region:bw
region:eu
topic:klimaschutz
topic:energiewende
lang:de
lang:en
consent:newsletter
consent:fundraising-mail
consent:event-invite
```

## Präfixe

| Präfix | Bedeutung | Pflicht? |
|---|---|---|
| `stakeholder:` | Welche Rolle spielt die Person? | ja, mind. 1 |
| `topic:` | Welches Thema interessiert sie? | optional, beliebig viele |
| `region:` | Wo wirkt sie / wo ist sie geografisch? | optional |
| `party:` | Parteizugehörigkeit (nur bei Politiker:innen) | bei Politik |
| `parliament:` | Parlament-Zugehörigkeit | bei Politik |
| `lang:` | Bevorzugte Sprache | empfohlen |
| `consent:` | Welchen Kommunikations-Kanälen wurde zugestimmt? | DSGVO-Pflicht |

## Stakeholder-Hierarchie (Vollständige Liste)

| Tag | Bedeutung |
|---|---|
| `stakeholder:journalist` | Pressekontakt |
| `stakeholder:politiker` | Mandats- oder Funktionsträger:in |
| `stakeholder:wissenschaft` | Forscher:in / Institut |
| `stakeholder:spender:onetime` | Einmalspender:in |
| `stakeholder:spender:recurring` | Dauerspender:in |
| `stakeholder:spender:major` | Großspender:in (Schwellwert konfigurierbar) |
| `stakeholder:spender:foundation` | Stiftung |
| `stakeholder:spender:corporate` | CSR-Partner |
| `stakeholder:volunteer` | Ehrenamtliche:r |
| `stakeholder:beneficiary` | Empfänger:in der Hilfe (DSGVO-sensibel!) |
| `stakeholder:member` | Vereinsmitglied (e.V.) |
| `stakeholder:alliance` | Partner-NGO |
| `stakeholder:authority` | Behörde / Aufsicht |
| `stakeholder:funder` | Förder-Geber (DSEE, EU, BMZ) |
| `stakeholder:petition_signer` | Hat Petition unterzeichnet |
| `stakeholder:beirat` | Beirat / Vorstand / Aufsichtsrat |

## Consent-Tags (Pflicht pro Kanal)

| Tag | Wann setzen |
|---|---|
| `consent:newsletter` | Doppelt opted-in für Newsletter |
| `consent:fundraising-mail` | Doppelt opted-in für Spendenaufrufe |
| `consent:event-invite` | Doppelt opted-in für Event-Einladungen |
| `consent:advocacy-mail` | Hat Petition unterzeichnet ODER explizit für Mobilisierungs-Mails opted-in |
| `consent:photo-usage` | Beneficiary hat Bildrechte schriftlich erteilt |

**Wichtig:** Ein Tag wird nicht durch Einlesen einer Liste implizit gesetzt.
Consent muss aktiv eingeholt sein, dokumentiert in Brevo-Custom-Field
`CONSENT_DATE_<channel>`.

## Lifecycle-Tags (für Spender)

| Tag | Bedeutung |
|---|---|
| `lifecycle:lead` | Hat sich für Newsletter angemeldet, noch nicht gespendet |
| `lifecycle:firstdonor` | Erste Spende erfolgt |
| `lifecycle:active` | In den letzten 12 Monaten gespendet |
| `lifecycle:lapsed` | 12–24 Monate inaktiv (Reaktivierungs-Kampagne wert) |
| `lifecycle:churned` | &gt;24 Monate inaktiv (DSGVO-Lösch-Kandidat) |

## Was du nicht tun solltest

- ❌ Stakeholder-Tags in Custom-Fields packen (geht beides, aber Tags sind besser indizierbar)
- ❌ Consent-Tags in Brevo manuell setzen, ohne Quell-Beleg im Audit-Log
- ❌ Beneficiary-Tags ohne explizite Pseudonymisierung verwenden
- ❌ Tag-Werte mit Leerzeichen oder Umlauten — Brevo-API ist da empfindlich
