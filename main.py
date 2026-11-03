import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logpulse")

app = FastAPI(title="LogPulse AI")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# 1. Štatisticky najstabilnejšie a najdostupnejšie modely pre textovú analýzu
PREFERRED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class LogRequest(BaseModel):
    log_text: str = Field(..., min_length=5, description="Text logu na analýzu")


@app.get("/")
def read_root():
    return {"status": "online"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def get_all_supported_models() -> list[str]:
    """
    Vráti zoznam preferovaných modelov a doplní ich o akékoľvek ďalšie
    aktívne modely priamo z Google API cez client.models.list().
    """
    models = list(PREFERRED_MODELS)
    if client:
        try:
            for m in client.models.list():
                # Získa čistý názov modelu (odstráni predponu 'models/')
                model_name = m.name.replace("models/", "")
                # Zaujímajú nás iba textové/analytické Gemini modely
                if "gemini" in model_name and model_name not in models:
                    models.append(model_name)
        except Exception as e:
            logger.warning(f"Nepodarilo sa načítať dynamický zoznam modelov: {e}")
    return models


def generate_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Postupne prechádza modely a použije prvý, ktorý vráti odpoveď.
    """
    candidates = get_all_supported_models()
    last_error = None

    for model_name in candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text, model_name
        except APIError as e:
            logger.warning(f"Model {model_name} zlyhal: {e.code} - {e.message}")
            last_error = e
            # Pri 503 (Unavailable), 429 (Rate limit) alebo 404 (Not found) hneď preskakujeme na ďalší
            continue
        except Exception as e:
            logger.warning(f"Model {model_name} vrátil neočakávanú chybu: {e}")
            last_error = e
            continue

    raise HTTPException(
        status_code=503,
        detail=f"Všetky modely Gemini v zozname zlyhali. Posledná chyba: {str(last_error)}",
    )


@app.post("/analyze")
def analyze_log(request: LogRequest):
    if not client:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY nie je nakonfigurovaný v prostredí.",
        )

    prompt = (
        f"Analyzuj nasledujúci log. Urči úroveň závažnosti (Severity), "
        f"príčinu chyby (Root Cause) a odporúčané riešenie (Recommended Action):\n\n"
        f"{request.log_text}"
    )

    analysis_text, model_used = generate_with_fallback(prompt)
    return {
        "analysis": analysis_text,
        "model_used": model_used
    }
