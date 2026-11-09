from pathlib import Path
import pytest
import yaml
from app.core.config import Settings
from app.core.model_integrity import verify_model

ROOT=Path(__file__).resolve().parents[2]

def test_compose_contract():
    config=yaml.safe_load((ROOT/'docker-compose.yml').read_text())
    assert {'api','ui','model-setup'} == set(config['services'])
    assert config['services']['api']['depends_on']['model-setup']['condition']=='service_completed_successfully'
    assert '8006' in str(config['services']['api']['ports'])
    assert '8087' in str(config['services']['ui']['ports'])
    assert not (ROOT/'.gitlab-ci.yml').exists()

def test_production_requires_secret():
    with pytest.raises(ValueError): Settings(app_env='production',api_token='short')

def test_no_cached_weights_fails_closed(tmp_path):
    with pytest.raises(RuntimeError): verify_model(tmp_path)
