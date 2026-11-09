# SuperApp Module 06 | Stamp & Signature Detection

Standalone CPU-only image detection microservice using the **same pinned RF-DETR checkpoint as the Organizational Wiki Doc Scanner**. It detects **stamps** and **handwritten signatures** in JPG/PNG/WebP documents; two checkbox classes from the original four-class checkpoint are intentionally discarded.

**Components:** FastAPI backend, RF-DETR/PyTorch CPU model, one-shot Hugging Face model downloader with SHA256 manifest, React/TypeScript/Vite RTL UI served by non-root Nginx, Docker Compose, explicit local/production `.env` templates, tests and deployment docs. No Redis, MinIO, database, OCR, figure/table extraction, or separate worker is required. **The existing `.gitlab-ci.yml` is owned by the deployment team and is intentionally unchanged by this repository polish.**

## Source and model

- Reference: `alirzx/organizational-wiki-intelligence-doc-scanner` `app/modules/stamp_signature/`.
- Model: `bluecopa/rf-detr-stamp-signature-detector`, revision `c59fd4f451b254501700a56c7769f1a3d788c753`.
- Weights: `checkpoint_best_ema.pth`, SHA256 `3a831ae093be64a01a4d9c635dc6071ad7c43c3e95c3da0b33a17351df1e7909`, ~369 MB.
- Model classes: `0=stamp`, `1=signature`, `2=checkbox_checked`, `3=checkbox_unchecked`. Only 0 and 1 are returned.
- Model license listed as Apache-2.0. Review dependencies/checkpoint provenance before commercial release.
- Model runs **on CPU**, but RF-DETR Base has an appreciable RAM/latency cost. A 4 GB API memory limit and two CPU cores are provisional, **not validated performance guarantees**.
- PyTorch `.pth` weights may use Python pickle. This is a trusted, pinned and SHA256-verified third-party checkpoint, not arbitrary user-uploaded weights. Do not accept runtime model URLs.

## Server-only build and deployment

The production rollout is performed by the GitLab runner **on the server**. Developers do not need to download pretrained weights or build images locally. The commands below are intended for a privileged operator in the **server checkout** after the team verifies its CI pipeline, host address, and protected `.env`:

Requirements: Docker Engine, Compose v2, access to Docker base images, Liara/Chabokan PyPI mirrors, the official CPU-wheel index, the npm registry, and Hugging Face for the **first** model download. After bootstrap, inference stays offline.

```bash
cp .env.example .env
# Set API_TOKEN to an independent strong value in .env:
openssl rand -hex 32
make doctor
make build
make model          # optional: normal 'make up' automatically runs this one-shot setup
make model-verify
make up             # model-setup -> API -> UI
make ps
make health
```

Local: API `http://127.0.0.1:8006`, UI `http://127.0.0.1:8087`. API documentation in development: `http://127.0.0.1:8006/docs`.

For the existing SuperApp deployment host, use `.env.production.example` as a template and confirm `UI_BIND_IP=192.168.4.209`, `UI_PORT=8087`. API binds to loopback while the UI is accessible to approved LAN/VPN clients. **Nginx's injected API token does not authenticate individual browser users. Protect LAN access and require authenticated HTTPS ingress for broader exposure.**

## API examples

```bash
set -a; . ./.env; set +a
curl -fsS http://127.0.0.1:8006/health/ready
curl -fsS -H "X-API-Key: $API_TOKEN" http://127.0.0.1:8006/v1/models
curl -fsS -H "X-API-Key: $API_TOKEN" \
  -F file=@document.png -F document_id=doc-1 -F page_id=page-1 -F page_number=1 \
  http://127.0.0.1:8006/v1/detect
# Only stamps or only signatures:
# POST /v1/detect/stamps | POST /v1/detect/signatures
```

Results contain source-image XYXY `bbox`, confidence, label, provenance, document/page IDs, image dimensions, transform factors, counts, and timings. Boxes refer to **EXIF-corrected source pixels**, matching the Wiki adapter. The UI draws overlays and exports JSON. Empty detection returns `200` with `objects: []`, not a fabricated stamp.

## Implementation and verification

```bash
python -m pip install -r backend/requirements-test.txt
make test
cd frontend && npm install && npm run build
# Full model test after weights are installed:
PYTHONPATH=backend API_TOKEN="$API_TOKEN" python backend/scripts/smoke.py document.png
```

Unit tests use a deterministic fake engine; they test HTTP contracts, security, image transforms, class filtering, and Compose structure **without downloading the model**. Real model load, Docker builds, end-to-end CPU inference, accuracy, and memory/latency are deployment acceptance gates, not claimed results from unit tests.

See `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DEPLOYMENT.md`, `docs/MODEL_PROVENANCE.md`, `docs/SECURITY.md`, `docs/TEST_PLAN.md`.

## Repository and CI ownership

GitHub `personal/main` and organization GitLab `origin/master` are the release branches. The initial handoff is complete; `scripts/publish_to_github.sh` is legacy and should **not** be run during ongoing development. The team-managed `.gitlab-ci.yml` is already present on both release branches and must be reviewed separately. It triggers on GitLab `master` but currently uses `git pull origin main` inside its remote SSH command: **this is a known branch mismatch and can fail when server `origin/main` does not exist**. The CI owner must reconcile this with the actual deployment checkout before enabling rollout; do not create a stale `main` alias as a substitute. Existing CI is not modified by this source patch. The CI uses `ENV_FILE` as an SCP source and deploys into `/opt/apps/ai-service/signature_stamp_detection`. Server-first workflow: review the code, synchronize both remotes, and let the GitLab runner build/download/integration-test on the target server only after CI and production configuration are approved. No local model downloads or Docker builds are required.

Before deployment, copy the appropriate template to `.env` on the deployment host (or supply its contents through a protected GitLab file variable), set a strong independent API token and verify the LAN bind IP. `python3`, rather than `python`, may be the available Ubuntu command. Local tests are optional developer checks, not a server deployment prerequisite.