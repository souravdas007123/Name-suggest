"""Candidate naam generation: poori tarah rule-based, koi paid API nahi."""
from __future__ import annotations

import random

PREFIXES = ["Nova", "Zen", "Veda", "Arya", "Adi", "Neo", "Pra", "Sam", "Uday", "Ora", "Vyom",
            "Tej", "Sattva", "Kavi", "Lumi", "Alto", "Veer", "Ananta", "Dhruv", "Maitri"]
SUFFIXES = ["ly", "ify", "ora", "ix", "ara", "ium", "ova", "verse", "labs", "works",
            "hub", "nest", "grid", "wave", "forge", "kart", "ji", "ya", "tek", "ware"]
ROOTS = ["Surya", "Chandra", "Agni", "Vayu", "Prana", "Nidhi", "Shakti", "Dhara", "Setu",
         "Ankur", "Disha", "Kiran", "Sagar", "Tara", "Uday", "Pragati", "Srijan", "Vistar"]

# Industry keyword -> related shabd. Apne domains ke hisaab se badhate jaiye.
INDUSTRY_WORDS = {
    "tech": ["Byte", "Logic", "Code", "Cloud", "Pixel", "Stack", "Data"],
    "software": ["Byte", "Logic", "Code", "Cloud", "Stack", "Soft"],
    "food": ["Swad", "Rasoi", "Spice", "Bite", "Thali", "Anna"],
    "restaurant": ["Swad", "Rasoi", "Spice", "Bite", "Thali"],
    "education": ["Gyan", "Vidya", "Learn", "Shiksha", "Guru", "Pathshala"],
    "health": ["Aarogya", "Vita", "Heal", "Ayur", "Care", "Jeevan"],
    "fashion": ["Vastra", "Thread", "Drape", "Style", "Weave", "Zari"],
    "finance": ["Dhan", "Arth", "Coin", "Vault", "Lakshmi", "Capital"],
    "travel": ["Yatra", "Safar", "Trek", "Roam", "Marg", "Voyage"],
    "marketing": ["Reach", "Spark", "Buzz", "Amplify", "Vistar", "Pulse"],
    "real estate": ["Griha", "Bhumi", "Nivas", "Estate", "Dwar", "Nirman"],
    "ecommerce": ["Kart", "Bazaar", "Haat", "Shop", "Mart", "Cart"],
}


def _industry_words(industry: str, keywords: list[str]) -> list[str]:
    words = [w.capitalize() for w in keywords if w]
    low = industry.lower()
    for key, vals in INDUSTRY_WORDS.items():
        if key in low or low in key:
            words += vals
    return words or ["Prime", "Core", "Bright", "Edge", "Pure"]


def rule_based_candidates(industry: str, keywords: list[str], count: int, seed: int | None = None) -> list[str]:
    rng = random.Random(seed)
    words = _industry_words(industry, keywords)
    out: set[str] = set()
    attempts = 0
    while len(out) < count and attempts < count * 20:
        attempts += 1
        style = rng.choice(["prefix_word", "word_suffix", "root_word", "root_suffix", "word"])
        if style == "prefix_word":
            n = rng.choice(PREFIXES) + rng.choice(words).lower()
        elif style == "word_suffix":
            n = rng.choice(words) + rng.choice(SUFFIXES)
        elif style == "root_word":
            n = rng.choice(ROOTS) + rng.choice(words).lower()
        elif style == "root_suffix":
            n = rng.choice(ROOTS) + rng.choice(SUFFIXES)
        else:
            n = rng.choice(words) + rng.choice(["ify", "ly", "ora", "ium"])
        if 4 <= len(n) <= 14:
            out.add(n.capitalize() if n.islower() else n)
    return sorted(out)


def generate_candidates(industry: str, keywords: list[str], tone: str, count: int) -> list[str]:
    return rule_based_candidates(industry, keywords, count)
