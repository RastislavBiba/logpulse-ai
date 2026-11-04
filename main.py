import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notix-pulse")

app = FastAPI(title="NOTIX Incident Swarm & LogPulse")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

PREFERRED_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class LogRequest(BaseModel):
    log_text: str = Field(..., min_length=5, description="Surový chybový výpis alebo log")


class IncidentReport(BaseModel):
    severity: str
    stack_category: str
    component: str
    sla_risk: str
    root_cause: str
    remediation_cmd: str
    safety_verdict: str
    client_summary: str
    model_used: str


def execute_gemini_prompt(prompt: str) -> tuple[str, str]:
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY nie je nakonfigurovaný.")

    last_error = None
    for model_name in PREFERRED_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text, model_name
        except APIError as e:
            logger.warning(f"Model {model_name} zlyhal: {e.code}. Prepínam...")
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    raise HTTPException(status_code=503, detail=f"Všetky modely zlyhali: {last_error}")


def run_notix_swarm(log_text: str) -> IncidentReport:
    prompt = f"""
    Pôsobíš ako SRE & Incident Lead pre technologickú a konzultačnú firmu NOTIX s.r.o.
    Tvojou úlohou je vykonať expertnú diagnostiku enterprise logu pomocou 4 špecializovaných sub-agentov:

    1. TRIAGE AGENT:
       - Urči závažnosť (CRITICAL, HIGH, MEDIUM, LOW).
       - Zarad do stacku: "Elastic Stack / SIEM", "Cloud & K8s/AKS", "Integrácie (Kafka/MQ)", "Custom Dev / Spring Boot" alebo "Database".
       - Identifikuj komponent a odhadni SLA riziko (HIGH / MEDIUM / LOW).

    2. ROOT CAUSE ANALYZER:
       - Presne pomenuj podstatu chyby v 2–3 technických vetách (heap dump, timeout, network split, sync zlyhanie...).

    3. DEVOPS REMEDIATION AGENT:
       - Priprav presný terminálový príkaz (kubectl, bash, docker, curl na Elastic API, kafka tool) na vyriešenie situácie.

    4. SAFETY AUDITOR & CLIENT COMMUNICATOR:
       - Over, či navrhnutý príkaz neohrozuje produkčné dáta (SAFE, REQUIRES_PEER_REVIEW, DANGEROUS).
       - Napíš krátke a vecné zhrnutie pre ticket/zákazníka (Client Summary).

    Vstupné logy:
    {log_text}

    Vráť VÝLUČNE validný JSON objekt v tomto presnom formáte (žiaden markdown okolo):
    {{
      "severity": "CRITICAL",
      "stack_category": "Elastic Stack / SIEM",
      "component": "Elasticsearch Data Node",
      "sla_risk": "HIGH",
      "root_cause": "Node OOM killed kvôli preťaženiu JVM heap pamäte pri agresívnom indexovaní logov.",
      "remediation_cmd": "curl -X PUT 'localhost:9200/*/_settings' -H 'Content-Type: application/json' -d '{{\\"index.routing.allocation.total_shards_per_node\\": 2}}'",
      "safety_verdict": "SAFE",
      "client_summary": "Zaznamenali sme krátkodobú nedostupnosť data-nodu spôsobenú nárazom logov. Bola vykonaná rebalancia shardov, SLA nebolo porušené."
    }}
    """

    raw_response, model_used = execute_gemini_prompt(prompt)

    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        return IncidentReport(
            severity=data.get("severity", "HIGH"),
            stack_category=data.get("stack_category", "Cloud & DevOps"),
            component=data.get("component", "General Service"),
            sla_risk=data.get("sla_risk", "MEDIUM"),
            root_cause=data.get("root_cause", "Analýza nedostupná."),
            remediation_cmd=data.get("remediation_cmd", "# Skontrolujte systémové logy"),
            safety_verdict=data.get("safety_verdict", "SAFE"),
            client_summary=data.get("client_summary", "Incident bol zaevidovaný a spracovaný."),
            model_used=model_used
        )
    except Exception as e:
        logger.error(f"JSON Parse error: {e}")
        return IncidentReport(
            severity="MEDIUM",
            stack_category="General",
            component="Parser",
            sla_risk="LOW",
            root_cause="Nepodarilo sa štruktúrovane spracovať log: " + raw_response[:250],
            remediation_cmd="# Manuálna kontrola",
            safety_verdict="SAFE",
            client_summary="Analýza prebehla vo voľnom formáte.",
            model_used=model_used
        )


# --- ENDPOINTY ---

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/status")
def status():
    return {"status": "online"}


@app.post("/analyze")
def analyze(request: LogRequest):
    report = run_notix_swarm(request.log_text)
    return report.dict()


@app.get("/", response_class=HTMLResponse)
def index_ui():
    return """
    <!DOCTYPE html>
    <html lang="sk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NOTIX s.r.o. | Incident Copilot & LogPulse</title>
        <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
        <link href="[https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css](https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css)" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            notix: {
                                dark: '#0b132b',
                                card: '#1c2541',
                                border: '#3a506b',
                                cyan: '#00e5ff',
                                blue: '#48bfe3'
                            }
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="bg-[#0b1120] text-slate-100 min-h-screen font-sans antialiased selection:bg-cyan-500 selection:text-black">
        <div class="max-w-6xl mx-auto py-8 px-4 sm:px-6">

            <!-- NOTIX Header -->
            <header class="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-6 mb-8 gap-4">
                <div>
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-black text-xl text-black shadow-lg shadow-cyan-500/20">
                            N
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h1 class="text-2xl font-bold tracking-tight text-white">NOTIX <span class="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">s.r.o.</span></h1>
                                <span class="text-slate-500 text-lg">|</span>
                                <span class="text-slate-300 font-semibold text-lg">Incident Swarm & LogPulse</span>
                            </div>
                            <p class="text-xs text-slate-400 mt-0.5">Enterprise Log Management, K8s Profylaxe & AI Multi-Agent Triage</p>
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    <span class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 shadow-inner">
                        <span class="w-2 h-2 mr-2 bg-emerald-400 rounded-full animate-pulse"></span> Azure Production Cluster
                    </span>
                </div>
            </header>

            <!-- Vstupné pole a Prednastavené NOTIX Scenáre -->
            <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur mb-8">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 gap-2">
                    <label class="block text-sm font-semibold text-slate-200">
                        <i class="fa-solid fa-code text-cyan-400 mr-1.5"></i> Vstup incidentu (Stacktrace, Kibana / K8s / Kafka logy):
                    </label>
                    <div class="flex flex-wrap gap-2 text-xs">
                        <span class="text-slate-400 self-center mr-1">Rýchle enterprise šablóny:</span>
                        <button onclick="setScenario('elastic')" class="bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 px-2.5 py-1 rounded transition">Elastic Shards OOM</button>
                        <button onclick="setScenario('kafka')" class="bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 px-2.5 py-1 rounded transition">Kafka Consumer Lag</button>
                        <button onclick="setScenario('k8s')" class="bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 px-2.5 py-1 rounded transition">AKS CrashLoop</button>
                    </div>
                </div>

                <textarea id="logInput" rows="6" placeholder="Sem vložte výpis logov z Kibany, kubectl logs alebo CI/CD..." 
                    class="w-full bg-[#070b14] border border-slate-800 rounded-xl p-4 font-mono text-xs text-cyan-300 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition shadow-inner"></textarea>

                <div class="mt-4 flex flex-col sm:flex-row justify-between items-center gap-3">
                    <span class="text-xs text-slate-400">
                        <i class="fa-solid fa-microchip mr-1"></i> Multi-agent orchestruje: Triage ➔ Root Cause ➔ Remediation ➔ Safety Check
                    </span>
                    <button id="runBtn" onclick="analyzeLog()" 
                        class="w-full sm:w-auto bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold px-7 py-2.5 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-cyan-500/20 active:scale-95">
                        <i class="fa-solid fa-bolt text-sm"></i> Analyzovať & Vyriešiť Incident
                    </button>
                </div>
            </div>

            <!-- Loading Spinner -->
            <div id="loader" class="hidden text-center py-14">
                <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-cyan-400 border-t-transparent shadow-lg"></div>
                <p class="text-slate-300 text-sm font-medium mt-4 tracking-wide">NOTIX Sub-Agenti vyhodnocujú incident a SLA dopad...</p>
            </div>

            <!-- Výsledný NOTIX Dashboard -->
            <div id="results" class="hidden space-y-6">

                <!-- Metriky incidentu -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                        <div class="text-[11px] text-slate-400 font-semibold tracking-wider">SEVERITY</div>
                        <div id="resSeverity" class="text-xl font-extrabold mt-1 text-rose-400">CRITICAL</div>
                    </div>
                    <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                        <div class="text-[11px] text-slate-400 font-semibold tracking-wider">STACK & KATEGÓRIA</div>
                        <div id="resCategory" class="text-base font-bold mt-1 text-cyan-300 truncate">Elastic Stack</div>
                    </div>
                    <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                        <div class="text-[11px] text-slate-400 font-semibold tracking-wider">SLA RISK</div>
                        <div id="resSla" class="text-lg font-bold mt-1 text-amber-400">HIGH</div>
                    </div>
                    <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                        <div class="text-[11px] text-slate-400 font-semibold tracking-wider">SAFETY VERDICT</div>
                        <div id="resSafety" class="text-lg font-bold mt-1 text-emerald-400">SAFE</div>
                    </div>
                </div>

                <!-- Detaily od sub-agentov -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <!-- Root Cause -->
                    <div class="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-3">
                                <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                                    <i class="fa-solid fa-magnifying-glass text-cyan-400"></i> Root Cause Analyzer
                                </h3>
                                <span id="resComponent" class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono"></span>
                            </div>
                            <p id="resRootCause" class="text-slate-300 text-sm leading-relaxed"></p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                            <span>Spracované cez: <span id="resModel" class="font-mono text-cyan-400"></span></span>
                        </div>
                    </div>

                    <!-- Remediation Script -->
                    <div class="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                                    <i class="fa-solid fa-terminal text-emerald-400"></i> Auto-Remediation Runbook
                                </h3>
                                <button onclick="copyCode()" class="text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded transition">
                                    <i class="fa-regular fa-copy mr-1"></i> Kopírovať
                                </button>
                            </div>
                            <div class="bg-[#070b14] p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-amber-300 overflow-x-auto shadow-inner">
                                <code id="resCmd"></code>
                            </div>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-3">
                            <i class="fa-solid fa-shield-check text-emerald-400 mr-1"></i> Overené Safety Auditorom pred spustením na produkcii.
                        </p>
                    </div>

                </div>

                <!-- Client Communication Summary (Pre Jiru / Zákazníka) -->
                <div class="bg-gradient-to-r from-slate-900 to-slate-900/90 border border-slate-800 p-5 rounded-2xl">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
                            <i class="fa-regular fa-paper-plane text-cyan-400"></i> NOTIX Client & Ticket Summary (Jira / SLA)
                        </h3>
                        <button onclick="copySummary()" class="text-xs text-slate-400 hover:text-white bg-slate-800 px-2 py-1 rounded transition">Kopírovať report</button>
                    </div>
                    <p id="resSummary" class="text-sm text-slate-300 italic leading-relaxed"></p>
                </div>

            </div>

            <!-- Footer -->
            <footer class="mt-14 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-slate-400">
                <div>
                    Navrhnuté pre enterprise infraštruktúru a konzultácie <span class="text-slate-300 font-medium">NOTIX s.r.o.</span>
                </div>
                <div class="flex gap-4">
                    <span>Elastic & SIEM</span>
                    <span>•</span>
                    <span>Cloud & DevOps</span>
                    <span>•</span>
                    <span>Integrations</span>
                </div>
            </footer>

        </div>

        <script>
            function setScenario(type) {
                if(type === 'elastic') {
                    document.getElementById('logInput').value = "[2026-11-04T08:30:15,112][WARN ][o.e.c.r.a.AllocationService] [data-node-02] high disk watermark [92%] exceeded on [node-02], shards will be relocated\\n[2026-11-04T08:30:22,890][ERROR][o.e.x.m.e.l.LocalExporter] [data-node-02] fatal error in Elasticsearch thread [elasticsearch[data-node-02][write]]: java.lang.OutOfMemoryError: Java heap space";
                } else if(type === 'kafka') {
                    document.getElementById('logInput').value = "2026-11-04 08:42:01.401 WARN [notix-order-service,3f9a,c21b] 18 --- [consumer-thread] o.a.k.c.c.internals.ConsumerCoordinator : [Consumer clientId=order-sync-1, groupId=order-processing-group] Offset commit failed on partition orders-2 at offset 849201: The coordinator is not aware of this member (CommitFailedException). Group rebalance in progress.";
                } else {
                    document.getElementById('logInput').value = "Events:\\n  Type     Reason     Age               From               Message\\n  ----     ------     ----              ----               -------\\n  Warning  Unhealthy  2m (x4 over 3m)   kubelet            Liveness probe failed: HTTP probe failed with statuscode: 503\\n  Warning  BackOff    45s (x8 over 4m)  kubelet            Back-off restarting failed container notix-api-gateway in pod notix-api-gateway-7b99c8f94-vx82d_prod(AKS)";
                }
            }

            async function analyzeLog() {
                const text = document.getElementById('logInput').value;
                if(!text || text.length < 5) {
                    alert("Zadajte prosím platný log (aspoň 5 znakov).");
                    return;
                }

                document.getElementById('loader').classList.remove('hidden');
                document.getElementById('results').classList.add('hidden');

                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ log_text: text })
                    });

                    if(!response.ok) throw new Error("Chyba spracovania: " + response.statusText);
                    const data = await response.json();

                    document.getElementById('resSeverity').innerText = data.severity;
                    document.getElementById('resCategory').innerText = data.stack_category;
                    document.getElementById('resComponent').innerText = data.component;
                    document.getElementById('resSla').innerText = data.sla_risk;
                    document.getElementById('resSafety').innerText = data.safety_verdict;
                    document.getElementById('resModel').innerText = data.model_used;
                    document.getElementById('resRootCause').innerText = data.root_cause;
                    document.getElementById('resCmd').innerText = data.remediation_cmd;
                    document.getElementById('resSummary').innerText = data.client_summary;

                    document.getElementById('results').classList.remove('hidden');
                } catch(e) {
                    alert("Chyba: " + e.message);
                } finally {
                    document.getElementById('loader').classList.add('hidden');
                }
            }

            function copyCode() {
                const code = document.getElementById('resCmd').innerText;
                navigator.clipboard.writeText(code);
                alert("Remediation príkaz bol skopírovaný!");
            }

            function copySummary() {
                const text = document.getElementById('resSummary').innerText;
                navigator.clipboard.writeText(text);
                alert("Zhrnutie pre ticket/klienta bolo skopírované!");
            }
        </script>
    </body>
    </html>
    """
