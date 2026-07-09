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


def test_activity_empty_for_new_user(client, auth_header):
    response = client.get("/api/v1/social/activity", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["unread_count"] == 0
    assert body["items"] == []


def test_activity_like_on_my_post(client, auth_header):
    top = _create_item(client, auth_header, "Activity tee")
    post = _create_post(client, auth_header, top_id=top["id"], look_name="Monday fit").json()

    other_header, _ = _register_user(client, "Liker Person")
    like = client.post(f"/api/v1/social/posts/{post['id']}/like", headers=other_header)
    assert like.status_code == 200

    activity = client.get("/api/v1/social/activity", headers=auth_header)
    assert activity.status_code == 200
    body = activity.json()
    assert body["unread_count"] >= 1
    like_items = [i for i in body["items"] if i["type"] == "like"]
    assert len(like_items) == 1
    assert like_items[0]["actor_name"] == "Liker Person"
    assert like_items[0]["post_id"] == post["id"]
    assert "Monday fit" in like_items[0]["message"]


def test_activity_comment_and_mark_seen(client, auth_header):
    top = _create_item(client, auth_header, "Comment activity tee")
    post = _create_post(client, auth_header, top_id=top["id"]).json()

    other_header, _ = _register_user(client, "Commenter Person")
    comment = client.post(
        f"/api/v1/social/posts/{post['id']}/comments",
        json={"body": "This slaps"},
        headers=other_header,
    )
    assert comment.status_code == 201

    before_seen = client.get("/api/v1/social/activity", headers=auth_header).json()
    assert before_seen["unread_count"] >= 1

    seen = client.post("/api/v1/social/activity/seen", headers=auth_header)
    assert seen.status_code == 200
    assert seen.json()["unread_count"] == 0

    after_seen = client.get("/api/v1/social/activity", headers=auth_header).json()
    assert after_seen["unread_count"] == 0
    assert all(not item["is_unread"] for item in after_seen["items"])


def test_activity_new_follower(client, auth_header):
    me = client.get("/api/v1/auth/me", headers=auth_header).json()
    other_header, _ = _register_user(client, "New Follower")
    follow = client.post(f"/api/v1/social/users/{me['id']}/follow", headers=other_header)
    assert follow.status_code == 200

    activity = client.get("/api/v1/social/activity", headers=auth_header)
    follow_items = [i for i in activity.json()["items"] if i["type"] == "follow"]
    assert len(follow_items) == 1
    assert follow_items[0]["actor_name"] == "New Follower"


def test_activity_new_post_from_following(client, auth_header):
    other_header, other_user = _register_user(client, "Poster Friend")
    client.post(f"/api/v1/social/users/{other_user['id']}/follow", headers=auth_header)

    top = _create_item(client, other_header, "Friend fit tee")
    post = _create_post(client, other_header, top_id=top["id"], caption="Gym day").json()

    activity = client.get("/api/v1/social/activity", headers=auth_header)
    post_items = [i for i in activity.json()["items"] if i["type"] == "new_post"]
    assert len(post_items) == 1
    assert post_items[0]["post_id"] == post["id"]
    assert "Gym day" in post_items[0]["message"]
