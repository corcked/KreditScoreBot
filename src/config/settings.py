import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Bot settings
    bot_token: str
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    bot_username: str = "KreditScoreBot"
    
    # Database
    database_url: str
    postgres_user: str = "kreditscore_user"
    postgres_password: str = "secure_password"
    postgres_db: str = "kreditscore"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    environment: str = "development"
    debug: bool = True
    secret_key: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    # Telegram
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090
    
    # Referral system
    referral_bonus_points: int = 20
    referral_link_prefix: str = "https://t.me/KreditScoreBot?start="
    
    # Loan limits (in UZS)
    microloan_max_amount: int = 100_000_000
    carloan_max_amount: int = 1_000_000_000
    
    # PDN limits (in percent)
    pdn_warning_threshold: int = 35
    pdn_danger_threshold: int = 50
    
    # Scoring
    scoring_min: int = 300
    scoring_max: int = 900
    scoring_base: int = 600
    
    # Rate limiting
    rate_limit_messages_per_minute: int = 20
    rate_limit_commands_per_minute: int = 10
    
    # Bank simulation
    bank_response_delay_minutes: int = 10
    bank_approval_probability: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.webhook_url and self.webhook_secret)

    @property
    def database_url_async(self) -> str:
        """Преобразование URL для асинхронного драйвера"""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url

    def get_webhook_path(self) -> str:
        """Получение пути для webhook"""
        if not self.webhook_secret:
            return "/webhook"
        return f"/webhook/{self.webhook_secret}"


# Singleton для настроек
settings = Settings()