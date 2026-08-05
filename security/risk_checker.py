"""
security/risk_checker.py
Non-blocking heuristics that flag potentially expensive or careless
queries (e.g. SELECT *, missing LIMIT on large scans, cartesian joins).
These are advisory only and never prevent execution of safe SELECTs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RiskReport:
    """Advisory risk findings for a query."""

    level: str = "low"                       # low | medium | high
    findings: list[str] = field(default_factory=list)


class RiskChecker:
    """Produce advisory warnings about query cost / hygiene."""

    def check(self, sql: str) -> RiskReport:
        upper = sql.upper()
        findings: list[str] = []
        score = 0

        if re.search(r"SELECT\s+\*", upper):
            findings.append("Uses SELECT * — selecting only needed columns is faster.")
            score += 1

        if " JOIN " in upper and " ON " not in upper and "," in upper:
            findings.append("Possible cartesian join — verify join conditions.")
            score += 2

        if "LIMIT" not in upper and ("ORDER BY" in upper or "SELECT *" in upper):
            findings.append("No LIMIT clause — large result sets may be slow to render.")
            score += 1

        if upper.count("JOIN") >= 4:
            findings.append("Many joins detected — confirm each one is required.")
            score += 1

        level = "low" if score <= 1 else "medium" if score <= 2 else "high"
        return RiskReport(level=level, findings=findings)
