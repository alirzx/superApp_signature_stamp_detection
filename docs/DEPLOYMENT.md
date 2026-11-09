# Local and server deployment

1. Copy `.env.example` locally or `.env.production.example` for the deployment host. Replace the API token with `openssl rand -hex 32`; keep `.env` out of Git. Set API port 8006 and UI port 8087, provided they are available on the host.
2. The other SuperApp services use an approved LAN interface `192.168.4.209`; production template binds `UI_BIND_IP` to that address, while `API_BIND_IP=127.0.0.1`. **Confirm that interface and network route before deployment.** Remote clients on the same permitted LAN/VPN can open `http://192.168.4.209:8087` if the firewall allows it. Avoid public exposure without authenticated HTTPS ingress.
3. Build/download/start using `make doctor && make build && make model && make model-verify && make up`. Ordinary `docker compose up --build -d` automatically runs the one-shot setup before API. Keep `model_cache` (do **not** use `docker compose down -v`).
4. Check `docker compose ps -a`, then `docker compose logs --tail=150 model-setup api ui`, `curl -f http://127.0.0.1:8006/health/ready`, and `curl -f http://192.168.4.209:8087/healthz` from an allowed host (replace the IP if changed).
5. Run a **real sample** through `/v1/detect`, validate overlays and JSON coordinates, test file limits, then record RSS and p50/p95 latency. API budget `4g`/`2.0` cores is only a provisional starting point.

## Build supply chains

Backend uses `python:3.11-slim-bookworm` with Liara as primary and Chabokan as fallback for normal Python packages. CPU-specific Torch (`2.14.0+cpu`) and torchvision (`0.29.0+cpu`) are installed via the official CPU wheel index with `--no-deps`; their ordinary dependencies are first installed from the regional mirrors. A final `pip check` plus `torch.version.cuda is None` assert is mandatory. Frontend npm uses the Liara npm registry. Hugging Face weights, Docker Hub images and the PyTorch binary wheel come from their own distinct sources; Python mirrors do not cover them.

No `.gitlab-ci.yml` is included. Teammate should configure GitLab `main` deployment with protected File-type `.env` variable, SSH credentials, a pinned known_hosts file, safe fast-forward remote checkout, `docker compose config --quiet`, image builds, model verification, and optional health-gated startup. Do not deploy on every push before CPU and memory benchmarks are accepted. Standard path suggestion: `/opt/apps/ai-service/signature_stamp_detection_module`.

## Operational constraints

The model is retained on the `superapp-signature-stamp-detection_model_cache` named volume, mounted read-only by the API. The API uses a non-root user and a read-only root filesystem with bounded `/tmp` tmpfs. UI Nginx is non-root and runs on internal port 8080. `API_TOKEN` is only inside the server's environment and Nginx config, never in React's compiled JavaScript. **Nginx proxy token is not per-user auth.** Require trusted firewall/VPN and preferably an authenticated HTTPS ingress. Distinguish UI `/healthz` from API `/health/ready`.
