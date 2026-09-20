import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.security_boundary import SecurityBoundary
from test_req003 import harness  # noqa: F401


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


def test_login_logout_cookie_flags(harness, monkeypatch):
    from app.api import auth
    from app.config import settings

    client, _, _ = harness
    monkeypatch.setattr(auth.pwd, "verify", lambda *args: True)
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "cookie_samesite", "strict")
    response = client.post("/api/v1/auth/login", json={"email": "market@example.com", "password": "synthetic-only"})
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    assert "access_token" not in response.json()
    logout = client.post("/api/v1/auth/logout").headers["set-cookie"]
    assert "Max-Age=0" in logout and "Secure" in logout and "SameSite=strict" in logout


def test_only_explicit_trusted_proxy_can_supply_https_scheme():
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    app = FastAPI()
    app.add_api_route("/probe", lambda: {"ok": True})
    secured = SecurityBoundary(app, production())
    proxied = ProxyHeadersMiddleware(secured, trusted_hosts=["10.20.0.2"])
    for ip, status in [("10.20.0.2", 200), ("10.20.0.3", 400)]:

        async def transport(scope, receive, send):
            scope = {**scope, "client": (ip, 1234)}
            await proxied(scope, receive, send)

        with TestClient(transport, base_url="http://backend") as client:
            assert client.get("/probe", headers={"X-Forwarded-Proto": "https"}).status_code == status
