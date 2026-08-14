# Campus Sentinel — Coding Standards & Developer Guidance

Purpose
- Keep code readable, safe, and maintainable while enforcing deterministic backend control for critical logic.

General
- Use Git + GitHub for SCM. Small, focused commits with descriptive messages.
- Use feature branches and PR reviews. Require at least one approving review before merge.
- Write clear PR descriptions with testing steps and screenshots where relevant.

Languages & formatting
- Frontend: React + TypeScript. Use ESLint + Prettier.
- Styling: Tailwind CSS; prefer utility classes and component-level style encapsulation.
- Forms: React Hook Form + Zod for schema validation.
- Backend: FastAPI + Python 3.11+. Use Pydantic models for schema validation and typed endpoints.
- Use black/isort/ruff for Python formatting/linting.

Typing & tests
- Prefer explicit types in TypeScript; avoid `any`.
- Add unit tests for critical logic: fusion, risk scoring, authorization middleware, and audit logging.
- Use testing frameworks: Jest for frontend, pytest for backend.

AI integration practices
- Treat AI as an external service: validate all responses, log context, and never trust free-form text.
- Define and version schemas for AI outputs; validate with Pydantic before using them.
- Encapsulate AI calls behind a dedicated integration layer.

Security & secrets
- Use environment variables and Secrets Manager; do not commit secrets.
- Run dependency vulnerability scans in CI.

API & contracts
- Keep the backend API contract explicit and versioned (v1, v2).
- Use OpenAPI specs generated from FastAPI for client generation and documentation.
- Design idempotent endpoints where appropriate (e.g., re-submitting a report should not create duplicate records).

Deterministic logic rules
- Implement fusion thresholds, risk thresholds, authorization checks, and state transitions in backend code with clear unit tests.
- Keep rule definitions human-readable and, where appropriate, configurable via admin-only settings (changes must be audited).

Logging & observability
- Emit structured logs (JSON) for backend services.
- Instrument metrics for fusion errors, AI confidence distributions, escalations, and API error rates.

Developer workflow
- Pre-commit hooks for linting and tests.
- CI pipeline: lint → unit tests → build artifacts → optional deploy step to staging.

Documentation
- Keep architecture decisions and runbooks in the repo docs/ folder.
- Document expected AI schemas and example payloads in docs/ai.md (when added).

Prohibitions
- Do not allow LLMs to directly mutate critical system state; all state-changing operations must pass deterministic backend validation and produce auditable events.


