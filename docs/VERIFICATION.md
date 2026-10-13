# Verification record — 13 October 2026

## Passed locally

- **53 backend checks inside Docker**: 22 workflow/access-control tests on SQLite, the same 22 on isolated PostgreSQL schemas, 8 provider configuration cases, and a PostgreSQL save/publish/concurrent-save integration test. All passed.
- **3 frontend tests**, TypeScript strict compilation, and Vite production build. The Docker build runs frontend tests before bundling.
- PostgreSQL 17 migrations applied successfully; `alembic check` reports no schema drift.
- Docker image built successfully and runs as a non-root user. App and PostgreSQL containers report healthy.
- External HTTP flow: dietitian registration, patient creation, assessment, allergy rejection, server-calculated nutrition, stale-version rejection, plan publication, patient invitation/activation, patient role enforcement, check-in, and compiled frontend delivery.
- Patient records and sessions survived an app restart. Records survived a PostgreSQL restart.
- A PostgreSQL custom-format backup restored to a separate test database; the expected patient, published plan, and check-in were confirmed there.
- Logout rejected replay of the old session cookie.
- Browser with Docker/PostgreSQL: dietitian sign-in, patient profile, new version with oats changed from 180 to 200 g, publication/supersession, mobile navigation and sign-out, and patient sign-in displaying published version 2.
- Both Python and frontend dependency audits reported **zero known advisories** at verification time. Vitest was upgraded to 4.1.11 after test-tool advisories were detected. Package audits are not a substitute for a security review.
- Normal, isolated verification, and HTTP-test Compose configurations validate.

## Cloud preparation

- Dedicated Neon project created in Singapore with PostgreSQL 17 and 0.25 CU compute allocation.
- `render.yaml` configures a free Docker web service, secure cookies, production mode, health checks, and deployment after CI passes.
- Provider PostgreSQL URL aliases are normalized to the installed psycopg driver while preserving credentials and TLS parameters.
- The app accepts Render's platform-assigned origin and port. Production startup rejects SQLite fallback, insecure cookies, and missing/non-HTTPS UI origins.

## Still pending

- Render deployment and live Neon connectivity/migrations.
- HTTPS browser checks and production secure-cookie behavior.
- GitHub Actions execution after source publication.
- Production load/capacity testing, distributed rate limiting, password recovery/MFA, email delivery, automated backup schedules, monitoring and clinical validation.

The Starlette test client reports one deprecation warning about its httpx backend. Tests pass without suppressing the warning. Vite/Vitest use native configuration loading to avoid a config-loading hang observed in the authoring environment.
