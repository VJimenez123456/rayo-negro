from pydantic_settings import BaseSettings
from pydantic import Extra


class Settings(BaseSettings):
    SHOPIFY_SECRET: str
    SHOPIFY_API_KEY: str
    SHOPIFY_API_PASSWORD: str
    SHOPIFY_STORE_URL: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    class Config:
        env_file = ".env"
        extra = Extra.allow


settings = Settings()
