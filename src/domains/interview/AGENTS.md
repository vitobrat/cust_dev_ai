# Interview Domain Notes

This file is the local working context for agents editing `src/domains/interview`.
It reflects the interview domain as checked on 2026-05-04.

## Domain Purpose

The interview domain owns AI-assisted custdev interview execution and final
report generation. It does not own persona generation, Redis queue mechanics,
or Minio infrastructure, but it depends on those boundaries through typed
schemas, services, and DI.

Core responsibilities:

- CRUD and persistence for `interviews`.
- Full simulated interview orchestration over existing verified personas.
- Per-persona simulated dialogue persistence into `sub_interviews`.
- Final analytics report generation from completed simulated sessions.
- Markdown final report storage through object storage and download through the
  interview API.

## Read Order

When working in this domain, read these files first:

1. `app/usecases/service.py` - application boundary for simulation, final report
   generation, persistence, and report download.
1. `infrastructure/graph/interview_orchestrator.py` - full simulation cycle.
1. `infrastructure/graph/interview_simulation.py` - one persona dialogue.
1. `infrastructure/graph/final_report_generation.py` - final report pipeline.
1. `infrastructure/prompt/prompt_manager.py` - prompt construction and context
   truncation.
1. `schemas/common.py` and stage-specific schema files in `schemas/`.
1. `app/workers/handler.py` - Redis worker handlers for interview tasks.
1. `app/requests/router.py` - interview CRUD and final-report download endpoint.
1. `db/postgres/repository.py` and `db/postgres/model.py` - persistence details.
1. `src/infrastructure/containers/domain.py` - DI wiring for the domain.

## Public Workflows

### Interview Simulation Task

1. API route in `src/domains/task/app/requests/router.py` registers
   `interview_simulation`.
1. `TaskService.register_interview_simulation_task` persists and enqueues the
   task.
1. Redis worker resolves `InterviewSimulationTaskHandler` through
   `build_handler_registry`.
1. `InterviewService.simulate_interviews` loads the interview and personas.
1. `InterviewOrchestratorGraph` runs:
   - industry description generation;
   - `PreInterviewPreparationGraph`;
   - bounded batches of `InterviewSimulationGraph`;
   - `PostInterviewUpdateGraph` after each batch;
   - final collection of all reports and sessions.
1. `InterviewService` persists each simulated session into
   `sub_interviews.chat_history` with `type="custdev_interview_simulation"`.

### Final Report Task

1. API route in `src/domains/task/app/requests/router.py`
   registers `report_generation`.
1. Redis worker resolves `FinalReportGenerationTaskHandler`.
1. `InterviewService.generate_final_report` loads completed simulated sessions
   from `sub_interviews`.
1. `FinalReportGenerationGraph` plans the report, generates analytical
   sections in parallel, writes opening/conclusion, and assembles markdown.
1. `InterviewService` uploads markdown to Minio through
   `ObjectStorageClientProtocol`.
1. `interviews.report_content_url` stores the internal `minio://bucket/key`
   reference; `interviews.final_report` stores structured JSONB fallback data.

### Final Report Download

`GET /api/v1/interviews/{interview_id}/final_report/download` calls
`InterviewService.get_final_report_file`.

Download behavior:

- Prefer `report_content_url` and download markdown from object storage.
- Fall back to legacy `final_report["markdown_content"]` when no object URI is
  present.
- Raise `InterviewFinalReportNotFound` if neither source has markdown content.

## Graph Contracts

All graph classes extend `BaseGraph` and use structured LLM outputs through
`LLMAdapter.structured_ainvoke`.

Stage contracts:

- `PreInterviewPreparationGraph` returns `PreInterviewPreparationOutputData`
  with a `PreInterviewPlan`.
- `InterviewSimulationGraph` returns `InterviewSimulationOutputData` with
  `interview_report`, `interviewer_notes`, and `chat_history`.
- `PostInterviewUpdateGraph` returns `PostInterviewUpdateOutputData` with an
  updated `PreInterviewPlan`.
- `InterviewOrchestratorGraph` returns all accumulated reports, sessions, and
  the final pre-interview plan.
- `FinalReportGenerationGraph` returns `FinalReportGenerationOutputData` with
  one `FinalInterviewReport`.

Important invariants:

- `InterviewSimulationGraph` must always route through
  `update_interview_notes` before `analyze_interview`, including validator
  finish and `max_iterations` paths.
- `InterviewOrchestratorGraph` must pass only latest-batch reports into
  `PostInterviewUpdateGraph`, while preserving all reports in final state.
- `InterviewOrchestrationInputData.batch_size` must stay bounded by
  `INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE`.
- Prompt builders must not serialize unbounded persona sets or full raw session
  data without truncation.
- Final report input is capped by `FINAL_REPORT_MAX_INTERVIEW_SESSIONS`.

## Persistence

`interviews` table fields used by this domain:

- `report_content_url`: internal object URI for final report markdown.
- `final_report`: structured JSONB fallback for `FinalInterviewReport`.
- `personas`: loaded personas for simulation input.
- `sub_interviews`: completed simulated sessions for final report input.

`sub_interviews.chat_history` stores a versioned JSON payload, not only raw chat
messages. The current payload includes:

- `schema_version`
- `type`
- `rewritten_user_request`
- `segment_name`
- `segment_description`
- `persona_context`
- `chat_history`
- `interviewer_notes`
- `interview_report`
- `final_pre_interview_plan`

Do not change this payload shape casually; final report generation depends on
it.

## Error Handling

Domain exceptions live in `exceptions.py`.

Use `InterviewError` for domain-level execution failures, and more specific
subclasses when a missing entity or missing final report content should map to a
404-style API response.

Expected failure points:

- Interview has no personas for simulation.
- Interview has no completed simulated sessions for final report generation.
- Stored simulated session payload is malformed.
- Object storage client is not configured when final report upload/download is
  required.
- Final report markdown is missing in both Minio and JSONB fallback.

## Boundaries

Keep these boundaries intact:

- Routers call services.
- Services call repositories, graphs, and object storage.
- Graphs call prompt manager and LLM adapter only.
- Repositories own SQLAlchemy details.
- Redis worker handlers call service methods and validate task payload type.
- This domain does not call Qdrant, Triton, or the ML service directly.

RAG/tooling context is currently represented through prompt fields and planned
external-search flags. Concrete vector-search producer calls should be added
through a designed cross-service boundary, not directly inside graph nodes.

## Tests To Run

For graph or prompt changes:

```bash
python3 -m pytest -vv tests/unit/domains/interview/test_interview_agent_graphs.py
python3 -m pytest -vv tests/unit/domains/interview/test_interview_simulation_graph.py
python3 -m pytest -vv tests/unit/domains/interview/test_interview_orchestrator_graph.py
python3 -m pytest -vv tests/unit/domains/interview/test_final_report_generation_graph.py
python3 -m pytest -vv tests/unit/domains/interview/test_post_interview_update_graph.py
```

For service, worker, or API changes:

```bash
python3 -m pytest -vv tests/unit/domains/interview/test_interview_service.py
python3 -m pytest -vv tests/unit/domains/interview/test_interview_task_handler.py
python3 -m pytest -vv tests/unit/domains/interview/test_interview_router.py
python3 -m pytest -vv tests/integration/domains/interview/test_interview_service.py
```

For domain-wide confidence:

```bash
python3 -m pytest -vv tests/unit/domains/interview
python3 -m pytest -vv tests/integration/domains/interview
```

Integration tests require Docker because they use testcontainers.

## Change Checklist

Before finishing interview-domain work:

- Validate schema changes against both graph state and persisted JSONB payloads.
- Check DI in `src/infrastructure/containers/domain.py`.
- Check task registration and worker registry when task types change.
- Check migration requirements when persistence or PostgreSQL enums change.
- Run focused unit tests and any needed integration tests.
- Avoid logging full prompts, raw LLM responses, full biographies, or full
  interview transcripts unless explicitly required for a test.
