import pytest
from fastapi.testclient import TestClient
from medinote.config import Settings
from medinote.main import create_app
from pydantic import ValidationError


def test_recorded_default(settings):
    assert not settings.live_enabled
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health/live").json()["status"] == "ok"


def test_live_configuration():
    with pytest.raises(ValidationError):
        Settings(live_enabled=True)
    with pytest.raises(ValidationError):
        Settings(env="production", live_enabled=True, openai_api_key="fake")
    with pytest.raises(ValidationError):
        Settings(model_id="other")
