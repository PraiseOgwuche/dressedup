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
    assert me_response.json().get("avatar_url") is None

    avatar_url = "https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb"
    patch_response = client.patch(
        "/api/v1/auth/me",
        json={"avatar_url": avatar_url},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["avatar_url"] == avatar_url

    clear_response = client.patch(
        "/api/v1/auth/me",
        json={"avatar_url": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["avatar_url"] is None


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


def test_clear_needs_review(client, auth_header):
    create = client.post(
        "/api/v1/closet/items",
        json={
            "name": "Review Jean",
            "category": "bottom",
            "needs_review": True,
            "is_clean": True,
        },
        headers=auth_header,
    )
    assert create.status_code == 201
    item_id = create.json()["id"]
    assert create.json()["needs_review"] is True

    update = client.put(
        f"/api/v1/closet/items/{item_id}",
        json={"needs_review": False},
        headers=auth_header,
    )
    assert update.status_code == 200
    assert update.json()["needs_review"] is False


def test_replace_item_photo(client, auth_header):
    create = client.post(
        "/api/v1/closet/items",
        json={"name": "Photo Tee", "category": "top", "is_clean": True},
        headers=auth_header,
    )
    item_id = create.json()["id"]

    # Minimal valid JPEG header bytes — storage accepts raw bytes.
    jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )
    response = client.post(
        f"/api/v1/closet/items/{item_id}/photo",
        headers=auth_header,
        files={"garment": ("tee.jpg", jpeg, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["image_url"]
    assert body["thumbnail_url"]


def test_closet_item_context_and_gaps(client, auth_header):
    top = client.post(
        "/api/v1/closet/items",
        json={"name": "Blue Tee", "category": "top", "is_clean": True, "tags": ["work"]},
        headers=auth_header,
    )
    assert top.status_code == 201
    top_id = top.json()["id"]
    assert top.json()["tags"] == ["work"]

    bottom = client.post(
        "/api/v1/closet/items",
        json={"name": "Jeans", "category": "bottom", "is_clean": True, "tags": ["weekend"]},
        headers=auth_header,
    )
    assert bottom.status_code == 201

    context = client.get(f"/api/v1/closet/items/{top_id}/context", headers=auth_header)
    assert context.status_code == 200
    body = context.json()
    assert body["item"]["id"] == top_id
    assert body["slot"] == "top"
    assert "usage" in body
    assert body["pair_preview"] is not None
    assert body["pair_preview"]["bottom"]["id"] == bottom.json()["id"]

    gaps = client.get("/api/v1/closet/gaps", headers=auth_header)
    assert gaps.status_code == 200
    gap_body = gaps.json()
    assert gap_body["total_items"] >= 2
    assert gap_body["by_slot"]["top"] >= 1
    assert gap_body["by_slot"]["bottom"] >= 1
    assert gap_body["summary"]

