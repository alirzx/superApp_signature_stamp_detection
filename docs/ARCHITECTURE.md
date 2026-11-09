# Architecture and Wiki extraction compatibility

```text
Browser (RTL React) -> Nginx :8080 (inject server-side X-API-Key) -> FastAPI :8000
                                                                   |
                                       upload byte/pixel validation + EXIF orientation
                                                                   |
                                             resize longest side <=2500, RGB
                                                                   |
                                      RFDETRBase(pretrain_weights=pinned.pth), CPU
                                                                   |
                                supervision boxes, class ids 0=stamp,1=signature
                                                                   |
                                    filter checkbox classes 2/3 + threshold
                                                                   |
                               map coordinates by per-axis scale to source pixels
                                                                   |
                             JSON objects / counts / Wiki-compatible provenance

model-setup (one-shot) -> HF pinned revision -> SHA256 -> manifest -> model_cache
API (non-root, read-only filesystem) -> model_cache:ro (no runtime network)
```

Uses the same checkpoint/class mapping and coordinate convention as Wiki `app/modules/stamp_signature/rfdetr_backend.py`, `adapter.py`, `service.py` and `app/preprocessing/pipeline.py`. Wiki accepts MinIO URLs and emits `ModulePageResponse`. SuperApp instead accepts direct image uploads, returns a stable independent `superapp.stamp-signature.v1` response, and retains the Wiki-style object identity, page metadata, and provenance.

**Boundaries:** no OCR, no figure/table, no MinIO/callback, no persistent uploaded image storage, no PDF-to-image conversion, no handwriting recognition, no signature identity/authenticity verification. It only localizes visual marks. CPU requests use one model instance, one Uvicorn worker and a bounded semaphore. Images and results are processed in memory; temporary multipart spooling is restricted by tmpfs and Nginx body limits. The code never exposes a model selection endpoint.

**Coordinate policy:** the original image is rotated using EXIF orientation, then resized uniformly only if its long edge exceeds the cap. RF-DETR receives the processed RGB image. Bounding boxes from the model use processed pixels; the backend divides by `scale_x`,`scale_y`, clamps to the EXIF-corrected original dimensions, and drops invalid boxes.
