# syntax=docker/dockerfile:1.6
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES="" TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ARG PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/
ARG TORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu
WORKDIR /srv
RUN useradd -r -u 10001 -d /srv app
COPY backend/requirements-torch-deps.txt /tmp/requirements-torch-deps.txt
COPY backend/requirements.txt /tmp/requirements.txt
# Pre-install CPU-wheel dependencies from Liara, falling back to Chabokan.
RUN --mount=type=cache,target=/root/.cache/pip \
    (python -m pip install --timeout 60 --retries 3 --index-url "$PIP_PRIMARY_INDEX_URL" -r /tmp/requirements-torch-deps.txt \
     || python -m pip install --timeout 60 --retries 3 --index-url "$PIP_FALLBACK_INDEX_URL" -r /tmp/requirements-torch-deps.txt)
# Keep exact CPU-specific Torch/Torchvision in lockstep with the source Wiki CPU profile.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --no-deps --timeout 120 --retries 3 --index-url "$TORCH_CPU_INDEX_URL" \
      'torch==2.14.0+cpu' 'torchvision==0.29.0+cpu'
RUN --mount=type=cache,target=/root/.cache/pip \
    (python -m pip install --timeout 60 --retries 3 --index-url "$PIP_PRIMARY_INDEX_URL" -r /tmp/requirements.txt \
     || python -m pip install --timeout 60 --retries 3 --index-url "$PIP_FALLBACK_INDEX_URL" -r /tmp/requirements.txt) \
    && python -m pip check \
    && python -c "import torch; assert torch.version.cuda is None; print('Verified CPU Torch',torch.__version__)"
COPY backend/app /srv/app
RUN mkdir -p /models && chown -R app:app /srv
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
