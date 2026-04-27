from __future__ import annotations

import re

from app.models.schema import Alternatives, GenerateRecipeRequest, RecipeIngredient, RecipeResponse
from app.utils.nutrition import estimate_recipe_calories
from app.utils.pricing import estimate_recipe_cost


DEFAULT_QUANTITY_MAP: dict[str, str] = {
    "chicken": "200 g",
    "beef": "200 g",
    "rice": "150 g",
    "pasta": "150 g",
    "egg": "2 pieces",
    "tomato": "2 pieces",
    "onion": "1 piece",
    "potato": "2 pieces",
    "olive oil": "1 tbsp",
    "garlic": "2 cloves",
    "lentils": "150 g",
}

HEALTHIER_SWAP_MAP: dict[str, str] = {
    "rice": "Use brown rice instead of white rice for more fiber.",
    "beef": "Replace part of beef with lentils to reduce saturated fat.",
    "butter": "Use olive oil instead of butter for healthier fats.",
    "pasta": "Use whole-wheat pasta for better fiber intake.",
}

CHEAPER_SWAP_MAP: dict[str, str] = {
    "beef": "Use chicken or lentils instead of beef to reduce cost.",
    "olive oil": "Use sunflower oil if available at lower local price.",
    "cheese": "Reduce cheese quantity or use local white cheese.",
    "chicken": "Replace part of chicken with lentils or eggs.",
}


def _tokenize_free_text(text: str) -> list[str]:
    tokens = [part.strip() for part in re.split(r"[,:;\n]", text.lower()) if part.strip()]
    return [token for token in tokens if token.isalpha() and len(token) > 2]


def _build_ingredients(payload: GenerateRecipeRequest) -> list[RecipeIngredient]:
    names = [name.strip().lower() for name in payload.ingredients if name.strip()]
    if not names:
        names = _tokenize_free_text(payload.free_text)

    if not names:
        names = ["tomato", "onion", "egg"]

    unique_names: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    ingredients: list[RecipeIngredient] = []
    for name in unique_names[:8]:
        quantity = DEFAULT_QUANTITY_MAP.get(name, "1 piece")
        ingredients.append(RecipeIngredient(name=name, quantity=quantity))
    return ingredients


def _build_steps(ingredients: list[RecipeIngredient]) -> list[str]:
    joined_names = ", ".join(item.name for item in ingredients[:4])
    return [
        f"Wash and prepare the ingredients: {joined_names}.",
        "Heat a pan with a small amount of oil and saute aromatics first.",
        "Add the main ingredients, season with salt and pepper, and cook until tender.",
        "Adjust seasoning, plate, and serve warm.",
    ]


def _build_alternatives(ingredients: list[RecipeIngredient]) -> Alternatives:
    healthier: list[str] = []
    cheaper: list[str] = []

    for ingredient in ingredients:
        key = ingredient.name.lower()
        if key in HEALTHIER_SWAP_MAP and HEALTHIER_SWAP_MAP[key] not in healthier:
            healthier.append(HEALTHIER_SWAP_MAP[key])
        if key in CHEAPER_SWAP_MAP and CHEAPER_SWAP_MAP[key] not in cheaper:
            cheaper.append(CHEAPER_SWAP_MAP[key])

    if not healthier:
        healthier = [
            "Use less oil and increase vegetables to lower calories.",
            "Bake or grill instead of deep frying when possible.",
        ]
    if not cheaper:
        cheaper = [
            "Use seasonal local produce to reduce ingredient costs.",
            "Replace part of meat with lentils or beans for a cheaper protein mix.",
        ]

    return Alternatives(healthier=healthier[:4], cheaper=cheaper[:4])


def generate_fallback_recipe(payload: GenerateRecipeRequest, reason: str = "") -> RecipeResponse:
    ingredients = _build_ingredients(payload)
    steps = _build_steps(ingredients)

    calories = estimate_recipe_calories(ingredients)
    cost = estimate_recipe_cost(ingredients)
    alternatives = _build_alternatives(ingredients)

    main = ingredients[0].name.title() if ingredients else "Kitchen"
    cooking_time = min(45, max(15, 10 + len(ingredients) * 4))

    recipe_name = f"Quick {main} Home Bowl"
    if reason:
        recipe_name = recipe_name

    return RecipeResponse(
        recipe_name=recipe_name,
        cooking_time=cooking_time,
        calories=round(calories.total_calories, 2),
        cost=round(cost.total_cost, 2),
        ingredients=ingredients,
        steps=steps,
        alternatives=alternatives,
    )
