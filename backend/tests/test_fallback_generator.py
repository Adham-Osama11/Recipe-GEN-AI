from app.models.schema import GenerateRecipeRequest
from app.services.fallback_generator import generate_fallback_recipe


def test_fallback_generator_produces_required_shape() -> None:
    payload = GenerateRecipeRequest(
        ingredients=["chicken", "rice", "onion", "tomato"],
        free_text="high protein under 30 minutes",
    )

    result = generate_fallback_recipe(payload, reason="quota exceeded")

    assert result.recipe_name
    assert result.cooking_time > 0
    assert result.calories >= 0
    assert result.cost >= 0
    assert len(result.ingredients) > 0
    assert len(result.steps) > 0
    assert isinstance(result.alternatives.healthier, list)
    assert isinstance(result.alternatives.cheaper, list)


def test_fallback_respects_inline_quantity_input() -> None:
    payload = GenerateRecipeRequest(
        ingredients=["100 gm oats", "2 eggs", "green salad"],
        free_text="under 25 minutes",
    )

    result = generate_fallback_recipe(payload)

    quantity_by_name = {item.name: item.quantity for item in result.ingredients}
    assert quantity_by_name.get("oats") == "100 g"
    assert quantity_by_name.get("egg") == "2 pieces"


def test_fallback_varies_recipe_across_distinct_inputs() -> None:
    savory_payload = GenerateRecipeRequest(
        ingredients=["chicken", "rice", "onion"],
        free_text="high protein skillet meal",
    )
    baked_payload = GenerateRecipeRequest(
        ingredients=["potato", "tomato", "lentils"],
        free_text="bake in the oven",
    )

    savory_result = generate_fallback_recipe(savory_payload)
    baked_result = generate_fallback_recipe(baked_payload)

    assert savory_result.recipe_name != baked_result.recipe_name
    assert savory_result.steps != baked_result.steps
