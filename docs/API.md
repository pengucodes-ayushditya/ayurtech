# API map

FastAPI generates the full OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.

All routes below are prefixed `/api`. Authenticated mutations require the session cookie and `X-CSRF-Token` returned by login or `/auth/me`.

| Method | Route | Access / purpose |
| --- | --- | --- |
| GET | /health | Public database health |
| POST | /auth/register | Public; create isolated clinic/dietitian |
| POST | /auth/login | Public; password-authenticated session |
| GET | /auth/me | Current user and CSRF secret |
| POST | /auth/logout | Revoke current session |
| POST | /auth/claim | Activate single-use patient invitation |
| GET | /patients?q=&status=&offset=&limit= | Own clinic or linked patient; bounded pagination |
| POST | /patients | Dietitian; create patient |
| GET | /patients/{id} | Clinic owner / linked patient; plan visibility enforced |
| PUT | /patients/{id} | Dietitian; edit/archive; active portal email protected |
| POST | /patients/{id}/invite | Dietitian; 48-hour invite; reissue invalidates old token |
| GET | /foods?q=&offset=&limit= | Signed-in reference catalog |
| POST | /patients/{id}/assessments | Authorized patient/dietitian; six answers; server scoring |
| POST | /patients/{id}/plans | Dietitian; save immutable draft; expected_version required |
| POST | /patients/{id}/plans/{plan_id}/publish | Dietitian; latest version only |
| POST | /patients/{id}/checkins | Authorized patient/dietitian; one record per date |
| GET | /dashboard | Dietitian; clinic-scoped counts and recent audit events |

Error semantics: 401 missing/expired session; 403 wrong role or CSRF/origin failure; 404 inaccessible/missing object; 409 duplicate account, stale plan or conflicting state; 422 invalid fields, food references or recorded allergen conflict; 429 authentication limiter.

Example plan payload:

```json
{
  "title": "Daily sample plan",
  "expected_version": 0,
  "notes": "Fictional portfolio example",
  "items": [{"meal": "Lunch", "food_id": "2", "grams": 150}]
}
```

`food_id` is obtained from `/foods`. Nutrient totals are computed on the server and returned in `totals`, along with immutable food snapshots in `items`.
