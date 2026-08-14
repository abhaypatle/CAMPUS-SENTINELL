# Campus Sentinel — Architecture Steering

Goal
- Describe a minimal, secure, cost-aware AWS-compatible architecture that implements the CORE PRODUCT PIPELINE while keeping the backend as the central control point.

High-level components
- Frontend: React + TypeScript, Tailwind CSS. Single-page app delivering reporting UI and Admin command center.
- Backend API: FastAPI (Python). Central control point for authorization, state transitions, fusion, risk scoring, and audit logging.
- Database: PostgreSQL (primary data store for reports, incidents, users, audit trail, assignments).
- AI: Amazon Bedrock for extraction, SOP grounding, and recommendation generation.
- RAG: Amazon Bedrock Knowledge Bases or equivalent AWS retrieval architecture for SOP retrieval.
- Evidence store: Amazon S3 (private buckets, signed URLs for access).
- Realtime: WebSockets (API Gateway WebSocket / AppSync / equivalent) for push updates to clients.
- Secrets: AWS Secrets Manager for credentials and API keys.
- Monitoring: Amazon CloudWatch (metrics, logs, alarms).

Data flow (report -> resolve)
1. Reporter submits report via frontend form (React Hook Form + Zod validation client-side).
2. Frontend posts to Backend API over HTTPS with user auth token.
3. Backend persists raw report to PostgreSQL and stores any uploaded evidence to S3 (private) with safe object naming and size/type validation.
4. Backend enqueues or calls AI analysis (Bedrock) to extract structured facts and confidence scores. AI output is validated by backend schemas (Pydantic) before use.
5. Backend runs deterministic fusion logic (multi-factor) that considers semantic similarity (AI extraction), time proximity, location proximity, category, evidence correlation, and structured attributes. Fusion produces explainable reasoning (ranked contributing factors) which is stored in the incident record.
6. Backend computes operational risk score using deterministic rules combined with AI-extracted signals; stores contributing factors and history.
7. If escalation thresholds are met, backend marks incident as ESCALATING and emits realtime notifications to Admin clients. Admin can view intelligence view which shows timeline, reports, evidence, fusion reasoning and risk contributors.
8. Admin may retrieve SOP via RAG/Bedrock; Bedrock returns grounded recommendation which is validated and displayed for human review.
9. Admin assigns responder; actions and state changes are recorded in audit trail. Realtime updates notify responsible clients.

Design constraints & principles
- Backend is central control: enforce auth, state transitions, fusion thresholds, risk thresholds, and audit logging.
- Keep system modular but avoid needless microservices; prefer a single well-structured backend service.
- Do not introduce Kubernetes or Redis by default.
- Prefer working code over speculative architecture; favor minimal, testable components.
- Minimize AWS cost: use managed services conservatively.
- Validate all AI outputs before use.
- Do not let an LLM directly control critical application state; use deterministic backend logic.

Fusion service responsibilities
- Accept new report(s) and candidate incident matches.
- Compute multi-factor similarity scores and produce a fusion decision with an ordered list of contributing factors and confidence bands.
- Expose intermediate signals for explainability (e.g., time_delta_minutes, location_distance_meters, semantic_score, evidence_matches, reporter_independence_count).
- Provide an API to simulate/preview fusion decisions for operators.

Risk engine responsibilities
- Accept structured signals from AI + incident metrics and compute an operational risk score deterministically.
- Expose factor breakdown, thresholds hit, and recommended severity level.
- Provide hooks for manually adjusting weights in admin-only configuration (tracked in audit logs).

Realtime considerations
- Use WebSockets or AWS AppSync subscriptions for low-latency updates.
- Keep messages small (incident IDs + change summary); fetch details via API when needed.
- Respect RBAC on subscription channels and messages.

Deployment notes
- Simple AWS deployment: EC2/Elastic Beanstalk/Cloud Run or Fargate for backend; RDS for Postgres; S3 for evidence; Secrets Manager for secrets.
- Use HTTPS and strict IAM policies.
- Add CloudWatch alarms for error rates, unexpected fusion errors, or rapid escalation events.

Testing and observability
- Include unit tests for deterministic fusion and risk logic.
- Log AI inputs/outputs minimally (avoid PII); store enough context to reproduce fusion decisions.
- Provide dashboards for incidents over time, escalations, and system health.
