from functools import lru_cache

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET = "change-me-in-env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    database_url: PostgresDsn

    # Auth (used from Phase 2 onward)
    jwt_secret: str = _DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = False  # set True behind HTTPS in production

    # App
    debug: bool = False

    @model_validator(mode="after")
    def _reject_default_secret(self) -> "Settings":
        if not self.debug and self.jwt_secret == _DEFAULT_SECRET:
            raise ValueError(
                "JWT_SECRET must be set to a real value when DEBUG is false"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
