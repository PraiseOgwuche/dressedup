def _create(client, auth_header, category, name="Item"):
    response = client.post(
        "/api/v1/closet/items",
        json={"name": name, "category": category, "is_clean": True},
        headers=auth_header,
    )
    assert response.status_code == 201
    return response.json()


def _wear(client, auth_header, item_id):
    response = client.post(f"/api/v1/closet/items/{item_id}/wear", headers=auth_header)
    assert response.status_code == 200
    return response.json()


def test_wear_marks_dirty_at_category_limit(client, auth_header):
    item = _create(client, auth_header, "top", "Tee")  # top limit = 2

    after_one = _wear(client, auth_header, item["id"])
    assert after_one["wears_since_wash"] == 1
    assert after_one["is_clean"] is True
    assert after_one["effective_wear_limit"] == 2

    after_two = _wear(client, auth_header, item["id"])
    assert after_two["wears_since_wash"] == 2
    assert after_two["times_worn"] == 2
    assert after_two["is_clean"] is False  # reached limit


def test_wash_resets_counter(client, auth_header):
    item = _create(client, auth_header, "top", "Tee")
    _wear(client, auth_header, item["id"])
    _wear(client, auth_header, item["id"])

    washed = client.post(f"/api/v1/closet/items/{item['id']}/wash", headers=auth_header).json()
    assert washed["is_clean"] is True
    assert washed["wears_since_wash"] == 0
    assert washed["last_washed_at"] is not None


def test_jewelry_is_never_auto_dirtied(client, auth_header):
    item = _create(client, auth_header, "jewelry", "Ring")
    body = item
    for _ in range(5):
        body = _wear(client, auth_header, item["id"])
    assert body["effective_wear_limit"] is None
    assert body["is_clean"] is True
    assert body["times_worn"] == 5


def test_soil_marks_dirty_out_of_cycle(client, auth_header):
    item = _create(client, auth_header, "bottom", "Jeans")  # limit 4, one wear only
    _wear(client, auth_header, item["id"])
    soiled = client.post(f"/api/v1/closet/items/{item['id']}/soil", headers=auth_header).json()
    assert soiled["is_clean"] is False


def test_laundry_summary_and_wash_all(client, auth_header):
    item = _create(client, auth_header, "top", "Only Tee")
    _wear(client, auth_header, item["id"])
    _wear(client, auth_header, item["id"])  # now dirty; it's the only top

    summary = client.get("/api/v1/closet/laundry/summary", headers=auth_header).json()
    assert summary["dirty_count"] == 1
    assert "top" in summary["depleted_categories"]
    assert summary["laundry_due"] is True

    after = client.post("/api/v1/closet/laundry/wash-all", json={}, headers=auth_header).json()
    assert after["dirty_count"] == 0
    assert after["laundry_due"] is False
