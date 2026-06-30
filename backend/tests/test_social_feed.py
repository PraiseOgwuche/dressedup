def _create_item(client, auth_header, name: str, category: str = "Top"):
    return client.post(
        "/api/v1/closet/items",
        json={"name": name, "category": category},
        headers=auth_header,
    ).json()


def test_create_post_requires_outfit_items(client, auth_header):
    response = client.post(
        "/api/v1/social/posts",
        data={"caption": "No outfit attached"},
        headers=auth_header,
    )
    assert response.status_code == 400


def test_create_and_list_outfit_post(client, auth_header):
    top = _create_item(client, auth_header, "White tee")
    bottom = _create_item(client, auth_header, "Blue jeans", "Bottom")
    shoes = _create_item(client, auth_header, "Sneakers", "Shoes")

    create = client.post(
        "/api/v1/social/posts",
        data={
            "top_id": top["id"],
            "bottom_id": bottom["id"],
            "shoes_id": shoes["id"],
            "caption": "Office fit",
        },
        headers=auth_header,
    )
    assert create.status_code == 201
    payload = create.json()
    assert payload["caption"] == "Office fit"
    assert payload["top"]["id"] == top["id"]
    assert payload["bottom"]["id"] == bottom["id"]
    assert payload["shoes"]["id"] == shoes["id"]
    assert payload["user_name"] == "Test User"
    assert payload["reactions_count"] == 0
    assert payload["liked_by_me"] is False

    feed = client.get("/api/v1/social/posts", headers=auth_header)
    assert feed.status_code == 200
    posts = feed.json()
    assert len(posts) >= 1
    assert posts[0]["top"]["name"] == "White tee"


def test_toggle_like(client, auth_header):
    top = _create_item(client, auth_header, "Like tee")
    post = client.post(
        "/api/v1/social/posts",
        data={"top_id": top["id"]},
        headers=auth_header,
    ).json()

    like = client.post(f"/api/v1/social/posts/{post['id']}/like", headers=auth_header)
    assert like.status_code == 200
    assert like.json() == {"liked": True, "reactions_count": 1}

    feed = client.get("/api/v1/social/posts", headers=auth_header)
    assert feed.json()[0]["liked_by_me"] is True
    assert feed.json()[0]["reactions_count"] == 1

    unlike = client.post(f"/api/v1/social/posts/{post['id']}/like", headers=auth_header)
    assert unlike.status_code == 200
    assert unlike.json() == {"liked": False, "reactions_count": 0}


def test_cannot_like_missing_post(client, auth_header):
    response = client.post("/api/v1/social/posts/99999/like", headers=auth_header)
    assert response.status_code == 404
