import pytest
from medinote.client_identity import derive_client_key, normalize_client_ip


def test_identity():
    assert normalize_client_ip("::ffff:192.0.2.1") == "192.0.2.1"
    assert derive_client_key("ab" * 32, "2026-09-11", "::ffff:192.0.2.1") == derive_client_key(
        "ab" * 32, "2026-09-11", "192.0.2.1"
    )
    assert derive_client_key("ab" * 32, "2026-09-12", "192.0.2.1") != derive_client_key(
        "ab" * 32, "2026-09-11", "192.0.2.1"
    )
    for value in ["", "1.2.3.4,5.6.7.8", "fe80::1%eth0"]:
        with pytest.raises(ValueError):
            normalize_client_ip(value)
