"""Poora pipeline: profile -> generate -> numerology filter -> domain check -> rank.

Domain check 2 phase mein hota hai taaki search tez rahe:
  1. Sabhi compatible naamo ka sirf primary TLD (.com)
  2. Bache hue top naamo ke baaki TLDs, aur jinka .com taken hai unke
     variations (getX.com, Xhq.com).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import domains, generator, numerology

VARIANT_PATTERNS = ["get{}", "{}hq"]


@dataclass
class Suggestion:
    name: str
    name_number: int
    compound_number: int
    domain_status: dict                      # {"com": "available", "in": "taken", ...}
    score: int
    alt_domains: list = field(default_factory=list)  # [(domain, status)] jab .com taken ho


def score_suggestion(
    name: str, status: dict, tlds: list[str], strong: bool = False, alt_available: bool = False
) -> int:
    score = 50
    if strong:
        score += 15                      # Moolank aur Bhagyank, dono se match
    primary = status.get(tlds[0])
    if primary == domains.AVAILABLE:
        score += 30
    elif primary == domains.UNKNOWN:
        score += 5
    elif alt_available:
        score += 10                      # .com taken, lekin variation khaali
    extra = sum(1 for t in tlds[1:] if status.get(t) == domains.AVAILABLE)
    score += min(extra, 3) * 5
    n = len(name)
    score += 10 if n <= 8 else 5 if n <= 11 else 0
    return score


def run_search(
    dob: date,
    industry: str,
    keywords: list[str],
    tone: str,
    cfg: dict,
    check=domains.check_domains,
) -> tuple[numerology.AstroProfile, list[Suggestion]]:
    profile = numerology.build_profile(dob)
    tlds = cfg["TLDS"]
    primary = tlds[0]
    workers, timeout = cfg["DOMAIN_CHECK_WORKERS"], cfg["DOMAIN_CHECK_TIMEOUT"]

    candidates = generator.generate_candidates(industry, keywords, tone, cfg["CANDIDATE_COUNT"])
    compatible = [n for n in candidates if numerology.is_compatible(n, profile)]
    slug = {n: domains.slugify(n) for n in compatible}

    # ---- Phase 1: sirf primary TLD ----
    p1 = check([f"{slug[n]}.{primary}" for n in compatible], workers=workers, timeout=timeout)
    status = {n: {primary: p1.get(f"{slug[n]}.{primary}", domains.UNKNOWN)} for n in compatible}

    free = [n for n in compatible if status[n][primary] != domains.TAKEN]
    taken = [n for n in compatible if status[n][primary] == domains.TAKEN]
    free.sort(key=lambda n: (status[n][primary] != domains.AVAILABLE, len(n), n))
    taken.sort(key=lambda n: (len(n), n))
    top = free[: cfg["EXTRA_TLD_LIMIT"]]
    alt_names = taken[: cfg["ALT_LIMIT"]]

    # ---- Phase 2: baaki TLDs + variations, ek hi batch mein ----
    extra = [f"{slug[n]}.{t}" for n in top for t in tlds[1:]]
    variants = {n: [f"{p.format(slug[n])}.{primary}" for p in VARIANT_PATTERNS] for n in alt_names}
    p2 = check(extra + [d for ds in variants.values() for d in ds], workers=workers, timeout=timeout)

    results: list[Suggestion] = []
    for n in top:
        st = dict(status[n])
        for t in tlds[1:]:
            st[t] = p2.get(f"{slug[n]}.{t}", domains.UNKNOWN)
        results.append(
            Suggestion(
                n, numerology.name_number(n), numerology.compound_number(n), st,
                score_suggestion(n, st, tlds, numerology.is_strong(n, profile)),
            )
        )
    for n in alt_names:
        free_alts = [(d, p2[d]) for d in variants[n] if p2.get(d) == domains.AVAILABLE]
        if not free_alts:
            continue  # .com bhi taken aur variation bhi taken: dikhane ka fayda nahi
        st = dict(status[n])
        results.append(
            Suggestion(
                n, numerology.name_number(n), numerology.compound_number(n), st,
                score_suggestion(n, st, tlds, numerology.is_strong(n, profile), alt_available=True),
                alt_domains=free_alts,
            )
        )

    results.sort(key=lambda s: (-s.score, len(s.name), s.name))
    return profile, results[: cfg["MAX_RESULTS"]]
