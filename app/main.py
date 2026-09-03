from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="ragdocs")

@app.get("/health")
def health():
    return {
        "status":"ok",
        "groq_key_loaded": bool(settings.groq_api_key)
    } 