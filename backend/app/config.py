from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str = 'sqlite:///./ciberquant.db'
    jwt_secret: str = 'change-me-in-development'
    seed_admin_email: str = 'admin@example.com'
    seed_admin_password: str = 'change-me-now'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
settings = Settings()
