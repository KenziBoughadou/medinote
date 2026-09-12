import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "live_admin", Path(__file__).resolve().parents[2] / "scripts/configure-live-admin.py"
)
admin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(admin)


def test_initialization_preserves_secret_format_and_generates_independent_hmac():
    from medinote.config import Settings

    key = "sk-project-example_" + "x" * 40
    outputs = [admin.initial_config("MEDINOTE_LIVE_ENABLED=false\n", key) for _ in range(2)]
    configs = [dict(line.split("=", 1) for line in output.splitlines()) for output in outputs]
    for config in configs:
        settings = Settings(
            env="production",
            live_enabled=True,
            openai_api_key=config["MEDINOTE_OPENAI_API_KEY"],
            quota_hmac_key=config["MEDINOTE_QUOTA_HMAC_KEY"],
        )
        assert settings.openai_api_key.get_secret_value() == key
        assert len(bytes.fromhex(settings.quota_hmac_key.get_secret_value())) == 32
    assert configs[0]["MEDINOTE_QUOTA_HMAC_KEY"] != configs[1]["MEDINOTE_QUOTA_HMAC_KEY"]


@pytest.mark.parametrize(
    "existing",
    [
        "MEDINOTE_LIVE_ENABLED=true\n",
        "MEDINOTE_LIVE_ENABLED=false\nMEDINOTE_OPENAI_API_KEY=existing-secret\n",
        "MEDINOTE_LIVE_ENABLED=false\nUNKNOWN=existing-secret\n",
    ],
)
def test_existing_configuration_cannot_be_overwritten(existing):
    with pytest.raises(ValueError) as caught:
        admin.initial_config(existing, "sk-" + "x" * 40)
    assert "existing-secret" not in str(caught.value)


@pytest.mark.parametrize("key", ["", "invalid-secret", "sk-" + "x" * 40 + "\nINJECT=true"])
def test_invalid_keys_are_rejected_without_echoing_them(key):
    with pytest.raises(ValueError, match="Format de clé incorrect"):
        admin.initial_config("MEDINOTE_LIVE_ENABLED=false\n", key)


def test_non_admin_does_not_prompt_for_key(monkeypatch, capsys):
    monkeypatch.setattr(admin.os, "geteuid", lambda: 1001)
    monkeypatch.setattr(admin.getpass, "getpass", lambda *_: pytest.fail("Unexpected key prompt"))
    assert admin.main() == 2
    assert "administrateur root" in capsys.readouterr().err


@pytest.mark.parametrize("live", ["true", "false"])
def test_rotation_preserves_hmac_and_live(live):
    original = admin.initial_config("MEDINOTE_LIVE_ENABLED=false\n", "sk-" + "a" * 40)
    original = original.replace("LIVE_ENABLED=true", f"LIVE_ENABLED={live}")
    replacement = admin.rotated_config(original, "sk-" + "b" * 40)
    before = admin.rotation_settings(original)
    after = admin.rotation_settings(replacement)
    assert after["MEDINOTE_QUOTA_HMAC_KEY"] == before["MEDINOTE_QUOTA_HMAC_KEY"]
    assert after["MEDINOTE_LIVE_ENABLED"] == live
    assert after["MEDINOTE_OPENAI_API_KEY"] == "sk-" + "b" * 40


def test_rotation_rejects_reusing_key():
    key = "sk-" + "a" * 40
    original = admin.initial_config("MEDINOTE_LIVE_ENABLED=false\n", key)
    with pytest.raises(ValueError, match="différente"):
        admin.rotated_config(original, key)


@pytest.mark.parametrize("suffix", ["UNKNOWN=private\n", "MEDINOTE_LIVE_ENABLED=false\n"])
def test_rotation_rejects_unknown_or_duplicate_fields_without_disclosure(suffix):
    original = admin.initial_config("MEDINOTE_LIVE_ENABLED=false\n", "sk-" + "a" * 40)
    with pytest.raises(ValueError, match="Configuration non reconnue"):
        admin.rotated_config(original + suffix, "sk-" + "b" * 40)
