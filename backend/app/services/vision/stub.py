from typing import List, Optional

from app.schemas.ingestion import BoundingBox, DraftItem, ReceiptExtract
from app.services.vision.base import VisionProvider


class StubVisionProvider(VisionProvider):
    """Returns realistic canned data so the pipeline/UI can be built without
    spending tokens. Visual attributes come back confident; identity (brand,
    material) is only confident when a label image is supplied."""

    def extract_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> DraftItem:
        confidence = {
            "category": 0.97,
            "subcategory": 0.9,
            "color": 0.93,
            "pattern": 0.88,
            "formality": 0.82,
        }

        brand = None
        material = None
        size = None
        source = "photo"

        if label_image is not None:
            brand = "Uniqlo"
            material = "100% cotton"
            size = "M"
            source = "label_ocr"
            confidence.update({"brand": 0.94, "material": 0.95, "size": 0.9})

        return DraftItem(
            name="Black crewneck t-shirt",
            category="top",
            subcategory="t-shirt",
            brand=brand,
            product_name=None,
            size=size,
            color="black",
            color_hex="#111111",
            pattern="solid",
            material=material,
            occasion=["everyday"],
            formality="casual",
            weather_tag=["warm", "mild"],
            seasons=["spring", "summer", "fall"],
            source=source,
            confidence=confidence,
            needs_review=brand is None,
        )

    def extract_multi_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> List[DraftItem]:
        """Simulate a flat-lay with three distinct pieces (free, no API)."""
        top = self.extract_attributes(garment_image, label_image)
        top.name = "White Oxford shirt"
        top.category = "top"
        top.subcategory = "shirt"
        top.color = "white"
        top.color_hex = "#F5F5F5"
        top.bbox = BoundingBox(x=0.08, y=0.04, w=0.84, h=0.28)

        bottom = DraftItem(
            name="Navy chinos",
            category="bottom",
            subcategory="trousers",
            color="navy",
            color_hex="#1B2A4A",
            pattern="solid",
            occasion=["work", "everyday"],
            formality="smart-casual",
            weather_tag=["mild", "warm"],
            seasons=["spring", "fall", "all-season"],
            source="photo",
            confidence={"category": 0.91, "color": 0.88},
            needs_review=True,
            bbox=BoundingBox(x=0.08, y=0.36, w=0.84, h=0.28),
        )
        belt = DraftItem(
            name="Brown leather belt",
            category="accessory",
            subcategory="belt",
            color="brown",
            color_hex="#6B4423",
            pattern="solid",
            occasion=["everyday", "work"],
            formality="casual",
            weather_tag=["warm", "mild", "cold"],
            seasons=["all-season"],
            source="photo",
            confidence={"category": 0.85, "color": 0.8},
            needs_review=True,
            bbox=BoundingBox(x=0.15, y=0.68, w=0.7, h=0.24),
        )
        return [top, bottom, belt]

    def extract_from_receipt(self, receipt_image: bytes) -> ReceiptExtract:
        items = [
            DraftItem(
                name="Airism crew neck T-shirt",
                category="top",
                subcategory="t-shirt",
                brand="Uniqlo",
                product_name="AIRism Cotton Crew Neck T-Shirt",
                size="M",
                color="white",
                sku="475356",
                price=19.90,
                source="receipt",
                confidence={"brand": 0.96, "product_name": 0.94, "size": 0.92, "price": 0.98, "sku": 0.9},
                needs_review=False,
            ),
            DraftItem(
                name="Slim-fit chinos",
                category="bottom",
                subcategory="trousers",
                brand="Uniqlo",
                product_name="Slim Fit Chino Pants",
                size="32",
                color="navy",
                sku="455221",
                price=49.90,
                source="receipt",
                confidence={"brand": 0.96, "product_name": 0.93, "size": 0.91, "price": 0.98, "sku": 0.88},
                needs_review=False,
            ),
        ]
        return ReceiptExtract(
            merchant="Uniqlo",
            purchase_date="2025-03-14",
            items=items,
        )

    def extract_from_care_label(self, label_image: bytes) -> DraftItem:
        return DraftItem(
            name="Cotton crew neck tee",
            category="top",
            subcategory="t-shirt",
            brand="Uniqlo",
            product_name="AIRism Cotton Crew Neck T-Shirt",
            size="M",
            material="100% cotton",
            source="label_ocr",
            confidence={"brand": 0.95, "material": 0.96, "size": 0.93, "product_name": 0.9},
            needs_review=False,
        )
