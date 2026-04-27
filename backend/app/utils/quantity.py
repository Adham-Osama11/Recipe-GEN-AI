from __future__ import annotations

import re
from fractions import Fraction


UNIT_ALIASES: dict[str, str] = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "liter": "l",
    "litre": "l",
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "clove": "clove",
    "cloves": "clove",
}


def _parse_fraction(token: str) -> float | None:
    try:
        if "/" in token:
            return float(Fraction(token))
        return float(token)
    except (ValueError, ZeroDivisionError):
        return None


def extract_amount(quantity: str) -> float:
    normalized = quantity.strip().lower()
    if not normalized:
        return 1.0

    mixed_number = re.search(r"(\d+)\s+(\d+/\d+)", normalized)
    if mixed_number:
        whole = float(mixed_number.group(1))
        frac = _parse_fraction(mixed_number.group(2)) or 0.0
        return whole + frac

    direct = re.search(r"(\d+(?:\.\d+)?|\d+/\d+)", normalized)
    if direct:
        value = _parse_fraction(direct.group(1))
        if value is not None and value > 0:
            return value
    return 1.0


def extract_unit(quantity: str) -> str:
    normalized = quantity.strip().lower()
    tokens = re.findall(r"[a-zA-Z]+", normalized)
    for token in tokens:
        if token in UNIT_ALIASES:
            return UNIT_ALIASES[token]
    return "unit"


def quantity_to_grams(amount: float, unit: str) -> float:
    unit_to_grams = {
        "g": 1.0,
        "kg": 1000.0,
        "ml": 1.0,
        "l": 1000.0,
        "cup": 240.0,
        "tbsp": 15.0,
        "tsp": 5.0,
        "piece": 60.0,
        "clove": 5.0,
        "unit": 60.0,
    }
    return amount * unit_to_grams.get(unit, 60.0)
