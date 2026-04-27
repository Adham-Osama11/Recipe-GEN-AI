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
                    """
You are a professional chef, cookbook author, and meal planner.

Generate recipes that feel like real cookbook recipes, not AI summaries.

STRICT RULES:

1. Use the user's ingredients as the main ingredients.
2. You may add common pantry ingredients when useful:
salt, pepper, oil, butter, garlic, onion, lemon, herbs, spices.
3. Recipe title must sound appetizing and realistic.
4. Steps must be highly detailed and practical.
5. Minimum 8 steps. Maximum 14 steps.
6. Each step must include at least one of:
   - cooking time
   - heat level
   - texture cue
   - color cue
   - aroma cue
7. Never use vague phrases:
   - cook until done
   - prepare ingredients
   - serve warm
   - mix everything
8. Recipe must be useful for real home cooking.
9. Cooking time must match the steps.
10. Return JSON only.

{format_instructions}
"""
                ),
                (
                    "human",
                    """
User ingredients:
{ingredients}

User request:
{free_text}

Rules:
- Include exact ingredient quantities.
- Include seasoning.
- Make recipe flavorful.
- Steps should read like a cookbook.
- Return JSON only.
"""
                ),
            ]
        )

    def run(self, payload: GenerateRecipeRequest) -> RecipeDraft:
        ingredients_text = ", ".join(payload.ingredients) if payload.ingredients else ""

        result = invoke_structured_chain(
            llm=self.llm,
            prompt=self.prompt,
            parser=self.parser,
            input_data={
                "ingredients": ingredients_text,
                "free_text": payload.free_text,
            },
            parser_max_retries=self.parser_max_retries,
        )

        if not isinstance(result, RecipeDraft):
            raise TypeError("RecipeGenerationChain returned invalid type")

        return result