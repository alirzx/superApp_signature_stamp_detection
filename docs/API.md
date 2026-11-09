# REST API v1

All `/v1/*` and `/metrics` require `X-API-Key` when configured. Production requires a token at least 24 characters long. Health is public to permit Docker orchestration.

| Method | Route | Purpose |
|---|---|---|
| GET | `/health/live` | Process live |
| GET | `/health/ready` | Model loaded and ready |
| GET | `/v1/models` | Pinned model identity/labels |
| POST | `/v1/detect` | Find stamps and signatures |
| POST | `/v1/detect/stamps` | Return stamp objects only |
| POST | `/v1/detect/signatures` | Return signature objects only |
| GET | `/metrics` | Prometheus counters/latency |

All POST routes accept multipart `file` plus optional `document_id` (default `upload`), `page_id` (`page-1`), `page_number` (1), `threshold` (configured threshold by default, range 0.01-0.99).

Example response (synthetic values):

```json
{
  "schema_version": "superapp.stamp-signature.v1",
  "request_id": "abc123",
  "document_id": "doc-1",
  "page_id": "page-1",
  "page_number": 1,
  "module": "stamp_signature",
  "image": {"filename": "document.png", "source_width": 1600, "source_height": 1200, "processed_width": 1600, "processed_height": 1200, "source_coordinate_space": "exif_corrected_source_pixels"},
  "transform": {"exif_orientation_applied": false, "scale_x": 1.0, "scale_y": 1.0},
  "objects": [{"object_id":"stamp_123", "document_id":"doc-1", "page_id":"page-1", "page_number":1, "type":"stamp", "bbox":{"x1":10.0,"y1":20.0,"x2":100.0,"y2":150.0}, "confidence":0.93, "metadata":{"source_label":"stamp","source_class_id":0}, "provenance":{"module":"stamp_signature","backend":"rfdetr","model_id":"bluecopa/rf-detr-stamp-signature-detector","model_version":"c59fd4f451b254501700a56c7769f1a3d788c753"}}],
  "counts": {"stamp":1,"signature":0}, "processing_time_ms":123.4, "warnings":[]
}
```

`bbox` uses XYXY values in EXIF-corrected source pixels. Detections can be empty and scores are model confidence, not calibrated probabilities. HTTP 401 auth error; 413 oversized declared/image body; 422 unsupported image or input; 503 saturated inference queue; 500 runtime model failure. One request = one image; no DB, asynchronous jobs, or long-running task IDs.
