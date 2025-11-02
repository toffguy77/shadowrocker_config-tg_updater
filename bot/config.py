from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    bot_token: str = Field(alias="BOT_TOKEN")

    github_token: str = Field(alias="GITHUB_TOKEN")
    github_owner: str = Field(default="toffguy77", alias="GITHUB_OWNER")
    github_repo: str = Field(default="shadowrocket-configuration-file", alias="GITHUB_REPO")
    github_path: str = Field(default="rules/private.list", alias="GITHUB_PATH")
    github_branch: str = Field(default="main", alias="GITHUB_BRANCH")

    allowed_users: List[int] = Field(default_factory=list, alias="ALLOWED_USERS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    metrics_addr: str = Field(default="0.0.0.0:9123", alias="METRICS_ADDR")

    @field_validator("allowed_users", mode="before")
    @classmethod
    def _parse_allowed_users(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            out: List[int] = []
            for p in parts:
                try:
                    out.append(int(p))
                except ValueError:
                    continue
            return out
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
