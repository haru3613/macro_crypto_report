"""Configuration helpers for the API service."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the service."""

    app_name: str = "Macro Crypto Report"
    report_timezone: str = "UTC"
    report_locale: str = "zh-TW"
    fred_api_key: str = ""
    fmp_api_key: str = ""
    sqlite_path: str = "runtime/macro_crypto.db"
    top_n_symbols: int = 10
    short_refresh_minutes: int = 15
    long_refresh_hours: int = 24
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        app_name=os.getenv("APP_NAME", "Macro Crypto Report"),
        report_timezone=os.getenv("REPORT_TIMEZONE", "UTC"),
        report_locale=os.getenv("REPORT_LOCALE", "zh-TW"),
        fred_api_key=os.getenv("FRED_API_KEY", ""),
        fmp_api_key=os.getenv("FMP_API_KEY", ""),
        sqlite_path=os.getenv("SQLITE_PATH", "runtime/macro_crypto.db"),
        top_n_symbols=int(os.getenv("TOP_N_SYMBOLS", "10")),
        short_refresh_minutes=int(os.getenv("SHORT_REFRESH_MINUTES", "15")),
        long_refresh_hours=int(os.getenv("LONG_REFRESH_HOURS", "24")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
