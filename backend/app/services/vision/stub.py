from typing import List, Optional

from app.schemas.ingestion import DraftItem
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
        )
        return [top, bottom, belt]
