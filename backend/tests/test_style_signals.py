from app.services.style_signal_service import StyleSignalService


def _add(client, auth_header, **fields):
    response = client.post(
        "/api/v1/closet/items", json={"is_clean": True, **fields}, headers=auth_header
    )
    assert response.status_code == 201
    return response.json()


def test_record_style_signal_endpoint(client, auth_header):
    response = client.post(
        "/api/v1/style/signals",
        json={"event_type": "shop_tap", "product_id": "patagonia-fleece"},
        headers=auth_header,
    )
    assert response.status_code == 201
    assert response.json()["event_type"] == "shop_tap"


def test_outfit_feedback_writes_style_signal(client, auth_header):
    top = _add(client, auth_header, name="Signal tee", category="top")
    bottom = _add(client, auth_header, name="Signal jeans", category="bottom")

    response = client.post(
        "/api/v1/outfits/feedback",
        json={
            "top_id": top["id"],
            "bottom_id": bottom["id"],
            "signal": "like",
            "occasion": "everyday",
        },
        headers=auth_header,
    )
    assert response.status_code == 201

    signals = client.get("/api/v1/outfits/suggestion", headers=auth_header)
    assert signals.status_code == 200


def test_swap_logs_style_signal(client, auth_header):
    top_a = _add(client, auth_header, name="Swap top A", category="top", color="white")
    top_b = _add(client, auth_header, name="Swap top B", category="top", color="blue")
    bottom = _add(client, auth_header, name="Swap jeans", category="bottom", color="black")
    shoes = _add(client, auth_header, name="Swap sneakers", category="footwear", color="white")

    initial = client.get("/api/v1/outfits/suggestion", headers=auth_header).json()
    swap = client.get(
        "/api/v1/outfits/suggestion",
        params={
            "swap_slot": "top",
            "top_id": initial["top"]["id"],
            "bottom_id": bottom["id"],
            "shoes_id": shoes["id"],
        },
        headers=auth_header,
    )
    assert swap.status_code == 200
    assert swap.json()["top"]["id"] in {top_a["id"], top_b["id"]}


def test_shop_signal_weight(client, auth_header):
    assert StyleSignalService.event_weight("shop_tap") > 0
    assert StyleSignalService.event_weight("dislike") < 0
