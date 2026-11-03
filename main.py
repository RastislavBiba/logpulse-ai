import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

app = FastAPI(title="LogPulse AI")

# Inicializácia Gemini klienta (automaticky načíta GEMINI_API_KEY z prostredia kontajnera)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


class LogRequest(BaseModel):
    log_text: str


@app.get("/")
def read_root():
    return {"status": "LogPulse AI is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


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
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Chyba pri volaní Gemini API: {str(e)}"
        )
