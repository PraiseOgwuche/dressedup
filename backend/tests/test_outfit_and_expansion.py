def _seed_closet(client, auth_header):
    items = [
        {"name": "Blue Shirt", "category": "top", "is_clean": True, "weather_tag": ["warm", "mild"]},
        {"name": "Black Jeans", "category": "bottom", "is_clean": True, "weather_tag": ["warm"]},
        {"name": "White Sneakers", "category": "shoes", "is_clean": True, "weather_tag": ["warm"]},
    ]
    for item in items:
        payload = {
            "name": item["name"],
            "category": item["category"],
            "is_clean": item["is_clean"],
            "weather_tag": item["weather_tag"],
        }
        client.post("/api/v1/closet/items", json=payload, headers=auth_header)


def test_outfit_suggestion(client, auth_header):
    _seed_closet(client, auth_header)
    response = client.get(
        "/api/v1/outfits/suggestion",
        params={"weather_tag": "warm", "occasion": "casual"},
        headers=auth_header,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["top"] is not None
    assert payload["bottom"] is not None
    assert payload["shoes"] is not None


def test_outfit_prefers_formality_coherent_top(client, auth_header):
    # A business-formal bottom + shoes should pull a matching dress shirt over a
    # loungewear graphic hoodie, even though both tops are equally fresh.
    items = [
        {"name": "Black trousers", "category": "bottom", "formality": "business", "color_hex": "#1a1a1a"},
        {"name": "Black loafers", "category": "footwear", "formality": "business", "color_hex": "#101010"},
        {"name": "White dress shirt", "category": "top", "formality": "business", "color_hex": "#ffffff"},
        {"name": "Orange graphic hoodie", "category": "top", "formality": "loungewear", "color_hex": "#ff5a00", "pattern": "graphic"},
    ]
    for item in items:
        client.post("/api/v1/closet/items", json={**item, "is_clean": True}, headers=auth_header)

    response = client.get("/api/v1/outfits/suggestion", headers=auth_header)
    assert response.status_code == 200
    payload = response.json()
    assert payload["top"]["name"] == "White dress shirt"
    assert payload["bottom"]["name"] == "Black trousers"
    assert payload["shoes"]["name"] == "Black loafers"


def _add(client, auth_header, **fields):
    response = client.post(
        "/api/v1/closet/items", json={"is_clean": True, **fields}, headers=auth_header
    )
    assert response.status_code == 201
    return response.json()


def test_daily_plan_work_then_gym(client, auth_header):
    _add(client, auth_header, name="Oxford shirt", category="top", occasion=["work"], formality="business")
    _add(client, auth_header, name="Slacks", category="bottom", occasion=["work"], formality="business")
    _add(client, auth_header, name="Loafers", category="footwear", occasion=["work"])
    _add(client, auth_header, name="Dri-fit tee", category="activewear", subcategory="athletic-top", occasion=["workout"])
    _add(client, auth_header, name="Gym shorts", category="activewear", subcategory="athletic-shorts", occasion=["workout"])
    _add(client, auth_header, name="Trainers", category="footwear", occasion=["workout"])

    response = client.get(
        "/api/v1/outfits/plan",
        params={"activities": "work,gym", "weather_tag": "mild"},
        headers=auth_header,
    )
    assert response.status_code == 200
    activities = response.json()["activities"]

    assert len(activities) == 2
    assert activities[0]["mode"] == "wear" and activities[0]["activity"] == "work"
    assert activities[1]["mode"] == "pack" and activities[1]["activity"] == "gym"
    assert activities[0]["top"]["name"] == "Oxford shirt"

    # Activewear is slotted via subcategory and shows up as a packing list for gym.
    assert activities[1]["top"]["name"] == "Dri-fit tee"
    gym_packing = [i["name"] for i in activities[1]["packing_list"]]
    assert "Dri-fit tee" in gym_packing

    # The same physical item is never assigned to two activities.
    work_ids = {activities[0][s]["id"] for s in ("top", "bottom", "shoes") if activities[0][s]}
    gym_ids = {i["id"] for i in activities[1]["packing_list"]}
    assert work_ids.isdisjoint(gym_ids)


def test_swap_top_keeps_bottom_and_shoes(client, auth_header):
    top_a = _add(
        client,
        auth_header,
        name="White tee",
        category="top",
        formality="casual",
        color="white",
        color_hex="#ffffff",
    )
    top_b = _add(
        client,
        auth_header,
        name="Blue oxford",
        category="top",
        formality="casual",
        color="blue",
        color_hex="#2244aa",
    )
    bottom = _add(
        client,
        auth_header,
        name="Jeans",
        category="bottom",
        formality="casual",
        color="navy",
        color_hex="#1a2a4a",
    )
    shoes = _add(
        client,
        auth_header,
        name="Sneakers",
        category="footwear",
        formality="casual",
        color="white",
    )

    response = client.get(
        "/api/v1/outfits/suggestion",
        params={
            "swap_slot": "top",
            "top_id": top_a["id"],
            "bottom_id": bottom["id"],
            "shoes_id": shoes["id"],
        },
        headers=auth_header,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["top"]["id"] == top_b["id"]
    assert payload["bottom"]["id"] == bottom["id"]
    assert payload["shoes"]["id"] == shoes["id"]
    assert "Swapped" in (payload["rationale"] or "")


def test_social_and_shop_endpoints(client, auth_header):
    post_response = client.post(
        "/api/v1/social/posts",
        json={"caption": "Simple office fit today"},
        headers=auth_header,
    )
    assert post_response.status_code == 201

    feed_response = client.get("/api/v1/social/posts")
    assert feed_response.status_code == 200
    assert isinstance(feed_response.json(), list)

    shop_response = client.get("/api/v1/shop/recommendations", headers=auth_header)
    assert shop_response.status_code == 200
    assert "recommendations" in shop_response.json()

