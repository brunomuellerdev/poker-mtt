from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.defaults import DEFAULT_EVALUATION_RANGES
from app.db.models import EvaluationRange, User, UserSettings

REG = {"name": "Bruno", "email": "Bruno@Example.com", "password": "supersecret1"}


def _register(client: TestClient, **over) -> dict:
    payload = {**REG, **over}
    return client.post("/api/v1/auth/register", json=payload)


def test_register_creates_user_settings_and_seeds_ranges(
    client: TestClient, db: Session
) -> None:
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "bruno@example.com"  # normalized lowercase
    assert "id" in body and "password" not in body

    user = db.scalar(select(User).where(User.email == "bruno@example.com"))
    assert user is not None
    # password is hashed, never stored plain
    assert user.password_hash != REG["password"]
    assert user.password_hash.startswith("$argon2id$")

    settings_row = db.scalar(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    assert settings_row is not None
    assert settings_row.base_currency == "USD"

    expected = sum(len(v) for v in DEFAULT_EVALUATION_RANGES.values())
    count = db.scalar(
        select(func.count())
        .select_from(EvaluationRange)
        .where(EvaluationRange.user_id == user.id)
    )
    assert count == expected  # all default bands seeded


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    assert _register(client).status_code == 201
    dup = _register(client, name="Other")  # same email, different case already lowercased
    assert dup.status_code == 409


def test_login_returns_access_token_and_sets_refresh_cookie(
    client: TestClient,
) -> None:
    _register(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]
    assert "refresh_token" in r.cookies


def test_login_wrong_password_401(client: TestClient) -> None:
    _register(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": "wrongpassword"},
    )
    assert r.status_code == 401


def test_login_unknown_email_401(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever12"},
    )
    assert r.status_code == 401


def test_me_requires_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401  # no bearer -> 401


def test_me_returns_current_user(client: TestClient) -> None:
    _register(client)
    token = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    ).json()["access_token"]
    r = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "bruno@example.com"


def test_me_rejects_garbage_token(client: TestClient) -> None:
    r = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert r.status_code == 401


def test_refresh_issues_new_access_token(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    )
    refresh_cookie = login.cookies["refresh_token"]
    r = client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_refresh_without_cookie_401(client: TestClient) -> None:
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_access_token_not_accepted_as_refresh(client: TestClient) -> None:
    _register(client)
    access = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    ).json()["access_token"]
    # feeding an access token where a refresh token is expected must fail (type guard)
    r = client.post(
        "/api/v1/auth/refresh", cookies={"refresh_token": access}
    )
    assert r.status_code == 401


def test_refresh_cookie_path_matches_api_prefix(client: TestClient) -> None:
    """Regression: the refresh cookie must be scoped to the actual endpoint path
    (/api/v1/auth), otherwise the browser never sends it back to /refresh."""
    _register(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    )
    set_cookie = r.headers.get("set-cookie", "")
    assert "Path=/api/v1/auth" in set_cookie
