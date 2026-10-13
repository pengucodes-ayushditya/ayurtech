# Showcase and interview guide

## Resume wording grounded in this implementation

**AyurTech — Full-stack Dietitian Practice Platform** | React, TypeScript, FastAPI, SQLAlchemy, PostgreSQL, Docker

- Rebuilt a browser-only hackathon prototype into a full-stack practice platform with authenticated dietitian/patient portals, clinic-scoped authorization, and persistent relational data.
- Implemented versioned diet plans with server-calculated nutrition, allergy checks, transactional audit events, and conflict detection for stale edits.
- Added automated access-control and workflow tests, Alembic migrations, Docker Compose configuration, and a GitHub Actions pipeline.

Say “configured PostgreSQL and container deployment” until you actually run the supplied stack and deploy it. Do not claim deployment, performance improvements, clinical accuracy, compliance, microservices, or AI capabilities without evidence. Customize the bullets once you understand and can explain the code.

## Demo sequence

Show the dashboard, a patient profile, the assessment, a new diet draft, and publication. Switch to the patient account, show the published plan, record a daily check-in, and return to the dietitian view. Then show a passing authorization test and the schema migration. That demonstrates both product behavior and engineering discipline.

## Questions you should be able to answer

1. Why a modular monolith? A single transaction boundary and deployment are appropriate for the current scale; services can be extracted when independent scaling or ownership warrants them.
2. Why PostgreSQL plus SQLite? PostgreSQL is the deployable relational database; SQLite makes local demos easy. Locking and write concurrency differ, so PostgreSQL-specific behavior needs integration verification.
3. How do you prevent insecure direct object references? Each patient lookup checks clinic ownership and patient account linkage, independently of any UI filtering.
4. Why server-side sessions rather than storing JWTs in localStorage? Revocation is direct; HttpOnly cookies keep bearer tokens out of JavaScript; CSRF protection addresses cookie-based requests.
5. How are nutrition totals trusted? The server reads catalog values, scales grams, and persists immutable snapshots rather than accepting client totals.
6. How do conflicting edits behave? The expected version is checked under a PostgreSQL row lock; database uniqueness is a final guard. Stale clients receive 409.
7. What is the clinical model? There is no validated model. The assessment is deterministic educational scoring, and food properties remain prototype data.
8. How would you scale? Add measured load tests, indexed workload-driven queries, connection pooling capacity, shared rate limiting, a release migration step, and observability before adding services.
9. What remains before real users? Clinician verification, privacy/consent/retention, validated nutrition/allergen data, password recovery/MFA, email delivery, HTTPS, encrypted backups, restore testing, monitoring, and operational review.

## Own the project

Read `security.py`, `services.py`, and the plan routes before presenting it. Run the tests, create your own clinic, and reproduce a 409 conflict using two browser tabs. Change one feature yourself and add a meaningful test. Deploy the Docker stack to your chosen host and add a screenshot, live URL, and actual verification result to the README.
