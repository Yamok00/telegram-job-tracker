from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Optional

class Settings(BaseSettings):
    google_client_id: str = "your_client_id_here"
    google_client_secret: str = "your_client_secret_here"
    google_token_json: Optional[str] = None
    
    gemini_api_key: str = "your_gemini_api_key_here"
    
    telegram_bot_token: str = "your_telegram_bot_token_here"
    user_telegram_chat_id: str = "your_chat_id_here"
    
    database_url: str = "sqlite:///./job_tracker.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
