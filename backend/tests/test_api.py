import pytest
from fastapi.testclient import TestClient
from medinote.main import create_app


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def test_six_examples_and_no_key(client):
    examples = client.get("/api/examples").json()
    assert len(examples) == 6
    for example in examples:
        result = client.get("/api/examples/" + example["case_id"]).json()
        assert len(result["results"]) == 2
        assert all(r["fidelity_metrics"] is None for r in result["results"].values())
    assert client.get("/api/health/ready").status_code == 200
    assert client.get("/api/capabilities").json()["live_available"] is False
    assert client.get("/api/examples/main-digestif-03").status_code == 404
    assert (
        client.post(
            "/api/generate", json={"case_id": "main-digestif-03", "method": "direct"}
        ).status_code
        == 404
    )


@pytest.mark.parametrize("field", ["text", "model", "prompt"])
def test_free_parameters_rejected(client, field):
    response = client.post(
        "/api/generate", json={"case_id": "main-digestif-01", "method": "direct", field: "bad"}
    )
    assert response.status_code == 422 and response.json()["error"]["code"] == "INVALID_REQUEST"


def test_body_and_origin(client):
    assert client.post("/api/generate", content="{}").status_code == 415
    assert (
        client.post(
            "/api/generate",
            content="x" * 1025,
            headers={"Content-Type": "application/json", "Content-Length": "2"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/generate", json={}, headers={"Origin": "https://other.invalid"}
        ).status_code
        == 403
    )
    response = client.post(
        "/api/generate", json={"case_id": "main-digestif-01", "method": "direct"}
    )
    assert response.status_code == 503 and response.json()["error"]["code"] == "LIVE_DISABLED"


def test_forged_proxy_headers_do_not_enable_local_live(settings):
    settings = settings.model_copy(update={"live_enabled": True, "openai_api_key": "unused-test"})
    with TestClient(create_app(settings)) as client:
        result = client.post(
            "/api/generate",
            json={"case_id": "main-digestif-01", "method": "direct"},
            headers={
                "X-Forwarded-For": "1.2.3.4",
                "CF-Connecting-IP": "1.2.3.4",
                "X-MediNote-Client-IP": "1.2.3.4",
            },
        )
        assert (
            result.status_code == 503
            and result.json()["error"]["code"] == "CLIENT_ADDRESS_UNAVAILABLE"
        )
