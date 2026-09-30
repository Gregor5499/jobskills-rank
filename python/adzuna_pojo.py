# -*- coding: utf-8 -*-
"""
AdzunaPojo - Gegenstueck zu AdzunaPojo.java.

Template fuer die JSON-Antwort: eine Liste von Jobs, dazu die Gesamtzahl der
Treffer. In Java uebernahm Gson das Befuellen, in Python macht es from_json().
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from job import Job


@dataclass
class AdzunaPojo:
    results: List[Job] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "AdzunaPojo":
        if not isinstance(payload, dict):
            return cls()
        raw_results = payload.get("results") or []
        jobs = [Job.from_api(item) for item in raw_results if isinstance(item, dict)]
        try:
            count = int(payload.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        return cls(results=jobs, count=count)

    def is_empty(self) -> bool:
        return not self.results
