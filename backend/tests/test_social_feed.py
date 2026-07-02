def _create_item(client, auth_header, name: str, category: str = "top"):
    return client.post(
        "/api/v1/closet/items",
        json={"name": name, "category": category},
        headers=auth_header,
    ).json()


def _create_post(client, auth_header, **kwargs):
    return client.post(
        "/api/v1/social/posts",
        data=kwargs,
        headers=auth_header,
    )


def _register_user(client, full_name: str):
    import uuid

    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": full_name, "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    return {"Authorization": f"Bearer {token}"}, me


def test_create_post_requires_outfit_items(client, auth_header):
    response = _create_post(client, auth_header, caption="No outfit attached")
    assert response.status_code == 400


def test_create_and_list_outfit_post(client, auth_header):
    top = _create_item(client, auth_header, "White tee")
    bottom = _create_item(client, auth_header, "Blue jeans", "bottom")
    shoes = _create_item(client, auth_header, "Sneakers", "footwear")

    create = _create_post(
        client,
        auth_header,
        top_id=top["id"],
        bottom_id=bottom["id"],
        shoes_id=shoes["id"],
        caption="Office fit",
        occasion="work",
    )
    assert create.status_code == 201
    payload = create.json()
    assert payload["caption"] == "Office fit"
    assert payload["occasion"] == "work"
    assert payload["top"]["id"] == top["id"]
    assert payload["is_mine"] is True
    assert payload["reactions_count"] == 0
    assert payload["liked_by_me"] is False

    feed = client.get("/api/v1/social/posts", headers=auth_header)
    assert feed.status_code == 200
    posts = feed.json()
    assert len(posts) >= 1
    assert posts[0]["top"]["name"] == "White tee"


def test_toggle_like(client, auth_header):
    top = _create_item(client, auth_header, "Like tee")
    post = _create_post(client, auth_header, top_id=top["id"]).json()

    like = client.post(f"/api/v1/social/posts/{post['id']}/like", headers=auth_header)
    assert like.status_code == 200
    assert like.json() == {"liked": True, "reactions_count": 1}

    feed = client.get("/api/v1/social/posts", headers=auth_header)
    assert feed.json()[0]["liked_by_me"] is True

    unlike = client.post(f"/api/v1/social/posts/{post['id']}/like", headers=auth_header)
    assert unlike.json() == {"liked": False, "reactions_count": 0}


def test_cannot_like_missing_post(client, auth_header):
    response = client.post("/api/v1/social/posts/99999/like", headers=auth_header)
    assert response.status_code == 404


def test_comments_on_post(client, auth_header):
    top = _create_item(client, auth_header, "Comment tee")
    post = _create_post(client, auth_header, top_id=top["id"]).json()

    create = client.post(
        f"/api/v1/social/posts/{post['id']}/comments",
        json={"body": "Love this fit"},
        headers=auth_header,
    )
    assert create.status_code == 201
    comment = create.json()
    assert comment["body"] == "Love this fit"
    assert comment["is_mine"] is True

    listed = client.get(f"/api/v1/social/posts/{post['id']}/comments", headers=auth_header)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    feed = client.get("/api/v1/social/posts", headers=auth_header)
    assert feed.json()[0]["comments_count"] == 1

    delete = client.delete(f"/api/v1/social/comments/{comment['id']}", headers=auth_header)
    assert delete.status_code == 204


def test_follow_and_following_feed(client, auth_header):
    other_header, other_user = _register_user(client, "Friend User")
    top = _create_item(client, other_header, "Friend tee")
    _create_post(client, other_header, top_id=top["id"], caption="Friend fit")

    mine = _create_item(client, auth_header, "My tee")
    _create_post(client, auth_header, top_id=mine["id"], caption="My fit")

    following_before = client.get("/api/v1/social/posts?scope=following", headers=auth_header)
    assert len(following_before.json()) == 1
    assert following_before.json()[0]["caption"] == "My fit"

    follow = client.post(f"/api/v1/social/users/{other_user['id']}/follow", headers=auth_header)
    assert follow.status_code == 200
    assert follow.json()["following"] is True

    following_after = client.get("/api/v1/social/posts?scope=following", headers=auth_header)
    captions = {p["caption"] for p in following_after.json()}
    assert "Friend fit" in captions
    assert "My fit" in captions

    mine_feed = client.get("/api/v1/social/posts?scope=mine", headers=auth_header)
    assert len(mine_feed.json()) == 1
    assert mine_feed.json()[0]["is_mine"] is True


def test_delete_own_post(client, auth_header):
    top = _create_item(client, auth_header, "Delete tee")
    post = _create_post(client, auth_header, top_id=top["id"]).json()

    delete = client.delete(f"/api/v1/social/posts/{post['id']}", headers=auth_header)
    assert delete.status_code == 204

    get = client.get(f"/api/v1/social/posts/{post['id']}", headers=auth_header)
    assert get.status_code == 404


def test_list_people(client, auth_header):
    _register_user(client, "Another Person")
    people = client.get("/api/v1/social/people", headers=auth_header)
    assert people.status_code == 200
    assert len(people.json()) >= 2
