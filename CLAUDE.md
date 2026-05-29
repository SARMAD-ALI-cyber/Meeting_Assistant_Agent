# AI Meeting-to-Execution Agent

## Full Production-Grade Architecture (Claude.md Context File)

---

# 1. Project Overview

## Mission

Transform meeting transcripts into executable, trackable workflows using
a stateful, production-grade AI agent system.

The system: - Ingests meeting transcripts - Extracts structured action  
items - Resolves ambiguities - Creates tasks in external systems -  
Tracks execution - Performs automated follow-ups and escalation -  
Maintains long-term organizational memory

---

# 2. Core Architecture Philosophy

This is NOT a chatbot. This is a stateful, deterministic + agentic
workflow engine.

Architecture principles:

- Graph-based orchestration (LangGraph)
- Explicit state management
- Separation of reasoning vs tool execution
- Deterministic control flow where required
- Memory layers (STM + LTM)
- Human-in-the-loop checkpoints
- Observability-first design
- Production reliability (retry, timeout, fallback)

---

# 3. High-Level System Architecture

User / API Trigger  FastAPI Backend  LangGraph Orchestrator 
-------------------------------------------  Transcript  Extraction
 Clarification  ------------------------------------------- 
Approval Gate  Task Creation Tool Nodes  Memory Write (Vector + DB)
 Scheduler / Monitoring Agent  Follow-up / Escalation Engine

---

# 4. Technology Stack

## Core Agent Layer

- LangGraph (stateful graph orchestration)
- LangChain (tool abstraction, structured outputs)
- Deep Agents framework (optional advanced abstraction)
- GROQ (LLM inference provider)
- OpenAI / Anthropic fallback models

## Backend

- FastAPI
- Uvicorn
- Pydantic v2
- PostgreSQL (persistent graph state)
- Redis (short-term memory cache + job queue)

## Memory

- Vector DB (Chroma / Pinecone / Weaviate)
- Embedding model (OpenAI / bge-large)
- PostgreSQL for structured memory

## Tool Integrations

- Slack API
- Jira API
- Notion API
- Google Calendar API
- Email (SMTP / Gmail API)

## Observability

- OpenTelemetry
- Structured logging (JSON logs)
- Prometheus + Grafana

## Deployment

- Docker
- Kubernetes (optional)
- CI/CD pipeline (GitHub Actions)

---

# 5. LangGraph Design

## State Object

class MeetingState(BaseModel): transcript: str extracted_tasks:
ListTask ambiguities: Liststr clarified_tasks: ListTask
approval_status: str created_task_ids: Liststr followup_schedule:
Dict memory_refs: Liststr errors: Liststr

State is persisted in PostgreSQL.

---

# 6. Graph Nodes

## 1. Transcript Ingestion Node

- Input: raw transcript
- Output: cleaned structured transcript
- Preprocessing:
  - Speaker segmentation
  - Noise removal
  - Chunking if  context window

## 2. Action Extraction Node

- Uses structured output (Pydantic schema)
- Extracts:
  - Task title
  - Description
  - Owner
  - Deadline
  - Dependencies
  - Confidence score

Model: GROQ-hosted LLM (fast inference)

## 3. Ambiguity Detection Node

- Checks missing owner or deadline
- Checks low confidence
- Adds clarification prompts

## 4. Clarification Loop Node

- If ambiguity exists:
  - Sends Slack message
  - Waits for human response
  - Updates state
- Loop until resolved

## 5. Human Approval Gate

- Summary generated
- Sent to meeting organizer
- Requires explicit confirmation

## 6. Task Creation Node (Tool Node)

- Deterministic execution
- Creates tasks in:
  - Jira
  - Notion
- Retry policy:
  - Exponential backoff
  - Max 3 retries

## 7. Memory Write Node

- Store embeddings in vector DB
- Store structured task record in PostgreSQL
- Create relationship graph (optional)

## 8. Scheduler Node

- Background cron
- Checks task status daily
- Triggers follow-up agent

## 9. Escalation Node

- If deadline passed:
  - Notify owner
  - Notify manager after threshold

---

# 7. Memory Architecture

## Short-Term Memory (STM)

- Redis
- Holds active workflow context
- TTL-based expiry
- Used during clarification loop

## Long-Term Memory (LTM)

### 1. Vector Memory

Stores: - Meeting summaries - Decisions - Task embeddings

Used for: - Retrieval during future meetings - Trend detection

### 2. Structured Memory

PostgreSQL tables: - meetings - tasks - decisions - stakeholders -
followups

---

# 8. LLM Routing Strategy

Model Router: - GROQ for extraction (low latency) - Higher-quality model
for ambiguity resolution - Smaller model for summarization - Fallback
model on failure

---

# 9. Reliability Engineering

## Retry Strategy

- Tool calls wrapped in retry decorator
- Circuit breaker pattern

## Timeout Handling

- Node-level timeouts
- Kill long-running execution

## Idempotency

- Task creation uses idempotency keys
- Prevent duplicate ticket creation

---

# 10. Observability

Each graph execution logs: - Node transitions - Latency per node - Tool
call duration - Model token usage - Failure points

Tracing via OpenTelemetry.

---

# 11. Security Considerations

- API authentication (JWT)
- Role-based access control
- Audit logs for task creation
- Encrypted vector store
- Secret management via environment variables

---

# 12. Scalability

Horizontal Scaling: - Stateless API layer - Shared Postgres - Redis
cluster - Worker queue for async nodes

Batch meeting processing supported.

---

# 13. Future Extensions

- Multi-agent role separation
- Predictive deadline risk detection
- Performance analytics dashboard
- Automatic meeting agenda generation
- Organizational knowledge graph

---

# 14. Development Phases

Phase 1: Core graph + extraction  
Phase 2: Tool integrations  
Phase 3: Memory layer  
Phase 4: Follow-up automation  
Phase 5: Observability + hardening  
Phase 6: Production deployment

---

# 15. Definition of Done

The system is production-ready when:

- Graph state persists across crashes
- Task duplication impossible
- All tool calls retriable
- Monitoring dashboards active
- Memory retrieval validated
- SLA metrics defined

---

END OF CLAUDE CONTEXT FILE