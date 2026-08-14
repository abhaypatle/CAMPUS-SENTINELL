# authentication-rbac — Design (P0)

Overview
- FastAPI backend is the central authority for authentication and RBAC.
- Use Pydantic models for request/response validation and AI safety patterns.
- Password hashing with bcrypt/argon2; secrets stored in AWS Secrets Manager (or env during local dev).
- Token strategy: short-lived JWT access tokens signed by server private key (rotateable). Refresh tokens deferred; consider Cognito later.

Auth flow
1. Registration: client POSTs to /api/v1/auth/register with name, email, password.
2. Backend validates input, hashes password, creates user with role=REPORTER, returns user summary (no password fields).
3. Login: client POSTs to /api/v1/auth/login with email/password. Backend verifies password hash and returns short-lived JWT access token.
4. Client stores token in memory (or secure httpOnly cookie if chosen) and uses Bearer token for subsequent requests.
5. Backend dependency extracts current user from token, verifies user is active and role.

Token considerations
- Use JWTs with short TTL (e.g., 15 minutes). Sign tokens with an asymmetric keypair or HMAC secret stored in Secrets Manager.
- Do not embed mutable authorization state (e.g., revocation) solely in JWTs; support token revocation via server-side blacklist or token version in DB (store `token_version` on users).
- Design so Cognito/OPA can replace token issuance later with minimal code changes by abstracting provider behind an `IAuthProvider` interface.

FastAPI dependencies (conceptual)
- def get_db(): yields DB session
- def get_settings(): returns config
- def get_password_hasher(): returns bcrypt/argon2 hasher

- def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
  - validate token signature and expiry
  - load user by id from token
  - ensure user exists
  - return user model

- def require_role(*roles: RoleEnum):
  - returns a dependency that checks `current_user.role in roles` else raises 403

- def require_resource_owner(resource_user_id_field: str):
  - checks that `current_user.id == resource_owner_id` or current_user.role == ADMIN

Authorization patterns
- Centralize authorization in dependency modules; do not repeat logic in endpoints.
- Use `Depends(get_current_user)` on protected endpoints and wrap with `Depends(require_role('ADMIN'))` where needed.
- For resource access (evidence upload, viewing a report) use owner check `Depends(require_resource_owner('report.owner_id'))` or check assignment for RESPONDER role.

Example endpoint signatures (conceptual)
- POST /api/v1/auth/register -> create_user(request: RegisterIn) -> RegisterOut
- POST /api/v1/auth/login -> TokenOut
- GET /api/v1/auth/me -> requires get_current_user -> UserOut

Schemas (Pydantic)
- RegisterIn: name: str, email: EmailStr, password: constr(min_length=8)
- UserOut: id: UUID, name: str, email: EmailStr, role: Literal['REPORTER','RESPONDER','ADMIN'], created_at: datetime, updated_at: datetime
- TokenOut: access_token: str, token_type: 'bearer', expires_in: int

Database model (ORM conceptual)
- users table:
  - id: UUID, PK
  - name: text
  - email: text, unique
  - password_hash: text
  - role: enum('REPORTER','RESPONDER','ADMIN')
  - token_version: int (for revocation strategy)
  - created_at, updated_at timestamps

Password hashing
- Use bcrypt or argon2 with appropriate work factor.
- Use a tested library (passlib or argon2-cffi).
- Never log passwords.

Error handling
- Consistent error responses (problem details). Return 401 for auth failures, 403 for authorization failures, 409 for conflicts.

Audit considerations
- Record auth events in audit trail: registration, login (optionally), failed login attempts, role changes, logout if tracked.
- Ensure audit logs redact sensitive details.

Frontend integration points
- Client calls register/login endpoints and stores tokens in memory or secure cookie.
- Provide `AuthProvider` React context exposing: currentUser, login(), logout(), register(), hasRole(role).
- Protect routes UI-side but rely on backend checks for enforcement.

Cognito readiness
- Abstract token issuance/verification behind an `AuthProvider` abstraction so switching to Cognito later requires implementing the same interface.

Operational
- Rate-limit registration and login endpoints to mitigate brute force.
- Enforce strong password policy later via zxcvbn or similar if desired.

Notes
- The design aims to be minimal and auditable; avoid heavy auth libraries that obscure behavior.
