from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.ingestion import DraftItem


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
