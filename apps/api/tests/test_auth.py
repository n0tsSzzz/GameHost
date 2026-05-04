from httpx import AsyncClient


async def test_register_login_refresh_me_logout(api_client: AsyncClient) -> None:
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "Player@example.com", "password": "correct-horse-battery-staple"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "player@example.com"

    duplicate_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.headers["content-type"].startswith("application/problem+json")

    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    assert login_response.status_code == 200
    access = login_response.json()["access"]
    assert access
    assert "refresh_token" in api_client.cookies

    me_response = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "player@example.com"

    refresh_response = await api_client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access"]

    logout_response = await api_client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204


async def test_login_rejects_bad_password(api_client: AsyncClient) -> None:
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )

    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "player@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
