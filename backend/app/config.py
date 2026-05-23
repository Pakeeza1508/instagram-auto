import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MongoDB Configuration (Defaulting to localhost fallback, user overrides with Atlas link)
    MONGODB_URI: str = "mongodb://localhost:27017"
    # Optional non-SRV URI fallback for environments where DNS SRV lookups fail
    MONGODB_DIRECT_URI: str = ""
    DATABASE_NAME: str = "insta_outreach"
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 8000

    # Groq API Key for B2B Content Generation
    GROQ_API_KEY: str = ""
    # Default Groq model for content generation
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Global Safe Limits (B2B Outreach Guidelines)
    DAILY_DM_LIMIT_PER_ACCOUNT: int = 40
    DAILY_FOLLOW_LIMIT_PER_ACCOUNT: int = 50
    DAILY_LIKE_LIMIT_PER_ACCOUNT: int = 80

    # If false, backend only prepares leads and never claims real Instagram actions.
    LIVE_EXECUTION_ENABLED: bool = False
    
    # Cooldowns (in seconds) between targets
    MIN_DELAY_SECONDS: int = 180  # 3 minutes
    MAX_DELAY_SECONDS: int = 420  # 7 minutes

    # Security Config
    API_SECRET_KEY: str = "supersecretkey_change_me_in_production"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
