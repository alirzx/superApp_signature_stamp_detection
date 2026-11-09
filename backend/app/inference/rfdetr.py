"""Standalone adapter extracted from the Wiki RF-DETR detector, strictly CPU-only."""
from dataclasses import dataclass
from threading import Lock
from typing import Any
import math
import numpy as np
from PIL import Image
from app.core.model_integrity import verify_model
from app.core.config import Settings

CLASS_NAMES = {0: "stamp", 1: "signature", 2: "checkbox_checked", 3: "checkbox_unchecked"}


@dataclass(frozen=True)
class RawDetection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    class_id: int | None


def parse_detections(raw: Any, threshold: float) -> list[RawDetection]:
    """Accept supervision.Detections and legacy Wiki-compatible dict iterations."""
    if hasattr(raw, "xyxy"):
        boxes = np.asarray(raw.xyxy, dtype=float).reshape(-1, 4)
        ids = np.asarray(getattr(raw, "class_id", []), dtype=object).reshape(-1)
        scores = np.asarray(getattr(raw, "confidence", []), dtype=float).reshape(-1)
        data = getattr(raw, "data", {}) or {}
        names = data.get("class_name") if isinstance(data, dict) else None
        if names is None:
            names = []
        def row(i, box):
            cid = int(ids[i]) if i < len(ids) and ids[i] is not None else None
            label = CLASS_NAMES.get(cid, str(names[i]).lower() if i < len(names) else "")
            score = float(scores[i]) if i < len(scores) else 0.0
            return cid, label, score, box
        rows = (row(i, b) for i, b in enumerate(boxes))
    else:
        def items():
            for entry in raw:
                if not isinstance(entry, dict):
                    continue
                v = entry.get("class_id", entry.get("class"))
                cid = int(v) if isinstance(v, (int, np.integer)) else None
                label = CLASS_NAMES.get(cid, str(entry.get("class_name", "")).lower())
                yield cid, label, float(entry.get("confidence", entry.get("score", 0.0))), entry.get("bbox", entry.get("xyxy", []))
        rows = items()
    result = []
    for cid, label, score, box in rows:
        if label not in {"stamp", "signature"} or not math.isfinite(score) or score < threshold or score > 1:
            continue
        try:
            coords = tuple(float(v) for v in box)
        except (TypeError, ValueError):
            continue
        if len(coords) != 4 or not all(math.isfinite(v) for v in coords):
            continue
        result.append(RawDetection(label, score, coords, cid))
    return result


class RFDETREngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: Any = None
        self._lock = Lock()
        self.ready = False

    def initialize(self) -> None:
        verify_model(self.settings.model_dir)
        import torch
        from rfdetr import RFDETRBase
        torch.set_num_threads(self.settings.cpu_threads)
        if torch.version.cuda is not None:
            raise RuntimeError("CUDA build detected; expected CPU-only torch")
        # No RFDETRBase() fallback: it could fetch unrelated weights and change predictions.
        model = RFDETRBase(pretrain_weights=str(self.settings.checkpoint), num_classes=4)
        context = getattr(model, "model", None)
        if context is None or getattr(context, "model", None) is None:
            raise RuntimeError("RF-DETR model context incompatible with Wiki adapter")
        context.model = context.model.to(torch.device("cpu"))
        context.device = torch.device("cpu")
        context.model.eval()
        self._model = model
        self.ready = True

    def predict(self, image: Image.Image, threshold: float) -> list[RawDetection]:
        if not self.ready:
            raise RuntimeError("RF-DETR unavailable")
        with self._lock:
            raw = self._model.predict(image.convert("RGB"), threshold=threshold, include_source_image=False)
        return parse_detections(raw, threshold)
