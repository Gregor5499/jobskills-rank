# -*- coding: utf-8 -*-
"""
Main - Gegenstueck zu Main.java.

Startet entweder das Hauptmenue (wie im Java-Programm) oder laeuft ueber
Kommandozeilenargumente direkt durch:

    python3 main.py                 # Menue
    python3 main.py --once          # ein Durchlauf, Report schreiben
    python3 main.py --watch 60      # alle 60 Minuten neu suchen
    python3 main.py --once --geocode  # Adresse einmalig exakt aufloesen
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg      # noqa: E402
import methods            # noqa: E402


def menu() -> None:
    running = True

    while running:
        print("")
        print("--- Hauptmenue ---")
        print("1 - Werkstudentenstellen suchen und Top-%d-Report erstellen" % cfg.TOP_N)
        print("2 - Dauerbetrieb (alle %d Minuten neu suchen)" % cfg.WATCH_INTERVAL_MINUTES)
        print("3 - Skill-Ranking ueber die KI (wie im Java-Programm)")
        print("4 - Konfiguration anzeigen")
        print("5 - Adresse exakt aufloesen und Kategorien pruefen")
        print("6 - Exit program")

        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return

        if cmd == "1":
            methods.analyze_jobs()
        elif cmd == "2":
            raw = input("Intervall in Minuten [%d]: " % cfg.WATCH_INTERVAL_MINUTES).strip()
            interval = int(raw) if raw.isdigit() and int(raw) > 0 else cfg.WATCH_INTERVAL_MINUTES
            methods.watch(interval)
        elif cmd == "3":
            methods.analyze_job_skill()
        elif cmd == "4":
            methods.show_config()
        elif cmd == "5":
            state = methods.load_state()
            methods.geocode_home(state, force=True)
            methods.check_categories()
        elif cmd == "6":
            running = False
        else:
            print("Unbekannte Eingabe.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Werkstudentenstellen in Berlin ueber die Adzuna-API suchen, "
                    "nach Entfernung, Skillset und Lernwert bewerten und als "
                    "Markdown-Report ausgeben.")
    parser.add_argument("--once", action="store_true",
                        help="einmal suchen, Report schreiben, beenden")
    parser.add_argument("--watch", type=int, metavar="MINUTEN", nargs="?",
                        const=cfg.WATCH_INTERVAL_MINUTES,
                        help="Dauerbetrieb mit dem angegebenen Intervall")
    parser.add_argument("--geocode", action="store_true",
                        help="Wohnadresse einmalig ueber OpenStreetMap aufloesen")
    args = parser.parse_args()

    if args.watch:
        methods.watch(args.watch, use_geocoding=args.geocode)
    elif args.once:
        methods.analyze_jobs(use_geocoding=args.geocode)
    else:
        menu()


if __name__ == "__main__":
    main()
