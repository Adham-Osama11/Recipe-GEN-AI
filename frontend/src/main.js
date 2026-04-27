import { generateRecipe } from "./services/api.js";

const form = document.getElementById("recipe-form");
const ingredientsField = document.getElementById("ingredients");
const contextField = document.getElementById("context");
const ingredientCountEl = document.getElementById("ingredient-count");
const submitButton = document.getElementById("submit-button");
const errorMessageEl = document.getElementById("error-message");
const recipeCardEl = document.getElementById("recipe-card");

function parseIngredients(rawValue) {
  return rawValue
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderRecipe(recipe) {
  const ingredientsMarkup = recipe.ingredients
    .map((ingredient) => {
      return `<li><strong>${escapeHtml(ingredient.name)}</strong> - ${escapeHtml(ingredient.quantity)}</li>`;
    })
    .join("");

  const stepsMarkup = recipe.steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("");

  const healthierMarkup =
    recipe.alternatives.healthier.length > 0
      ? recipe.alternatives.healthier.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : "<li>No suggestion</li>";

  const cheaperMarkup =
    recipe.alternatives.cheaper.length > 0
      ? recipe.alternatives.cheaper.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : "<li>No suggestion</li>";

  recipeCardEl.innerHTML = `
    <header class="recipe-header">
      <h2>${escapeHtml(recipe.recipe_name)}</h2>
      <div class="recipe-meta">
        <span>${Number(recipe.cooking_time)} min</span>
        <span>${Math.round(Number(recipe.calories))} kcal</span>
        <span>${Number(recipe.cost).toFixed(2)} EGP</span>
      </div>
    </header>

    <div class="recipe-grid">
      <div>
        <h3>Ingredients</h3>
        <ul>${ingredientsMarkup}</ul>
      </div>

      <div>
        <h3>Steps</h3>
        <ol>${stepsMarkup}</ol>
      </div>
    </div>

    <div class="alternatives">
      <h3>Alternatives</h3>
      <div class="alt-columns">
        <div>
          <h4>Healthier</h4>
          <ul>${healthierMarkup}</ul>
        </div>
        <div>
          <h4>Cheaper</h4>
          <ul>${cheaperMarkup}</ul>
        </div>
      </div>
    </div>
  `;

  recipeCardEl.hidden = false;
}

function setLoadingState(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Generating..." : "Generate Recipe";
}

function setError(message) {
  const hasError = Boolean(message);
  errorMessageEl.hidden = !hasError;
  errorMessageEl.textContent = message || "";
}

function updateIngredientCount() {
  const ingredientCount = parseIngredients(ingredientsField.value).length;
  ingredientCountEl.textContent = `${ingredientCount} ingredient(s) detected`;
}

ingredientsField.addEventListener("input", updateIngredientCount);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError("");

  const ingredients = parseIngredients(ingredientsField.value);
  const freeText = contextField.value.trim();

  if (!ingredients.length && !freeText) {
    setError("Add at least one ingredient or some free text.");
    return;
  }

  setLoadingState(true);
  try {
    const data = await generateRecipe({ ingredients, free_text: freeText });
    renderRecipe(data);
  } catch (error) {
    setError(error instanceof Error ? error.message : "Failed to generate recipe");
  } finally {
    setLoadingState(false);
  }
});

updateIngredientCount();
