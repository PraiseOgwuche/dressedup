from app.services.shop_service import ShopService
from app.shop.catalog import load_catalog


def test_catalog_loads_products():
    products = load_catalog()
    assert len(products) >= 12
    assert products[0].brand
    assert products[0].price_usd > 0
    assert products[0].image_url
    assert products[0].affiliate_url or products[0].product_url


def test_shop_recommends_with_outfit_counts(client, auth_header):
    for item in (
        {
            "name": "Grey tee",
            "category": "top",
            "subcategory": "t-shirt",
            "color": "grey",
            "color_hex": "#9A9A9A",
            "formality": "casual",
            "pattern": "solid",
        },
        {
            "name": "Black jeans",
            "category": "bottom",
            "subcategory": "jeans",
            "color": "black",
            "color_hex": "#1C1C1C",
            "formality": "casual",
            "pattern": "solid",
        },
    ):
        created = client.post("/api/v1/closet/items", json=item, headers=auth_header)
        assert created.status_code == 201

    response = client.get("/api/v1/shop/recommendations", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "styling_insight" in body
    if body["recommendations"]:
        rec = body["recommendations"][0]
        assert rec["outfit_count"] >= 1
        assert "sample_outfits" in rec
        assert isinstance(rec["sample_outfits"], list)
        assert rec["product_id"]
        assert rec["brand"]
        assert rec["product_url"]
        assert rec["buy_url"]
        assert rec.get("image_url")


def test_shop_category_filter(client, auth_header):
    for item in (
        {"name": "White oxford", "category": "top", "color": "white", "formality": "business"},
        {"name": "Khaki chinos", "category": "bottom", "color": "tan", "formality": "smart-casual"},
        {"name": "Brown loafers", "category": "footwear", "color": "brown", "formality": "smart-casual"},
    ):
        client.post("/api/v1/closet/items", json=item, headers=auth_header)

    tops = client.get("/api/v1/shop/recommendations?category=top", headers=auth_header)
    assert tops.status_code == 200
    for rec in tops.json()["recommendations"]:
        assert rec["category"] == "top"


def test_shop_empty_closet_message(client, auth_header):
    response = client.get("/api/v1/shop/recommendations", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert "closet" in body["summary"].lower()
    assert body.get("styling_insight")
