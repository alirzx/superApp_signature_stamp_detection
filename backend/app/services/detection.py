"""Service-level coordination and Wiki-compatible object adaptation."""
from time import perf_counter
from uuid import uuid4
from app.api.schemas import BBox, Provenance, Detection, DetectionResponse, ImageMetadata, TransformMetadata
from app.preprocessing.images import prepare_image, restore_box
from app.core.config import Settings


class DetectionService:
    def __init__(self, engine, settings: Settings):
        self.engine = engine
        self.settings = settings

    def process(self, data: bytes, filename: str, document_id: str, page_id: str, page_number: int, threshold: float, kind: str | None = None):
        start = perf_counter()
        page = prepare_image(data, max_pixels=self.settings.max_image_pixels, max_long_edge=self.settings.preprocess_max_long_edge)
        raws = self.engine.predict(page.image, threshold)
        objects: list[Detection] = []
        for raw in raws:
            if kind is not None and raw.label != kind:
                continue
            box = restore_box(raw.bbox, page)
            if box is None:
                continue
            objects.append(Detection(
                object_id=f"{raw.label}_{uuid4().hex}", document_id=document_id, page_id=page_id, page_number=page_number,
                type=raw.label, bbox=BBox(x1=box[0], y1=box[1], x2=box[2], y2=box[3]),
                confidence=raw.confidence, metadata={"source_label": raw.label, "source_class_id": raw.class_id},
                provenance=Provenance(model_id=self.settings.model_repo, model_version=self.settings.model_revision)
            ))
        objects.sort(key=lambda obj: (obj.bbox.y1, obj.bbox.x1, obj.type, obj.object_id))
        return DetectionResponse(
            request_id=uuid4().hex, document_id=document_id, page_id=page_id, page_number=page_number,
            image=ImageMetadata(filename=filename, source_width=page.source_width, source_height=page.source_height,
                processed_width=page.processed_width, processed_height=page.processed_height),
            transform=TransformMetadata(exif_orientation_applied=page.exif_orientation_applied, scale_x=page.scale_x, scale_y=page.scale_y),
            objects=objects, counts={"stamp": sum(o.type == "stamp" for o in objects), "signature": sum(o.type == "signature" for o in objects)},
            processing_time_ms=round((perf_counter() - start) * 1000, 2),
            warnings=[] if objects else ["no_stamp_or_signature_detected"]
        )
