import os, secrets, time, logging
from collections import defaultdict, deque
from datetime import timedelta, timezone, date, datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession
from .db import get_db
from .models import (
    Clinic,
    User,
    Patient,
    Food,
    Assessment,
    Plan,
    CheckIn,
    Audit,
    Session,
    now,
)
from .schemas import (
    Credentials,
    Register,
    Claim,
    PatientIn,
    AssessmentIn,
    PlanIn,
    CheckInIn,
)
from .security import (
    current_user,
    dietitian,
    hash_password,
    verify_password,
    create_session,
    origin_check,
    ALLOWED_ORIGINS,
    COOKIE,
    digest,
    as_utc,
)
from .services import accessible_patient, calculate_plan, audit

app = FastAPI(
    title="AyurTech API",
    version="1.0.0",
    description="Multi-tenant dietitian practice platform. Educational Ayurvedic data, not a clinical decision engine.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ayurtech")
login_attempts = defaultdict(deque)
PRACTICE_TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Kolkata"))
DUMMY_PASSWORD_HASH = hash_password("invalid-account-placeholder")


@app.middleware("http")
async def headers(request, call_next):
    request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; script-src 'self'; frame-ancestors 'none'"
    )
    if request.url.path in ("/docs", "/redoc"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'; frame-ancestors 'none'"
        )
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    logger.info(
        "%s %s %s %s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


def rate_limit(request, email):
    # Single-process limiter; replace with Redis/shared gateway for multi-worker deployment.
    key = ((request.client.host if request.client else "unknown"), email)
    queue = login_attempts[key]
    clock = time.monotonic()
    while queue and clock - queue[0] > 900:
        queue.popleft()
    if len(queue) >= 10:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    queue.append(clock)
    if len(login_attempts) > 10000:
        for old in list(login_attempts):
            if not login_attempts[old] or clock - login_attempts[old][-1] > 900:
                del login_attempts[old]


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def user_json(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


def patient_json(p):
    return {
        k: getattr(p, k)
        for k in (
            "id",
            "name",
            "age",
            "gender",
            "email",
            "allergies",
            "notes",
            "status",
            "created_at",
        )
    } | {"portal_active": p.user_id is not None, "created_at": utc(p.created_at)}


def plan_json(p):
    return {
        k: getattr(p, k)
        for k in (
            "id",
            "patient_id",
            "version",
            "title",
            "notes",
            "status",
            "items",
            "totals",
            "created_at",
        )
    } | {"created_at": utc(p.created_at)}


@app.get("/api/health")
def health(db: DBSession = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/auth/register", status_code=201)
def register(
    data: Register,
    request: Request,
    response: Response,
    db: DBSession = Depends(get_db),
):
    origin_check(request)
    rate_limit(request, data.email)
    clinic = Clinic(name=data.clinic_name)
    db.add(clinic)
    db.flush()
    user = User(
        clinic_id=clinic.id,
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
        role="dietitian",
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    audit(db, user, "clinic.created", clinic.id)
    return create_session(db, user, response)


@app.post("/api/auth/login")
def login(
    data: Credentials,
    request: Request,
    response: Response,
    db: DBSession = Depends(get_db),
):
    origin_check(request)
    rate_limit(request, data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    # Same KDF cost for missing and existing accounts.
    encoded = user.password_hash if user else DUMMY_PASSWORD_HASH
    valid = verify_password(data.password, encoded)
    if not user or not valid:
        raise HTTPException(401, "Incorrect email or password")
    # Delete expired sessions without storing raw bearer credentials.
    db.execute(Session.__table__.delete().where(Session.expires_at < now()))
    return create_session(db, user, response)


@app.get("/api/auth/me")
def me(request: Request, user: User = Depends(current_user)):
    return {"user": user_json(user), "csrf": request.state.session.csrf}


@app.post("/api/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    db: DBSession = Depends(get_db),
):
    db.delete(request.state.session)
    db.commit()
    response.delete_cookie(COOKIE, path="/")


@app.post("/api/auth/claim", status_code=201)
def claim(
    data: Claim, request: Request, response: Response, db: DBSession = Depends(get_db)
):
    origin_check(request)
    rate_limit(request, data.email)
    p = db.scalar(
        select(Patient)
        .where(Patient.invite_hash == digest(data.token))
        .with_for_update()
    )
    if (
        not p
        or p.user_id
        or not p.invite_expires
        or as_utc(p.invite_expires) <= now()
        or p.email != data.email
    ):
        raise HTTPException(400, "Invalid or expired invitation")
    user = User(
        clinic_id=p.clinic_id,
        email=data.email,
        name=p.name,
        password_hash=hash_password(data.password),
        role="patient",
    )
    db.add(user)
    try:
        db.flush()
        p.user_id = user.id
        p.invite_hash = None
        p.invite_expires = None
        audit(db, user, "portal.activated", p.id)
        return create_session(db, user, response)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")


@app.get("/api/patients")
def patients(
    q: str = Query("", max_length=100),
    status: str = Query("active", pattern="^(active|archived|all)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    user: User = Depends(current_user),
    db: DBSession = Depends(get_db),
):
    query = select(Patient).where(Patient.clinic_id == user.clinic_id)
    if user.role == "patient":
        query = query.where(Patient.user_id == user.id)
    if status != "all":
        query = query.where(Patient.status == status)
    if q:
        query = query.where(
            Patient.name.ilike(
                "%" + q.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {
        "items": [
            patient_json(p)
            for p in db.scalars(
                query.order_by(Patient.created_at.desc(), Patient.id)
                .offset(offset)
                .limit(limit)
            )
        ],
        "total": total,
    }


@app.post("/api/patients", status_code=201)
def add_patient(
    data: PatientIn, user: User = Depends(dietitian), db: DBSession = Depends(get_db)
):
    p = Patient(clinic_id=user.clinic_id, **data.model_dump())
    db.add(p)
    db.flush()
    audit(db, user, "patient.created", p.id)
    db.commit()
    return patient_json(p)


@app.get("/api/patients/{patient_id}")
def detail(
    patient_id: str, user: User = Depends(current_user), db: DBSession = Depends(get_db)
):
    p = accessible_patient(db, user, patient_id)
    assessments = list(
        db.scalars(
            select(Assessment)
            .where(Assessment.patient_id == p.id)
            .order_by(Assessment.created_at.desc())
        )
    )
    plans = list(
        db.scalars(
            select(Plan).where(Plan.patient_id == p.id).order_by(Plan.version.desc())
        )
    )
    if user.role == "patient":
        plans = [x for x in plans if x.status == "published"]
    checkins = list(
        db.scalars(
            select(CheckIn)
            .where(CheckIn.patient_id == p.id)
            .order_by(CheckIn.day.desc())
            .limit(30)
        )
    )
    return {
        **patient_json(p),
        "assessments": [
            {
                "id": a.id,
                "kind": a.kind,
                "scores": a.scores,
                "result": a.result,
                "created_at": utc(a.created_at),
            }
            for a in assessments
        ],
        "plans": [plan_json(x) for x in plans],
        "checkins": [
            {"day": c.day, "adherence": c.adherence, "energy": c.energy, "note": c.note}
            for c in checkins
        ],
    }


@app.put("/api/patients/{patient_id}")
def edit_patient(
    patient_id: str,
    data: PatientIn,
    user: User = Depends(dietitian),
    db: DBSession = Depends(get_db),
):
    p = accessible_patient(db, user, patient_id)
    if p.user_id and data.email != p.email:
        raise HTTPException(409, "Active portal email cannot be changed here")
    if data.email != p.email:
        p.invite_hash = None
        p.invite_expires = None
    for key, value in data.model_dump().items():
        setattr(p, key, value)
    audit(db, user, "patient.updated", p.id)
    db.commit()
    return patient_json(p)


@app.post("/api/patients/{patient_id}/invite")
def invite(
    patient_id: str, user: User = Depends(dietitian), db: DBSession = Depends(get_db)
):
    p = accessible_patient(db, user, patient_id)
    if p.user_id:
        raise HTTPException(409, "Portal already activated")
    token = secrets.token_urlsafe(32)
    p.invite_hash = digest(token)
    p.invite_expires = now() + timedelta(days=2)
    audit(db, user, "invitation.created", p.id)
    db.commit()
    return {"token": token, "expires_at": p.invite_expires}


@app.get("/api/foods")
def foods(
    q: str = Query("", max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user: User = Depends(current_user),
    db: DBSession = Depends(get_db),
):
    query = select(Food)
    if q:
        query = query.where(
            Food.name.ilike(
                "%" + q.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"
            )
        )
    return {
        "items": [
            {
                "id": f.id,
                "name": f.name,
                "unit": f.unit,
                "nutrition": f.nutrition,
                "properties": f.properties,
                "rasas": f.rasas,
                "dosha_impact": f.dosha_impact,
                "allergens": f.allergens,
                "source": f.source,
            }
            for f in db.scalars(query.order_by(Food.name).offset(offset).limit(limit))
        ],
        "total": db.scalar(select(func.count()).select_from(query.subquery())),
    }


@app.post("/api/patients/{patient_id}/assessments", status_code=201)
def assess(
    patient_id: str,
    data: AssessmentIn,
    user: User = Depends(current_user),
    db: DBSession = Depends(get_db),
):
    p = accessible_patient(db, user, patient_id)
    scores = {d: data.answers.count(d) for d in ("Vata", "Pitta", "Kapha")}
    high = max(scores.values())
    result = "-".join(d for d in scores if scores[d] == high)
    a = Assessment(
        patient_id=p.id,
        kind=data.kind,
        answers=data.answers,
        scores=scores,
        result=result,
    )
    db.add(a)
    db.flush()
    audit(db, user, "assessment.recorded", a.id)
    db.commit()
    return {
        "id": a.id,
        "scores": scores,
        "result": result,
        "notice": "Educational questionnaire, not a validated clinical assessment",
    }


@app.post("/api/patients/{patient_id}/plans", status_code=201)
def save_plan(
    patient_id: str,
    data: PlanIn,
    user: User = Depends(dietitian),
    db: DBSession = Depends(get_db),
):
    p = accessible_patient(db, user, patient_id)
    # PostgreSQL serializes writers on patient; SQLite's unique constraint catches competing versions.
    db.refresh(p, with_for_update=True)
    version = (
        db.scalar(select(func.max(Plan.version)).where(Plan.patient_id == p.id)) or 0
    )
    if version != data.expected_version:
        raise HTTPException(409, "Plan changed. Reload before saving.")
    items, totals = calculate_plan(db, p, data.items)
    plan = Plan(
        patient_id=p.id,
        author_id=user.id,
        version=version + 1,
        title=data.title,
        notes=data.notes,
        items=items,
        totals=totals,
    )
    db.add(plan)
    try:
        db.flush()
        audit(db, user, "plan.saved", plan.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Plan changed. Reload before saving.")
    return plan_json(plan)


@app.post("/api/patients/{patient_id}/plans/{plan_id}/publish")
def publish(
    patient_id: str,
    plan_id: str,
    user: User = Depends(dietitian),
    db: DBSession = Depends(get_db),
):
    p = accessible_patient(db, user, patient_id)
    plan = db.get(Plan, plan_id)
    if not plan or plan.patient_id != p.id:
        raise HTTPException(404, "Plan not found")
    db.refresh(p, with_for_update=True)
    db.refresh(plan)
    latest = db.scalar(select(func.max(Plan.version)).where(Plan.patient_id == p.id))
    if plan.version != latest:
        raise HTTPException(409, "Only the latest version can be published")
    # Re-check newly recorded allergies against the immutable food snapshots.
    ids = [i["food_id"] for i in plan.items]
    for food in db.scalars(select(Food).where(Food.id.in_(ids))):
        if set(food.allergens) & set(p.allergies):
            raise HTTPException(422, f"{food.name} conflicts with recorded allergies")
    if plan.status == "published":
        return plan_json(plan)
    db.execute(
        update(Plan)
        .where(Plan.patient_id == p.id, Plan.status == "published")
        .values(status="superseded")
    )
    plan.status = "published"
    audit(db, user, "plan.published", plan.id)
    db.commit()
    return plan_json(plan)


@app.post("/api/patients/{patient_id}/checkins", status_code=201)
def checkin(
    patient_id: str,
    data: CheckInIn,
    user: User = Depends(current_user),
    db: DBSession = Depends(get_db),
):
    p = accessible_patient(db, user, patient_id)
    if data.day > datetime.now(PRACTICE_TZ).date():
        raise HTTPException(422, "Check-in date cannot be in the future")
    existing = db.scalar(
        select(CheckIn).where(
            CheckIn.patient_id == p.id, CheckIn.day == data.day.isoformat()
        )
    )
    c = existing or CheckIn(patient_id=p.id, day=data.day.isoformat())
    c.adherence = data.adherence
    c.energy = data.energy
    c.note = data.note
    db.add(c)
    try:
        db.flush()
        audit(db, user, "checkin.recorded", c.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Check-in changed. Reload and retry.")
    return {
        "id": c.id,
        "day": c.day,
        "adherence": c.adherence,
        "energy": c.energy,
        "note": c.note,
    }


@app.get("/api/dashboard")
def dashboard(user: User = Depends(dietitian), db: DBSession = Depends(get_db)):
    patient_ids = select(Patient.id).where(
        Patient.clinic_id == user.clinic_id, Patient.status == "active"
    )
    active = db.scalar(
        select(func.count()).select_from(Patient).where(Patient.id.in_(patient_ids))
    )
    published = db.scalar(
        select(func.count(func.distinct(Plan.patient_id))).where(
            Plan.patient_id.in_(patient_ids), Plan.status == "published"
        )
    )
    assessed = db.scalar(
        select(func.count(func.distinct(Assessment.patient_id))).where(
            Assessment.patient_id.in_(patient_ids)
        )
    )
    events = list(
        db.scalars(
            select(Audit)
            .where(Audit.clinic_id == user.clinic_id)
            .order_by(Audit.created_at.desc())
            .limit(8)
        )
    )
    return {
        "active_patients": active,
        "published_plans": published,
        "assessed_patients": assessed,
        "needs_plan": active - published,
        "events": [
            {
                "id": e.id,
                "action": e.action,
                "created_at": utc(e.created_at),
                "resource_id": e.resource_id,
            }
            for e in events
        ],
    }


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    def frontend():
        return FileResponse(DIST / "index.html")
