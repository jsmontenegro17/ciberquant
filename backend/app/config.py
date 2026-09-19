from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator
from typing import Literal
from urllib.parse import urlsplit


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ciberquant.db"
    jwt_secret: str = Field(default="change-me-in-development", repr=False)
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = Field(default="change-me-now", repr=False)
    environment: Literal["development", "test", "production"] = "development"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    allowed_origins: list[str] = ["http://localhost:5173"]
    https_required: bool = False
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
    iqoption_email: SecretStr = Field(default=SecretStr(""), repr=False)
    iqoption_password: SecretStr = Field(default=SecretStr(""), repr=False)
    iqoption_ssid: SecretStr = Field(default=SecretStr(""), repr=False)
    iqoption_balance: str = "PRACTICE"
    iqoption_product: str = "turbo"
    iqoption_canonical_origin: str | None = None
    iqoption_timeout_seconds: int = Field(default=15, ge=3, le=45)
    enable_replay_provider: bool = False
    live_stale_factor: int = Field(default=2, ge=1, le=10)
    live_clock_drift_seconds: int = Field(default=30, ge=1, le=300)
    live_heartbeat_seconds: int = Field(default=15, ge=3, le=120)
    live_poll_seconds: float = Field(default=1, ge=0.1, le=30)
    replay_prefix_candles: int = Field(default=100, ge=1, le=250000)
    replay_speed: str = "MAX"
    replay_payout: str | None = None
    mt5_broker: str = "UNSPECIFIED"
    mt5_canonical_origin: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    @model_validator(mode="after")
    def security_contract(self):
        if not self.allowed_origins or any("*" in origin for origin in self.allowed_origins):
            raise ValueError("Explicit credentialed CORS origins required")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                raise ValueError("Invalid origin configuration")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("SameSite none requires secure cookies")
        if self.environment == "production":
            invalid = (not self.cookie_secure or not self.https_required or len(self.jwt_secret) < 32
                       or self.jwt_secret in ("change-me-in-development", "ci-only-secret")
                       or self.seed_admin_password in ("change-me-now", "ci-only-password")
                       or len(self.seed_admin_password) < 12
                       or self.seed_admin_email == "admin@example.com"
                       or not self.database_url.startswith("postgresql")
                       or any(urlsplit(x).scheme != "https" or urlsplit(x).hostname in ("localhost", "127.0.0.1", "::1") for x in self.allowed_origins))
            if invalid:
                raise ValueError("Unsafe production configuration; review deployment security requirements")
        return self


settings = Settings()
