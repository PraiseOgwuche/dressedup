def _create_item(client, auth_header, **fields):
    return client.post("/api/v1/closet/items", json=fields, headers=auth_header).json()


def test_create_and_browse_listing(client, auth_header):
    item = _create_item(
        client,
        auth_header,
        name="Vintage denim jacket",
        category="outerwear",
        color="blue",
        brand="Levi's",
    )

    create = client.post(
        "/api/v1/marketplace/listings",
        json={
            "clothing_item_id": item["id"],
            "listing_type": "sell",
            "price_cents": 4500,
            "condition": "good",
            "description": "Barely worn, great layer.",
        },
        headers=auth_header,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["listing_type"] == "sell"
    assert body["price_cents"] == 4500
    assert body["is_mine"] is True
    assert body["item"]["name"] == "Vintage denim jacket"

    browse = client.get("/api/v1/marketplace/listings", headers=auth_header)
    assert browse.status_code == 200
    assert len(browse.json()) >= 1


def test_gift_listing_no_price(client, auth_header):
    item = _create_item(client, auth_header, name="Striped tee", category="top")
    create = client.post(
        "/api/v1/marketplace/listings",
        json={"clothing_item_id": item["id"], "listing_type": "gift", "condition": "like_new"},
        headers=auth_header,
    )
    assert create.status_code == 201
    assert create.json()["price_cents"] is None


def test_duplicate_active_listing_rejected(client, auth_header):
    item = _create_item(client, auth_header, name="Duplicate test", category="top")
    payload = {"clothing_item_id": item["id"], "listing_type": "gift", "condition": "good"}
    assert client.post("/api/v1/marketplace/listings", json=payload, headers=auth_header).status_code == 201
    dup = client.post("/api/v1/marketplace/listings", json=payload, headers=auth_header)
    assert dup.status_code == 400


def test_express_interest_mailto(client, auth_header):
    item = _create_item(client, auth_header, name="Interest tee", category="top")
    listing = client.post(
        "/api/v1/marketplace/listings",
        json={"clothing_item_id": item["id"], "listing_type": "gift", "condition": "good"},
        headers=auth_header,
    ).json()

    # Second user
    import uuid

    email = f"buyer-{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Buyer User", "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    buyer_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    interest = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/interest",
        headers=buyer_header,
    )
    assert interest.status_code == 200
    mailto = interest.json()["mailto"]
    assert mailto.startswith("mailto:")
    from urllib.parse import unquote

    assert "Interest tee" in unquote(mailto)


def test_mark_as_gone(client, auth_header):
    item = _create_item(client, auth_header, name="Sold pants", category="bottom")
    listing = client.post(
        "/api/v1/marketplace/listings",
        json={
            "clothing_item_id": item["id"],
            "listing_type": "sell",
            "price_cents": 2000,
            "condition": "fair",
        },
        headers=auth_header,
    ).json()

    updated = client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"status": "gone"},
        headers=auth_header,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "gone"

    browse = client.get("/api/v1/marketplace/listings", headers=auth_header)
    assert all(row["id"] != listing["id"] for row in browse.json())


def test_interest_saved_and_listed(client, auth_header):
    item = _create_item(client, auth_header, name="Interest jacket", category="outerwear")
    listing = client.post(
        "/api/v1/marketplace/listings",
        json={
            "clothing_item_id": item["id"],
            "listing_type": "sell",
            "price_cents": 3000,
            "condition": "good",
        },
        headers=auth_header,
    ).json()

    import uuid

    email = f"buyer-{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Buyer User", "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    buyer_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    interest = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/interest",
        headers=buyer_header,
    )
    assert interest.status_code == 200
    assert interest.json()["saved"] is True

    mine = client.get("/api/v1/marketplace/listings/mine", headers=auth_header)
    assert mine.json()[0]["interest_count"] == 1

    received = client.get("/api/v1/marketplace/interests/received", headers=auth_header)
    assert len(received.json()) == 1
    assert received.json()[0]["buyer_name"] == "Buyer User"

    my_interests = client.get("/api/v1/marketplace/interests/mine", headers=buyer_header)
    assert len(my_interests.json()) == 1
    assert my_interests.json()[0]["listing"]["title"] == "Interest jacket"

    listing_interests = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}/interests",
        headers=auth_header,
    )
    assert len(listing_interests.json()) == 1
    assert listing_interests.json()[0]["mailto"].startswith("mailto:")
