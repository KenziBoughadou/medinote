import argparse
import json
import urllib.request


def smoke(origin, expected_sha=None):
    for path in ["/healthz", "/api/health/ready", "/api/examples", "/"]:
        with urllib.request.urlopen(origin.rstrip("/") + path, timeout=15) as response:
            assert response.status == 200
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", "")
            body = response.read()
            if path == "/api/examples":
                assert len(json.loads(body)) == 6
            if path == "/":
                assert b"MediNote" in body
    if expected_sha:
        with urllib.request.urlopen(origin + "/api/health/live", timeout=10) as response:
            assert json.load(response)["version"] == expected_sha
    print("Smoke HTTPS/HTTP réussi : santé, six exemples, CSP, version")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--origin", required=True)
    p.add_argument("--sha")
    a = p.parse_args()
    smoke(a.origin, a.sha)
