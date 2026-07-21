"""FashionCLIP image encoder — self-hosted ONNX Runtime CPU inference.

Only the vision tower (~350 MB) is used in production; garment vectors are
computed once at ingest/backfill, never in the suggestion hot path. Session
options deliberately trade a little latency for a small, predictable memory
footprint (see Render instance sizing in PLAN.md).

Weights: scripts/download_fashionclip.py → models/fashionclip/vision_model.onnx
(export of patrickjohncyh/fashion-clip, MIT).
"""

from __future__ import annotations

import logging
import threading
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import settings
from app.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)

VISION_MODEL_FILENAME = "vision_model.onnx"

# Standard CLIP preprocessing constants (ViT-B/32).
_IMAGE_SIZE = 224
_CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
_CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Garment image bytes → CLIP pixel tensor of shape [1, 3, 224, 224].

    Transparent cutout PNGs (rembg output) are composited onto white first —
    the background the model expects for product-style imagery.
    """
    image = Image.open(BytesIO(image_bytes))
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    image = image.convert("RGB")

    # Resize shortest side to 224, then center-crop 224×224 (CLIP convention).
    width, height = image.size
    scale = _IMAGE_SIZE / min(width, height)
    resized = image.resize(
        (max(_IMAGE_SIZE, round(width * scale)), max(_IMAGE_SIZE, round(height * scale))),
        Image.Resampling.BICUBIC,
    )
    left = (resized.width - _IMAGE_SIZE) // 2
    top = (resized.height - _IMAGE_SIZE) // 2
    cropped = resized.crop((left, top, left + _IMAGE_SIZE, top + _IMAGE_SIZE))

    pixels = np.asarray(cropped, dtype=np.float32) / 255.0
    pixels = (pixels - _CLIP_MEAN) / _CLIP_STD
    return pixels.transpose(2, 0, 1)[np.newaxis, :]  # HWC -> 1CHW


class FashionClipEmbeddingProvider(EmbeddingProvider):
    model_name = "fashion-clip"
    model_version = "vit-b-32-onnx-1"
    dim = 512

    _session = None
    _session_lock = threading.Lock()

    def __init__(self) -> None:
        self._model_path = Path(settings.EMBEDDING_MODEL_DIR) / VISION_MODEL_FILENAME
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"FashionCLIP weights not found at {self._model_path}. "
                "Run: python scripts/download_fashionclip.py"
            )

    @classmethod
    def _get_session(cls, model_path: Path):
        """Lazy process-wide singleton so weights load once (~350 MB)."""
        if cls._session is None:
            with cls._session_lock:
                if cls._session is None:
                    import onnxruntime as ort

                    options = ort.SessionOptions()
                    # No pre-allocated arena: keeps RSS near actual model size
                    # at the cost of some ingest latency (acceptable off hot path).
                    options.enable_cpu_mem_arena = False
                    options.enable_mem_pattern = False
                    options.intra_op_num_threads = settings.EMBEDDING_INTRA_OP_THREADS
                    options.inter_op_num_threads = 1
                    cls._session = ort.InferenceSession(
                        str(model_path),
                        sess_options=options,
                        providers=["CPUExecutionProvider"],
                    )
                    logger.info("FashionCLIP vision encoder loaded from %s", model_path)
        return cls._session

    def embed_image(self, image_bytes: bytes) -> list[float]:
        session = self._get_session(self._model_path)
        pixel_values = preprocess_image(image_bytes)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        (embeds,) = session.run([output_name], {input_name: pixel_values})
        vector = np.asarray(embeds[0], dtype=np.float32)
        norm = float(np.linalg.norm(vector)) or 1.0  # outputs are not pre-normalized
        return (vector / norm).tolist()
