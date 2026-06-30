from app.services.shop_service import ShopService
from app.shop.catalog import load_catalog


def test_catalog_loads_products():
    products = load_catalog()
    assert len(products) >= 8
    assert products[0].brand
    assert products[0].price_usd > 0


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
    assert "recommendations" in body
    if body["recommendations"]:
        rec = body["recommendations"][0]
        assert rec["outfit_count"] >= 1
        assert rec["product_id"]
        assert rec["brand"]
        assert rec["product_url"]


def test_shop_empty_closet_message(client, auth_header):
    response = client.get("/api/v1/shop/recommendations", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert "closet" in body["summary"].lower()
