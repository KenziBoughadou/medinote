from pathlib import Path

import yaml


def check_deployment_config(root):
    config = yaml.safe_load((root / "deploy/compose.production.yml").read_text())
    services = config["services"]
    assert set(services) == {"frontend", "api"}
    assert config["networks"]["public"] == {"external": True, "name": "web"}
    assert not config["networks"]["private"].get("internal", False)
    for name, uid, limit in [("api", "10001:10001", "512m"), ("frontend", "101:101", "128m")]:
        service = services[name]
        assert "ports" not in service and "build" not in service
        assert service["user"] == uid and service["read_only"]
        assert service["mem_limit"] == limit and service["memswap_limit"] == limit
        assert service["cap_drop"] == ["ALL"] and service["security_opt"] == [
            "no-new-privileges:true"
        ]
        assert service["logging"]["options"] == {"max-size": "5m", "max-file": "2"}
    assert set(services["api"]["networks"]) == {"private"}
    assert set(services["frontend"]["networks"]) == {"public", "private"}
    secret = services["api"]["volumes"][1]
    assert secret["read_only"] and secret["bind"]["create_host_path"] is False
    assert (
        secret["source"] == "/opt/secrets/medinote.env"
        and secret["target"] == "/run/secrets/medinote.env"
    )
    assert "env_file" not in services["api"]
    assert services["api"]["labels"]["traefik.enable"] == "false"
    assert services["frontend"]["labels"]["traefik.docker.network"] == "web"
    nginx = (root / "frontend/nginx.conf").read_text()
    assert (
        "resolver 127.0.0.11" in nginx
        and "proxy_set_header X-MediNote-Client-IP $http_cf_connecting_ip;" in nginx
    )
    assert "proxy_read_timeout 65s" in nginx and "Content-Security-Policy" in nginx
    assert "--no-proxy-headers" in (root / "backend/Dockerfile").read_text()
    return True


def main():
    check_deployment_config(Path(__file__).resolve().parents[1])
    print("Configuration de déploiement conforme")


if __name__ == "__main__":
    main()
