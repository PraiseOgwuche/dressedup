from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.ingestion import DraftItem, ReceiptExtract


class VisionProvider(ABC):
    """Extracts confirmable DraftItems from images of garment(s).

    Implementations stay behind this contract so the whole ingestion pipeline
    and UI can be built/tested against a stub, then swapped for a real model.
    """

    @abstractmethod
    def extract_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> DraftItem:
        """Return a draft for a single item. `label_image` improves brand/material."""
        raise NotImplementedError

    def extract_multi_attributes(
        self,
        garment_image: bytes,
        label_image: Optional[bytes] = None,
    ) -> List[DraftItem]:
        """Return one draft per distinct garment in the photo (flat-lay, outfit pile)."""
        return [self.extract_attributes(garment_image, label_image)]

    @abstractmethod
    def extract_from_receipt(self, receipt_image: bytes) -> ReceiptExtract:
        """Parse a retail receipt photo into clothing line items with brand/SKU/price."""
        raise NotImplementedError

    @abstractmethod
    def extract_from_care_label(self, label_image: bytes) -> DraftItem:
        """Parse a care-label / hang-tag photo (no garment photo). Identity fields only."""
        raise NotImplementedError
