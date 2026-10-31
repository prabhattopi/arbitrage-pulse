from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "ArbitragePulse Agent"
    ENV: str = "development"
    MIN_PROFIT_MARGIN_PCT: float = Field(default=15.0, description="Minimum acceptable margin %")
    MAX_PRICE_DROP_PCT: float = Field(default=25.0, description="Max single price drop allowed")
    HUMAN_APPROVAL_REQUIRED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()