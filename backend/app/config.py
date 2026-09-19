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
    feature_api_max_return_rows: int = Field(default=10000, ge=1, le=50000)
    feature_engine_max_source_candles: int = Field(default=250000, ge=1, le=1000000)
    feature_api_max_indicator_specs: int = Field(default=12, ge=1, le=50)
    backtest_max_source_candles: int = Field(default=250000, ge=1, le=1000000)
    backtest_max_trades: int = Field(default=10000, ge=1, le=100000)
    enable_mt5_provider: bool = False
    enable_iqoption_experimental: bool = False
    enable_replay_provider: bool = False
    live_stale_factor: int = Field(default=2, ge=1, le=10)
    live_clock_drift_seconds: int = Field(default=30, ge=1, le=300)
    live_heartbeat_seconds: int = Field(default=15, ge=3, le=120)
    live_poll_seconds: float = Field(default=1, ge=0.1, le=30)
    replay_prefix_candles: int = Field(default=100, ge=1, le=250000)
    replay_speed: str = 'MAX'
    replay_payout: str | None = None
    mt5_broker: str = 'UNSPECIFIED'
    mt5_canonical_origin: str | None = None
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
settings = Settings()
