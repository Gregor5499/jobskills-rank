# -*- coding: utf-8 -*-
"""
Methods - Gegenstueck zu Methods.java.

Gleicher Ablauf wie im Java-Programm: URL bauen, ueber mehrere Seiten pagen,
JSON in das POJO giessen, Ergebnisse einsammeln. Neu ist alles danach:
filtern, bewerten, sortieren und als Markdown-Report ausgeben.

HTTP laeuft ueber urllib aus der Standardbibliothek - das ist das Pendant zu
java.net.http.HttpClient und spart eine externe Abhaengigkeit.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Set

import config as cfg
import report as report_module
from adzuna_pojo import AdzunaPojo
from job import Job
from scoring import ScoredJob, contains, rank, topics_of

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_AGENT = "JobSkillFinder/1.0 (Python; privates Projekt)"


# ==========================================================================
# HTTP - in Java der HttpClient mit HttpRequest/HttpResponse
# ==========================================================================
def _get_json(url: str, params: Dict[str, object],
              retries: int = 3) -> Optional[dict]:
    full_url = url + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(full_url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                body = response.read().decode("utf-8", errors="replace")
            return json.loads(body)

        except urllib.error.HTTPError as error:
            if error.code == 429:
                pause = 5 * attempt
                print("    Rate-Limit erreicht, warte %d s ..." % pause)
                time.sleep(pause)
                continue
            if error.code in (401, 403):
                print("    Zugang abgelehnt (HTTP %d) - App-ID/Key pruefen."
                      % error.code)
                return None
            print("    HTTP %d bei der Anfrage, Versuch %d/%d"
                  % (error.code, attempt, retries))
        except urllib.error.URLError as error:
            print("    Netzwerkfehler (%s), Versuch %d/%d"
                  % (error.reason, attempt, retries))
        except ValueError:
            print("    Antwort war kein gueltiges JSON.")
            return None
        time.sleep(2 * attempt)

    return None


def _adzuna(path: str, params: Dict[str, object]) -> Optional[dict]:
    if not cfg.APP_ID or not cfg.APP_KEY:
        print("    Keine Adzuna-Zugangsdaten gefunden. Bitte setzen:")
        print("    export ADZUNA_APP_ID=...  und  export ADZUNA_APP_KEY=...")
        print("    (kostenlos unter https://developer.adzuna.com/)")
        return None
    query = {
        "app_id": cfg.APP_ID,
        "app_key": cfg.APP_KEY,
        "content-type": "application/json",
    }
    query.update(params)
    return _get_json("%s/%s" % (cfg.BASE_URL, path), query)


def check_categories() -> None:
    """Kategorienliste der API holen und die eigene Konfiguration pruefen."""
    payload = _adzuna("categories", {})
    if not payload:
        return
    known = {item.get("tag") for item in payload.get("results", [])
             if isinstance(item, dict)}
    unknown = [tag for tag in cfg.ADZUNA_CATEGORIES if tag not in known]
    if unknown:
        print("  Hinweis: unbekannte Kategorien in config.py -> %s"
              % ", ".join(unknown))
    else:
        print("  Alle %d Kategorien aus config.py sind gueltig."
              % len(cfg.ADZUNA_CATEGORIES))


# ==========================================================================
# Suche mit Paging (im Java-Code die for-Schleife ueber 5 Seiten)
# ==========================================================================
def search(category: Optional[str] = None,
           what_or: Optional[str] = None) -> Dict[str, Job]:
    found: Dict[str, Job] = {}

    for page in range(1, cfg.MAX_PAGES + 1):
        params = {
            "results_per_page": cfg.RESULTS_PER_PAGE,
            "what_or": what_or or cfg.WHAT_OR,
            "where": cfg.WHERE,
            "distance": cfg.SEARCH_RADIUS_KM,
            "max_days_old": cfg.MAX_DAYS_OLD,
            "sort_by": "date",
        }
        if category:
            params["category"] = category

        payload = _adzuna("search/%d" % page, params)
        if payload is None:
            break

        pojo = AdzunaPojo.from_json(payload)
        if pojo.is_empty():                 # leere Inhalte abfangen, wie in Java
            break

        for job in pojo.results:
            if job.id:
                found[job.id] = job

        if len(pojo.results) < cfg.RESULTS_PER_PAGE:
            break                           # letzte Seite erreicht
        time.sleep(cfg.REQUEST_PAUSE)

    return found


def collect_jobs(verbose: bool = True) -> Dict[str, Job]:
    """Alle konfigurierten Kategorien abklappern, Duplikate fallen weg."""
    all_jobs: Dict[str, Job] = {}

    for category in cfg.ADZUNA_CATEGORIES:
        found = search(category=category)
        fresh = len([job_id for job_id in found if job_id not in all_jobs])
        all_jobs.update(found)
        if verbose:
            print("  %-26s %4d Treffer (%d neu)" % (category, len(found), fresh))

    # Zusaetzlich ohne Kategoriefilter, damit falsch einsortierte Anzeigen
    # nicht durchrutschen.
    generic = search(category=None)
    fresh = len([job_id for job_id in generic if job_id not in all_jobs])
    all_jobs.update(generic)
    if verbose:
        print("  %-26s %4d Treffer (%d neu)"
              % ("ohne Kategoriefilter", len(generic), fresh))

    return all_jobs


# ==========================================================================
# Filter
# ==========================================================================
def is_werkstudent(job: Job) -> bool:
    text = job.text_lower
    return any(contains(text, term) for term in cfg.WERKSTUDENT_TERMS)


def is_blocked(job: Job) -> bool:
    title = job.title_lower
    return any(term in title for term in cfg.TITLE_BLOCKLIST)


def filter_jobs(jobs: Dict[str, Job], verbose: bool = True) -> List[Job]:
    kept: List[Job] = []
    no_werkstudent = off_topic = blocked = 0

    for job in jobs.values():
        if not is_werkstudent(job):
            no_werkstudent += 1
            continue
        if is_blocked(job):
            blocked += 1
            continue
        if not topics_of(job):
            off_topic += 1
            continue
        kept.append(job)

    if verbose:
        print("  aussortiert: %d ohne Werkstudentenbezug, %d ausserhalb der "
              "Fachgebiete, %d auf der Blockliste"
              % (no_werkstudent, off_topic, blocked))
    return kept


# ==========================================================================
# Zustand - damit wiederholte Laeufe "neu seit letztem Mal" zeigen koennen
# ==========================================================================
def _state_path() -> str:
    return os.path.join(BASE_DIR, cfg.STATE_FILE)


def load_state() -> dict:
    path = _state_path()
    if not os.path.exists(path):
        return {"seen": [], "home": None, "last_run": None}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
        state.setdefault("seen", [])
        state.setdefault("home", None)
        state.setdefault("last_run", None)
        return state
    except (ValueError, OSError):
        return {"seen": [], "home": None, "last_run": None}


def save_state(state: dict) -> None:
    path = _state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)


# ==========================================================================
# Optional: Adresse exakt aufloesen (OpenStreetMap / Nominatim)
# ==========================================================================
def geocode_home(state: dict, force: bool = False):
    cached = state.get("home")
    if cached and not force:
        return cached["lat"], cached["lon"]

    hits = _get_json("https://nominatim.openstreetmap.org/search",
                     {"q": cfg.HOME_ADDRESS, "format": "json", "limit": 1})
    if isinstance(hits, list) and hits:
        try:
            lat, lon = float(hits[0]["lat"]), float(hits[0]["lon"])
        except (KeyError, TypeError, ValueError):
            print("  Antwort des Geocoders unbrauchbar, nutze Naeherungswert")
            return cfg.HOME_LAT, cfg.HOME_LON
        state["home"] = {"lat": lat, "lon": lon, "address": cfg.HOME_ADDRESS}
        save_state(state)
        print("  Adresse aufgeloest: %.5f, %.5f" % (lat, lon))
        return lat, lon

    print("  Adresse nicht aufloesbar, nutze Naeherungswert aus config.py")
    return cfg.HOME_LAT, cfg.HOME_LON


# ==========================================================================
# Hauptfunktion: suchen, bewerten, Report schreiben
# ==========================================================================
def analyze_jobs(use_geocoding: bool = False, verbose: bool = True) -> List[ScoredJob]:
    state = load_state()
    home_lat, home_lon = cfg.HOME_LAT, cfg.HOME_LON
    if use_geocoding:
        home_lat, home_lon = geocode_home(state)
    elif state.get("home"):
        home_lat, home_lon = state["home"]["lat"], state["home"]["lon"]

    print("Suche Werkstudentenstellen in %s (Umkreis %d km) ..."
          % (cfg.WHERE, cfg.SEARCH_RADIUS_KM))
    jobs = collect_jobs(verbose=verbose)
    print("  Rohtreffer gesamt: %d" % len(jobs))

    relevant = filter_jobs(jobs, verbose=verbose)
    print("  passend zum Profil: %d" % len(relevant))

    seen: Set[str] = set(state.get("seen", []))
    new_ids = {job.id for job in relevant if job.id not in seen}

    scored = rank(relevant, home_lat, home_lon, new_ids)

    stats = {"raw": len(jobs), "kept": len(relevant), "new": len(new_ids)}
    markdown = report_module.build_markdown(scored, stats)
    paths = report_module.write_report(markdown, BASE_DIR)

    state["seen"] = sorted(seen.union(job.id for job in relevant))
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    save_state(state)

    print("")
    print("Top %d:" % min(cfg.TOP_N, len(scored)))
    for index, item in enumerate(scored[:cfg.TOP_N], start=1):
        km = "%.1f km" % item.km if item.km is not None else "k. A."
        print("  %2d. %-55s %-9s Score %.2f%s"
              % (index, item.job.title[:55], km, item.total,
                 "  NEU" if item.is_new else ""))

    print("")
    print("Report geschrieben:")
    for path in paths:
        print("  %s" % path)
    print("  neu seit dem letzten Lauf: %d" % len(new_ids))
    return scored


def watch(interval_minutes: Optional[int] = None, use_geocoding: bool = False) -> None:
    """Dauerbetrieb: immer wieder lesen, bis Strg+C."""
    interval = interval_minutes or cfg.WATCH_INTERVAL_MINUTES
    print("Dauerbetrieb aktiv - alle %d Minuten ein neuer Lauf (Strg+C beendet)."
          % interval)
    run = 1
    try:
        while True:
            print("")
            print("=== Lauf %d - %s ==="
                  % (run, datetime.now().strftime("%d.%m.%Y %H:%M")))
            analyze_jobs(use_geocoding=use_geocoding)
            run += 1
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        print("")
        print("Dauerbetrieb beendet.")


# ==========================================================================
# Wie im Java-Programm: Skillranking der Stellenbeschreibungen ueber die KI.
# Braucht  pip install google-genai  und  export GOOGLE_API_KEY=...
# ==========================================================================
def analyze_job_skill() -> None:
    job_name = input("Enter job name: ").strip() or "Werkstudent"
    location = input("Enter location: ").strip() or cfg.WHERE
    print("Searching for job: %s in %s!" % (job_name, location))

    all_descriptions: List[str] = []
    for page in range(1, cfg.MAX_PAGES + 1):
        payload = _adzuna("search/%d" % page, {
            "results_per_page": cfg.RESULTS_PER_PAGE,
            "what": job_name,
            "where": location,
            "max_days_old": 365,
        })
        if payload is None:
            break
        pojo = AdzunaPojo.from_json(payload)
        if pojo.is_empty():
            break
        print("Gefundene Jobs: %d" % len(pojo.results))
        all_descriptions.extend(job.description for job in pojo.results)
        time.sleep(cfg.REQUEST_PAUSE)

    if not all_descriptions:
        print("Keine Stellenbeschreibungen gefunden.")
        return

    prompt = (
        "Du bist ein Datenanalyst. Extrahiere aus den folgenden Stellenbeschreibungen "
        "die haeufigst genannten Faehigkeiten (bevorzugt anwendungsorientiert, "
        "z. B. Python statt Software Engineering). Gib mir nur ein Ranking der 10 "
        "haeufigsten Skills zurueck (einfache 1.-10. Liste).\n\n"
        "Stellenbeschreibungen:\n" + "\n".join(all_descriptions)
    )

    try:
        from google import genai
    except ImportError:
        print("Paket google-genai fehlt. Installation:  pip install google-genai")
        return

    try:
        client = genai.Client()
        response = client.models.generate_content(model=cfg.GEMINI_MODEL,
                                                  contents=prompt)
        print("")
        print(response.text)
    except Exception as error:   # bewusst breit, wie das catch(Exception) in Java
        print("KI-Aufruf fehlgeschlagen: %s" % error)
        print("Pruefen: GOOGLE_API_KEY gesetzt? Modellname GEMINI_MODEL gueltig?")


def show_config() -> None:
    state = load_state()
    home = state.get("home")
    lat, lon = (home["lat"], home["lon"]) if home else (cfg.HOME_LAT, cfg.HOME_LON)
    print("Adresse            : %s (%.4f, %.4f%s)"
          % (cfg.HOME_ADDRESS, lat, lon, ", geocodiert" if home else ", Naeherung"))
    print("Ort / Radius       : %s / %d km" % (cfg.WHERE, cfg.SEARCH_RADIUS_KM))
    print("Suchbegriffe       : %s" % cfg.WHAT_OR)
    print("Fachgebiete        : %s" % ", ".join(cfg.TOPICS.keys()))
    print("Adzuna-Kategorien  : %s" % ", ".join(cfg.ADZUNA_CATEGORIES))
    print("Gewichte           : Entfernung %.2f | Skillset %.2f | Lernwert %.2f"
          % (cfg.WEIGHT_DISTANCE, cfg.WEIGHT_SKILL, cfg.WEIGHT_LEARNING))
    print("Seiten x Treffer   : %d x %d, max. %d Tage alt"
          % (cfg.MAX_PAGES, cfg.RESULTS_PER_PAGE, cfg.MAX_DAYS_OLD))
    print("Skills im Profil   : %d" % len(cfg.SKILLS))
    print("Letzter Lauf       : %s" % (state.get("last_run") or "noch keiner"))
    print("Bekannte Anzeigen  : %d" % len(state.get("seen", [])))
