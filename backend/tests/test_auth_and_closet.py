def test_auth_register_login_and_profile(client):
    payload = {
        "email": "alice@example.com",
        "full_name": "Alice Example",
        "password": "password123",
    }
    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == payload["email"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == payload["email"]


def test_closet_crud_flow(client, auth_header):
    create_response = client.post(
        "/api/v1/closet/items",
        json={
            "name": "White Tee",
            "category": "top",
            "color": "white",
            "occasion": ["everyday", "date"],
            "weather_tag": ["warm", "mild"],
            "is_clean": True,
        },
        headers=auth_header,
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    list_response = client.get("/api/v1/closet/items", headers=auth_header)
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    update_response = client.put(
        f"/api/v1/closet/items/{item_id}",
        json={"is_clean": False},
        headers=auth_header,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_clean"] is False

    delete_response = client.delete(f"/api/v1/closet/items/{item_id}", headers=auth_header)
    assert delete_response.status_code == 204

