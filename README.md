# Meeting-to-Execution Agent

Stateful LangGraph workflow (see [`CLAUDE.md`](CLAUDE.md) and [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)).

## Setup

```bash
uv sync --extra dev
cp .env.example .env   # Windows: copy .env.example .env — then set GROQ_API_KEY when using the LLM
```

## Run API (Phase 1)

```bash
uv run uvicorn app.main:app --reload
```

- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- [http://127.0.0.1:8000/health/config](http://127.0.0.1:8000/health/config) (no secrets; shows whether `GROQ_API_KEY` is set)
- **Phase 1 workflow:** `POST http://127.0.0.1:8000/v1/workflows/from-transcript` with JSON body `{"transcript": "..."}` (requires `GROQ_API_KEY` for real extraction).

See [`docs/AGENT_INTERVIEW_PRIMER.md`](docs/AGENT_INTERVIEW_PRIMER.md) for how the LangGraph flow maps to interview talking points.

## Checks

```bash
uv run pytest
uv run ruff check .
```

## Optional LLM smoke test

Requires `GROQ_API_KEY` in `.env`. Run from the **repository root** (so `app` resolves):

```bash
python scripts/groq_smoke.py
# or
uv run python scripts/groq_smoke.py
```
