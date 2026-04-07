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

    # PDF Export Configuration
    pdf_logo_path: Optional[str] = None
    pdf_company_name: str = "Techno Terminal"
    pdf_company_address: str = ""
    pdf_primary_signature: str = "Financial Manager"
    pdf_secondary_signature: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate identically so it acts as a global singleton 
settings = Settings()
