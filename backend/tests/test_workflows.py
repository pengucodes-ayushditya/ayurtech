from datetime import date, timedelta, datetime
from app.main import PRACTICE_TZ
from .conftest import register, patient, plan


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_authentication_required(client):
    assert client.get("/api/patients").status_code == 401


def test_register_and_duplicate_email(client):
    register(client)
    assert client.get("/api/auth/me").json()["user"]["role"] == "dietitian"
    assert (
        client.post(
            "/api/auth/register",
            json={
                "email": "doctor@example.com",
                "password": "LongPassword!123",
                "name": "Doctor",
                "clinic_name": "Clinic",
            },
        ).status_code
        == 409
    )


def test_cookie_is_http_only(client):
    r = client.post(
        "/api/auth/register",
        json={
            "email": "doctor@example.com",
            "password": "LongPassword!123",
            "name": "Doctor",
            "clinic_name": "Clinic",
        },
    )
    assert (
        "HttpOnly" in r.headers["set-cookie"]
        and "SameSite=lax" in r.headers["set-cookie"]
    )


def test_csrf_required(client):
    register(client)
    client.headers.pop("X-CSRF-Token")
    assert (
        client.post(
            "/api/patients",
            json={"name": "Patient", "age": 30, "email": "p@example.com"},
        ).status_code
        == 403
    )


def test_origin_rejected(client):
    assert (
        client.post(
            "/api/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "x@example.com", "password": "LongPassword!123"},
        ).status_code
        == 403
    )


def test_logout_revokes_session(client):
    register(client)
    cookie = client.cookies.get("ayurtech_session")
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.set("ayurtech_session", cookie)
    assert client.get("/api/auth/me").status_code == 401


def test_cross_clinic_access_denied(client):
    register(client)
    pid = patient(client)
    register(client, "other@example.com")
    assert client.get("/api/patients").json()["items"] == []
    assert client.get("/api/patients/" + pid).status_code == 404
    assert plan(client, pid).status_code == 404
    assert client.post("/api/patients/" + pid + "/invite").status_code == 404
    assert client.get("/api/dashboard").json()["active_patients"] == 0


def test_plan_calculation_and_conflict(client):
    register(client)
    pid = patient(client)
    r = plan(client, pid)
    assert r.status_code == 201, r.text
    assert r.json()["totals"] == {
        "calories": 195,
        "protein": 4.05,
        "carbs": 42,
        "fat": 0.45,
    }
    assert r.json()["version"] == 1
    assert plan(client, pid).status_code == 409
    assert plan(client, pid, 1).json()["version"] == 2


def test_allergy_blocks_plan(client):
    register(client)
    pid = patient(client, allergies=["milk"])
    assert plan(client, pid, food="milk").status_code == 422


def test_invalid_food_and_quantity(client):
    register(client)
    pid = patient(client)
    assert plan(client, pid, food="missing").status_code == 422
    assert plan(client, pid, grams=-20).status_code == 422
    assert plan(client, pid, grams=2001).status_code == 422


def test_publish_latest_and_supersede(client):
    register(client)
    pid = patient(client)
    p1 = plan(client, pid).json()
    assert (
        client.post(f'/api/patients/{pid}/plans/{p1["id"]}/publish').status_code == 200
    )
    p2 = plan(client, pid, 1).json()
    assert (
        client.post(f'/api/patients/{pid}/plans/{p1["id"]}/publish').status_code == 409
    )
    assert (
        client.post(f'/api/patients/{pid}/plans/{p2["id"]}/publish').status_code == 200
    )
    assert [
        p["status"] for p in client.get("/api/patients/" + pid).json()["plans"]
    ] == ["published", "superseded"]


def test_allergy_rechecked_on_publish(client):
    register(client)
    pid = patient(client)
    p = plan(client, pid, food="milk").json()
    assert (
        client.put(
            "/api/patients/" + pid,
            json={
                "name": "Patient",
                "age": 30,
                "email": "patient@example.com",
                "allergies": ["milk"],
            },
        ).status_code
        == 200
    )
    assert (
        client.post(f'/api/patients/{pid}/plans/{p["id"]}/publish').status_code == 422
    )


def test_plan_cannot_be_published_for_other_patient(client):
    register(client)
    pid = patient(client)
    other = patient(client, "other-p@example.com")
    p = plan(client, pid).json()
    assert (
        client.post(f'/api/patients/{other}/plans/{p["id"]}/publish').status_code == 404
    )


def test_invitation_and_patient_permissions(client):
    doctor = register(client)
    doctor_cookie = client.cookies.get("ayurtech_session")
    pid = patient(client)
    other = patient(client, "other-p@example.com")
    published = plan(client, pid).json()
    client.post(f'/api/patients/{pid}/plans/{published["id"]}/publish')
    plan(client, pid, 1)
    token = client.post("/api/patients/" + pid + "/invite").json()["token"]
    r = client.post(
        "/api/auth/claim",
        json={
            "email": "patient@example.com",
            "password": "PatientPass!123",
            "token": token,
        },
    )
    assert r.status_code == 201, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf"]
    assert len(client.get("/api/patients").json()["items"]) == 1
    assert client.get("/api/patients/" + other).status_code == 404
    visible = client.get("/api/patients/" + pid).json()["plans"]
    assert len(visible) == 1 and visible[0]["status"] == "published"
    assert plan(client, pid, 2).status_code == 403
    assert client.post("/api/patients/" + pid + "/invite").status_code == 403
    assert client.get("/api/dashboard").status_code == 403
    assert (
        client.post(
            "/api/auth/claim",
            json={
                "email": "patient@example.com",
                "password": "PatientPass!123",
                "token": token,
            },
        ).status_code
        == 400
    )
    client.cookies.set("ayurtech_session", doctor_cookie)
    client.headers["X-CSRF-Token"] = doctor["csrf"]
    assert client.get("/api/patients/" + pid).json()["portal_active"]


def test_reissued_invitation_invalidates_old(client):
    register(client)
    pid = patient(client)
    old = client.post("/api/patients/" + pid + "/invite").json()["token"]
    new = client.post("/api/patients/" + pid + "/invite").json()["token"]
    assert old != new
    assert (
        client.post(
            "/api/auth/claim",
            json={
                "email": "patient@example.com",
                "password": "PatientPass!123",
                "token": old,
            },
        ).status_code
        == 400
    )


def test_assessment_scoring_and_validation(client):
    register(client)
    pid = patient(client)
    r = client.post(
        "/api/patients/" + pid + "/assessments",
        json={"kind": "prakriti", "answers": ["Vata", "Pitta", "Kapha"] * 2},
    )
    assert r.status_code == 201 and r.json()["result"] == "Vata-Pitta-Kapha"
    assert (
        client.post(
            "/api/patients/" + pid + "/assessments",
            json={"kind": "prakriti", "answers": ["Vata"]},
        ).status_code
        == 422
    )


def test_checkin_upsert_and_future_rejection(client):
    register(client)
    pid = patient(client)
    url = "/api/patients/" + pid + "/checkins"
    first = client.post(
        url, json={"day": str(date.today()), "adherence": 80, "energy": 3}
    )
    second = client.post(
        url, json={"day": str(date.today()), "adherence": 90, "energy": 4}
    )
    assert first.json()["id"] == second.json()["id"]
    assert len(client.get("/api/patients/" + pid).json()["checkins"]) == 1
    assert (
        client.post(
            url,
            json={
                "day": str(datetime.now(PRACTICE_TZ).date() + timedelta(days=1)),
                "adherence": 80,
                "energy": 3,
            },
        ).status_code
        == 422
    )


def test_search_pagination_archive(client):
    register(client)
    pid = patient(client)
    assert client.get("/api/patients?q=test").json()["total"] == 1
    assert client.get("/api/patients?q=missing").json()["total"] == 0
    assert client.get("/api/patients?limit=101").status_code == 422
    client.put(
        "/api/patients/" + pid,
        json={
            "name": "Test Patient",
            "age": 30,
            "email": "patient@example.com",
            "status": "archived",
        },
    )
    assert client.get("/api/patients").json()["total"] == 0
    assert client.get("/api/patients?status=archived").json()["total"] == 1


def test_login_rate_limit(client):
    for _ in range(10):
        assert (
            client.post(
                "/api/auth/login",
                json={"email": "missing@example.com", "password": "LongPassword!123"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "LongPassword!123"},
        ).status_code
        == 429
    )


def test_normalized_email_and_allergens(client):
    register(client, "Doctor@Example.com")
    pid = patient(client, allergies=[" Milk ", "milk"])
    assert client.get("/api/patients/" + pid).json()["allergies"] == ["milk"]
