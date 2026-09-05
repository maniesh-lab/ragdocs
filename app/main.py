from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router

app = FastAPI(title="ragdocs")
app.include_router(router)

@app.get("/health")
def health():
    return {
        "status":"ok",
        "gemini_key_loaded": bool(settings.GEMINI_API_KEY)
    } 