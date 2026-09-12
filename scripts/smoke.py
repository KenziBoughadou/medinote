import argparse
import json
import urllib.request

USER_AGENT = "MediNote-Healthcheck/1.0 (+https://github.com/KenziBoughadou/medinote)"


def open_public(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout)


def smoke(origin, expected_sha=None):
    for path in ["/healthz", "/api/health/ready", "/api/examples", "/"]:
        with open_public(origin.rstrip("/") + path, timeout=15) as response:
            assert response.status == 200
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", "")
            body = response.read()
            if path == "/api/examples":
                assert len(json.loads(body)) == 6
            if path == "/":
                assert b"MediNote" in body
    if expected_sha:
        with open_public(origin + "/api/health/live", timeout=10) as response:
            assert json.load(response)["version"] == expected_sha
    print("Smoke HTTPS/HTTP réussi : santé, six exemples, CSP, version")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--origin", required=True)
    p.add_argument("--sha")
    a = p.parse_args()
    smoke(a.origin, a.sha)
