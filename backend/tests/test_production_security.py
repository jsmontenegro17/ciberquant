import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.security_boundary import SecurityBoundary


def production(**kwargs):
    config = dict(
        environment="production",
        cookie_secure=True,
        https_required=True,
        jwt_secret="synthetic-test-only-" * 3,
        seed_admin_email="operator@example.invalid",
        seed_admin_password="synthetic-test-only-admin",
        allowed_origins=["https://research.example.invalid"],
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
    )
    return Settings(_env_file=None, **(config | kwargs))


@pytest.mark.parametrize(
    "change",
    [
        dict(cookie_secure=False),
        dict(https_required=False),
        dict(jwt_secret="short"),
        dict(allowed_origins=["*"]),
        dict(allowed_origins=["http://research.example.invalid"]),
        dict(seed_admin_password="change-me-now"),
        dict(seed_admin_email="admin@example.com"),
        dict(database_url="sqlite://"),
        dict(allowed_origins=["https://research.example.invalid/path"]),
    ],
)
def test_reject_insecure_production_without_secret_in_error(change):
    with pytest.raises(ValidationError) as caught:
        production(**change)
    assert "synthetic-test-only" not in str(caught.value)


def test_development_and_production_https_cors_proxy_boundary():
    assert not Settings(_env_file=None).cookie_secure
    config = production()
    app = FastAPI()
    app.add_api_route("/probe", lambda: {"ok": True}, methods=["GET", "POST"])
    app.add_middleware(CORSMiddleware, allow_origins=config.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST"])
    app.add_middleware(SecurityBoundary, config=config)
    with TestClient(app, base_url="http://testserver") as client:
        assert client.get("/probe", headers={"X-Forwarded-Proto": "https"}).status_code == 400
    with TestClient(app, base_url="https://testserver") as client:
        assert client.get("/probe").status_code == 200
        assert client.post("/probe").status_code == 403
        assert client.post("/probe", headers={"Origin": "https://evil.example.invalid"}).status_code == 403
        ok = client.post("/probe", headers={"Origin": config.allowed_origins[0]})
        assert ok.status_code == 200
        assert ok.headers["access-control-allow-origin"] == config.allowed_origins[0]
        bad = client.options("/probe", headers={"Origin": "https://evil.example.invalid", "Access-Control-Request-Method": "POST"})
        assert bad.status_code == 400
        assert "access-control-allow-origin" not in bad.headers
