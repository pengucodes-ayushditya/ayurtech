import pytest
from sqlalchemy.engine import make_url
from app.config import normalize_database_url, allowed_origins


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_database_urls_preserve_credentials_and_tls(scheme):
    url = make_url(
        normalize_database_url(
            f"{scheme}://demo:p%40ss%25word@db.example:5432/app?sslmode=require&channel_binding=require"
        )
    )
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss%word"
    assert url.query == {"sslmode": "require", "channel_binding": "require"}
    assert url.database == "app"


def test_render_origin_supports_first_deploy_without_guessing_hostname():
    assert allowed_origins(
        {
            "APP_ENV": "production",
            "RENDER_EXTERNAL_URL": "https://ayurtech-example.onrender.com/",
        }
    ) == {"https://ayurtech-example.onrender.com"}


@pytest.mark.parametrize(
    "env",
    [
        {"APP_ENV": "production"},
        {"APP_ENV": "production", "ALLOWED_ORIGINS": "http://example.com"},
        {"ALLOWED_ORIGINS": "https://example.com/login"},
        {"ALLOWED_ORIGINS": "*"},
    ],
)
def test_invalid_or_missing_production_origin_is_rejected(env):
    with pytest.raises(RuntimeError):
        allowed_origins(env)
