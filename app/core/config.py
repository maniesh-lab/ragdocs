from pydantic_settings import BaseSettings, SettingsConfigDict  # auto-reads values from env variables


class Settings(BaseSettings):
    # Pydantic v2 style: settings for the class itself go in model_config
    # (the old `class Config:` inner class is the v1 way of doing this).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str  # has no default; the app refuses to start without it
    chroma_persist_dir: str = "data/chroma_db"
    upload_dir: str = "data/uploads"
    max_upload_mb: int = 50  # reject bigger uploads before parsing them


settings = Settings()  # every other file imports this same object instead of re-reading env vars everywhere
