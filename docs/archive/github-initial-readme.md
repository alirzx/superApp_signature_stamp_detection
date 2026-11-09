# SuperApp Module 06 | Signature & Stamp Detection

Standalone CPU-first detection of stamps and handwritten signatures from document images, using the Wiki Doc Scanner's pinned RF-DETR Base checkpoint (bluecopa/rf-detr-stamp-signature-detector).

**Repository status:** Initialized only. The complete 49-file source tree has been generated and locally committed in the ChatGPT sandbox, and is provided as a downloadable ZIP in the associated conversation. It has **not** been published to this GitHub branch. This README is not a deployment-ready source checkout.

## Intended architecture

- FastAPI API: `/v1/detect`, `/v1/detect/stamps`, `/v1/detect/signatures`, `/v1/models`, health and metrics.
- CPU-only PyTorch/RF-DETR inference; input JPEG/PNG/WebP, EXIF-corrected source-coordinate boxes, checksum-verified model bootstrap.
- React/Vite RTL frontend served through non-root Nginx with an authenticated internal API proxy.
- Docker Compose with two long-running containers and a one-shot model-setup service, configuration via local/production `.env` templates.
- Planned host ports: API 8006 loopback, UI 8087 (LAN address `192.168.4.209` after host confirmation).
- CI file intentionally excluded for integration by the SuperApp deployment team.

The model is roughly 369 MB on disk and CPU memory/latency are not yet benchmarked. Offline backend tests of the sandbox source have passed; deployment must still validate Docker, npm dependencies and real model inference.
