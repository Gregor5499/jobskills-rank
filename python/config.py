# -*- coding: utf-8 -*-
"""
Konfiguration - alle Stellschrauben an einem Ort.

Hier stehen Zugangsdaten, Suchprofil, Kategorien, Skillset und die Gewichte
der Bewertung. Wer das Ranking veraendern will, aendert nur diese Datei.
"""

import os

# --------------------------------------------------------------------------
# Adzuna Zugang - wird ausschliesslich aus Umgebungsvariablen gelesen,
# damit keine Zugangsdaten im Repository landen:
#   export ADZUNA_APP_ID=...   export ADZUNA_APP_KEY=...
# Kostenlose Keys: https://developer.adzuna.com/
# --------------------------------------------------------------------------
APP_ID = os.getenv("ADZUNA_APP_ID", "")
APP_KEY = os.getenv("ADZUNA_APP_KEY", "")

COUNTRY = "de"
BASE_URL = "https://api.adzuna.com/v1/api/jobs/" + COUNTRY

RESULTS_PER_PAGE = 50      # Adzuna deckelt bei 50 (der Java-Code fragte 100 an)
MAX_PAGES = 5              # wie im Java-Code: 5 Seiten pro Suche
MAX_DAYS_OLD = 30          # nur halbwegs frische Anzeigen
SEARCH_RADIUS_KM = 30      # Umkreis um "where"
REQUEST_PAUSE = 0.4        # Pause zwischen Requests, damit Adzuna nicht dichtmacht

# --------------------------------------------------------------------------
# Suchprofil
# --------------------------------------------------------------------------
WHERE = "Berlin"
WHAT_OR = "Werkstudent Werkstudentin Werkstudierende Working Student"

# Eine Anzeige zaehlt nur als Werkstudentenstelle, wenn einer dieser Begriffe
# im Titel oder in der Beschreibung auftaucht.
WERKSTUDENT_TERMS = ("werkstudent", "werkstudentin", "werkstudierende",
                     "working student", "studentische hilfskraft", "shk")

# Anzeigen mit diesen Begriffen im Titel fliegen raus (falsche Trefferklasse).
TITLE_BLOCKLIST = ("pflege", "reinigung", "kellner", "barkeeper", "fahrer",
                   "security", "verkaeufer", "verkäufer", "kasse", "promoter")

# --------------------------------------------------------------------------
# Wohnort - Basis fuer die Entfernungsberechnung
# Standard ist der Berliner Alexanderplatz. Die eigene Adresse wird per
# Umgebungsvariable gesetzt (bleibt so privat) und mit  --geocode  einmalig
# ueber OpenStreetMap/Nominatim exakt aufgeloest (Ergebnis wird gecached):
#   export HOME_ADDRESS="Musterstr. 1, 10115 Berlin"
# --------------------------------------------------------------------------
HOME_ADDRESS = os.getenv("HOME_ADDRESS", "Alexanderplatz, 10178 Berlin")
HOME_LAT = float(os.getenv("HOME_LAT", "52.5219"))
HOME_LON = float(os.getenv("HOME_LON", "13.4132"))

# --------------------------------------------------------------------------
# Kategorien
# Links: Adzuna-Kategorien, die abgefragt werden.
# Rechts (TOPICS): eigene Fachgebiete + Stichworte, mit denen jede Anzeige
# zusaetzlich eingeordnet wird. Eine Anzeige ohne Treffer fliegt raus.
# --------------------------------------------------------------------------
ADZUNA_CATEGORIES = [
    "it-jobs",                  # IT / Technik / Programmieren / Data
    "engineering-jobs",         # Maschinenbau / Konstruktion
    "consultancy-jobs",         # Consulting
    "accounting-finance-jobs",  # Wirtschaft
    "scientific-qa-jobs",       # Data / Analytics / Forschung
    "manufacturing-jobs",       # Maschinenbau / Produktion
    "graduate-jobs",            # Einstiegsstellen, oft Werkstudenten
]

TOPICS = {
    "IT / Technik": [
        "it", "informatik", "software", "systemadministration", "netzwerk",
        "cloud", "aws", "azure", "devops", "linux", "hardware", "technik",
        "digitalisierung", "automatisierung", "embedded", "cyber security",
        "it-security", "datenbank", "schnittstelle", "api",
    ],
    "Wirtschaft": [
        "wirtschaft", "betriebswirtschaft", "bwl", "controlling", "finance",
        "finanzen", "rechnungswesen", "buchhaltung", "vertrieb", "marketing",
        "einkauf", "supply chain", "business development", "reporting",
        "kaufmaennisch", "kaufmännisch", "prozessoptimierung", "projektmanagement",
    ],
    "Consulting": [
        "consulting", "consultant", "beratung", "berater", "strategieberatung",
        "unternehmensberatung", "advisory", "inhouse consulting", "transformation",
    ],
    "Data": [
        "data", "daten", "datenanalyse", "analytics", "business intelligence",
        "data science", "data engineering", "machine learning", "kuenstliche intelligenz",
        "künstliche intelligenz", "statistik", "sql", "power bi", "tableau",
        "dashboard", "datenmodell", "etl", "big data",
    ],
    "Maschinenbau": [
        "maschinenbau", "mechanical", "antriebstechnik", "fertigung", "produktion",
        "werkstoff", "thermodynamik", "simulation", "fem", "cfd", "verfahrenstechnik",
        "anlagenbau", "qualitaetssicherung", "qualitätssicherung", "instandhaltung",
    ],
    "Konstruktion": [
        "konstruktion", "konstrukteur", "cad", "catia", "solidworks", "inventor",
        "creo", "nx", "autocad", "technische zeichnung", "produktentwicklung",
        "bauteil", "toleranz", "prototyp", "design engineering",
    ],
    "Programmieren": [
        "python", "java", "javascript", "typescript", "c++", "c#", "kotlin",
        "programmier", "entwickler", "developer", "coding", "softwareentwicklung",
        "backend", "frontend", "fullstack", "git", "react", "spring", "django",
        "algorithmus", "skript",
    ],
}

# Adzuna-Kategorie -> eigenes Fachgebiet (Fallback, wenn die Stichworte
# in einer sehr kurzen Anzeige nicht greifen)
CATEGORY_TO_TOPIC = {
    "it-jobs": "IT / Technik",
    "engineering-jobs": "Maschinenbau",
    "consultancy-jobs": "Consulting",
    "accounting-finance-jobs": "Wirtschaft",
    "scientific-qa-jobs": "Data",
    "manufacturing-jobs": "Maschinenbau",
}

# --------------------------------------------------------------------------
# Eigenes Skillset - Gewicht 1 (kann ich ein bisschen) bis 3 (Kernkompetenz).
# Das ist der Hebel fuer "passendes Skillset": hier eigene Faehigkeiten pflegen.
# --------------------------------------------------------------------------
SKILLS = {
    # Programmierung
    "java": 3.0, "python": 3.0, "sql": 2.5, "git": 2.0, "maven": 1.5,
    "javascript": 1.5, "typescript": 1.0, "html": 1.0, "css": 1.0,
    "react": 1.0, "rest": 2.0, "api": 2.0, "json": 1.5, "objektorientiert": 1.5,
    # Daten
    "datenanalyse": 2.5, "data analytics": 2.5, "pandas": 2.0, "numpy": 1.5,
    "power bi": 1.5, "excel": 1.5, "statistik": 2.0, "r": 1.5, "julia": 1.0,
    "machine learning": 1.5, "datenbank": 2.0, "mysql": 2.0, "etl": 1.0,
    # Technik / Ingenieurwesen
    "cad": 1.5, "solidworks": 1.5, "catia": 1.0, "matlab": 1.5, "simulation": 1.5,
    "technisches verstaendnis": 1.5, "technisches verständnis": 1.5,
    # Arbeitsweise
    "analytisch": 1.5, "eigenstaendig": 1.0, "eigenständig": 1.0,
    "strukturiert": 1.0, "deutsch": 0.5, "englisch": 1.0,
    "automatisierung": 1.5, "prozessanalyse": 1.0,
}

# Ab dieser Summe an Skill-Treffern gilt der Skill-Score als voll (1.0).
# Achtung: Adzuna kuerzt jede Beschreibung auf 500 Zeichen, es steht also
# wenig Text zur Verfuegung. Gemessen an echten Treffern liegt die Summe
# im Median bei 0 und im Maximum bei rund 6.5 - daher der niedrige Wert.
SKILL_SATURATION = 4.0
TITLE_BONUS = 1.6   # Treffer im Titel wiegen schwerer als im Fliesstext

# --------------------------------------------------------------------------
# Lernwert - was macht eine Stelle lehrreich (+) bzw. stumpf (-)?
# --------------------------------------------------------------------------
LEARNING_SIGNALS = {
    "mentoring": 1.5, "mentor": 1.2, "betreuung": 0.8, "einarbeitung": 1.0,
    "weiterbildung": 1.2, "schulung": 1.0, "fortbildung": 1.0, "coaching": 0.8,
    "abschlussarbeit": 1.5, "bachelorarbeit": 1.5, "masterarbeit": 1.5,
    "eigenverantwortlich": 1.2, "eigene projekte": 1.5, "verantwortung": 0.8,
    "spannende projekte": 0.8, "moderne technologien": 1.2, "innovativ": 0.6,
    "steile lernkurve": 1.5, "lernen": 0.8, "entwicklungsmoeglichkeiten": 1.0,
    "entwicklungsmöglichkeiten": 1.0, "perspektive": 0.8, "uebernahme": 1.2,
    "übernahme": 1.2, "einblick": 1.0, "interdisziplinaer": 0.8,
    "interdisziplinär": 0.8, "forschung": 1.0, "prototyp": 1.0,
    "flexible arbeitszeit": 0.5, "hybrid": 0.4, "homeoffice": 0.4,
}

LEARNING_PENALTIES = {
    "dateneingabe": 1.5, "datenerfassung": 1.2, "telefonie": 1.5,
    "kaltakquise": 1.5, "einfache taetigkeiten": 1.5, "einfache tätigkeiten": 1.5,
    "ablage": 1.0, "archivierung": 1.0, "kopieren": 1.0, "postbearbeitung": 1.0,
    "hilfstaetigkeit": 1.0, "hilfstätigkeit": 1.0, "zuarbeit": 0.8,
}

# Anzahl unterschiedlicher Technologien in der Anzeige zaehlt als Lernwert
TECH_DIVERSITY_BONUS = 0.5
TECH_DIVERSITY_CAP = 3.0
LEARNING_SATURATION = 2.0   # ebenfalls an 500-Zeichen-Texte angepasst

# --------------------------------------------------------------------------
# Gewichtung der drei Kriterien (Summe sollte 1.0 ergeben)
# --------------------------------------------------------------------------
WEIGHT_DISTANCE = 0.30
WEIGHT_SKILL = 0.40
WEIGHT_LEARNING = 0.30

DISTANCE_HALF_LIFE_KM = 8.0   # alle 8 km halbiert sich der Entfernungs-Score
UNKNOWN_DISTANCE_SCORE = 0.35 # Anzeige ohne Koordinaten -> neutraler Wert

# --------------------------------------------------------------------------
# Ausgabe
# --------------------------------------------------------------------------
TOP_N = 10                 # Laenge der Hauptliste
SHORTLIST_N = 25           # zusaetzliche Kurzuebersicht bis Platz N
REPORT_DIR = "reports"
STATE_FILE = "state/seen_jobs.json"
LATEST_REPORT = "top10_aktuell.md"

WATCH_INTERVAL_MINUTES = 60   # Standard fuer den Dauerbetrieb

# --------------------------------------------------------------------------
# Optional: KI-Skillranking wie im Java-Programm (Menuepunkt 3)
# --------------------------------------------------------------------------
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
