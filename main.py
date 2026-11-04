from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.schemas import LogRequest, FinalIncidentReport
from app.orchestrator import orchestrate_incident
from app.ui import get_dashboard_html

app = FastAPI(title="NOTIX Incident Swarm & LogPulse")

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
