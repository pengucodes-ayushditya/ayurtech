# AyurTech

A full-stack dietitian practice workspace and patient portal, rebuilt from a second-year hackathon prototype. React + TypeScript frontend, FastAPI API, SQLAlchemy persistence, PostgreSQL deployment configuration, and SQLite for local development.

This release is a working **portfolio MVP**, not a clinically validated healthcare product. It retains the original use case without inventing trained AI, clinical accuracy, compliance certifications, or production usage metrics. Use fictional records.

## What works

- Dietitian registration creates an isolated clinic workspace.
- Password hashing with scrypt; revocable server-side sessions; only hashed session credentials are stored.
- HttpOnly, SameSite cookies; configurable Secure cookies; CSRF and origin checks on mutations.
- Patient creation, editing, archiving, name search, and paginated listings.
- Single-use, expiring patient invitations. Patients see their own records and published plans.
- Prakriti / Vikriti self-report questionnaires with server-side scoring and history.
- 23 searchable foods imported from the supplied prototype with provenance labels.
- Meal planning with gram quantities and server-calculated calories and macronutrients.
- Immutable plan versions, draft/publish lifecycle, superseding earlier published plans, and stale-edit detection.
- Allergy conflicts checked on both save and publication against recorded catalog allergens.
- Daily adherence and energy check-ins, updated idempotently by patient/date.
- Clinic-scoped dashboard, audit events, JSON plan export, and responsive interfaces.
- Alembic migrations, API documentation, backend/frontend tests, Docker Compose, and GitHub Actions.

## Quick start: Docker + PostgreSQL

Requirements: Docker Engine / Docker Desktop with Compose running. No local Python or Node installation needed.

```sh
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000 and create a practice. The application seeds the food catalog but **does not create demo users automatically**. To add fictional demo users in development:

```sh
docker compose exec app python -m app.seed --demo
```

Demo logins:

| Role | Email | Password |
| --- | --- | --- |
| Dietitian | dietitian@ayurtech.demo | AyurTechDemo!2026 |
| Patient | patient@ayurtech.demo | AyurTechDemo!2026 |

The demo seeder is idempotent and refuses `--demo` when `APP_ENV=production`. Database state persists in the `postgres_data` volume. Do not run `docker compose down -v` unless you intend to erase that database.

## Quick start: local SQLite

Requirements: Python 3.12+, Node.js 22.12+, pnpm 11.25.0.

The download includes a prebuilt `frontend/dist` for a first look; you can skip the frontend install/build steps below when using that bundle. Rebuild after source edits.

From the project root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
cd frontend
pnpm install --frozen-lockfile
pnpm run build
cd ../backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed --demo
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs. Sign in with the demo credentials above, or register your own practice. New practices start empty and do not share the seeded clinic's patients.

For frontend development, leave the API running and use a second terminal:

```sh
cd frontend
pnpm dev
```

Open the printed port 5173 URL. Vite proxies `/api` to the backend. Use `/docs` on port 8000, not on Vite. Production serves the compiled React app and API from the same origin.

## Five-minute demo

1. Sign in as the demo dietitian. Open a patient.
2. Edit their notes or recorded allergies; run either educational assessment.
3. Select **Build diet plan**, add foods and quantities, and save a new draft version.
4. Publish that version. Older published versions become superseded.
5. For an unconnected patient, create a portal invitation. Copy its link into a separate browser session. Activate using that patient's recorded email and a new password. Links expire in 48 hours and work once.
6. Alternatively, sign out and use the seeded patient login. View the published plan and record a check-in.
7. Return as a dietitian and inspect the check-in and audit events.
8. Export a plan as JSON to inspect its immutable food and nutrition snapshots.

## Checks

```sh
cd backend
../.venv/bin/python -m pytest -q
../.venv/bin/alembic check
cd ../frontend
pnpm test
pnpm run build
```

`test_postgres.py` skips unless `DATABASE_URL` points at an isolated PostgreSQL database whose name contains `_test`. CI creates that database, applies migrations, seeds foods, and tests the save/publish workflow. Never point test infrastructure at real patient data.

Verified: 53 backend checks passed inside Docker across SQLite/PostgreSQL, 3 frontend tests passed, and the production bundle and migrations passed. External HTTP and browser workflows, app/database restarts, and backup restoration were verified. Dependency audits reported zero known advisories after updating the test tooling. Cloud deployment and GitHub Actions remain pending. See `docs/VERIFICATION.md` for the exact scope.

## Verify the Docker/PostgreSQL implementation

With Docker Desktop running, use the isolated verification stack:

```sh
docker compose -p ayurtech-verify -f compose.verify.yaml up --build --abort-on-container-exit --exit-code-from verify
docker compose -p ayurtech-verify -f compose.verify.yaml down
```

This creates a disposable test database, applies/checks migrations, seeds reference foods, and runs the tests against SQLite plus the real PostgreSQL workflow. The PostgreSQL test also races two saves with the same expected version and requires one success and one 409 conflict. The verification stack has no public database port or persistent volume. It does not touch the normal Compose database.

After that passes, run the normal stack and verify persistence: create a fictional practice/patient, publish a plan, restart the app service, sign in again, and confirm the records remain. Database backup/restore and a deployed HTTPS smoke test remain separate checks.

## Configuration

| Variable | Default / purpose |
| --- | --- |
| `DATABASE_URL` | `sqlite:///./ayurtech.db`; PostgreSQL uses `postgresql+psycopg://…` |
| `ALLOWED_ORIGINS` | Exact allowed UI origins; defaults to `RENDER_EXTERNAL_URL` on Render, otherwise local origins |
| `COOKIE_SECURE` | `false` locally; **true behind HTTPS** |
| `APP_TIMEZONE` | `Asia/Kolkata`; clinic timezone used for check-in date validation |
| `APP_ENV` | `production` prohibits demo seeding and requires PostgreSQL, Secure cookies, and HTTPS UI origins |
| `PORT` | Container HTTP port; defaults to 8000, set to 10000 in Render |
| `POSTGRES_PASSWORD` | Required by Compose; use a long random password without URL-reserved characters, or percent-encode the DB URL separately |

## Deployment

The Docker image serves both React and FastAPI, so it can run on a container host with managed PostgreSQL. A dedicated Neon project is provisioned; the Render deployment is prepared but not live yet. See `docs/DEPLOYMENT.md` for the selected free Render + Neon setup. Do not upload the local SQLite database or demo credentials to a real patient deployment.

1. Build the Dockerfile from the project root.
2. Provision PostgreSQL and set `DATABASE_URL` as a runtime secret.
3. Set `APP_ENV=production`, `COOKIE_SECURE=true`, and `ALLOWED_ORIGINS=https://your-domain`.
4. Terminate HTTPS at your hosting provider/reverse proxy; expose container port 8000 and use `/api/health` for readiness.
5. Apply `alembic upgrade head` once as a release step before scaling replicas. The default image command is intended for one application instance and runs migrations at startup.
6. Configure encrypted storage/backups, restoration tests, monitoring, email delivery, password reset, clinician identity verification, consent, and appropriate retention policies before accepting real data.
7. Replace the in-process authentication limiter with a shared gateway/Redis limiter before multiple workers or replicas. Do not trust arbitrary client-supplied proxy headers.

The Sites runtime hosts JavaScript Workers, so this Python/PostgreSQL backend is delivered as a portable repository rather than an incompatible Sites deployment.

## Repository map

```text
backend/
  app/           API routes, validation, auth, ORM models, business services, seeder
  migrations/    Versioned database schema
  tests/         Access-control and workflow tests
frontend/
  src/           Typed React workspace, patient portal, API client, styles, preview tests
  pnpm-lock.yaml Reproducible frontend dependency graph
.github/workflows/ci.yml
Dockerfile       Multi-stage frontend build + non-root Python runtime
compose.yaml     App and persistent PostgreSQL with health checks
docs/            Architecture, API map, verification, and interview preparation
```

## Honest limitations

The food nutrient values and Ayurvedic properties came from the original hackathon demo; they are not verified food-composition data. Allergen labels are illustrative and incomplete. The questionnaire is a six-question deterministic self-report exercise, not a validated diagnostic model. Planning is manual, with no automated treatment recommendations.

This version does not include appointments, billing, MFA, password reset, email delivery, custom food editing, clinician verification, background jobs, distributed rate limiting, or clinically validated recommendations. Patient invitations currently connect a patient account to one practice. Patient data uses JSON-backed snapshots for plans and assessments, while identity and ownership are relational. See architecture notes for the rationale and next steps.
