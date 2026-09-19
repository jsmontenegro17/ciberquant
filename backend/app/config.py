from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
class Settings(BaseSettings):
    database_url: str = 'sqlite:///./ciberquant.db'
    jwt_secret: str = 'change-me-in-development'
    seed_admin_email: str = 'admin@example.com'
    seed_admin_password: str = 'change-me-now'
    market_data_max_upload_mb: int = Field(default=20, ge=1, le=100)
    market_data_max_rows: int = Field(default=100000, ge=1, le=1000000)
    market_data_max_catalog_candles: int = Field(default=250000, ge=1, le=1000000)
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
settings = Settings()
