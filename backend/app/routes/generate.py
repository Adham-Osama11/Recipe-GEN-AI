from __future__ import annotations

from pydantic import ValidationError

from app.models.schema import GenerateRecipeRequest, RecipeResponse
from app.services.orchestrator import RecipeOrchestrator, get_orchestrator

def generate_recipe(
    payload: GenerateRecipeRequest,
    orchestrator: RecipeOrchestrator,
) -> RecipeResponse:
    try:
        return orchestrator.generate(payload)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc


def handle_generate_request(
    payload_data: dict,
    orchestrator: RecipeOrchestrator | None = None,
) -> tuple[int, dict]:
    try:
        payload = GenerateRecipeRequest.model_validate(payload_data)
    except ValidationError as exc:
        return 422, {"detail": exc.errors(include_url=False)}

    active_orchestrator = orchestrator or get_orchestrator()
    try:
        recipe = generate_recipe(payload=payload, orchestrator=active_orchestrator)
        return 200, recipe.model_dump()
    except ValueError as exc:
        return 400, {"detail": str(exc)}
    except RuntimeError as exc:
        return 500, {"detail": str(exc)}
