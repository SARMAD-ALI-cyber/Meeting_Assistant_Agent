# LangGraph, this agent, and interview talking points

This doc ties **Phase 1 code** to concepts you can explain in interviews: what LangGraph is, how *this* system works, and how it differs from a plain chatbot.

---

## 1. What problem Phase 1 solves

**Input:** raw meeting text.  
**Output:** structured `Task` objects plus **rule-based** `Ambiguity` flags (missing owner, missing deadline, low confidence, bad dependency refs).

Phase 1 does **not** create Jira tickets, pause for humans, or persist checkpoints. It is a **single-shot pipeline** behind one HTTP endpoint so you can prove the core loop: *normalize → LLM structure → validate with code*.

---

## 2. What LangGraph is (elevator pitch)

**LangGraph** is a library for building **stateful workflows** as a **directed graph**: nodes are steps, edges define order (and later branches). Each step receives **shared state**, returns an **update**, and the runtime merges updates until the graph reaches `END`.

Contrast with a **one-shot LLM call**: no explicit stages, no shared typed state, no standard place for “run Python rules after the model.”

Contrast with **Agent = tool loop in a chat**: often reactive and conversational. Here the flow is **fixed** (Phase 1: linear `ingest → extract → ambiguity_detect`), closer to **ETL + policy** than open-ended chat.

**Compiled graph:** `StateGraph(...).compile()` returns a runnable object you `invoke()` with initial state and optional `config` (e.g. `thread_id` later for checkpoints).

---

## 3. How *our* Phase 1 agent works (walk the code)

1. **HTTP:** `POST /v1/workflows/from-transcript` (`app/api/v1/workflows.py`) accepts `TranscriptIngestRequest`, generates `run_id` / `thread_id`, calls `run_from_transcript(...)`, maps the final `MeetingState` into `TranscriptWorkflowResponse`.

2. **Graph assembly:** `graph/workflow.py` builds a `StateGraph(MeetingState)` with three nodes and linear edges from `START` → `ingest` → `extract` → `ambiguity_detect` → `END`.

3. **State schema:** `MeetingState` (`schemas/state.py`) is a **Pydantic** model. LangGraph coerces dict updates into this schema so the same shape is used for graph I/O and validation.

4. **Ingest node** (`graph/nodes/ingest.py`): deterministic cleanup via `normalize_transcript` (`graph/ingest_utils.py`); sets `cleaned_transcript`. Logs JSON line with `run_id`, `node`, `duration_ms`.

5. **Extract node** (`graph/nodes/extract.py`): calls **Groq** through `ChatGroq` with `temperature=0`, uses `with_structured_output(ExtractedMeetingPayload)` so the model must return JSON matching your Pydantic schema. Fills `extracted_tasks`, `meeting_summary`, `raw_decisions`. On failure or missing API key, appends to `errors` and returns empty tasks (explicit failure path).

6. **Ambiguity node** (`graph/nodes/ambiguity.py`): **no LLM** — calls `collect_ambiguities` (`graph/ambiguity_rules.py`) with threshold from `Settings.extraction_confidence_threshold`. Appends `Ambiguity` rows for policy violations.

**Why split LLM vs rules?** Interview line: *“The model proposes structure; the system enforces invariants and business rules deterministically.”*

---

## 4. Configuration and reliability

- **Settings** (`app/config.py`, `pydantic-settings`): model name, thresholds, max transcript length — tunable without code changes.
- **Idempotency / tickets:** Phase 3; Phase 1 still assigns stable **`Task.id`** defaults for linking ambiguities and future tools.
- **Caching:** `get_compiled_meeting_graph` is `@lru_cache` so the graph structure is built once; nodes still read **fresh** settings each call.

---

## 5. Common interview questions (short answers)

**Q: Why LangGraph instead of a chain?**  
A: Explicit **state object** and **graph topology** scale to branching, HITL interrupts, and checkpointing (Phase 2+). A `RunnableSequence` is fine for linear-only; LangGraph gives one framework as complexity grows.

**Q: Where is the “agent”?**  
A: “Agent” here means **orchestrated workflow + LLM + tools** (tools come later). Phase 1 is an **orchestrated extraction pipeline**, not a free-form ReAct loop.

**Q: How do you prevent hallucinated owners?**  
A: Prompt says do not invent owners; **ambiguity rules** flag missing owner; Phase 2 can block writes until resolved.

**Q: How do you test without hitting Groq?**  
A: Unit-test **pure functions** (`ambiguity_rules`, `ingest_utils`); API tests **monkeypatch** `run_from_transcript`; optional live test with `GROQ_API_KEY`.

**Q: What is Pregel?**  
A: LangGraph’s internal execution model: **supersteps** — each node runs with a consistent view of state; updates are merged before the next superstep. You rarely implement Pregel directly; `StateGraph` compiles down to it.

---

## 6. Suggested reading order in this repo

1. `schemas/state.py`, `schemas/extraction.py`, `schemas/api.py`  
2. `graph/workflow.py`  
3. `graph/nodes/ingest.py` → `extract.py` → `ambiguity.py`  
4. `app/api/v1/workflows.py`  
5. `docs/IMPLEMENTATION_PLAN.md` §5.4 (Phase 1 contract)

---

## 7. Glossary

| Term | Meaning here |
|------|----------------|
| **Node** | One step in the graph (Python callable). |
| **State** | `MeetingState` — shared data passed through the run. |
| **Structured output** | LLM constrained to a Pydantic schema (`ExtractedMeetingPayload`). |
| **HITL** | Human-in-the-loop (Phase 2). |
| **Checkpoint** | Saved graph state for resume/replay (Phase 2+). |
