"""Configuration for isolated, CPU-only SuperApp signature/stamp inference."""
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MODEL_REPO = "bluecopa/rf-detr-stamp-signature-detector"
MODEL_REVISION = "c59fd4f451b254501700a56c7769f1a3d788c753"
MODEL_SHA256 = "3a831ae093be64a01a4d9c635dc6071ad7c43c3e95c3da0b33a17351df1e7909"
MODEL_FILENAME = "checkpoint_best_ema.pth"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_env: str = "development"
    api_token: str = ""
    model_dir: Path = Path("/models")
    model_repo: str = MODEL_REPO
    model_revision: str = MODEL_REVISION
    model_sha256: str = MODEL_SHA256
    model_filename: str = MODEL_FILENAME
    cpu_threads: int = Field(default=2, ge=1, le=32)
    max_concurrent_inference: int = Field(default=1, ge=1, le=4)
    max_queue_wait_seconds: float = Field(default=10, gt=0, le=120)
    max_upload_mb: int = Field(default=10, ge=1, le=50)
    max_image_pixels: int = Field(default=20_000_000, ge=1000, le=50_000_000)
    preprocess_max_long_edge: int = Field(default=2500, ge=256, le=8000)
    score_threshold: float = Field(default=0.5, ge=0.01, le=0.99)
    enable_metrics: bool = True
    max_request_bytes: int = Field(default=12 * 1024 * 1024, gt=0)

    @model_validator(mode="after")
    def validate_security(self):
        if self.max_request_bytes <= self.max_upload_mb * 1024 * 1024:
            raise ValueError("MAX_REQUEST_BYTES must exceed MAX_UPLOAD_MB to include multipart overhead")
        if self.app_env not in {"test", "development", "production"}:
            raise ValueError("APP_ENV must be test, development, or production")
        if self.app_env == "production" and len(self.api_token) < 24:
            raise ValueError("Production API_TOKEN must be at least 24 characters")
        if (self.model_repo, self.model_revision, self.model_filename, self.model_sha256) != (
            MODEL_REPO, MODEL_REVISION, MODEL_FILENAME, MODEL_SHA256
        ):
            raise ValueError("Model identity is pinned; changing it requires reviewed code/manifest update")
        return self

    @property
    def checkpoint(self):
        return self.model_dir / self.model_filename

    @property
    def manifest(self):
        return self.model_dir / "manifest.json"