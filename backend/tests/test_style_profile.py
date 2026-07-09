def _add(client, auth_header, **fields):
    response = client.post(
        "/api/v1/closet/items", json={"is_clean": True, **fields}, headers=auth_header
    )
    assert response.status_code == 201
    return response.json()


def test_style_profile_endpoint_empty(client, auth_header):
    response = client.get("/api/v1/style/profile", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["headline"] == "Your style profile"
    assert "summary" in body
    assert "activity" in body
    assert body["activity"]["wore"] == 0


def test_style_profile_reflects_activity(client, auth_header):
    top = _add(client, auth_header, name="Navy tee", category="top", color="navy", formality="casual")
    bottom = _add(client, auth_header, name="Jeans", category="bottom", color="black", formality="casual")

    for _ in range(2):
        client.post(
            "/api/v1/outfits/feedback",
            json={
                "top_id": top["id"],
                "bottom_id": bottom["id"],
                "signal": "wore",
                "occasion": "everyday",
            },
            headers=auth_header,
        )

    response = client.get("/api/v1/style/profile", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["activity"]["wore"] >= 2
    assert body["signal_count"] >= 2
    assert len(body["top_colors"]) >= 1
    assert len(body["insights"]) >= 1
