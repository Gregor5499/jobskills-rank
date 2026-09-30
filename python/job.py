# -*- coding: utf-8 -*-
"""
Job - Gegenstueck zu Job.java.

Im Java-Code enthielt die Klasse nur die 'description', weil nur die Skills
gezaehlt wurden. Fuer das Ranking brauchen wir mehr Felder: Ort, Koordinaten,
Kategorie und vor allem die redirect_url fuer den Link im Report.
"""

import html
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _text(value: Any) -> str:
    """Adzuna liefert gelegentlich None oder HTML-Entities."""
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def _number(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class Job:
    id: str = ""
    title: str = ""
    description: str = ""
    company: str = ""
    location: str = ""
    area: List[str] = field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category_label: str = ""
    category_tag: str = ""
    contract_time: str = ""
    contract_type: str = ""
    created: str = ""
    redirect_url: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    # -- Mapping aus dem JSON der API (in Java uebernahm das Gson) ----------
    @classmethod
    def from_api(cls, raw: Dict[str, Any]) -> "Job":
        category = raw.get("category") or {}
        company = raw.get("company") or {}
        location = raw.get("location") or {}
        return cls(
            id=_text(raw.get("id")),
            title=_text(raw.get("title")),
            description=_text(raw.get("description")),
            company=_text(company.get("display_name")) or "unbekannt",
            location=_text(location.get("display_name")) or "Berlin",
            area=[_text(part) for part in (location.get("area") or [])],
            latitude=_number(raw.get("latitude")),
            longitude=_number(raw.get("longitude")),
            category_label=_text(category.get("label")),
            category_tag=_text(category.get("tag")),
            contract_time=_text(raw.get("contract_time")),
            contract_type=_text(raw.get("contract_type")),
            created=_text(raw.get("created")),
            redirect_url=_text(raw.get("redirect_url")),
            salary_min=_number(raw.get("salary_min")),
            salary_max=_number(raw.get("salary_max")),
            raw=raw,
        )

    # -- Hilfsmethoden fuer die Bewertung ----------------------------------
    @property
    def location_precise(self) -> bool:
        """Adzuna setzt Anzeigen ohne Adresse auf den Stadt-Mittelpunkt.

        'area' verraet die Genauigkeit: ['Deutschland', 'Berlin'] heisst nur
        'irgendwo in Berlin', erst ab drei Ebenen steht ein echter Ortsteil
        dahinter. Entsprechend ist die Entfernung dann nur eine Schaetzung.
        """
        return len(self.area) >= 3

    @property
    def title_lower(self) -> str:
        return self.title.lower()

    @property
    def text_lower(self) -> str:
        return (self.title + "\n" + self.description).lower()

    @property
    def created_date(self) -> str:
        """'2026-08-21T10:12:33Z' -> '21.08.2026'"""
        if len(self.created) >= 10:
            y, m, d = self.created[0:4], self.created[5:7], self.created[8:10]
            if y.isdigit() and m.isdigit() and d.isdigit():
                return "%s.%s.%s" % (d, m, y)
        return "unbekannt"

    @property
    def salary_text(self) -> str:
        if self.salary_min and self.salary_max:
            if abs(self.salary_min - self.salary_max) < 1:
                return "%s EUR/Jahr" % format(int(self.salary_min), ",d").replace(",", ".")
            return "%s - %s EUR/Jahr" % (
                format(int(self.salary_min), ",d").replace(",", "."),
                format(int(self.salary_max), ",d").replace(",", "."),
            )
        return "keine Angabe"
