from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    shared_secret: str = "dev-shared-secret"  # noqa: S105
    model_dir: str = "./models"
    device: str = "cuda"  # "cuda" / "cpu"

    # mTLS — uvicorn ssl_certfile/keyfile/ca_certs 와 동일 의미. 셋이 모두 셋되면 mTLS 활성.
    ssl_certfile: str = ""
    ssl_keyfile: str = ""
    ssl_ca_certs: str = ""
    require_mtls: bool = False  # ssl_ca_certs 설정 시 cert_required 강제


settings = Settings()
