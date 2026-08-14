# Campus Sentinel — Security Steering

Objectives
- Protect user data, evidence, and system integrity while enabling rapid incident response.

Authentication & Authorization
- Implement strong authentication (OAuth2 / OIDC). Support short-lived tokens.
- Enforce RBAC with least-privilege: REPORTER, RESPONDER, ADMIN.
- Authorization middleware in backend must validate actions and state transitions deterministically.

Input validation & data safety
- Validate all inputs server-side using strict schemas (Pydantic/Zod equivalents).
- Enforce file type and size limits for evidence uploads; scan uploaded files if feasible.
- Safe object naming for S3 to prevent path traversal or object spoofing.

Network & transport
- HTTPS everywhere. No plaintext credentials in transit.
- Secure headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
- CORS configured to trusted origins only.

Storage & secrets
- Evidence stored in private S3 buckets; use signed URLs for limited-time access.
- Encrypt sensitive data at rest (S3, RDS encryption).
- Manage secrets with AWS Secrets Manager; never hardcode credentials.

Access control & IAM
- Apply least-privilege IAM roles for services.
- Use separate credentials for CI/CD and runtime; rotate secrets regularly.

Rate limiting & abuse prevention
- Apply rate limits to reporting endpoints to mitigate spam.
- Add CAPTCHAs or progressive friction if abuse detected.

Audit & logging
- Immutable audit trail for critical actions: report submit, fusion decision, risk escalation, assignment, resolution.
- Logs should redact PII but keep enough context to reconstruct decisions.
- Protect log storage and access; monitor for suspicious patterns.

Error handling & leak prevention
- Safe error messages: do not expose stack traces or credentials.
- Validate and sanitize any data that might be returned to clients.

Evidence handling
- Validate file types and sizes on upload.
- Generate signed URLs for evidence access with short TTLs.
- Consider virus/malware scanning for uploads.

Monitoring & incident response
- Centralized monitoring in CloudWatch: metrics, logs, alarms.
- Define on-call and incident response procedures for security incidents.

Compliance & privacy
- Minimize PII collection; retain only needed data.
- Document retention policies and deletion flows.

Operational constraints
- Never allow LLMs to perform actions that change critical system state without explicit human authorization and an auditable acceptance step.

Developer hygiene
- Secrets in environment only via Secrets Manager; CI reads secrets from protected stores.
- Pre-commit hooks and automated security scans in CI.
