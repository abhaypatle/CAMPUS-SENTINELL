# authentication-rbac — Requirements (P0)

Scope
- Covers only P0 Authentication & RBAC for Campus Sentinel.
- No implementation code in this spec.

Roles (exact)
1. REPORTER
2. RESPONDER
3. ADMIN

Permissions (per-role)

REPORTER
- Register
- Login
- View own profile
- Submit incident reports
- Upload evidence for own reports
- View own submitted reports
- View status of own reports
- View permitted notifications/status updates

RESPONDER
- Login
- View incidents assigned to them
- View permitted incident details
- Add response notes
- Update permitted incident lifecycle states
- Add resolution evidence
- Resolve assigned incidents when authorized

ADMIN
- Login
- View all authorized incidents
- View command center
- Review AI analysis
- Review incident fusion
- View risk score and risk factors
- View escalation state
- Assign responders
- Change authorized incident lifecycle states
- Request SOP recommendations
- Review AI recommendations
- View audit history
- Manage incident resolution workflow

Security requirements
- Use secure authentication (password-based or token-based) with short-lived tokens.
- Backend is final authority for authorization; never trust role info from frontend.
- Every protected endpoint must validate: authentication, user identity, user role, resource ownership (where applicable), requested action.
- Use least-privilege.
- Do not expose passwords/secrets through APIs.
- Store password hashes only; never plaintext.
- Use secure password hashing (e.g., bcrypt/argon2).
- Use short-lived authentication tokens or session handling appropriate for architecture.
- Design so authentication can later integrate with AWS Cognito.
- No AWS credentials exposed to frontend.

Backend technology
- FastAPI, Python 3.11+, Pydantic for schemas and validation.

API endpoints (auth)
- POST /api/v1/auth/register
  - Request: {"name": string, "email": string, "password": string}
  - Response 201: {"id": uuid, "name": string, "email": string, "role": "REPORTER", "created_at": iso8601}
  - Error 400: validation errors
  - Error 409: duplicate email
  - Note: Newly registered users default to REPORTER role.

- POST /api/v1/auth/login
  - Request: {"email": string, "password": string}
  - Response 200: {"access_token": string, "token_type": "bearer", "expires_in": int}
  - Error 401: invalid credentials
  - Note: access_token must be short-lived; refresh handling deferred to later design.

- GET /api/v1/auth/me
  - Auth required (Bearer token)
  - Response 200: {"id": uuid, "name": string, "email": string, "role": "REPORTER|RESPONDER|ADMIN", "created_at": iso8601, "updated_at": iso8601}
  - Note: never return password or password_hash.

Database: User model (minimum)
Table: users
- id: uuid, primary key
- name: text
- email: text, unique, indexed
- password_hash: text
- role: enum('REPORTER','RESPONDER','ADMIN')
- created_at: timestamp with timezone
- updated_at: timestamp with timezone

Frontend (React + TypeScript)
- Register page: form (name, email, password) with client-side validation (React Hook Form + Zod)
- Login page: email + password
- Protected application routes: require backend auth checks; frontend enforces UX-level protection only
- Role-aware navigation: show menu items based on current user's role
- Logout
- Current-user state: centralized context/store

Testing (coverage)
Backend tests (pytest):
1. Successful registration
2. Duplicate email rejection
3. Successful login
4. Invalid password rejection
5. Unauthenticated protected endpoint
6. REPORTER accessing reporter functionality
7. REPORTER denied ADMIN functionality
8. RESPONDER accessing permitted functionality
9. RESPONDER denied ADMIN-only functionality
10. ADMIN accessing admin functionality
11. User cannot access another user's protected resource
12. Invalid/unsupported role rejected
13. Password is never returned by API
14. Token/session validation failure
15. Expired/invalid authentication rejected

Frontend tests
- React testing for: registration flow, login flow, protected-route UX, role-aware navigation, logout, current-user state.

Non-functional
- Keep design simple and auditable.
- Backend remains central authority for auth and RBAC.
- Do not introduce Redis/Kubernetes/microservices for auth.
- Prepare for future Cognito integration by abstracting auth provider layer.
