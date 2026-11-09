"""Stable JSON contract; bboxes are pixels in EXIF-corrected source coordinates."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class BBox(BaseModel):
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(ge=0)
    y2: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("bbox must have strictly positive width and height")
        return self


class Provenance(BaseModel):
    module: Literal["stamp_signature"] = "stamp_signature"
    backend: Literal["rfdetr"] = "rfdetr"
    model_id: str
    model_version: str


class Detection(BaseModel):
    object_id: str
    document_id: str
    page_id: str
    page_number: int = Field(ge=1)
    type: Literal["stamp", "signature"]
    bbox: BBox
    confidence: float = Field(ge=0, le=1)
    metadata: dict = Field(default_factory=dict)
    provenance: Provenance


class ImageMetadata(BaseModel):
    filename: str
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    processed_width: int = Field(gt=0)
    processed_height: int = Field(gt=0)
    source_coordinate_space: Literal["exif_corrected_source_pixels"] = "exif_corrected_source_pixels"


class TransformMetadata(BaseModel):
    exif_orientation_applied: bool
    scale_x: float = Field(gt=0)
    scale_y: float = Field(gt=0)


class DetectionResponse(BaseModel):
    schema_version: Literal["superapp.stamp-signature.v1"] = "superapp.stamp-signature.v1"
    request_id: str
    document_id: str
    page_id: str
    page_number: int = Field(ge=1)
    module: Literal["stamp_signature"] = "stamp_signature"
    image: ImageMetadata
    transform: TransformMetadata
    objects: list[Detection] = Field(default_factory=list)
    counts: dict[str, int]
    processing_time_ms: float = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
