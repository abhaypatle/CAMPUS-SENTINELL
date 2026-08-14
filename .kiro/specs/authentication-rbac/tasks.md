# authentication-rbac — Tasks (P0)

This task list is ordered and includes dependencies, expected files/dirs, acceptance criteria, and testing requirements. Do not implement code in this spec.

1) Create backend auth project structure
- Description: scaffold folders and placeholder files for auth area.
- Files/dirs: backend/src/auth/, backend/src/auth/__init__.py, backend/src/auth/routes.py (stub), backend/src/auth/deps.py (stub), backend/src/auth/schemas.py (stub), backend/src/auth/models.py (stub)
- Dependencies: none
- Acceptance: files exist with TODO stubs and docstrings; imports resolve in CI lint step.
- Tests: none (scaffold-only)

2) Implement User model (ORM)
- Description: create `users` table ORM model matching spec.
- Files: backend/src/models/user.py, backend/src/db/models.py (where models are aggregated)
- Dependencies: DB connection module
- Acceptance: model defines fields `id,name,email,password_hash,role,created_at,updated_at,token_version`; role restricted to allowed enums; email unique constraint noted in migrations (deferred)
- Tests: unit test to instantiate model and validate role enum coercion

3) Password hashing utility
- Description: implement password hashing and verification using passlib/bcrypt or argon2.
- Files: backend/src/auth/hash.py
- Dependencies: User model
- Acceptance: provides `hash_password(plaintext)` and `verify_password(plaintext, hash)` functions; tests demonstrate correct verification and against wrong passwords
- Tests: unit tests for hashing and verification

4) Authentication schemas
- Description: Pydantic schemas for register/login/me and token responses.
- Files: backend/src/auth/schemas.py
- Dependencies: none
- Acceptance: schemas match design.md and reject invalid inputs
- Tests: schema validation unit tests

5) Registration API
- Description: implement POST /api/v1/auth/register endpoint logic (no DB migrations yet)
- Files: backend/src/api/v1/auth.py (or backend/src/auth/routes.py), tests/test_auth_register.py
- Dependencies: password hashing, User model, DB session
- Acceptance: successful registration returns 201 and does not return password; duplicate email returns 409
- Tests: tests 1 & 2 from Requirements

6) Login API
- Description: implement POST /api/v1/auth/login to verify credentials and issue short-lived token
- Files: backend/src/api/v1/auth.py
- Dependencies: password hashing, token util, User model
- Acceptance: valid credentials return token with `expires_in`; invalid credentials return 401
- Tests: tests 3 & 4

7) Current-user API
- Description: GET /api/v1/auth/me using auth dependency
- Files: backend/src/api/v1/auth.py
- Dependencies: get_current_user dependency
- Acceptance: returns user info excluding password/hash
- Tests: test 5, 13

8) Authentication dependency (get_current_user)
- Description: implement token parsing, validation, DB user lookup, and return user object
- Files: backend/src/auth/deps.py
- Dependencies: token util, DB
- Acceptance: invalid/expired token => 401; valid token => user
- Tests: tests 14 & 15

9) RBAC dependency (require_role)
- Description: implement dependency factory to require roles
- Files: backend/src/auth/deps.py
- Dependencies: get_current_user
- Acceptance: returns 403 when role not permitted; passes when permitted
- Tests: tests 6-10

10) Resource ownership checks
- Description: implement generic ownership dependency helper `require_resource_owner` for endpoints operating on user-owned resources
- Files: backend/src/auth/deps.py, backend/src/utils/ownership.py
- Dependencies: get_current_user, DB models
- Acceptance: REPORTER can access own resources; ADMIN can access all; others denied
- Tests: tests 11

11) Frontend authentication state
- Description: implement `AuthProvider` context and hooks in React repository
- Files: frontend/src/contexts/AuthContext.tsx, frontend/src/hooks/useAuth.ts
- Dependencies: API endpoints
- Acceptance: currentUser state available; login/register/logout methods work against API endpoints (mocked in tests)
- Tests: React tests for context

12) Login UI
- Description: Login page with form, error handling, and redirect on success
- Files: frontend/src/pages/Login.tsx
- Dependencies: AuthProvider
- Acceptance: valid login uses API and stores currentUser/token (in memory or cookie as chosen)
- Tests: login flow UI tests

13) Registration UI
- Description: Register page with form and client-side validation
- Files: frontend/src/pages/Register.tsx
- Dependencies: AuthProvider
- Acceptance: registration POST called; success redirects to login or auto-login based on design
- Tests: registration flow UI tests

14) Protected routes
- Description: route wrapper for protecting pages; UI shows unauthorized page if needed
- Files: frontend/src/components/ProtectedRoute.tsx
- Dependencies: AuthProvider
- Acceptance: routes blocked client-side for unauthenticated users; backend remains authoritative
- Tests: protected route behavior tests

15) Role-aware navigation
- Description: navbar/menu shows items per current user's role
- Files: frontend/src/components/NavBar.tsx
- Dependencies: AuthProvider
- Acceptance: Admin sees admin menu; Reporter/Responder see limited items
- Tests: unit tests for NavBar role cases

16) Backend tests (pytest)
- Description: implement tests listed in Requirements under tests/ directory
- Files: backend/tests/test_auth_*.py
- Dependencies: DB test fixtures, test client
- Acceptance: all auth tests pass in CI

17) Frontend tests
- Description: implement React tests for auth flows and protected routes
- Files: frontend/src/__tests__/auth.test.tsx
- Dependencies: testing-library/react, msw for mocking API
- Acceptance: tests cover flows listed in Requirements

18) Security verification
- Description: verify password hashing, token TTLs, role enforcement, no secrets leaked in APIs or logs
- Files: docs/security-checklist.md, backend/tests/test_security_auth.py
- Dependencies: completed implementation
- Acceptance: security checklist passes and automated tests validate key properties

Notes on ordering
- Tasks 1-4 are prerequisites for 5-9. Frontend tasks can be worked in parallel after contract (schemas) are defined.

Estimated minimal file tree for these tasks (backend/frontend)
- backend/
  - src/
    - auth/
      - deps.py
      - hash.py
      - schemas.py
      - routes.py
    - api/
      - v1/
        - auth.py
    - models/
      - user.py
    - db/
      - session.py
- frontend/
  - src/
    - contexts/
      - AuthContext.tsx
    - hooks/
      - useAuth.ts
    - pages/
      - Login.tsx
      - Register.tsx
    - components/
      - ProtectedRoute.tsx
      - NavBar.tsx

Acceptance criteria summary
- All auth endpoints validate input and enforce RBAC.
- Passwords hashed; none returned by API.
- Tests cover all required cases.
- Backend is central authority for authorization; frontend enforces UX only.

Testing requirements summary
- Use pytest for backend; include fixtures for DB and test client.
- Use React Testing Library and msw for frontend tests.

