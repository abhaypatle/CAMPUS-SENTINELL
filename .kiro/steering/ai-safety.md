# Campus Sentinel — AI Safety Steering

Principles
- AI is decision support only; humans retain final control for high-risk actions.
- Validate and constrain all AI outputs using backend schema validation before any use.
- Design for auditability and explainability.

Structured AI outputs
- Require all AI responses used by the system to be structured (JSON schema) with explicit fields such as `extracted_entities`, `semantic_score`, `confidence`, `evidence_matches`, and `recommendation`.
- Use Pydantic (backend) to strictly validate AI outputs and block or flag malformed or low-confidence results.

Grounding & RAG
- Use RAG to retrieve SOPs and grounding material from trusted knowledge bases.
- Record retrieval context (KB id, passages used, retrieval scores) with each recommendation.
- Avoid free-form LLM text for critical recommendations; require structured reasoning + source list.

Confidence & thresholds
- AI must surface confidence scores; backend must apply deterministic thresholds before using AI signals in fusion or risk scoring.
- Define explicit thresholds for when human review is required.

Explainability
- Fusion decisions must include a human-readable chain of reasoning plus numeric signals (e.g., time_delta, location_distance, semantic_score, evidence_matches).
- Risk score must expose contributing factors and the deterministic rules that combined them.

Human-in-the-loop
- Any AI-generated recommendation that could materially change response level must require human approval before action.
- Provide easy UI controls for Admin to accept/reject/annotate AI recommendations.

Restricted behaviors & prohibitions
- No autonomous emergency dispatch or decisions.
- No medical diagnosis or health guidance.
- No facial recognition or biometric identification.
- No ungrounded factual assertions presented as truth without source citations.

Hallucination mitigation
- Use RAG to ground recommendations; prefer short, source-linked outputs.
- Validate named entities and locations against structured campus data where possible.
- If AI confidence is low, surface the uncertainty prominently and fall back to conservative deterministic rules.

Logging & audit
- Log AI inputs, outputs, retrieval context, and how outputs were used (or rejected) by the backend.
- Retain enough data to reproduce the decision path during post-incident review.

Testing & validation
- Unit tests for schemas and threshold logic.
- Simulation tests for fusion and risk engine using synthetic and sanitized historical data.

Operational safety
- Rate-limit AI calls and monitor for cost/abuse.
- Have fallback deterministic behavior when AI service is unavailable (e.g., conservative fusion and escalation defaults).
