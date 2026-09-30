# -*- coding: utf-8 -*-
"""
Bewertung der Anzeigen nach den drei Kriterien:

  1. Entfernung von der Bezugsadresse HOME_ADDRESS  (Luftlinie, Haversine)
  2. passendes Skillset                             (Abgleich mit config.SKILLS)
  3. Lehrreich                                      (Lern-Signale minus Stumpfsinn)

Jedes Kriterium liefert 0.0 bis 1.0, der Gesamtscore ist die gewichtete Summe.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import config as cfg
from job import Job

# --------------------------------------------------------------------------
# Stichwortsuche mit Wortgrenzen (damit "r" nicht in jedem Wort trifft und
# "sql" nicht in "postgresql" haengenbleibt)
# --------------------------------------------------------------------------
_PATTERN_CACHE: Dict[str, "re.Pattern"] = {}


def _pattern(term: str) -> "re.Pattern":
    compiled = _PATTERN_CACHE.get(term)
    if compiled is None:
        escaped = re.escape(term.lower())
        if re.match(r"^\w", term) and re.search(r"\w$", term):
            source = r"\b" + escaped + r"\b"
        else:
            source = r"(?<!\w)" + escaped + r"(?!\w)"
        compiled = re.compile(source, re.IGNORECASE)
        _PATTERN_CACHE[term] = compiled
    return compiled


def contains(text: str, term: str) -> bool:
    return _pattern(term).search(text) is not None


# --------------------------------------------------------------------------
# 1. Entfernung
# --------------------------------------------------------------------------
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Luftlinie zwischen zwei Koordinaten in Kilometern."""
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * radius * math.asin(math.sqrt(a))


def distance_km(job: Job, home_lat: float, home_lon: float) -> Optional[float]:
    if job.latitude is None or job.longitude is None:
        return None
    return haversine_km(home_lat, home_lon, job.latitude, job.longitude)


def distance_score(km: Optional[float]) -> float:
    """Alle DISTANCE_HALF_LIFE_KM Kilometer halbiert sich der Score."""
    if km is None:
        return cfg.UNKNOWN_DISTANCE_SCORE
    return 0.5 ** (max(km, 0.0) / cfg.DISTANCE_HALF_LIFE_KM)


# --------------------------------------------------------------------------
# 2. Skillset
# --------------------------------------------------------------------------
def skill_match(job: Job) -> Tuple[float, List[str]]:
    title = job.title_lower
    text = job.text_lower
    total = 0.0
    hits: List[str] = []
    for skill, weight in cfg.SKILLS.items():
        if not contains(text, skill):
            continue
        factor = cfg.TITLE_BONUS if contains(title, skill) else 1.0
        total += weight * factor
        hits.append(skill)
    score = min(1.0, total / cfg.SKILL_SATURATION)
    hits.sort(key=lambda s: cfg.SKILLS.get(s, 0.0), reverse=True)
    return score, hits


# --------------------------------------------------------------------------
# 3. Lernwert
# --------------------------------------------------------------------------
_TECH_TERMS = [s for s in cfg.SKILLS
               if cfg.SKILLS[s] >= 1.0 and s not in
               ("deutsch", "englisch", "analytisch", "strukturiert",
                "eigenstaendig", "eigenständig", "excel")]


def learning_match(job: Job) -> Tuple[float, List[str], List[str]]:
    text = job.text_lower
    total = 0.0
    plus: List[str] = []
    minus: List[str] = []

    for term, weight in cfg.LEARNING_SIGNALS.items():
        if contains(text, term):
            total += weight
            plus.append(term)

    for term, weight in cfg.LEARNING_PENALTIES.items():
        if contains(text, term):
            total -= weight
            minus.append(term)

    # Viele verschiedene Technologien in einer Anzeige = viel zu lernen
    tech_count = sum(1 for term in _TECH_TERMS if contains(text, term))
    if tech_count:
        total += min(cfg.TECH_DIVERSITY_CAP, tech_count * cfg.TECH_DIVERSITY_BONUS)
        plus.append("%d Technologien genannt" % tech_count)

    score = max(0.0, min(1.0, total / cfg.LEARNING_SATURATION))
    return score, plus, minus


# --------------------------------------------------------------------------
# Fachgebiete (die Kategorien aus dem Suchprofil)
# --------------------------------------------------------------------------
def topics_of(job: Job) -> List[str]:
    text = job.text_lower
    found = [name for name, terms in cfg.TOPICS.items()
             if any(contains(text, term) for term in terms)]
    if not found:
        fallback = cfg.CATEGORY_TO_TOPIC.get(job.category_tag)
        if fallback:
            found = [fallback]
    return found


# --------------------------------------------------------------------------
# Ergebnis-Objekt
# --------------------------------------------------------------------------
@dataclass
class ScoredJob:
    job: Job
    total: float = 0.0
    km: Optional[float] = None
    distance: float = 0.0
    skill: float = 0.0
    learning: float = 0.0
    topics: List[str] = field(default_factory=list)
    skill_hits: List[str] = field(default_factory=list)
    learning_plus: List[str] = field(default_factory=list)
    learning_minus: List[str] = field(default_factory=list)
    precise: bool = True          # False = nur Stadtangabe, Entfernung geschaetzt
    is_new: bool = False

    def reason(self) -> str:
        """Ein Satz, warum die Stelle so weit oben steht."""
        parts = []
        if self.km is None:
            parts.append("ohne Ortsangabe")
        elif not self.precise:
            parts.append("Arbeitsort nur als 'Berlin' angegeben, geschaetzt %s km"
                         % _de(self.km, 1))
        elif self.km <= 6:
            parts.append("sehr nah an der Bezugsadresse (%s km)" % _de(self.km, 1))
        elif self.km <= 12:
            parts.append("gut erreichbar (%s km)" % _de(self.km, 1))
        else:
            parts.append("%s km entfernt" % _de(self.km, 1))
        if self.skill_hits:
            parts.append("trifft " + ", ".join(self.skill_hits[:4]))
        if self.learning_plus:
            parts.append("lehrreich durch " + ", ".join(self.learning_plus[:3]))
        if self.learning_minus:
            parts.append("Abzug wegen " + ", ".join(self.learning_minus[:2]))
        return "; ".join(parts) if parts else "Basistreffer im Suchprofil"


def _de(value: Optional[float], digits: int = 2) -> str:
    """Deutsche Zahlendarstellung mit Komma."""
    if value is None:
        return "k. A."
    return (("%." + str(digits) + "f") % value).replace(".", ",")


def score_job(job: Job, home_lat: float, home_lon: float,
              new_ids: Optional[set] = None) -> ScoredJob:
    km = distance_km(job, home_lat, home_lon)
    d_score = distance_score(km)
    s_score, s_hits = skill_match(job)
    l_score, l_plus, l_minus = learning_match(job)

    total = (cfg.WEIGHT_DISTANCE * d_score
             + cfg.WEIGHT_SKILL * s_score
             + cfg.WEIGHT_LEARNING * l_score)

    return ScoredJob(
        job=job,
        total=total,
        km=km,
        distance=d_score,
        skill=s_score,
        learning=l_score,
        topics=topics_of(job),
        skill_hits=s_hits,
        learning_plus=l_plus,
        learning_minus=l_minus,
        precise=job.location_precise,
        is_new=bool(new_ids) and job.id in new_ids,
    )


def rank(jobs, home_lat: float, home_lon: float,
         new_ids: Optional[set] = None) -> List[ScoredJob]:
    """Alle Jobs bewerten und absteigend nach Gesamtscore sortieren."""
    scored = [score_job(job, home_lat, home_lon, new_ids) for job in jobs]
    scored.sort(key=lambda s: (s.total, s.skill, -(s.km if s.km is not None else 99)),
                reverse=True)
    return scored
