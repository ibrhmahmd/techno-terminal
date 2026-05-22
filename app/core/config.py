import json
import logging
import logging.handlers
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global Application Configuration Settings.
    These values are strictly typed and loaded automatically from the `.env` file.
    """
    database_url: str
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: Optional[str] = None

    twilio_account_sid: str
    twilio_auth_token: str 
    twilio_whatsapp_from: str
    gmail_sender_address: str 
    gmail_app_password: str 

    # PDF Export Configuration
    pdf_logo_path: Optional[str] = None
    pdf_company_name: str = "Techno Terminal"
    pdf_company_address: str = ""
    pdf_primary_signature: str = ""
    pdf_secondary_signature: Optional[str] = None

    # Receipt PDF Configuration (Techno Kids Techno Future)
    receipt_company_name: str = "Techno Kids Techno Future"
    receipt_company_address: str = ""  # Center address/branch location
    receipt_tax_id: Optional[str] = None  # Company tax registration number
    receipt_signature_label: str = ""
    receipt_receipt_label: str = "Payment Receipt"

    # Logging Configuration
    log_level: str = "INFO"
    slow_request_ms: int = 5000
    json_logs: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class JsonFormatter(logging.Formatter):
    """Emit log records as newline-delimited JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            payload["extra"] = record.extra
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure root logger with level, rotating file handler, and optional JSON formatter."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]

    try:
        rf = logging.handlers.RotatingFileHandler(
            "logs/api.log", maxBytes=10_485_760, backupCount=5
        )
        handlers.append(rf)
    except OSError:
        pass

    if settings.json_logs:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(levelname)s: [%(name)s] %(message)s"
        )

    for h in handlers:
        h.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )

# Instantiate identically so it acts as a global singleton 
settings = Settings()
