"""Wiki scanner geometry contract without MinIO, OCR, or layout dependencies."""
from dataclasses import dataclass
from io import BytesIO
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED = {"JPEG", "PNG", "WEBP"}


class InvalidImage(ValueError):
    pass


@dataclass
class PreparedImage:
    image: Image.Image
    source_width: int
    source_height: int
    processed_width: int
    processed_height: int
    exif_orientation_applied: bool
    scale_x: float
    scale_y: float


def prepare_image(data: bytes, *, max_pixels: int, max_long_edge: int) -> PreparedImage:
    if not data:
        raise InvalidImage("Empty image")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as opened:
                if opened.format not in ALLOWED:
                    raise InvalidImage("Only JPEG, PNG, and WebP images are supported")
                w, h = opened.size
                if w < 2 or h < 2 or w * h > max_pixels:
                    raise InvalidImage("Invalid or oversized image dimensions")
                orientation = opened.getexif().get(274, 1)
                opened.load()
                oriented = ImageOps.exif_transpose(opened)
                original = oriented.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning, ValueError) as exc:
        if isinstance(exc, InvalidImage):
            raise
        raise InvalidImage("Corrupted or unsupported image") from exc
    sw, sh = original.size
    scale = min(1.0, max_long_edge / max(sw, sh))
    pw, ph = max(1, round(sw * scale)), max(1, round(sh * scale))
    processed = original.resize((pw, ph), Image.Resampling.LANCZOS) if scale < 1 else original
    return PreparedImage(processed, sw, sh, pw, ph, orientation not in (1, None), pw / sw, ph / sh)


def restore_box(box: tuple[float, float, float, float], page: PreparedImage):
    import math
    if len(box) != 4 or not all(math.isfinite(float(v)) for v in box):
        return None
    x1, y1, x2, y2 = (float(v) for v in box)
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    sx1, sy1 = max(0.0, min(page.source_width, x1 / page.scale_x)), max(0.0, min(page.source_height, y1 / page.scale_y))
    sx2, sy2 = max(0.0, min(page.source_width, x2 / page.scale_x)), max(0.0, min(page.source_height, y2 / page.scale_y))
    if sx2 <= sx1 or sy2 <= sy1:
        return None
    return (sx1, sy1, sx2, sy2)
