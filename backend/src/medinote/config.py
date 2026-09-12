from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MODEL_ID = "gpt-4.1-mini-2025-04-14"
MONTHLY_BUDGET = 10_000_000
RESERVATION = 25_000
PUBLIC_DAILY = 30
VISITOR_DAILY = 6
COOLDOWN_SECONDS = 60
LEASE_SECONDS = 75


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MEDINOTE_", extra="forbid")
    env: Literal["development", "test", "production"] = "development"
    root: Path = Path(__file__).resolve().parents[3]
    state_dir: Path = Path(".state")
    public_origin: str = "http://localhost:5173"
    build_sha: str = "development"
    model_id: Literal["gpt-4.1-mini-2025-04-14"] = MODEL_ID
    live_enabled: bool = False
    openai_api_key: SecretStr | None = Field(default=None, repr=False)
    quota_hmac_key: SecretStr | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def validate_live(self):
        if self.live_enabled and not self.openai_api_key:
            raise ValueError("Une clé propre à MediNote est requise pour le live")
        if self.live_enabled and self.env == "production":
            key = self.quota_hmac_key.get_secret_value() if self.quota_hmac_key else ""
            try:
                if len(bytes.fromhex(key)) < 32:
                    raise ValueError()
            except ValueError:
                raise ValueError("La clé HMAC doit contenir au moins 32 octets hexadécimaux")
        return self

    @property
    def db_path(self) -> Path:
        return self.state_dir / "usage.sqlite3"

    @classmethod
    def load(cls, config_file: Path | None = None):
        import os

        if os.environ.get("MEDINOTE_ENV") == "production":
            config_file = Path("/run/secrets/medinote.env")
            if not config_file.is_file():
                raise ValueError("Configuration runtime MediNote absente")
        return cls(_env_file=config_file)
