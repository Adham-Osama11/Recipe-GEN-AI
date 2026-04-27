from __future__ import annotations

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.models.schema import Alternatives, RecipeDraft
from app.services.chain_utils import invoke_structured_chain


class AlternativesChain:
    def __init__(self, llm, parser_max_retries: int) -> None:
        self.llm = llm
        self.parser_max_retries = parser_max_retries
        self.parser = PydanticOutputParser(pydantic_object=Alternatives)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a nutrition and budget optimization assistant. "
                    "Suggest realistic alternatives while preserving recipe intent. "
                    "Return JSON only and follow format instructions exactly.\n"
                    "{format_instructions}",
                ),
                (
                    "human",
                    "Recipe name: {recipe_name}\n"
                    "Calories estimate: {calories}\n"
                    "Cost estimate in EGP: {cost}\n"
                    "Ingredients: {ingredients}\n"
                    "Rules:\n"
                    "1) healthier: lower-calorie or higher-fiber/protein substitutions.\n"
                    "2) cheaper: substitutions likely to reduce EGP cost.\n"
                    "3) Max 4 items per list.\n"
                    "4) Return JSON only.",
                ),
            ]
        )

    def run(self, recipe: RecipeDraft, calories: float, cost: float) -> Alternatives:
        ingredients_text = ", ".join(ingredient.name for ingredient in recipe.ingredients)
        result = invoke_structured_chain(
            llm=self.llm,
            prompt=self.prompt,
            parser=self.parser,
            input_data={
                "recipe_name": recipe.recipe_name,
                "calories": calories,
                "cost": cost,
                "ingredients": ingredients_text,
            },
            parser_max_retries=self.parser_max_retries,
        )
        if not isinstance(result, Alternatives):
            raise TypeError("AlternativesChain returned invalid type")
        return result
