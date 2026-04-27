from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import get_settings
from app.models.schema import GenerateRecipeRequest, RecipeResponse
from app.services.alternatives_chain import AlternativesChain
from app.services.fallback_generator import generate_fallback_recipe
from app.services.nutrition_chain import NutritionCostChain
from app.services.recipe_chain import RecipeGenerationChain
from app.utils.nutrition import estimate_recipe_calories
from app.utils.pricing import estimate_recipe_cost


class RecipeOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings

        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.groq_temperature,
        )

        self.recipe_chain = RecipeGenerationChain(self.llm, settings.parser_max_retries)
        self.nutrition_chain = NutritionCostChain(self.llm, settings.parser_max_retries)
        self.alternatives_chain = AlternativesChain(self.llm, settings.parser_max_retries)

    def generate(self, payload: GenerateRecipeRequest) -> RecipeResponse:
        try:
            recipe_draft = self.recipe_chain.run(payload)

            nutrition_cost_draft = self.nutrition_chain.run(recipe_draft)

            calorie_result = estimate_recipe_calories(
                ingredients=recipe_draft.ingredients,
                estimates=nutrition_cost_draft.ingredient_estimates,
            )

            cost_result = estimate_recipe_cost(
                ingredients=recipe_draft.ingredients,
                estimates=nutrition_cost_draft.ingredient_estimates,
            )

            alternatives = self.alternatives_chain.run(
                recipe=recipe_draft,
                calories=calorie_result.total_calories,
                cost=cost_result.total_cost,
            )

            return RecipeResponse(
                recipe_name=recipe_draft.recipe_name,
                cooking_time=recipe_draft.cooking_time,
                calories=round(calorie_result.total_calories, 2),
                cost=round(cost_result.total_cost, 2),
                ingredients=recipe_draft.ingredients,
                steps=recipe_draft.steps,
                alternatives=alternatives,
            )

        except Exception as exc:
            print("MODEL FAILED:", str(exc))
            return generate_fallback_recipe(payload=payload, reason=str(exc))


@lru_cache(maxsize=1)
def get_orchestrator() -> RecipeOrchestrator:
    return RecipeOrchestrator()