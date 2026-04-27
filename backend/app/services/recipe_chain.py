from __future__ import annotations

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.models.schema import GenerateRecipeRequest, RecipeDraft
from app.services.chain_utils import invoke_structured_chain


class RecipeGenerationChain:
    def __init__(self, llm, parser_max_retries: int) -> None:
        self.llm = llm
        self.parser_max_retries = parser_max_retries
        self.parser = PydanticOutputParser(pydantic_object=RecipeDraft)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert chef assistant. "
                    "Generate one recipe using ONLY the provided ingredients when possible. "
                    "Do not add narrative text. Return JSON only and follow format instructions exactly.\n"
                    "If ingredients are insufficient, still produce a practical minimal recipe and keep assumptions small.\n"
                    "{format_instructions}",
                ),
                (
                    "human",
                    "User ingredients list: {ingredients}\n"
                    "User free text: {free_text}\n"
                    "Rules:\n"
                    "1) Keep steps concise and actionable.\n"
                    "2) Include explicit quantity for each ingredient in the output.\n"
                    "3) Cooking time must be integer minutes.\n"
                    "4) Return JSON only.",
                ),
            ]
        )

    def run(self, payload: GenerateRecipeRequest) -> RecipeDraft:
        ingredients_text = ", ".join(payload.ingredients) if payload.ingredients else ""

        result = invoke_structured_chain(
            llm=self.llm,
            prompt=self.prompt,
            parser=self.parser,
            input_data={"ingredients": ingredients_text, "free_text": payload.free_text},
            parser_max_retries=self.parser_max_retries,
        )
        if not isinstance(result, RecipeDraft):
            raise TypeError("RecipeGenerationChain returned invalid type")
        return result
