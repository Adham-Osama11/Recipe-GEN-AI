from app.models.schema import Alternatives, GenerateRecipeRequest, RecipeIngredient, RecipeResponse
from app.routes.generate import handle_generate_request


class FakeOrchestrator:
    def generate(self, payload: GenerateRecipeRequest) -> RecipeResponse:
        ingredients = payload.ingredients or ["tomato", "onion"]
        return RecipeResponse(
            recipe_name="Quick Tomato Skillet",
            cooking_time=20,
            calories=420.0,
            cost=68.5,
            ingredients=[
                RecipeIngredient(name=name, quantity="1 piece") for name in ingredients
            ],
            steps=[
                "Chop all ingredients.",
                "Saute onion, then add tomato and cook for 10 minutes.",
                "Season and serve.",
            ],
            alternatives=Alternatives(
                healthier=["Use less oil and add spinach."],
                cheaper=["Replace olive oil with sunflower oil."],
            ),
        )


def test_generate_success() -> None:
    status_code, data = handle_generate_request(
        payload_data={
            "ingredients": ["tomato", "onion", "egg"],
            "free_text": "high protein",
        },
        orchestrator=FakeOrchestrator(),
    )

    assert status_code == 200

    assert "recipe_name" in data
    assert "cooking_time" in data
    assert "calories" in data
    assert "cost" in data
    assert "ingredients" in data
    assert "steps" in data
    assert "alternatives" in data


def test_generate_empty_input_validation() -> None:
    status_code, data = handle_generate_request(
        payload_data={"ingredients": [], "free_text": ""},
        orchestrator=FakeOrchestrator(),
    )

    assert status_code == 422
    assert "detail" in data
