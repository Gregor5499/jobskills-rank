# -*- coding: utf-8 -*-
"""
Erzeugt den Markdown-Report: nummerierte Top-10-Liste mit Links auf die
jeweilige Stellenanzeige, dazu eine Kurzuebersicht und die Methodik.
"""

import os
from datetime import datetime
from typing import List, Optional

import config as cfg
from scoring import ScoredJob


def _de(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "k. A."
    return (("%." + str(digits) + "f") % value).replace(".", ",")


def _escape(text: str) -> str:
    """Markdown-Sonderzeichen in Titeln entschaerfen."""
    for char in ("[", "]", "|"):
        text = text.replace(char, "\\" + char)
    return text.replace("\n", " ").strip()


def _km(item: ScoredJob) -> str:
    """Entfernung mit Kennzeichnung, wenn nur die Stadt bekannt ist."""
    if item.km is None:
        return "k. A."
    if not item.precise:
        return "ca. %s km \\*" % _de(item.km, 1)
    return "%s km" % _de(item.km, 1)


def _link(item: ScoredJob) -> str:
    title = _escape(item.job.title) or "Stellenanzeige"
    if item.job.redirect_url:
        return "[%s](%s)" % (title, item.job.redirect_url)
    return title


def build_markdown(scored: List[ScoredJob], stats: dict) -> str:
    now = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
    top = scored[:cfg.TOP_N]
    rest = scored[cfg.TOP_N:cfg.SHORTLIST_N]

    lines: List[str] = []
    lines.append("# Top %d Werkstudentenstellen in Berlin" % cfg.TOP_N)
    lines.append("")
    lines.append("_Stand: %s &middot; Bezugsadresse: %s_" % (now, cfg.HOME_ADDRESS))
    lines.append("")
    lines.append("| Kennzahl | Wert |")
    lines.append("| --- | --- |")
    lines.append("| Abgefragte Adzuna-Kategorien | %d |" % len(cfg.ADZUNA_CATEGORIES))
    lines.append("| Rohtreffer der API | %d |" % stats.get("raw", 0))
    lines.append("| Nach Werkstudenten- und Fachfilter | %d |" % stats.get("kept", 0))
    lines.append("| Davon neu seit dem letzten Lauf | %d |" % stats.get("new", 0))
    lines.append("| Suchradius / Alter der Anzeigen | %d km / max. %d Tage |"
                 % (cfg.SEARCH_RADIUS_KM, cfg.MAX_DAYS_OLD))
    lines.append("")

    if not top:
        lines.append("> Keine passenden Anzeigen gefunden. Suchprofil in `config.py` lockern")
        lines.append("> (z. B. `MAX_DAYS_OLD` erhoehen oder `TOPICS` erweitern).")
        lines.append("")
        return "\n".join(lines)

    # ---- Uebersicht --------------------------------------------------
    lines.append("## Uebersicht")
    lines.append("")
    lines.append("| # | Stelle | Firma | Entfernung | Score |")
    lines.append("| --: | --- | --- | --: | --: |")
    for index, item in enumerate(top, start=1):
        flag = " **NEU**" if item.is_new else ""
        lines.append("| %d | %s%s | %s | %s | %s |" % (
            index, _link(item), flag, _escape(item.job.company),
            _km(item), _de(item.total, 2)))
    lines.append("")
    if any(not item.precise for item in top):
        lines.append("\\* Adzuna kennt hier nur \"Berlin\" und setzt die Anzeige auf den "
                     "Stadtmittelpunkt - die Entfernung ist eine Schaetzung, kein "
                     "Firmensitz.")
        lines.append("")

    # ---- Details -----------------------------------------------------
    lines.append("## Die Plaetze im Detail")
    lines.append("")
    for index, item in enumerate(top, start=1):
        job = item.job
        lines.append("### %d. %s%s" % (index, _link(item), "  `NEU`" if item.is_new else ""))
        lines.append("")
        lines.append("**%s** &middot; %s &middot; %s Luftlinie &middot; **Score %s / 1,00**" % (
            _escape(job.company), _escape(job.location), _km(item), _de(item.total, 2)))
        lines.append("")
        lines.append("| Kriterium | Bewertung | Grundlage |")
        lines.append("| --- | --: | --- |")
        lines.append("| Entfernung (%d %%) | %s | %s ab %s%s |" % (
            round(cfg.WEIGHT_DISTANCE * 100), _de(item.distance, 2),
            _km(item), cfg.HOME_ADDRESS,
            "" if item.precise else ", nur Stadtangabe"))
        lines.append("| Skillset (%d %%) | %s | %s |" % (
            round(cfg.WEIGHT_SKILL * 100), _de(item.skill, 2),
            ", ".join(item.skill_hits[:8]) if item.skill_hits else "keine Treffer"))
        lines.append("| Lernwert (%d %%) | %s | %s |" % (
            round(cfg.WEIGHT_LEARNING * 100), _de(item.learning, 2),
            ", ".join(item.learning_plus[:6]) if item.learning_plus else "keine Signale"))
        lines.append("")
        details = []
        details.append("- **Fachgebiete:** %s" % (", ".join(item.topics) or "-"))
        details.append("- **Adzuna-Kategorie:** %s" % (job.category_label or "-"))
        details.append("- **Vertrag:** %s" % (job.contract_time.replace("_", " ") or "keine Angabe"))
        details.append("- **Gehalt:** %s" % job.salary_text)
        details.append("- **Veroeffentlicht:** %s" % job.created_date)
        if item.learning_minus:
            details.append("- **Abzuege:** %s" % ", ".join(item.learning_minus))
        details.append("- **Warum hier:** %s" % item.reason())
        if job.redirect_url:
            details.append("- **Anzeige:** <%s>" % job.redirect_url)
        lines.extend(details)
        lines.append("")
        snippet = job.description.strip()
        if snippet:
            if len(snippet) > 400:
                snippet = snippet[:400].rsplit(" ", 1)[0] + " ..."
            lines.append("> %s" % snippet.replace("\n", " "))
            lines.append("")

    # ---- Kurzliste ---------------------------------------------------
    if rest:
        lines.append("## Plaetze %d bis %d" % (cfg.TOP_N + 1, cfg.TOP_N + len(rest)))
        lines.append("")
        for index, item in enumerate(rest, start=cfg.TOP_N + 1):
            lines.append("%d. %s &middot; %s &middot; %s &middot; Score %s" % (
                index, _link(item), _escape(item.job.company),
                _km(item), _de(item.total, 2)))
        lines.append("")

    # ---- Methodik ----------------------------------------------------
    lines.append("## Wie das Ranking zustande kommt")
    lines.append("")
    lines.append("Gesamtscore = %s x Entfernung + %s x Skillset + %s x Lernwert"
                 % (_de(cfg.WEIGHT_DISTANCE), _de(cfg.WEIGHT_SKILL),
                    _de(cfg.WEIGHT_LEARNING)))
    lines.append("")
    lines.append("- **Entfernung:** Luftlinie (Haversine) von %s zu den Koordinaten der "
                 "Anzeige. Alle %.0f km halbiert sich der Teilscore; ohne Koordinaten "
                 "gibt es den neutralen Wert %s." % (
                     cfg.HOME_ADDRESS, cfg.DISTANCE_HALF_LIFE_KM,
                     _de(cfg.UNKNOWN_DISTANCE_SCORE, 2)))
    lines.append("- **Skillset:** gewichteter Abgleich mit dem Profil in `config.py`; "
                 "Treffer im Titel zaehlen %sfach." % _de(cfg.TITLE_BONUS, 1))
    lines.append("- **Lernwert:** Signale wie Mentoring, Abschlussarbeit oder eigene "
                 "Projekte plus die Zahl verschiedener Technologien, abzueglich "
                 "Stumpfsinn wie Dateneingabe oder Kaltakquise.")
    lines.append("")
    lines.append("Grenzen der Datenquelle: Adzuna liefert je Anzeige nur 500 Zeichen "
                 "Beschreibung und bei vielen Anzeigen keinen genauen Arbeitsort. "
                 "Skill- und Lernwert beruhen also auf einem Textausschnitt - die "
                 "vollstaendige Anzeige lohnt sich vor der Bewerbung immer.")
    lines.append("")
    lines.append("_Erzeugt mit `python/main.py` &middot; Datenquelle: Adzuna API (%s)_"
                 % cfg.COUNTRY.upper())
    lines.append("")
    return "\n".join(lines)


def write_report(markdown: str, base_dir: str) -> List[str]:
    """Schreibt einen Zeitstempel-Report und ueberschreibt top10_aktuell.md."""
    report_dir = os.path.join(base_dir, cfg.REPORT_DIR)
    os.makedirs(report_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    dated = os.path.join(report_dir, "top10_werkstudent_berlin_%s.md" % stamp)
    latest = os.path.join(report_dir, cfg.LATEST_REPORT)
    for path in (dated, latest):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    return [dated, latest]
