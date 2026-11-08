"""Existing-business conflict signals for a name. Django-free, free APIs only.

These are SIGNALS, not proof. "No signals" never means the name is safe to use;
trademark search (IP India / WIPO) and MCA name search are still required.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import requests

from . import domains

CONFLICT_TLDS = ["net", "org", "io", "co.in"]
WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "NaamAstro/1.0 (company name suggestion tool)"}

HIGH, MEDIUM, LOW, NONE = "high", "medium", "low", "none"


def wikipedia_match(name: str, slug: str, timeout: int = 5) -> dict | None:
    """Wikipedia mein isi naam ka page ho to {"title", "url"}, warna None."""
    try:
        resp = requests.get(
            WIKI_API,
            params={"action": "opensearch", "search": name, "limit": 5, "namespace": 0, "format": "json"},
            headers=HEADERS,
            timeout=timeout,
        )
        data = resp.json()
        titles, urls = data[1], data[3]
    except (requests.RequestException, ValueError, IndexError, TypeError):
        return None
    for title, url in zip(titles, urls):
        base = re.sub(r"\s*\(.*?\)\s*$", "", title)  # "Zenora (company)" -> "Zenora"
        if domains.slugify(base) == slug:
            return {"title": title, "url": url}
    return None


def live_site(domain: str, timeout: int = 4) -> bool:
    """Domain par koi web server jawab de raha hai? (parked page bhi True de sakta hai)"""
    try:
        resp = requests.get(
            f"https://{domain}", timeout=timeout, allow_redirects=True, headers=HEADERS, stream=True
        )
        resp.close()
        return resp.status_code < 500
    except requests.RequestException:
        return False


def check_conflicts(
    name: str,
    slug: str,
    tlds: list[str] | None = None,
    check=domains.check_domain,
    wiki=wikipedia_match,
    live=live_site,
) -> dict:
    tlds = tlds or CONFLICT_TLDS
    candidates = [f"{slug}.{t}" for t in tlds]
    with ThreadPoolExecutor(max_workers=len(candidates) + 1) as pool:
        wiki_future = pool.submit(wiki, name, slug)
        statuses = list(pool.map(check, candidates))
        registered = [d for d, st in zip(candidates, statuses) if st == domains.TAKEN]
        live_flags = list(pool.map(live, registered)) if registered else []
        wikipedia = wiki_future.result()
    live_sites = [d for d, flag in zip(registered, live_flags) if flag]

    if wikipedia:
        level = HIGH
    elif live_sites:
        level = MEDIUM
    elif registered:
        level = LOW
    else:
        level = NONE
    return {"level": level, "wikipedia": wikipedia, "live_sites": live_sites, "registered": registered}
