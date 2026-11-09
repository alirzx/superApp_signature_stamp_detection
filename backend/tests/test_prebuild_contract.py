from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]


def test_ui_runs_without_api_ready():
    cfg=yaml.safe_load((ROOT/'docker-compose.yml').read_text())
    assert 'depends_on' not in cfg['services']['ui']
    assert 'service_completed_successfully' in str(cfg['services']['api']['depends_on'])


def test_signed_os_mirrors_configured():
    apt=(ROOT/'ops/install-debian-packages.sh').read_text()
    assert 'Signed-By:' in apt and 'https://' in apt
    front=(ROOT/'frontend/Dockerfile').read_text()
    assert 'APK_PRIMARY_MIRROR_URL' in front and 'APK_FALLBACK_MIRROR_URL' in front
    assert 'NPM_REGISTRY_URL' in front and 'NPM_FALLBACK_REGISTRY_URL' in front
    assert 'libglib2.0-0' in (ROOT/'backend/Dockerfile').read_text()


def test_env_templates_and_gitignore():
    ignores=(ROOT/'.gitignore').read_text()
    assert '.env' in ignores
    assert (ROOT/'.env.production.example').is_file()
    assert 'API_TOKEN=REPLACE_WITH_' in (ROOT/'.env.production.example').read_text()