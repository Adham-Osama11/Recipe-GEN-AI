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

Set your token in `backend/.env`:

```bash
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
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

## Deploy (Render)

This repo includes a Render blueprint at `render.yaml`.

1. Push the repository to GitHub.
2. In Render, choose New + > Blueprint.
3. Select this repository and deploy.
4. In the created service, set `HUGGINGFACEHUB_API_TOKEN` to your real token.
5. Open the service URL once deployment is finished.

Notes:
- Render injects `PORT` automatically. The app already reads it in `backend/app/main.py`.
- The frontend is served by the same backend process, so one web service is enough.
- If you want stricter CORS, set `ALLOWED_ORIGINS` in Render to your deployed URL.
- The blueprint pins `PYTHON_VERSION=3.12.8` to avoid Python 3.14 build issues with `pydantic-core`.

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
