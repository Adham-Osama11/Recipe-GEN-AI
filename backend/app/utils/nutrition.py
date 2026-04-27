from __future__ import annotations

from dataclasses import dataclass

from app.models.schema import IngredientEstimate, RecipeIngredient
from app.utils.quantity import extract_amount, extract_unit, quantity_to_grams


CALORIES_PER_100G: dict[str, float] = {
    "rice": 130.0,
    "chicken": 165.0,
    "beef": 250.0,
    "onion": 40.0,
    "tomato": 18.0,
    "potato": 77.0,
    "olive oil": 884.0,
    "butter": 717.0,
    "egg": 155.0,
    "milk": 42.0,
    "yogurt": 59.0,
    "carrot": 41.0,
    "bell pepper": 31.0,
    "garlic": 149.0,
    "lentils": 116.0,
    "pasta": 131.0,
    "cheese": 402.0,
    "bread": 265.0,
    "spinach": 23.0,
    "cucumber": 15.0,
}

DEFAULT_CALORIES_PER_100G = 120.0


@dataclass
class IngredientCalories:
    name: str
    grams: float
    calories: float
    source: str


@dataclass
class RecipeCalories:
    total_calories: float
    breakdown: list[IngredientCalories]
    unknown_ingredients: list[str]


def normalize_name(name: str) -> str:
    return name.strip().lower()


def _find_estimate(name: str, estimates: list[IngredientEstimate]) -> IngredientEstimate | None:
    normalized = normalize_name(name)
    for estimate in estimates:
        if normalize_name(estimate.name) == normalized:
            return estimate
    return None


def estimate_recipe_calories(
    ingredients: list[RecipeIngredient],
    estimates: list[IngredientEstimate] | None = None,
) -> RecipeCalories:
    estimates = estimates or []
    breakdown: list[IngredientCalories] = []
    unknown_ingredients: list[str] = []

    for ingredient in ingredients:
        match = _find_estimate(ingredient.name, estimates)
        if match and match.estimated_grams:
            grams = float(match.estimated_grams)
            source = "llm_estimate"
        else:
            amount = extract_amount(ingredient.quantity)
            unit = extract_unit(ingredient.quantity)
            grams = quantity_to_grams(amount, unit)
            source = "heuristic"

        normalized = normalize_name(ingredient.name)
        calories_per_100g = CALORIES_PER_100G.get(normalized)
        if calories_per_100g is None:
            calories_per_100g = DEFAULT_CALORIES_PER_100G
            unknown_ingredients.append(ingredient.name)

        calories = (grams / 100.0) * calories_per_100g
        breakdown.append(
            IngredientCalories(
                name=ingredient.name,
                grams=round(grams, 2),
                calories=round(calories, 2),
                source=source,
            )
        )

    total = round(sum(item.calories for item in breakdown), 2)
    return RecipeCalories(total_calories=total, breakdown=breakdown, unknown_ingredients=unknown_ingredients)
