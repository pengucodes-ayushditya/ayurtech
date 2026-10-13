"""External HTTP smoke test. Creates fictional records; prints no passwords/cookies.

Run from a Python environment with httpx installed. Optional Docker restart/restore
checks are restricted to the disposable ayurtech-e2e project.
"""

import argparse
import json
import secrets
import subprocess
import time
from datetime import datetime
from uuid import uuid4, UUID
from zoneinfo import ZoneInfo
import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:8001")
parser.add_argument("--docker-checks", action="store_true")
args = parser.parse_args()
if args.docker_checks and args.base_url.rstrip("/") != "http://127.0.0.1:8001":
    parser.error(
        "Docker restart/restore checks are restricted to the local ayurtech-e2e stack"
    )


def docker(*parts, data=None):
    return subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            "ayurtech-e2e",
            "--env-file",
            ".env.example",
            "-f",
            "compose.yaml",
            "-f",
            "compose.e2e.yaml",
            *parts,
        ],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def ready():
    for _ in range(60):
        try:
            if httpx.get(args.base_url + "/api/health", timeout=3).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise AssertionError("Application did not become ready")


def request(client, method, path, body=None, status=200):
    response = client.request(method, path, json=body)
    assert (
        response.status_code == status
    ), f"{method} {path}: expected {status}, got {response.status_code}"
    return response.json() if response.status_code != 204 else None


ready()
tag = uuid4().hex
password = secrets.token_urlsafe(24)
patient_password = secrets.token_urlsafe(24)
with httpx.Client(base_url=args.base_url, timeout=20) as doctor, httpx.Client(
    base_url=args.base_url, timeout=20
) as patient:
    response = request(
        doctor,
        "POST",
        "/api/auth/register",
        {
            "email": f"verify-{tag}@example.com",
            "password": password,
            "name": "Fictional Verification Dietitian",
            "clinic_name": "Fictional Verification Practice",
        },
        201,
    )
    doctor.headers["X-CSRF-Token"] = response["csrf"]
    pid = request(
        doctor,
        "POST",
        "/api/patients",
        {
            "name": "Fictional Verification Patient",
            "age": 30,
            "gender": "Female",
            "email": f"patient-{tag}@example.com",
            "allergies": ["milk"],
        },
        201,
    )["id"]
    foods = request(doctor, "GET", "/api/foods")["items"]
    food = next(f for f in foods if f["name"] == "Basmati Rice (cooked)")
    milk = next(f for f in foods if f["name"] == "Cow's Milk")
    request(
        doctor,
        "POST",
        f"/api/patients/{pid}/assessments",
        {"kind": "prakriti", "answers": ["Vata"] * 6},
        201,
    )
    payload = {
        "title": "Fictional HTTP verification plan",
        "notes": "Non-clinical automated verification",
        "expected_version": 0,
        "items": [{"meal": "Lunch", "food_id": food["id"], "grams": 150}],
    }
    request(
        doctor,
        "POST",
        f"/api/patients/{pid}/plans",
        {**payload, "items": [{"meal": "Lunch", "food_id": milk["id"], "grams": 150}]},
        422,
    )
    plan = request(doctor, "POST", f"/api/patients/{pid}/plans", payload, 201)
    assert plan["totals"]["calories"] == 195
    request(doctor, "POST", f"/api/patients/{pid}/plans", payload, 409)
    request(doctor, "POST", f'/api/patients/{pid}/plans/{plan["id"]}/publish')
    invite = request(doctor, "POST", f"/api/patients/{pid}/invite")
    claimed = request(
        patient,
        "POST",
        "/api/auth/claim",
        {
            "email": f"patient-{tag}@example.com",
            "password": patient_password,
            "token": invite["token"],
        },
        201,
    )
    patient.headers["X-CSRF-Token"] = claimed["csrf"]
    record = request(patient, "GET", f"/api/patients/{pid}")
    assert record["plans"][0]["id"] == plan["id"]
    request(patient, "POST", f"/api/patients/{pid}/plans", payload, 403)
    day = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    request(
        patient,
        "POST",
        f"/api/patients/{pid}/checkins",
        {
            "day": day,
            "adherence": 90,
            "energy": 4,
            "note": "Fictional smoke-test record",
        },
        201,
    )
    assert (
        request(doctor, "GET", f"/api/patients/{pid}")["checkins"][0]["adherence"] == 90
    )
    html = doctor.get("/")
    assert html.status_code == 200 and '<div id="root">' in html.text
    print(
        "PASS: external HTTP registration, profiles, assessments, allergy checks, plan versioning, publication, invitation, patient authorization, check-in, and frontend delivery"
    )
    if args.docker_checks:
        docker("restart", "app")
        ready()
        record = request(patient, "GET", f"/api/patients/{pid}")
        assert (
            record["plans"][0]["id"] == plan["id"]
            and record["checkins"][0]["adherence"] == 90
        )
        print("PASS: patient session and records survive app restart")
        docker("restart", "db")
        ready()
        assert (
            request(patient, "GET", f"/api/patients/{pid}")["plans"][0]["id"]
            == plan["id"]
        )
        print("PASS: records survive PostgreSQL restart")
        dump = docker(
            "exec",
            "-T",
            "db",
            "pg_dump",
            "-U",
            "ayurtech",
            "-d",
            "ayurtech_e2e_test",
            "-Fc",
        )
        docker(
            "exec",
            "-T",
            "db",
            "createdb",
            "-U",
            "ayurtech",
            "ayurtech_restore_" + tag + "_test",
        )
        docker(
            "exec",
            "-T",
            "db",
            "pg_restore",
            "-U",
            "ayurtech",
            "-d",
            "ayurtech_restore_" + tag + "_test",
            "--no-owner",
            "--exit-on-error",
            data=dump,
        )
        safe_pid = str(UUID(pid))
        safe_plan = str(UUID(plan["id"]))
        query = f"SELECT count(*) FROM patients p JOIN plans dp ON dp.patient_id=p.id JOIN checkins c ON c.patient_id=p.id WHERE p.id='{safe_pid}' AND dp.id='{safe_plan}' AND dp.status='published' AND c.adherence=90"
        count = (
            docker(
                "exec",
                "-T",
                "db",
                "psql",
                "-U",
                "ayurtech",
                "-d",
                "ayurtech_restore_" + tag + "_test",
                "-Atc",
                query,
            )
            .decode()
            .strip()
        )
        assert count == "1", count
        print(
            "PASS: backup restores patient, published plan, and check-in to a separate database"
        )
    old_cookie = patient.cookies.get("ayurtech_session")
    request(patient, "POST", "/api/auth/logout", status=204)
    request(patient, "GET", f"/api/patients/{pid}", status=401)
    patient.cookies.set("ayurtech_session", old_cookie)
    request(patient, "GET", f"/api/patients/{pid}", status=401)
    print("PASS: logout revokes patient access, including replay of the old cookie")
print("All requested HTTP checks passed.")
