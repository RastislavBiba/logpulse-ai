import os
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="LogPulse AI",
    description="DevOps mikroslužba na analýzu logov s pomocou umelej inteligencie",
    version="1.0.0"
)

# Konfigurácia cez systémové premenné (ideálne pre Docker a cloud)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
AI_MODEL = os.getenv("AI_MODEL", "llama3")


# Dátové schémy (Pydantic v2 kompatibilné – použité 'examples' namiesto 'example')
class LogAnalysisRequest(BaseModel):
    log_text: str = Field(
        ...,
        min_length=5,
        examples=["Error: connect ECONNREFUSED 127.0.0.1:5432 at TCPConnectWrap.afterConnect"]
    )


class LogAnalysisResponse(BaseModel):
    severity: str = Field(..., examples=["Critical"])
    root_cause: str = Field(..., examples=["Služba sa nevie pripojiť k lokálnej databáze PostgreSQL."])
    fix_suggestion: str = Field(..., examples=["Skontroluj, či PostgreSQL kontajner beží na porte 5432: docker ps"])
    raw_response: str | None = None


# Systémový prompt navrhnutý pre DevOps analýzu
SYSTEM_PROMPT = """
Si expert na DevOps, kontajnery (Docker/Kubernetes) a systémové logy.
Analyzuj nasledujúci log a vráť odpoveď VÝHRADNE ako platný JSON formát bez Markdown značiek (žiadne ```json):
{
  "severity": "Low" | "Medium" | "Critical",
  "root_cause": "stručné zhrnutie problému v 1-2 vetách (slovensky)",
  "fix_suggestion": "presný krok alebo príkaz na vyriešenie (slovensky)"
}
"""


@app.get("/")
def read_root():
    """Základný stav služby."""
    return {
        "status": "online",
        "service": "LogPulse AI",
        "model": AI_MODEL
    }


@app.get("/health")
def health_check():
    """Health check pre Docker a CI/CD pipelines."""
    return {"status": "healthy"}


@app.post("/analyze", response_model=LogAnalysisResponse)
def analyze_log(payload: LogAnalysisRequest):
    """
    Prijme chybový log, pošle ho do AI enginu a vráti štruktúrovanú analýzu.
    """
    full_prompt = f"{SYSTEM_PROMPT}\n\nLOG NA ANALÝZU:\n{payload.log_text}"

    request_body = {
        "model": AI_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": "json"  # Vynúti validný JSON výstup z Ollamy
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=request_body,
            timeout=45.0
        )
        response.raise_for_status()
        result = response.json()

        # Ollama vracia text v poli 'response'
        ai_output_raw = result.get("response", "{}")
        parsed_data = json.loads(ai_output_raw)

        return LogAnalysisResponse(
            severity=parsed_data.get("severity", "Medium"),
            root_cause=parsed_data.get("root_cause", "Nepodarilo sa určiť príčinu."),
            fix_suggestion=parsed_data.get("fix_suggestion", "Skontrolujte celkový stav služieb."),
            raw_response=ai_output_raw
        )

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=f"AI engine je nedostupný na adrese {OLLAMA_URL}. Uisti sa, že ti beží Ollama."
        )
    except json.JSONDecodeError:
        # Záložné spracovanie, ak model nevráti dokonale čistý JSON
        return LogAnalysisResponse(
            severity="Unknown",
            root_cause="Model vrátil neštruktúrovaný text.",
            fix_suggestion="Skontrolujte logy manuálne.",
            raw_response=ai_output_raw if 'ai_output_raw' in locals() else ""
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interná chyba pri analýze: {str(e)}"
        )


# Umožní priame spustenie cez zelené tlačidlo "Run" v IDE
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
