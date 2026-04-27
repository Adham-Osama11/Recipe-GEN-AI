from app.models.schema import RecipeIngredient
from app.utils.nutrition import estimate_recipe_calories


def test_estimate_recipe_calories_known_ingredients() -> None:
    ingredients = [
        RecipeIngredient(name="chicken", quantity="200 g"),
        RecipeIngredient(name="rice", quantity="150 g"),
    ]

    result = estimate_recipe_calories(ingredients)

    assert result.total_calories > 0
    assert not result.unknown_ingredients
    assert len(result.breakdown) == 2


def test_estimate_recipe_calories_unknown_ingredient_fallback() -> None:
    ingredients = [RecipeIngredient(name="dragon fruit", quantity="1 piece")]

    result = estimate_recipe_calories(ingredients)

    assert result.total_calories > 0
    assert "dragon fruit" in result.unknown_ingredients
