from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate identically so it acts as a global singleton 
settings = Settings()
