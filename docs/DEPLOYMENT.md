# Render + Neon portfolio deployment

Selected deployment: free Render Docker web service plus Neon PostgreSQL. The software is a fictional-data portfolio demo. Free tiers have usage limits and availability trade-offs; confirm the account's free plan before provisioning. Do not switch to paid plans as part of this setup.

## Source and CI

The source is published at https://github.com/pengucodes-ayushditya/ayurtech. Run GitHub Actions, deploy, and verify the live app. Hosting deployment is separate from source publication. Never commit `.env`, database dumps, API tokens, session cookies, or database connection strings.

The tracked `render.yaml` declares a free service and uses `autoDeployTrigger: checksPass`. The Docker build includes frontend tests and bundling; startup applies migrations, seeds only reference foods, and starts the API on the assigned `PORT`.

## Neon

Use PostgreSQL 17 in Singapore to place the database near the Render service. Create the `ayurtech` database and an application role. Obtain a TLS-enabled connection URL through the Neon connection interface. The application accepts `postgres://`, `postgresql://`, and `postgresql+psycopg://` URL prefixes; it preserves TLS query parameters and normalizes the first two to psycopg.

Store the connection string only as Render's `DATABASE_URL` secret. For migrations, use the direct database connection URL. Avoid exporting it into repository files, logs, or screenshots. Keep compute/storage within the free plan's limits and monitor usage in the provider dashboard.

## Render

Import the repository as a Blueprint or create a Docker web service using these settings:

| Setting | Value |
| --- | --- |
| Plan | Free |
| Region | Singapore |
| Dockerfile | `./Dockerfile` |
| Health check | `/api/health` |
| `DATABASE_URL` | Neon TLS connection string, secret |
| `APP_ENV` | `production` |
| `COOKIE_SECURE` | `true` |
| `APP_TIMEZONE` | `Asia/Kolkata` |
| `PORT` | `10000` |

`ALLOWED_ORIGINS` defaults to Render's `RENDER_EXTERNAL_URL`, so the hostname does not need to be guessed before the first deploy. Set it explicitly to exact HTTPS origins when adding a custom domain.

Render's free web service sleeps after inactivity; its first request may take time to wake. Neon is used instead of Render's expiring free PostgreSQL offering. This design has not been claimed as always-on production infrastructure.

## Live verification

1. Confirm the deployment and database health endpoint return success over HTTPS.
2. Register a fictional practice in the browser. Confirm the session cookie is HttpOnly, Secure, and SameSite=Lax.
3. Complete patient creation, assessment, plan draft/publication, portal invitation/activation, and patient check-in.
4. Confirm wrong-role and cross-clinic requests are rejected. Verify CSRF and unapproved-origin rejection.
5. Restart/redeploy the service and confirm records remain in Neon.
6. Run `python scripts/verify_http.py --base-url https://YOUR-DEPLOYMENT` for the reusable HTTP smoke flow. This creates clearly named fictional test records. Do not pass `--docker-checks` for a cloud URL.
7. Confirm GitHub Actions passes and add the actual live URL to README after the live checks pass.

## Reproduce Docker persistence and restore checks locally

From the repository root:

```sh
docker compose -p ayurtech-e2e --env-file .env.example -f compose.yaml -f compose.e2e.yaml up -d --build
python scripts/verify_http.py --docker-checks
```

This uses port 8001, an isolated `ayurtech_e2e_test` database, and a project-specific volume. The script verifies records/sessions after app restart, records after database restart, and restores a backup into a separate uniquely named test database. Credentials remain in process memory and are not printed. Use a Python environment with httpx installed.

Stop it afterward with the same Compose arguments and `stop`. Its fictional test volume can be retained for inspecting results. The separate `compose.verify.yaml` stack uses disposable test schemas for pytest and has no public database port.

## References checked during preparation

- [Render free-tier limits](https://render.com/docs/free)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render platform environment variables](https://render.com/docs/environment-variables)
- [Neon free plan and compute behavior](https://neon.com/blog/building-patterns-unlocked-by-scale-to-zero)
