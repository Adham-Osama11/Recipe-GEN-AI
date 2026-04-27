from __future__ import annotations

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.models.schema import NutritionCostDraft, RecipeDraft
from app.services.chain_utils import invoke_structured_chain


class NutritionCostChain:
    def __init__(self, llm, parser_max_retries: int) -> None:
        self.llm = llm
        self.parser_max_retries = parser_max_retries
        self.parser = PydanticOutputParser(pydantic_object=NutritionCostDraft)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a culinary data assistant. "
                    "Estimate ingredient grams/units for nutrition and cost calculation support. "
                    "Return JSON only and strictly follow format instructions.\n"
                    "Do not fabricate high-confidence totals. Leave unknown values null.\n"
                    "{format_instructions}",
                ),
                (
                    "human",
                    "Recipe name: {recipe_name}\n"
                    "Cooking time: {cooking_time}\n"
                    "Ingredients (name + quantity): {ingredients}\n"
                    "Return ingredient_estimates matching each ingredient.\n"
                    "Set estimated_grams and estimated_units when reasonably inferable.\n"
                    "Return JSON only.",
                ),
            ]
        )

    def run(self, recipe: RecipeDraft) -> NutritionCostDraft:
        ingredients_text = "; ".join(
            f"{ingredient.name}: {ingredient.quantity}" for ingredient in recipe.ingredients
        )

        result = invoke_structured_chain(
            llm=self.llm,
            prompt=self.prompt,
            parser=self.parser,
            input_data={
                "recipe_name": recipe.recipe_name,
                "cooking_time": recipe.cooking_time,
                "ingredients": ingredients_text,
            },
            parser_max_retries=self.parser_max_retries,
        )
        if not isinstance(result, NutritionCostDraft):
            raise TypeError("NutritionCostChain returned invalid type")
        return result
