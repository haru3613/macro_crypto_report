"""Configuration helpers for the API service."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the service."""

    app_name: str = "Macro Crypto Report"
    report_timezone: str = "UTC"
    report_locale: str = "zh-TW"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1/responses"
    sqlite_path: str = "runtime/macro_crypto.db"
    top_n_symbols: int = 10
    short_refresh_minutes: int = 15
    long_refresh_hours: int = 24


def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        app_name=os.getenv("APP_NAME", "Macro Crypto Report"),
        report_timezone=os.getenv("REPORT_TIMEZONE", "UTC"),
        report_locale=os.getenv("REPORT_LOCALE", "zh-TW"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/responses"),
        sqlite_path=os.getenv("SQLITE_PATH", "runtime/macro_crypto.db"),
        top_n_symbols=int(os.getenv("TOP_N_SYMBOLS", "10")),
        short_refresh_minutes=int(os.getenv("SHORT_REFRESH_MINUTES", "15")),
        long_refresh_hours=int(os.getenv("LONG_REFRESH_HOURS", "24")),
    )
