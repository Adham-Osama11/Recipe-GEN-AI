from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class GenerateRecipeRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list, description="Ingredient names from user")
    free_text: str = Field(default="", description="Natural language instruction")

    @model_validator(mode="after")
    def validate_non_empty_input(self) -> "GenerateRecipeRequest":
        has_ingredients = any(item.strip() for item in self.ingredients)
        has_text = bool(self.free_text.strip())
        if not has_ingredients and not has_text:
            raise ValueError("Provide at least one ingredient or free_text.")

        self.ingredients = [item.strip() for item in self.ingredients if item.strip()]
        self.free_text = self.free_text.strip()
        return self


class RecipeIngredient(BaseModel):
    name: str = Field(min_length=1)
    quantity: str = Field(min_length=1)


class RecipeDraft(BaseModel):
    recipe_name: str = Field(min_length=3)
    cooking_time: int = Field(ge=1, le=360)
    ingredients: list[RecipeIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)


class IngredientEstimate(BaseModel):
    name: str = Field(min_length=1)
    quantity: str = Field(min_length=1)
    estimated_grams: float | None = Field(default=None, ge=0)
    estimated_units: float | None = Field(default=None, ge=0)


class NutritionCostDraft(BaseModel):
    ingredient_estimates: list[IngredientEstimate] = Field(default_factory=list)
    calories_hint: float | None = Field(default=None, ge=0)
    cost_hint: float | None = Field(default=None, ge=0)
    notes: str = ""


class Alternatives(BaseModel):
    healthier: list[str] = Field(default_factory=list)
    cheaper: list[str] = Field(default_factory=list)


class RecipeResponse(BaseModel):
    recipe_name: str
    cooking_time: int
    calories: float = Field(ge=0)
    cost: float = Field(ge=0)
    ingredients: list[RecipeIngredient]
    steps: list[str]
    alternatives: Alternatives


class GenerateResponseEnvelope(BaseModel):
    data: RecipeResponse
