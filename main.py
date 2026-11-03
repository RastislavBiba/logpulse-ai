import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai

app = FastAPI(title="LogPulse AI")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


class LogRequest(BaseModel):
    # Test posiela "err" (3 znaky) a čaká 422, preto nastavíme min_length=5
    log_text: str = Field(..., min_length=5, description="Text logu na analýzu")


@app.get("/")
def read_root():
    # Test vyžaduje presne hodnotu "online"
    return {"status": "online"}


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
            model="gemini-2.5-flash",
            contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba pri volaní Gemini API: {str(e)}"
        )
