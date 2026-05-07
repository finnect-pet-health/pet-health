from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    jwt_secret: str = "dev-only-secret"  # noqa: S105
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 14

    postgres_dsn: str = "postgresql+asyncpg://petfinect:petfinect@localhost:5434/petfinect"
    redis_url: str = "redis://localhost:6382/0"
    s3_bucket: str = "petfinect-dev"
    s3_region: str = "ap-northeast-2"

    ai_server_url: str = "http://localhost:8800"
    ai_server_shared_secret: str = "dev-shared-secret"  # noqa: S105

    kakao_rest_api_key: str = ""
    kakao_native_app_key: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = ""

    caretail_client_id: str = ""
    caretail_client_secret: str = ""
    caretail_base_url: str = "https://api.caretail.example/v1"

    fatsecret_client_id: str = ""
    fatsecret_client_secret: str = ""

    data_go_kr_api_key: str = ""

    sentry_dsn: str = ""


settings = Settings()
