# Campus Sentinel — Product Steering

Project: Campus Sentinel

Full name: AI-Powered Real-Time Campus Incident Intelligence & Response System

Competition: KIRO BUILDATHON: CAMPUS EDITION 2026

Purpose
- Provide an AI-assisted incident intelligence layer for campuses that reliably fuses fragmented reports into coherent incidents, calculates explainable operational risk, detects escalation, and supports human decision-making and response.

Core product pipeline

REPORT → UNDERSTAND → FUSE → ASSESS → ESCALATE → RECOMMEND → HUMAN ACTION → RESOLVE

Core innovation
- Incident fusion that considers semantic similarity, time proximity, location proximity, incident category, evidence (when available), and other structured attributes.
- Never merge incidents based only on text similarity; require multi-factor evidence and deterministic checks.
- Provide explainable fusion reasoning and expose contributing factors to operators.

Operational risk scoring
- Risk is computed by deterministic backend logic that combines AI-extracted structured facts with fixed weights, thresholds, and rules.
- The risk score must expose contributing factors (e.g., report volume, severity indicators, multiple independent reporters, evidence quality).
- AI provides extracted signals and confidence; backend enforces thresholds and combines inputs deterministically.

Escalation detection
- Detect meaningful escalation such as rising report volume, increasing severity, new corroborating evidence, or multiple independent reports.
- Only backend-detected escalations marked as actionable should be surfaced prominently. AI may flag potential escalations as supporting signals.

P0 features (minimum viable for demo)
1. Authentication and RBAC
2. Incident reporting (web form + structured fields)
3. AI report analysis (structured extraction + confidence)
4. Incident fusion (explainable)
5. Explainable operational risk score
6. Escalation detection
7. Admin command center
8. Incident intelligence view (timeline, reports, evidence, fusion reasoning)
9. SOP retrieval (RAG + Amazon Bedrock)
10. Incident assignment
11. Incident lifecycle management
12. Resolution workflow
13. Audit trail (immutable events)
14. Realtime updates (websocket-based)

Roles
- REPORTER: campus community member submitting reports.
- RESPONDER: on-the-ground staff who action incidents.
- ADMIN: command center operator who monitors escalations and assigns responders.

Demo scenario (KIRO BUILDATHON)
- Input: three fragmented reports about smoke/electrical smell + one image upload.
- Expected flow: three reports → fusion into a single incident → risk increases → incident becomes ESCALATING → surfaces at top of Admin command center → Admin opens intelligence view (shows reports, timeline, evidence, fusion reasoning, risk contributors) → relevant SOP retrieved via RAG + Bedrock → Bedrock generates grounded recommendation → Admin reviews → Responder assigned → Responder updates status and adds evidence → Incident becomes RESOLVED → audit trail records important actions.

Constraints & non-goals
- AI is decision support only; humans make final decisions for high-risk actions.
- Do not implement autonomous emergency actions, medical diagnosis, biometric identification, or unsupported factual claims.
- No native mobile app or CCTV/IoT/CCTV integration for demo scope.

Metrics (success criteria for demo)
- Fusion accuracy (manual verification for demo incident)
- Risk score explainability (operator can read contributing factors)
- Time from first report to escalation detection
- Admin UI surfaces incident and SOP in under X seconds (demo target)
