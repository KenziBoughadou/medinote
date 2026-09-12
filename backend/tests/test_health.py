from fastapi.testclient import TestClient
from medinote.main import create_app


def test_liveness_without_dependencies(settings, tmp_path):
    settings = settings.model_copy(update={"root": tmp_path / "missing"})
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health/live").status_code == 200
        assert client.get("/api/health/ready").status_code == 503
