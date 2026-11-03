import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

app = FastAPI(title="LogPulse AI")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Primárny a záložný model pri nedostupnosti
PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"


class LogRequest(BaseModel):
    log_text: str = Field(..., min_length=5, description="Text logu na analýzu")


@app.get("/")
def read_root():
    return {"status": "online"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def call_gemini_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Zavolá Gemini API s automatickým opakovaním pri 503 a fallbackom."""
    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

    for model_name in models_to_try:
        delay = 1.5
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except APIError as e:
                # Ak je model preťažený (503 alebo RESOURCE_EXHAUSTED), počkáme a skúsime znova
                if e.code in (503, 429) and attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                # Ak vyčerpal pokusy pre primárny model, vyskúša fallback model
                break
            except Exception:
                raise

    raise RuntimeError("Všetky modely Gemini sú momentálne preťažené. Skúste znova o chvíľu.")


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

    try:
        analysis_result = call_gemini_with_retry(prompt)
        return {"analysis": analysis_result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba pri volaní Gemini API: {str(e)}",
        )
