from app.models.schema import RecipeIngredient
from app.utils.pricing import estimate_recipe_cost


def test_estimate_recipe_cost_known_ingredients() -> None:
    ingredients = [
        RecipeIngredient(name="egg", quantity="2 pieces"),
        RecipeIngredient(name="tomato", quantity="200 g"),
    ]

    result = estimate_recipe_cost(ingredients)

    assert result.total_cost > 0
    assert len(result.breakdown) == 2


def test_estimate_recipe_cost_unknown_fallback() -> None:
    ingredients = [RecipeIngredient(name="mystery spice", quantity="1 tsp")]

    result = estimate_recipe_cost(ingredients)

    assert result.total_cost > 0
    assert "mystery spice" in result.unknown_ingredients
