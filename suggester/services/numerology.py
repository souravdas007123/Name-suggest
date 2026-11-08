"""Chaldean numerology helpers. Is file mein Django import nahi hai.

NOTE: COMPATIBLE_NUMBERS table graha-maitri (planetary friendship) par based ek
starting point hai. Ise kisi numerologist/astrologer se verify karke apne hisaab
se badal lein -- product ki credibility yahi table hai.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# Standard Chaldean letter values (9 ko letters assign nahi hota)
CHALDEAN = {
    **dict.fromkeys("AIJQY", 1),
    **dict.fromkeys("BKR", 2),
    **dict.fromkeys("CGLS", 3),
    **dict.fromkeys("DMT", 4),
    **dict.fromkeys("EHNX", 5),
    **dict.fromkeys("UVW", 6),
    **dict.fromkeys("OZ", 7),
    **dict.fromkeys("FP", 8),
}

PLANETS = {
    1: "Sun (Surya)", 2: "Moon (Chandra)", 3: "Jupiter (Guru)",
    4: "Rahu", 5: "Mercury (Budh)", 6: "Venus (Shukra)",
    7: "Ketu", 8: "Saturn (Shani)", 9: "Mars (Mangal)",
}

# Har number ke liye uske friendly numbers (khud ka number bhi shamil)
COMPATIBLE_NUMBERS = {
    1: {1, 2, 3, 9},
    2: {1, 2, 5, 7},
    3: {1, 2, 3, 9},
    4: {4, 5, 6, 8},
    5: {2, 4, 5, 6},
    6: {4, 5, 6, 8},
    7: {2, 6, 7},
    8: {4, 5, 6, 8},
    9: {1, 2, 3, 9},
}


def digit_root(n: int, keep_master: bool = False) -> int:
    """Number ko single digit tak reduce karo (optionally 11/22 rakhte hue)."""
    n = abs(int(n))
    while n > 9:
        if keep_master and n in (11, 22):
            return n
        n = sum(int(d) for d in str(n))
    return n


def moolank(dob: date) -> int:
    """Janm tarikh (day of month) ka single digit."""
    return digit_root(dob.day)


def bhagyank(dob: date) -> int:
    """Poori DOB ke digits ka yog."""
    return digit_root(sum(int(c) for c in dob.strftime("%d%m%Y")))


def raw_name_total(name: str) -> int:
    return sum(CHALDEAN.get(c, 0) for c in name.upper() if c.isalpha())


def name_number(name: str) -> int:
    """Naam ka single-digit Chaldean number."""
    return digit_root(raw_name_total(name))


def compound_number(name: str) -> int:
    """Reduce hone se pehle ka total (jaise 23, 32 -- compound number)."""
    return raw_name_total(name)


@dataclass(frozen=True)
class AstroProfile:
    moolank: int
    bhagyank: int
    sun_sign: str
    allowed_numbers: frozenset   # Moolank ke anukul naam-ank (filter yahi hai)
    strong_numbers: frozenset    # jo Moolank aur Bhagyank, dono se match karte hain

    @property
    def allowed_sorted(self) -> list:
        return sorted(self.allowed_numbers)

    @property
    def allowed_marked(self) -> list:
        """[(number, is_strong)] template ke liye."""
        return [(n, n in self.strong_numbers) for n in sorted(self.allowed_numbers)]

    @property
    def moolank_planet(self) -> str:
        return PLANETS[self.moolank]

    @property
    def bhagyank_planet(self) -> str:
        return PLANETS[self.bhagyank]


_SIGNS = [
    ((1, 20), "Capricorn (Makar)"), ((2, 19), "Aquarius (Kumbh)"), ((3, 21), "Pisces (Meen)"),
    ((4, 20), "Aries (Mesh)"), ((5, 21), "Taurus (Vrishabh)"), ((6, 21), "Gemini (Mithun)"),
    ((7, 23), "Cancer (Kark)"), ((8, 23), "Leo (Singh)"), ((9, 23), "Virgo (Kanya)"),
    ((10, 23), "Libra (Tula)"), ((11, 22), "Scorpio (Vrishchik)"), ((12, 22), "Sagittarius (Dhanu)"),
]


def sun_sign(dob: date) -> str:
    """Western/tropical sun sign. (Vedic rashi ke liye birth time+place chahiye.)"""
    for (month, last_day), sign in _SIGNS:
        if (dob.month, dob.day) < (month, last_day):
            return sign
    return "Capricorn (Makar)"


def build_profile(dob: date) -> AstroProfile:
    """Moolank primary hai (naam usi ke anukul hona chahiye); Bhagyank se bhi
    match ho to naam 'strong' maana jata hai aur score mein bonus milta hai.
    (Dono ka intersection filter banane se bahut kam naam bachte the, aur union
    se lagbhag har naam pass ho jata tha.)"""
    m, b = moolank(dob), bhagyank(dob)
    allowed = frozenset(COMPATIBLE_NUMBERS[m])
    strong = frozenset(COMPATIBLE_NUMBERS[m] & COMPATIBLE_NUMBERS[b])
    return AstroProfile(m, b, sun_sign(dob), allowed, strong)


def is_strong(name: str, profile: AstroProfile) -> bool:
    return name_number(name) in profile.strong_numbers


def is_compatible(name: str, profile: AstroProfile) -> bool:
    return name_number(name) in profile.allowed_numbers
