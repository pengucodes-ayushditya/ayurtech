import hashlib, secrets, os
from datetime import timedelta, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from .db import get_db
from .config import allowed_origins
from .models import User, Session, now

COOKIE = "ayurtech_session"
SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
if os.getenv("APP_ENV") == "production" and not SECURE:
    raise RuntimeError("COOKIE_SECURE must be true in production")
ALLOWED_ORIGINS = allowed_origins(os.environ)


def as_utc(v):
    return (
        v.replace(tzinfo=timezone.utc)
        if v.tzinfo is None
        else v.astimezone(timezone.utc)
    )


def digest(v):
    return hashlib.sha256(v.encode()).hexdigest()


def hash_password(password):
    salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${key}"


def verify_password(password, encoded):
    _, salt, key = encoded.split("$")
    actual = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return secrets.compare_digest(actual, key)


def origin_check(request: Request):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(403, "Origin not allowed")


def create_session(db, user, response):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_hex(24)
    db.add(
        Session(
            id=digest(token),
            user_id=user.id,
            csrf=csrf,
            expires_at=now() + timedelta(hours=12),
        )
    )
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=SECURE,
        samesite="lax",
        max_age=43200,
        path="/",
    )
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
        "csrf": csrf,
    }


def current_user(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    session = db.get(Session, digest(token)) if token else None
    if not session or as_utc(session.expires_at) <= now():
        raise HTTPException(401, "Please sign in")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin_check(request)
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), session.csrf
        ):
            raise HTTPException(403, "Invalid CSRF token")
    request.state.session = session
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Please sign in")
    return user


def dietitian(user: User = Depends(current_user)):
    if user.role != "dietitian":
        raise HTTPException(403, "Dietitian access required")
    return user
