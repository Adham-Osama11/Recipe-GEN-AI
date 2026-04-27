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
