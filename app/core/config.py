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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instantiate identically so it acts as a global singleton 
settings = Settings()
