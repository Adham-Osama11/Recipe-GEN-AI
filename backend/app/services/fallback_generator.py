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
    "beans": "150 g",
    "oats": "100 g",
    "fish": "180 g",
    "spinach": "120 g",
    "carrot": "1 piece",
    "cucumber": "1 piece",
    "pepper": "1 piece",
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

NAME_ALIASES: dict[str, str] = {
    "eggs": "egg",
    "tomatoes": "tomato",
    "potatoes": "potato",
    "lentil": "lentils",
    "bean": "beans",
}

KNOWN_FREE_TEXT_INGREDIENTS: tuple[str, ...] = tuple(
    sorted(
        set(DEFAULT_QUANTITY_MAP)
        | {
            "beans",
            "fish",
            "oats",
            "pepper",
            "spinach",
            "carrot",
            "cucumber",
            "salad",
        }
    )
)

QUANTITY_PREFIX_PATTERN = re.compile(
    r"^\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|gm|ml|l|tbsp|tsp|cup|cups|piece|pieces|clove|cloves)?\s+(?P<name>[a-zA-Z][a-zA-Z\s\-]{1,})\s*$"
)

UNIT_ALIASES: dict[str, str] = {
    "gm": "g",
    "cups": "cup",
    "pieces": "piece",
    "cloves": "clove",
}

PROTEIN_INGREDIENTS: set[str] = {"chicken", "beef", "egg", "lentils", "beans", "fish", "cheese", "tuna"}
CARB_INGREDIENTS: set[str] = {"rice", "pasta", "potato", "oats", "bread"}
AROMATIC_INGREDIENTS: set[str] = {"onion", "garlic", "ginger"}


def _clean_name(raw_name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z\s\-]", " ", raw_name.lower())
    normalized = " ".join(normalized.split())
    return NAME_ALIASES.get(normalized, normalized)


def _format_quantity(amount: float, unit: str | None) -> str:
    value_text = str(int(amount)) if amount.is_integer() else f"{amount:g}"
    if not unit:
        label = "piece" if amount == 1 else "pieces"
        return f"{value_text} {label}"

    canonical_unit = UNIT_ALIASES.get(unit, unit)
    if canonical_unit == "piece":
        label = "piece" if amount == 1 else "pieces"
        return f"{value_text} {label}"
    if canonical_unit == "clove":
        label = "clove" if amount == 1 else "cloves"
        return f"{value_text} {label}"
    if canonical_unit == "cup":
        label = "cup" if amount == 1 else "cups"
        return f"{value_text} {label}"
    return f"{value_text} {canonical_unit}"


def _parse_ingredient_entry(entry: str) -> tuple[str, str] | None:
    cleaned = entry.strip()
    if not cleaned:
        return None

    match = QUANTITY_PREFIX_PATTERN.match(cleaned)
    if match:
        amount = float(match.group("amount"))
        unit = match.group("unit")
        name = _clean_name(match.group("name"))
        if not name:
            return None
        return name, _format_quantity(amount, unit)

    name = _clean_name(cleaned)
    if not name:
        return None
    quantity = DEFAULT_QUANTITY_MAP.get(name, "1 piece")
    return name, quantity


def _tokenize_free_text(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for ingredient in KNOWN_FREE_TEXT_INGREDIENTS:
        if re.search(rf"\b{re.escape(ingredient)}\b", lowered):
            found.append(ingredient)
    return found


def _default_ingredients_from_context(free_text: str) -> list[str]:
    lowered = free_text.lower()
    if "high protein" in lowered or "protein" in lowered:
        return ["egg", "lentils", "onion"]
    if "vegan" in lowered or "vegetarian" in lowered:
        return ["lentils", "rice", "tomato"]
    if "breakfast" in lowered:
        return ["oats", "egg", "tomato"]
    if "quick" in lowered or re.search(r"under\s*2\d", lowered):
        return ["egg", "tomato", "onion"]
    return ["tomato", "onion", "egg"]


def _build_ingredients(payload: GenerateRecipeRequest) -> list[RecipeIngredient]:
    candidates: list[tuple[str, str]] = []
    for name in payload.ingredients:
        parsed = _parse_ingredient_entry(name)
        if parsed:
            candidates.append(parsed)

    if not candidates:
        names = _tokenize_free_text(payload.free_text)
        if not names:
            names = _default_ingredients_from_context(payload.free_text)
        candidates = [(name, DEFAULT_QUANTITY_MAP.get(name, "1 piece")) for name in names]

    ingredients: list[RecipeIngredient] = []
    seen: set[str] = set()
    for name, quantity in candidates:
        if name in seen:
            continue
        seen.add(name)
        ingredients.append(RecipeIngredient(name=name, quantity=quantity))
        if len(ingredients) == 8:
            break
    return ingredients


def _infer_style(free_text: str) -> str:
    lowered = free_text.lower()
    if "bake" in lowered or "oven" in lowered:
        return "baked"
    if "grill" in lowered:
        return "grilled"
    if "soup" in lowered or "stew" in lowered:
        return "simmered"
    if "salad" in lowered:
        return "salad"
    return "skillet"


def _build_steps(ingredients: list[RecipeIngredient], free_text: str) -> list[str]:
    names = [item.name for item in ingredients]
    prep_names = ", ".join(f"{item.quantity} {item.name}" for item in ingredients[:4])
    aromatics = [name for name in names if name in AROMATIC_INGREDIENTS]
    proteins = [name for name in names if name in PROTEIN_INGREDIENTS]
    carbs = [name for name in names if name in CARB_INGREDIENTS]
    style = _infer_style(free_text)

    steps = [f"Prepare and portion: {prep_names}. Keep similar cut size for even cooking."]

    if aromatics:
        aromatic_text = ", ".join(aromatics[:2])
        steps.append(f"Heat 1 tbsp oil and cook {aromatic_text} for 2 minutes until fragrant.")
    else:
        steps.append("Heat 1 tbsp oil in a pan over medium heat for 1 minute.")

    main_protein = proteins[0] if proteins else (names[0] if names else "ingredients")
    main_carb = carbs[0] if carbs else ""

    if style == "baked":
        steps.append(
            f"Combine {', '.join(names[:3])} with salt, pepper, and spices, then bake at 200C for 18-22 minutes."
        )
    elif style == "grilled":
        steps.append(f"Season {main_protein} and grill each side for 4-6 minutes until cooked through.")
    elif style == "simmered":
        steps.append(
            f"Add {', '.join(names[:3])} with 2 cups water or stock and simmer gently for 15-20 minutes."
        )
    elif style == "salad":
        steps.append(
            f"Cook {main_protein} if needed, then toss with {', '.join(names[:3])} and a light lemon-olive oil dressing."
        )
    elif main_carb:
        steps.append(
            f"Add {main_protein} and {main_carb}, then cook with 2 cups water for 12-15 minutes until tender."
        )
    else:
        steps.append(f"Cook {', '.join(names[:3])} for 8-10 minutes, stirring often to avoid sticking.")

    lowered = free_text.lower()
    if "high protein" in lowered or "protein" in lowered:
        steps.append("Finish with a protein boost such as boiled egg, beans, or yogurt topping before serving.")
    elif "low calorie" in lowered or "light" in lowered:
        steps.append("Use minimal oil, taste and adjust seasoning, then serve warm with extra vegetables.")
    else:
        steps.append("Taste, adjust salt and pepper, and serve warm.")

    return steps


def _build_alternatives(ingredients: list[RecipeIngredient], free_text: str) -> Alternatives:
    healthier: list[str] = []
    cheaper: list[str] = []

    for ingredient in ingredients:
        key = ingredient.name.lower()
        if key in HEALTHIER_SWAP_MAP and HEALTHIER_SWAP_MAP[key] not in healthier:
            healthier.append(HEALTHIER_SWAP_MAP[key])
        if key in CHEAPER_SWAP_MAP and CHEAPER_SWAP_MAP[key] not in cheaper:
            cheaper.append(CHEAPER_SWAP_MAP[key])

    ingredient_names = {ingredient.name.lower() for ingredient in ingredients}
    lowered = free_text.lower()

    if "high protein" in lowered and not ingredient_names.intersection(PROTEIN_INGREDIENTS):
        healthier.append("Add eggs, beans, or lentils to increase protein without major cost increase.")
    if "budget" in lowered or "cheap" in lowered:
        cheaper.append("Batch-cook and freeze portions to reduce waste and daily cooking cost.")

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


def _build_recipe_name(ingredients: list[RecipeIngredient], free_text: str) -> str:
    style = _infer_style(free_text)
    style_label = {
        "baked": "Bake",
        "grilled": "Grill",
        "simmered": "Stew",
        "salad": "Salad",
        "skillet": "Skillet",
    }.get(style, "Bowl")

    first = ingredients[0].name.title() if ingredients else "Kitchen"
    second = ingredients[1].name.title() if len(ingredients) > 1 else ""

    lowered = free_text.lower()
    if "high protein" in lowered or "protein" in lowered:
        prefix = "High-Protein"
    elif "budget" in lowered or "cheap" in lowered:
        prefix = "Budget"
    elif "low calorie" in lowered or "light" in lowered:
        prefix = "Light"
    else:
        prefix = "Quick"

    if second:
        return f"{prefix} {first} and {second} {style_label}"
    return f"{prefix} {first} {style_label}"


def generate_fallback_recipe(payload: GenerateRecipeRequest, reason: str = "") -> RecipeResponse:
    ingredients = _build_ingredients(payload)
    steps = _build_steps(ingredients, payload.free_text)

    calories = estimate_recipe_calories(ingredients)
    cost = estimate_recipe_cost(ingredients)
    alternatives = _build_alternatives(ingredients, payload.free_text)

    style = _infer_style(payload.free_text)
    base_time = 10 + len(ingredients) * 4
    if style == "baked":
        base_time += 8
    elif style == "simmered":
        base_time += 5
    elif style == "salad":
        base_time -= 2
    cooking_time = min(55, max(12, base_time))

    recipe_name = _build_recipe_name(ingredients, payload.free_text)
    _ = reason  # Reserved for logging/debugging hooks without changing API shape.

    return RecipeResponse(
        recipe_name=recipe_name,
        cooking_time=cooking_time,
        calories=round(calories.total_calories, 2),
        cost=round(cost.total_cost, 2),
        ingredients=ingredients,
        steps=steps,
        alternatives=alternatives,
    )
