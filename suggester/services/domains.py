"""Domain availability check via RDAP (WHOIS ka official JSON successor).

RDAP 404 => domain registered nahi hai (available), 200 => registered.
Jo cheez confirm na ho sake use UNKNOWN maanna chahiye, "available" nahi.
Final buy se pehle registrar API se dobara confirm karna na bhoolein.
"""
from __future__ import annotations

import re
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import requests

AVAILABLE = "available"
TAKEN = "taken"
UNKNOWN = "unknown"

RDAP_URL = "https://rdap.org/domain/{domain}"
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def slugify(name: str) -> str:
    """'Nova Tech' -> 'novatech' (domain label)."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def check_domain(domain: str, timeout: int = 6, session: requests.Session | None = None) -> str:
    label = domain.split(".")[0]
    if not _LABEL_RE.match(label):
        return UNKNOWN
    http = session or requests
    try:
        resp = http.get(
            RDAP_URL.format(domain=domain),
            timeout=timeout,
            allow_redirects=True,
            headers={"Accept": "application/rdap+json"},
        )
    except requests.RequestException:
        return _dns_fallback(domain)
    if resp.status_code == 404:
        return AVAILABLE
    if resp.status_code == 200:
        return TAKEN
    return _dns_fallback(domain)


def _dns_fallback(domain: str) -> str:
    """RDAP fail hone par: DNS resolve hota hai to pakka taken, warna unknown."""
    try:
        socket.gethostbyname(domain)
        return TAKEN
    except OSError:
        return UNKNOWN


def check_many(
    names: Iterable[str],
    tlds: list[str],
    workers: int = 12,
    timeout: int = 6,
) -> dict[str, dict[str, str]]:
    """{name: {tld: status}} -- parallel mein."""
    jobs = [(n, t) for n in names for t in tlds]
    results: dict[str, dict[str, str]] = {n: {} for n in names}

    def run(job):
        n, t = job
        slug = slugify(n)
        return n, t, check_domain(f"{slug}.{t}", timeout=timeout) if slug else UNKNOWN

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for n, t, status in pool.map(run, jobs):
            results[n][t] = status
    return results
