"""Garment photo cleanup: ML background removal (rembg) → trimmed transparent PNG.

The cutout is stored alongside the original and used as `thumbnail_url`, which
the mobile app already prefers for closet cards and the 3D avatar's fabric
texture. Every step degrades gracefully: any failure (model unavailable,
undecodable image, nothing detected) returns None and callers keep the
original photo.
"""

import io
import logging
import threading
from pathlib import Path
from typing import Optional

from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

_session = None
_session_lock = threading.Lock()
_rembg_failed = False


def _get_session():
    """Lazily create (and cache) the rembg ONNX session — the model is only
    loaded into memory on the first real request, not at import/startup."""
    global _session, _rembg_failed
    if _rembg_failed:
        return None
    if _session is not None:
        return _session
    with _session_lock:
        if _session is not None or _rembg_failed:
            return _session
        try:
            from rembg import new_session

            _session = new_session(settings.BG_REMOVAL_MODEL)
        except Exception:
            logger.exception(
                "rembg unavailable (model=%s); background removal disabled for this process",
                settings.BG_REMOVAL_MODEL,
            )
            _rembg_failed = True
            return None
    return _session


def remove_background(data: bytes) -> Optional[bytes]:
    """Return a transparent PNG cutout of the garment, trimmed to content with
    a small margin and downscaled to BG_REMOVAL_MAX_PX. None means "keep the
    original" — never raises."""
    if not settings.BG_REMOVAL_ENABLED:
        return None

    # Validate the bytes decode as an image BEFORE touching the ML session, so
    # bad uploads (and unit tests with fake bytes) never trigger model loading.
    try:
        Image.open(io.BytesIO(data)).verify()
    except Exception:
        return None

    session = _get_session()
    if session is None:
        return None

    try:
        from rembg import remove

        cutout_bytes = remove(data, session=session)
        image = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

        bbox = image.getchannel("A").getbbox()
        if bbox is None:
            return None  # model found no foreground at all

        # If the detected garment is a sliver of the frame, the segmentation
        # probably failed — better to keep the original photo.
        area_ratio = ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])) / (image.width * image.height)
        if area_ratio < 0.03:
            return None

        image = image.crop(bbox)

        # Small transparent margin so the garment doesn't touch the edges.
        margin = max(8, int(max(image.size) * 0.04))
        canvas = Image.new("RGBA", (image.width + 2 * margin, image.height + 2 * margin), (0, 0, 0, 0))
        canvas.paste(image, (margin, margin))

        canvas.thumbnail((settings.BG_REMOVAL_MAX_PX, settings.BG_REMOVAL_MAX_PX))

        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
    except Exception:
        logger.exception("Background removal failed; keeping original image")
        return None


def crop_normalized(
    data: bytes,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    padding: float = 0.04,
) -> Optional[bytes]:
    """Crop a JPEG region using normalized 0–1 box coords. Returns JPEG bytes or None."""
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None

    if image.width < 8 or image.height < 8:
        return None

    # Clamp + pad so tight vision boxes don't clip sleeves/hems.
    x0 = max(0.0, min(1.0, x - padding))
    y0 = max(0.0, min(1.0, y - padding))
    x1 = max(0.0, min(1.0, x + w + padding))
    y1 = max(0.0, min(1.0, y + h + padding))
    if x1 - x0 < 0.05 or y1 - y0 < 0.05:
        return None

    left = int(x0 * image.width)
    top = int(y0 * image.height)
    right = max(left + 1, int(x1 * image.width))
    bottom = max(top + 1, int(y1 * image.height))
    cropped = image.crop((left, top, right, bottom))

    buffer = io.BytesIO()
    cropped.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def fetch_stored_image_bytes(url: str) -> Optional[bytes]:
    """Resolve a stored image_url to raw bytes — local media path or HTTP(S)."""
    if not url:
        return None
    if url.startswith(settings.MEDIA_URL_PREFIX):
        relative = url[len(settings.MEDIA_URL_PREFIX) :].lstrip("/")
        path = Path(settings.MEDIA_DIR) / relative
        return path.read_bytes() if path.exists() else None
    if url.startswith("http://") or url.startswith("https://"):
        try:
            import httpx

            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except Exception:
            logger.exception("Failed to fetch stored image %s", url)
            return None
    return None
