"""One-shot, checksum-gated Hugging Face bootstrap (not an API runtime dependency)."""
import argparse
import json
import os
from pathlib import Path
from shutil import copyfile
from app.core.config import MODEL_REPO, MODEL_REVISION, MODEL_FILENAME, MODEL_SHA256
from app.core.model_integrity import digest, verify_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    dest = Path(os.environ.get("MODEL_DIR", "/models"))
    dest.mkdir(parents=True, exist_ok=True)
    try:
        manifest = verify_model(dest)
        print(f"Verified cached model {manifest['revision']} ({manifest['size_bytes']} bytes)")
        return
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        if args.verify_only:
            raise SystemExit(f"Model verification failed: {exc}") from exc

    from huggingface_hub import hf_hub_download
    # Never use floating 'main': this version is pinned to the Wiki source revision.
    downloaded = Path(hf_hub_download(
        repo_id=MODEL_REPO, filename=MODEL_FILENAME, revision=MODEL_REVISION,
        cache_dir=str(dest / ".hf-cache"),
    ))
    if digest(downloaded) != MODEL_SHA256:
        raise RuntimeError("Downloaded checkpoint SHA256 differs from verified Hugging Face LFS digest")
    target = dest / MODEL_FILENAME
    temporary = dest / (MODEL_FILENAME + ".tmp")
    copyfile(downloaded, temporary)
    if digest(temporary) != MODEL_SHA256:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("Staged checkpoint checksum mismatch")
    os.replace(temporary, target)
    manifest = {"repo": MODEL_REPO, "revision": MODEL_REVISION, "filename": MODEL_FILENAME,
                "sha256": MODEL_SHA256, "size_bytes": target.stat().st_size}
    temp_manifest = dest / "manifest.json.tmp"
    temp_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_manifest, dest / "manifest.json")
    verify_model(dest)
    print("Model prepared and SHA256 verified")


if __name__ == "__main__":
    main()
