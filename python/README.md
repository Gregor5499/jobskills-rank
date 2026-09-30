# JobSkillFinder – Python-Version

Python-Pendant zum Java-Programm im selben Repository. Der Ablauf ist derselbe
(Menü → Adzuna-API mit Paging → Auswertung), nur wertet diese Version die
Anzeigen nach einem persönlichen Profil aus statt die häufigsten Skills zu
zählen.

## Was das Programm macht

1. Fragt die Adzuna-API wiederholt ab – je Kategorie 5 Seiten à 50 Treffer,
   plus einen Durchlauf ohne Kategoriefilter. Duplikate fallen über die Job-ID weg.
2. Filtert auf **Berlin**, **Werkstudent** und die Fachgebiete
   *IT / Technik, Wirtschaft, Consulting, Data, Maschinenbau, Konstruktion,
   Programmieren*.
3. Bewertet jede Anzeige nach drei Kriterien:

   | Kriterium | Gewicht | Grundlage |
   | --- | --- | --- |
   | Entfernung | 30 % | Luftlinie (Haversine) ab `HOME_ADDRESS`; alle 8 km halbiert sich der Teilscore |
   | Skillset | 40 % | gewichteter Abgleich mit `SKILLS` in `config.py`, Treffer im Titel zählen 1,6-fach |
   | Lernwert | 30 % | Mentoring, Abschlussarbeit, eigene Projekte, Technologie-Vielfalt … abzüglich Dateneingabe, Kaltakquise & Co. |

4. Schreibt eine nummerierte **Top-10-Liste als Markdown** nach `reports/` –
   mit Link auf jede Anzeige, Score-Aufschlüsselung und Begründung.

## Start

```bash
python3 main.py                  # Hauptmenü wie im Java-Programm
python3 main.py --once           # ein Durchlauf, Report schreiben, fertig
python3 main.py --watch 60       # Dauerbetrieb: alle 60 Minuten neu suchen
python3 main.py --once --geocode # Wohnadresse einmalig exakt auflösen
```

Es wird **keine externe Bibliothek** gebraucht – HTTP läuft über `urllib` aus
der Standardbibliothek (das Gegenstück zu Javas `HttpClient`). Getestet mit
Python 3.9 und 3.14.

Nur für Menüpunkt 3 (KI-Skillranking wie im Java-Programm) sind
`pip install google-genai` und ein gesetztes `GOOGLE_API_KEY` nötig.

## Ausgabe

* `reports/top10_aktuell.md` – immer der neueste Stand
* `reports/top10_werkstudent_berlin_JJJJ-MM-TT_HH-MM.md` – Archiv je Lauf
* `state/seen_jobs.json` – bereits gesehene Anzeigen, damit wiederholte Läufe
  neue Treffer mit `NEU` markieren

## Aufbau (spiegelt die Java-Klassen)

| Python | Java | Aufgabe |
| --- | --- | --- |
| `main.py` | `Main.java` | Menü und Kommandozeile |
| `methods.py` | `Methods.java` | API-Abfrage, Paging, Filter, Ablaufsteuerung |
| `job.py` | `Job.java` | eine Stellenanzeige |
| `adzuna_pojo.py` | `AdzunaPojo.java` | JSON-Template der API-Antwort |
| `scoring.py` | – | Entfernung, Skillset, Lernwert |
| `report.py` | – | Markdown-Report |
| `config.py` | – | alle Stellschrauben |

## Schrauben, die sich lohnen

Alles in `config.py`:

* `SKILLS` – **das eigene Profil pflegen**, Gewicht 1 (Grundkenntnisse) bis 3
  (Kernkompetenz). Das ist der größte Hebel auf das Ranking.
* `WEIGHT_DISTANCE` / `WEIGHT_SKILL` / `WEIGHT_LEARNING` – Gewichtung der
  Kriterien, Summe 1,0.
* `TOPICS` – Fachgebiete und ihre Stichworte.
* `MAX_DAYS_OLD`, `SEARCH_RADIUS_KM`, `MAX_PAGES` – Breite der Suche.
* `HOME_ADDRESS` / `HOME_LAT` / `HOME_LON` – Bezugspunkt, per Umgebungsvariable setzbar (Standard: Alexanderplatz). Mit `--geocode`
  wird die Adresse einmalig über OpenStreetMap exakt aufgelöst und in
  `state/seen_jobs.json` gecached.

## Grenzen der Datenquelle

* Adzuna liefert je Anzeige nur **500 Zeichen** Beschreibung. Skill- und
  Lernwert beruhen also auf einem Textausschnitt, nicht auf der ganzen Anzeige.
* Viele Anzeigen haben **keinen genauen Arbeitsort**; Adzuna setzt sie dann auf
  den Stadtmittelpunkt. Solche Einträge sind im Report mit
  `*` markiert – die Entfernung ist dort eine Schätzung.
* App-ID und App-Key werden nur aus den Umgebungsvariablen `ADZUNA_APP_ID` und
  `ADZUNA_APP_KEY` gelesen, damit keine Zugangsdaten im Repository liegen.
