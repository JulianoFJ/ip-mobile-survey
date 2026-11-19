"""Configuração por ambiente (pydantic-settings + .env)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, lida de variáveis `IPS_*` e do arquivo `.env`."""

    model_config = SettingsConfigDict(env_prefix="IPS_", env_file=".env", extra="ignore")

    env: Literal["local", "dev", "prod", "test"] = "local"
    log_level: str = "INFO"
    log_json: bool = False

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ipsurvey"
    db_user: str = "ipsurvey"
    db_password: SecretStr = SecretStr("ipsurvey")

    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_bucket: str = "ipsurvey"
    s3_access_key: SecretStr = SecretStr("minioadmin")
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_region: str = "sa-east-1"

    storage_crs: str = "EPSG:4674"
    processing_crs: str = "EPSG:31983"

    mapillary_token: SecretStr | None = None

    @property
    def database_url(self) -> str:
        """URL SQLAlchemy (driver psycopg) montada a partir dos campos `db_*`."""
        pwd = self.db_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única de configuração."""
    return Settings()
