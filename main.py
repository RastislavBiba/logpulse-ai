import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from app.schemas import LogRequest, FinalIncidentReport
from app.orchestrator import orchestrate_incident
from app.ui import get_dashboard_html

logger = logging.getLogger("notix-app")

app = FastAPI(
    title="NOTIX Incident Swarm & LogPulse",
    description="Enterprise Multi-Agent Incident Command Center pre NOTIX s.r.o.",
    version="2.1.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Neodchytená chyba pri spracovaní požiadavky: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Nastala neočakávaná systémová chyba pri orchestrácii incidentu.",
            "detail": str(exc)
        }
    )

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/status")
def status():
    return {"status": "online"}

@app.post("/analyze", response_model=FinalIncidentReport)
def analyze(request: LogRequest):
    return orchestrate_incident(request.log_text)

@app.get("/", response_class=HTMLResponse)
def index():
    return get_dashboard_html()
