# Test and acceptance matrix

Offline and fake-engine checks: `make test` verifies contract/auth, response provenance, stamp/signature filtering, blank/invalid inputs, EXIF orientation, resize coordinate restoration, Docker Compose structure, missing-weight failure and production token checks. These tests do **not** prove RF-DETR CPU compatibility.

Real deployment gates on target host:

1. Docker build both images, inspect CPU-only torch/torchvision versions, run `pip check`.
2. One-shot Hugging Face download + SHA256 verification + cache reuse across restart; wrong digest must fail.
3. Real JPEG, PNG, WebP document examples with known stamps/signatures; check both classes, empty cases and no checkbox leakage.
4. Correct bounding boxes after resize and EXIF rotation; overlay visually matches originals.
5. Measure API RSS peak at initialization, loaded baseline, and concurrent requests; do not assume 4 GB sufficient.
6. Measure CPU model load, median, p95, and throughput on the intended 2-CPU server quota; watch for timeout.
7. Verify `127.0.0.1:8006` is not LAN reachable, UI is reachable on approved `192.168.4.209:8087`, and API token is not in the downloaded JS.
8. Verify 401 unauthenticated, 413 oversize, 422 corrupt image, 503 saturation, no empty placeholder detections, and that UI works after restart.
9. Inspect ASGI streamed/multipart body limit, missing Content-Length, API load saturation and early-return cleanup.
10. Record the model inference result, peak resident memory, CPU latency, and deployment evidence on the server. Enable automatic GitLab deploy only after the team reviews and validates the pipeline. No laptop Docker build is required.