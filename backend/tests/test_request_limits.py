"""ASGI request size limit prevents oversized bodies before multipart parsing."""
from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from conftest import FakeEngine


def test_declared_oversize_is_413(tmp_path):
    settings = Settings(app_env="test", api_token="key", model_dir=tmp_path,
                        max_upload_mb=1, max_request_bytes=1048577)
    with TestClient(create_app(settings=settings, engine_factory=FakeEngine)) as client:
        response = client.post("/v1/detect", headers={"X-API-Key": "key"},
                               files={"file": ("large.png", b"x" * 1048580, "image/png")})
        assert response.status_code == 413


def test_early_validation_releases_resources(client, png_bytes):
    headers = {"X-API-Key": "abc-123-testing-secret"}
    wrong = client.post("/v1/detect", headers=headers, files={"file": ("x.png", png_bytes)},
                        data={"document_id": " "})
    assert wrong.status_code == 422
    good = client.post("/v1/detect", headers=headers, files={"file": ("x.png", png_bytes)})
    assert good.status_code == 200


def test_invalid_request_budget(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        Settings(app_env="test", api_token="key", model_dir=tmp_path,
                 max_upload_mb=10, max_request_bytes=10*1024*1024)