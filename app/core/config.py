from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    WHATSAPP_VERIFY_TOKEN: str = "dev"
    ENV: str = "dev"

    class Config:
        env_file = ".env"


settings = Settings()
