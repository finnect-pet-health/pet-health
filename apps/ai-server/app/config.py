from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    shared_secret: str = "dev-shared-secret"
    model_dir: str = "./models"
    device: str = "cuda"  # "cuda" / "cpu"


settings = Settings()
