# AI Meeting-to-Execution Agent — Implementation Plan

This document is the working roadmap for building the system described in `[CLAUDE.md](../CLAUDE.md)` and the project problem statement (meeting-to-execution gap, LangGraph orchestration, STM/LTM, tools, HITL, production hardening).

**How to use this file:** complete phases in order unless noted. Each phase ends with **exit criteria** you can verify before moving on.

---

## 1. Guiding principles


| Principle                         | What it means                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Vertical slices**               | Each phase ships something **runnable and demoable** end-to-end, not a layer of unused infrastructure.             |
| **Contracts before integrations** | Pydantic models and API shapes are fixed **before** Jira, Redis, or vector DB wiring.                              |
| **Adapters for externals**        | Transcript sources (Zoom, Teams, upload) and task sinks (Jira, Notion) are **swappable** behind stable interfaces. |
| **Complexity when earned**        | SQLite/memory checkpointers and mocked tools come **before** PostgreSQL and full OTel/Kubernetes.                  |


---

## 2. High-level architecture (target)

Reference: `[CLAUDE.md](../CLAUDE.md)` sections 3–7.

```text
User / API  →  FastAPI  →  LangGraph (state + nodes)
                              ↓
         Transcript → Extract → Ambiguity → [HITL] → Approve → Tools → Memory
                              ↓
                    PostgreSQL (state + domain) · Redis (STM) · Vector DB (LTM)
```

This plan sequences **when** you introduce each box.

---

## 3. Suggested repository layout

Establish early in Phase 0; adjust names to taste.

```text
app/                 # FastAPI app factory, routes, dependencies
app/api/             # Versioned routers (e.g. v1/transcripts.py)
graph/               # LangGraph definition, node functions, routing
graph/nodes/         # Optional: one module per node cluster
schemas/             # Pydantic models (contracts) — shared import surface
tools/               # External integrations; protocols + implementations
tools/sinks/         # Jira, Notion, mock implementations
workers/             # Schedulers, queue consumers (later phases)
tests/               # Unit + integration tests; fixtures/sample transcripts
docs/                # This plan and other project docs
```

---

## 4. Phase 0 — Foundations

### 4.1 Goals

- Runnable project with consistent config and import paths.
- **Contracts first:** all core types and API payloads defined in code before heavy logic.

### 4.2 Tasks

1. **Layout**
  - Create packages (`app`, `graph`, `schemas`, `tools`) with `__init__.py` as needed.  
  - Keep a single entrypoint (e.g. `main.py` or `uvicorn app.main:app`) documented in `README` or comments.
2. **Configuration**
  - Environment variables for: LLM provider keys, model names, log level, optional feature flags (`REQUIRE_APPROVAL`, etc.).  
  - Use `.env` locally; never commit secrets.
3. **Contracts (Pydantic v2) — do this before Phase 1 graph code**
  Define models in `schemas/` (names illustrative; align field names with `[CLAUDE.md](../CLAUDE.md)` `MeetingState` idea):

  | Model / module                                      | Purpose                                                                                                                                                                                                                     |
  | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `Task`                                              | Single action item: `title`, `description`, `owner` (optional), `deadline` (optional), `dependencies` (list of ids or titles), `confidence` (float 0–1 or enum), stable `id` or client-generated key for idempotency later. |
  | `ExtractedMeetingPayload`                           | Wrapper for extraction LLM output: list of `Task`, optional `meeting_summary`, optional `raw_decisions`.                                                                                                                    |
  | `Ambiguity`                                         | One detected issue: e.g. `task_ref`, `kind` (missing_owner, missing_deadline, low_confidence, …), `message` for HITL.                                                                                                       |
  | `MeetingState` (or split read/write)                | Graph state: `transcript`, `extracted_tasks`, `ambiguities`, `clarified_tasks` / patches, `approval_status`, `created_task_ids`, `followup_schedule`, `memory_refs`, `errors` — start minimal; extend as nodes appear.      |
  | `TranscriptIngestRequest` / `WorkflowStartResponse` | API: body for “start workflow from transcript”; response includes `thread_id` / `run_id` when you add checkpointing.                                                                                                        |
  | `ApiError`                                          | Consistent error body for FastAPI exception handlers (optional but useful).                                                                                                                                                 |

   **Rules for contracts:**
  - Prefer **explicit optional fields** (`Optional[str]`) over loose dicts.  
  - Add **field descriptions** / `json_schema_extra` where they help the LLM structured-output schema.  
  - Version breaking changes (e.g. `TaskV2`) only when necessary; otherwise evolve in place during Phase 0–1.
4. **Tooling**
  - Formatter/linter (ruff or equivalent) if not already present.  
  - A `tests/` folder with one trivial test that imports `schemas` (ensures package path is correct).

### 4.3 Phase 0 exit criteria

- `schemas` imports cleanly from `app` and `graph` without circular imports.  
- Sample instances of `Task`, `MeetingState`, and API models serialize to JSON without ad-hoc dicts.  
- `.env.example` (or documented list) lists required variables for local dev.

---

## 5. Phase 1 — Core graph + extraction

### 5.1 Goals

One **vertical slice**: HTTP receives a transcript → LangGraph runs → structured tasks (+ ambiguity flags) returned as JSON. No Jira, no Postgres, no Redis required.

### 5.2 Tasks (recommended order)

1. **FastAPI route**
  - `POST` (e.g. `/v1/workflows/from-transcript`) accepting `TranscriptIngestRequest`.  
  - Returns JSON aligned with a response model (list of tasks + ambiguities, or full partial state).
2. **LangGraph skeleton**
  - Define `MeetingState` (or TypedDict + reducer pattern per LangGraph docs) consistent with `schemas`.  
  - **Node: ingest** — normalize whitespace, optional max length / chunking placeholder; output updates `transcript` or a `cleaned_transcript` field.  
  - **Node: extract** — call Groq (existing stack: `langchain-groq`) with **structured output** bound to `ExtractedMeetingPayload` or list of `Task`.  
  - **Node: ambiguity** — **pure Python**: scan tasks for missing owner/deadline, low `confidence`; append `Ambiguity` records.
3. **Graph edges**
  - Start **linear**: `ingest → extract → ambiguity_detect → END`.  
  - Conditional routing comes in Phase 2.
4. **Golden samples**
  - 2–3 short synthetic transcripts in `tests/fixtures/` to run the graph or a thin integration test.
5. **Logging**
  - Structured log line per node: `run_id`, node name, duration.

### 5.3 Phase 1 exit criteria

- Same transcript produces stable structured output (temperature 0 for extraction).  
- Ambiguity node flags known-bad fixture cases (e.g. no owner).  
- API returns Pydantic-validated JSON (no raw dict leakage at the boundary).

### 5.4 Phase 1 — finalized scope (what we build now)

This subsection locks **scope and behavior** for Phase 1 so implementation matches expectations. Anything not listed under *in scope* is intentionally deferred.

#### In scope


| Area                | Deliverable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **HTTP API**        | `POST /v1/workflows/from-transcript` under an API router (e.g. `app/api/v1/…`). Request body: existing `TranscriptIngestRequest`. Response body: a **dedicated Pydantic response model** (add in `schemas/api.py`, e.g. `TranscriptWorkflowResponse`) containing at minimum: `run_id`, `thread_id`, `cleaned_transcript`, `meeting_summary` (optional), `extracted_tasks`, `ambiguities`. Reuse `Task` and `Ambiguity`; do not return raw dicts at the route boundary.                                                                                                                                                                                                                                                                   |
| **Identifiers**     | Generate `run_id` and `thread_id` (UUID strings) **per request** for logs and future Phase 2 resume; Phase 1 does **not** persist threads or expose resume APIs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **LangGraph**       | A **linear** graph: `ingest → extract → ambiguity_detect → END`. No conditional edges, no interrupts, no human branches.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Graph state**     | Field names and semantics **aligned with** `MeetingState` in `schemas/state.py`. Implementation may use LangGraph `TypedDict` + reducers or a dict built from `MeetingState.model_dump()`; the **HTTP response** must still validate against the chosen response model.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Node: ingest**    | Normalize transcript: trim ends, collapse internal runs of whitespace to a single space; optional hard `max_chars` with truncation + log warning (placeholder for later chunking). Write result to `cleaned_transcript` (and keep original `transcript` from the request).                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Node: extract**   | Call configured Groq model via `langchain-groq` with `**temperature=0`**. Bind **structured output** to `ExtractedMeetingPayload`. Merge LLM `tasks` into `extracted_tasks`; carry `meeting_summary` / `raw_decisions` through state as available. On LLM/schema failure: append a clear string to `errors` and avoid partial silent success (define one consistent behavior, e.g. empty tasks + error).                                                                                                                                                                                                                                                                                                                                 |
| **Node: ambiguity** | **Pure Python** (no LLM): scan `extracted_tasks` and **append** to `ambiguities` (do not mutate task objects unless you explicitly decide to). Rules for Phase 1: (1) `owner` missing or blank → `AmbiguityKind.MISSING_OWNER`; (2) `deadline` missing or blank → `AmbiguityKind.MISSING_DEADLINE`; (3) `confidence` strictly below **0.5** → `AmbiguityKind.LOW_CONFIDENCE` (single constant in config or module, easy to tune); (4) each non-empty `dependencies` entry that is **not** equal to any `Task.id` in the current batch → `AmbiguityKind.UNCLEAR_DEPENDENCY` (one ambiguity per bad ref or one combined message — pick one approach and stay consistent). `task_ref` must point at the relevant `Task.id` when applicable. |
| **Logging**         | At least one structured or keyword-rich log line **per node** including `run_id`, node name, and duration (milliseconds).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **Tests**           | 2–3 synthetic transcripts under `tests/fixtures/`; tests that (a) ambiguity detection flags expected cases on **fixed** extracted tasks (unit), and/or (b) full graph + API integration behind a mocked LLM where network is unavailable in CI.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |


#### Explicitly out of scope (Phase 1)

- Human-in-the-loop pause/resume, LangGraph interrupts, Slack or email.  
- Jira, Notion, or any external task creation.  
- PostgreSQL, Redis, durable LangGraph checkpointer, vector memory.  
- JWT/RBAC, OpenTelemetry, Prometheus, Docker/Kubernetes as required deliverables (optional local Docker is fine if you want it, but it is not part of Phase 1 *definition of done*).

#### Phase 1 “done” checklist (restatement)

- `POST /v1/workflows/from-transcript` returns the new response model as JSON.  
- Same fixture transcript + `temperature=0` yields stable extracted tasks across runs (allowing for rare provider nondeterminism — document if observed).  
- Ambiguity rules fire on fixture cases (e.g. task with no owner).  
- Tests + `ruff`/`pytest` green in CI or locally before calling Phase 1 complete.

---

## 6. Phase 2 — Human-in-the-loop (API-first)

- Represent **pause** and **resume** using LangGraph interrupt/checkpoint patterns or explicit `pending_input` state.  
- Endpoints to submit clarification / approval payloads and continue the same `thread_id`.  
- **Slack** (and similar) later: thin adapters calling the same resume API.

**Exit criteria:** paused run resumes deterministically; state after resume is validated against schemas.

---

## 7. Phase 3 — Tool integrations

- Define a `**TaskSink`** (protocol): `create_task`, idempotency key, error types.  
- Implement **mock sink** (log + in-memory) first; then **one** real target (Jira *or* Notion *or* Slack-as-notify).  
- HTTP client wrapper: retries, exponential backoff, timeouts.

**Exit criteria:** duplicate requests do not create duplicate external tasks (idempotency verified).

---

## 8. Phase 4 — Persistence and durability

- LangGraph **checkpointer**: SQLite or file-backed locally; design state so migrating to **PostgreSQL** is straightforward.  
- Domain tables: meetings, tasks, external IDs, run metadata.

**Exit criteria:** process killed mid-run; resume from checkpoint without corrupting domain invariants.

---

## 9. Phase 5 — Memory layer

- **STM:** Redis for active context, TTL, rate limiting (optional defer: in-process with TODO).  
- **LTM:** vector store (e.g. Chroma locally); embeddings for summaries/tasks; retrieval node when you have data.

**Exit criteria:** retrieval measurably helps on a small eval set or manual review.

---

## 10. Phase 6 — Follow-up, escalation, scheduling

- Worker or scheduler (APScheduler, queue consumer) for periodic status checks.  
- Escalation rules: deadline passed → notify owner → manager after threshold.

**Exit criteria:** scheduled job runs in dev with mocked external status.

---

## 11. Phase 7 — Production hardening

- JWT auth, RBAC, audit logs for task creation.  
- Structured JSON logs; OpenTelemetry when APIs are stable.  
- Docker Compose: API + Postgres + Redis (+ optional Chroma). CI (e.g. GitHub Actions) for lint + tests.

**Exit criteria:** aligned with `[CLAUDE.md](../CLAUDE.md)` Definition of Done (checkpointing, idempotency, retries, monitoring story defined).

---

## 12. Risk controls


| Risk                              | Mitigation                                                                                 |
| --------------------------------- | ------------------------------------------------------------------------------------------ |
| Schema drift between LLM and code | Single Pydantic model for structured output; regenerate / fix prompts when schema changes. |
| Over-building infra early         | Phase 1 completes without Postgres/Redis.                                                  |
| HITL complexity                   | API resume first; Slack second.                                                            |
| Duplicate tickets                 | Idempotency keys in Phase 3 from day one of real tools.                                    |


---

## 13. Current focus (next work session)

Per team agreement:

1. **Phase 0 — Contracts first**
  Implement `schemas/` per section 4.3 checklist.
2. **Phase 1 — Core graph + extraction**
  FastAPI route + linear LangGraph + structured extraction + ambiguity detection.

When both are done, update this document’s checklists or add a short `CHANGELOG` entry under `docs/` if you want a dated log of phase completions.

---

## 14. References

- `[CLAUDE.md](../CLAUDE.md)` — full architecture, node list, memory, reliability, Definition of Done.  
- Problem statement — meeting-to-execution gap, business outcomes (project Word doc).

---

*Last updated: plan authored for Phase 0–1 kickoff.*