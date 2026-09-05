from pydantic_settings import BaseSettings  #auto-reads values from env variables

class Settings(BaseSettings):
    GEMINI_API_KEY: str  # has no defaults; crashes out if there's no value
    chroma_persist_dir: str = "data/chroma_db" # has default
    upload_dir: str = "data/uploads"

    class Config:
        env_file = ".env"


settings = Settings() #every other file in the app imports this same object instead of re-reading env vars everywhere