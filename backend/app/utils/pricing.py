from __future__ import annotations

from dataclasses import dataclass

from app.models.schema import IngredientEstimate, RecipeIngredient
from app.utils.quantity import extract_amount, extract_unit, quantity_to_grams


PRICE_PER_100G_EGP: dict[str, float] = {
    "rice": 4.0,
    "chicken": 9.5,
    "beef": 18.0,
    "onion": 1.8,
    "tomato": 2.0,
    "potato": 1.5,
    "olive oil": 12.0,
    "butter": 10.0,
    "milk": 2.6,
    "yogurt": 4.0,
    "carrot": 1.9,
    "bell pepper": 5.0,
    "garlic": 7.5,
    "lentils": 6.0,
    "pasta": 5.5,
    "cheese": 12.5,
    "bread": 4.0,
    "spinach": 2.2,
    "cucumber": 1.7,
}

PRICE_PER_UNIT_EGP: dict[str, float] = {
    "egg": 6.0,
    "onion": 3.0,
    "tomato": 4.0,
    "potato": 3.0,
    "garlic": 2.5,
}

DEFAULT_INGREDIENT_COST_EGP = 8.0


@dataclass
class IngredientCost:
    name: str
    amount: float
    unit: str
    cost: float
    source: str


@dataclass
class RecipeCost:
    total_cost: float
    breakdown: list[IngredientCost]
    unknown_ingredients: list[str]


def normalize_name(name: str) -> str:
    return name.strip().lower()


def _find_estimate(name: str, estimates: list[IngredientEstimate]) -> IngredientEstimate | None:
    normalized = normalize_name(name)
    for estimate in estimates:
        if normalize_name(estimate.name) == normalized:
            return estimate
    return None


def estimate_recipe_cost(
    ingredients: list[RecipeIngredient],
    estimates: list[IngredientEstimate] | None = None,
) -> RecipeCost:
    estimates = estimates or []
    breakdown: list[IngredientCost] = []
    unknown_ingredients: list[str] = []

    for ingredient in ingredients:
        normalized = normalize_name(ingredient.name)
        estimate = _find_estimate(ingredient.name, estimates)

        amount = extract_amount(ingredient.quantity)
        unit = extract_unit(ingredient.quantity)

        if estimate and estimate.estimated_units and normalized in PRICE_PER_UNIT_EGP:
            amount = float(estimate.estimated_units)
            unit = "piece"
            cost = amount * PRICE_PER_UNIT_EGP[normalized]
            source = "llm_estimate"
        elif normalized in PRICE_PER_UNIT_EGP and unit in {"piece", "clove", "unit"}:
            cost = amount * PRICE_PER_UNIT_EGP[normalized]
            source = "deterministic_unit"
        elif normalized in PRICE_PER_100G_EGP:
            grams = float(estimate.estimated_grams) if estimate and estimate.estimated_grams else quantity_to_grams(amount, unit)
            cost = (grams / 100.0) * PRICE_PER_100G_EGP[normalized]
            amount = grams
            unit = "g"
            source = "deterministic_weight"
        else:
            cost = DEFAULT_INGREDIENT_COST_EGP
            source = "fallback_default"
            unknown_ingredients.append(ingredient.name)

        breakdown.append(
            IngredientCost(
                name=ingredient.name,
                amount=round(amount, 2),
                unit=unit,
                cost=round(cost, 2),
                source=source,
            )
        )

    total = round(sum(item.cost for item in breakdown), 2)
    return RecipeCost(total_cost=total, breakdown=breakdown, unknown_ingredients=unknown_ingredients)
