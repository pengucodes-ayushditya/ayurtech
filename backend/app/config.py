"""Provider-neutral configuration helpers; never log database URLs."""

from collections.abc import Mapping
from urllib.parse import urlsplit

LOCAL_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"


def normalize_database_url(value: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if value.startswith(prefix):
            return "postgresql+psycopg://" + value[len(prefix) :]
    return value


def allowed_origins(env: Mapping[str, str]) -> set[str]:
    production = env.get("APP_ENV") == "production"
    raw = env.get("ALLOWED_ORIGINS") or env.get("RENDER_EXTERNAL_URL")
    if not raw:
        if production:
            raise RuntimeError(
                "Set ALLOWED_ORIGINS or RENDER_EXTERNAL_URL in production"
            )
        raw = LOCAL_ORIGINS
    origins = {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}
    if not origins:
        raise RuntimeError("At least one UI origin is required")
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.netloc
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
        ):
            raise RuntimeError(
                "UI origins must be exact http(s) origins, without paths or credentials"
            )
        if production and parsed.scheme != "https":
            raise RuntimeError("Production UI origins must use HTTPS")
    return origins
