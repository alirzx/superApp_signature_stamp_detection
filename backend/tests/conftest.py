import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.inference.rfdetr import RawDetection

class FakeEngine:
    def __init__(self, settings):
        self.settings = settings
        self.ready = False
    def initialize(self):
        self.ready = True
    def predict(self, image, threshold):
        w, h = image.size
        return [RawDetection("stamp", 0.91, (w*0.2,h*0.2,w*0.4,h*0.4), 0),
                RawDetection("signature", 0.82, (w*0.5,h*0.6,w*0.9,h*0.8), 1)]

@pytest.fixture
def settings(tmp_path):
    return Settings(app_env="test", api_token="abc-123-testing-secret", model_dir=tmp_path)

@pytest.fixture
def client(settings):
    with TestClient(create_app(settings=settings, engine_factory=FakeEngine)) as app:
        yield app

@pytest.fixture
def png_bytes():
    image = Image.new("RGB", (1000, 500), "white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
