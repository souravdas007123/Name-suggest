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
        # rdap.org un extensions ke liye bhi 404 de sakta hai jinka RDAP server nahi milta,
        # isliye "available" tabhi maanein jab DNS bhi resolve na ho.
        return TAKEN if _resolves(domain) else AVAILABLE
    if resp.status_code == 200:
        return TAKEN
    return _dns_fallback(domain)


def _resolves(domain: str) -> bool:
    try:
        socket.gethostbyname(domain)
        return True
    except OSError:
        return False


def _dns_fallback(domain: str) -> str:
    """RDAP fail hone par: DNS resolve hota hai to pakka taken, warna unknown."""
    return TAKEN if _resolves(domain) else UNKNOWN


def check_domains(domain_list: Iterable[str], workers: int = 12, timeout: int = 6) -> dict[str, str]:
    """{domain: status}, parallel mein. Duplicate domains ek hi baar check hote hain."""
    unique = list(dict.fromkeys(domain_list))
    if not unique:
        return {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        statuses = list(pool.map(lambda d: check_domain(d, timeout=timeout), unique))
    return dict(zip(unique, statuses))


if __name__ == "__main__":
    # Quick manual test: python suggester/services/domains.py google.com google.co example.app
    import sys

    for d in sys.argv[1:] or ["google.com", "google.in", "google.co", "google.app"]:
        print(f"{d:30s} {check_domain(d)}")
