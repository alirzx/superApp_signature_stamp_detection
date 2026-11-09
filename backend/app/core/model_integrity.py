"""Verify the exact Wiki RF-DETR checkpoint before torch deserialization."""
import hashlib
import json
from pathlib import Path
from .config import MODEL_REPO, MODEL_REVISION, MODEL_FILENAME, MODEL_SHA256


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_model(model_dir: Path) -> dict:
    model_dir = Path(model_dir)
    path, manifest_file = model_dir / MODEL_FILENAME, model_dir / "manifest.json"
    if not path.is_file() or not manifest_file.is_file():
        raise RuntimeError("Model not prepared; run model-setup before starting API")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    expected = {"repo": MODEL_REPO, "revision": MODEL_REVISION, "filename": MODEL_FILENAME, "sha256": MODEL_SHA256}
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise RuntimeError("Model identity/manifest mismatch")
    size = path.stat().st_size
    if size < 1_000_000 or manifest.get("size_bytes") != size:
        raise RuntimeError("Model size mismatch")
    if digest(path) != MODEL_SHA256:
        raise RuntimeError("Model checksum mismatch; do not deserialize unverified checkpoint")
    return manifest
