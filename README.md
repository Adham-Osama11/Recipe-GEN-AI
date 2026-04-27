# AI Recipe Generator (Simple, No Frameworks)

This project is intentionally minimal:
- Backend: built-in Python HTTP server (no FastAPI/Flask/Django)
- Frontend: plain HTML, CSS, and vanilla JavaScript (no React/Vue/Angular)
- Core value: LangChain orchestration for recipe generation, nutrition support, and alternatives

## Architecture

1. Browser sends a JSON request to `/api/v1/generate`.
2. Backend validates input with Pydantic.
3. Orchestrator runs the LangChain pipeline:
   - Recipe generation chain
   - Nutrition/cost support chain
   - Alternatives chain
4. Deterministic utilities compute calories and cost.
5. Backend returns strict JSON response.

## Project Layout

- `backend/app/main.py`: tiny HTTP server + API/static routing
- `backend/app/routes/generate.py`: request validation and generate handler
- `backend/app/services/`: LangChain chains and orchestrator
- `backend/app/utils/`: nutrition/pricing/quantity deterministic logic
- `frontend/index.html`: full UI markup
- `frontend/src/main.js`: UI behavior and rendering
- `frontend/src/services/api.js`: API calls
- `frontend/src/styles/app.css`: styling

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your Groq credentials in `backend/.env`:

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

## Run the App

From the backend folder:

```bash
cd backend
source .venv/bin/activate
python -m app.main
```

Default address:
- `http://localhost:8000/`

Endpoints:
- `GET /health`
- `POST /api/v1/generate`
- `POST /generate` (also supported)

The same server also serves the frontend static files from the `frontend` folder.

## Request / Response

Request:

```json
{
  "ingredients": ["chicken", "rice", "onion", "tomato"],
  "free_text": "high protein and under 30 minutes"
}
```

Response shape:

```json
{
  "recipe_name": "Chicken Tomato Rice Bowl",
  "cooking_time": 28,
  "calories": 640.5,
  "cost": 94.2,
  "ingredients": [
    { "name": "chicken", "quantity": "200 g" }
  ],
  "steps": ["..."],
  "alternatives": {
    "healthier": ["..."],
    "cheaper": ["..."]
  }
}
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Included tests cover:
- Generate handler success and input validation
- Fallback generation shape
- Nutrition utility calculations
- Pricing utility calculations
