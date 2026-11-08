"""Poora pipeline: profile -> generate -> numerology filter -> domain check -> rank."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from . import domains, generator, numerology


@dataclass
class Suggestion:
    name: str
    name_number: int
    compound_number: int
    domain_status: dict  # {"com": "available", "in": "taken"}
    score: int


def score_suggestion(name: str, status: dict, tlds: list[str]) -> int:
    score = 50  # compatible number (filter ke baad sab compatible hain)
    primary = status.get(tlds[0])
    if primary == domains.AVAILABLE:
        score += 35
    elif primary == domains.UNKNOWN:
        score += 5
    for extra in tlds[1:]:
        if status.get(extra) == domains.AVAILABLE:
            score += 8
    n = len(name)
    score += 10 if n <= 8 else 5 if n <= 11 else 0
    return score


def run_search(
    dob: date,
    industry: str,
    keywords: list[str],
    tone: str,
    cfg: dict,
    check=domains.check_many,
) -> tuple[numerology.AstroProfile, list[Suggestion]]:
    profile = numerology.build_profile(dob)
    tlds = cfg["TLDS"]

    candidates = generator.generate_candidates(
        industry, keywords, tone, cfg["CANDIDATE_COUNT"], cfg["ANTHROPIC_MODEL"]
    )
    compatible = [n for n in candidates if numerology.is_compatible(n, profile)]

    statuses = check(
        compatible, tlds, workers=cfg["DOMAIN_CHECK_WORKERS"], timeout=cfg["DOMAIN_CHECK_TIMEOUT"]
    )

    results = []
    for n in compatible:
        st = statuses.get(n, {})
        # Primary domain taken hai to dikhane ka koi fayda nahi
        if st.get(tlds[0]) == domains.TAKEN:
            continue
        results.append(
            Suggestion(
                name=n,
                name_number=numerology.name_number(n),
                compound_number=numerology.compound_number(n),
                domain_status=st,
                score=score_suggestion(n, st, tlds),
            )
        )
    results.sort(key=lambda s: (-s.score, len(s.name), s.name))
    return profile, results[: cfg["MAX_RESULTS"]]
