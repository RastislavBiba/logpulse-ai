import json
from app.config import query_gemini
from app.schemas import TriageResult, RootCauseResult
from app.agents.triage import clean_json_string


def run_root_cause_agent(triage: TriageResult, raw_log: str) -> RootCauseResult:
    prompt = f"""
    Si Senior Root Cause Diagnostics Specialist pre NOTIX s.r.o.
    Na základe triage analýzy presne urči príčinu incidentu a dopad na SLA.

    Triage:
    Komponent: {triage.component} ({triage.stack_category})
    Extrahovaná chyba: {triage.clean_error}

    Pôvodný log:
    {raw_log[:1500]}

    Vráť VÝLUČNE validný JSON bez markdown obalu:
    {{
      "root_cause": "Node OOM killed kvôli JVM heap pamäti pri agresívnom zápise indexov bez rebalancie.",
      "sla_risk": "HIGH",
      "failure_domain": "Memory"
    }}
    """
    raw_res, _ = query_gemini(prompt)
    data = json.loads(clean_json_string(raw_res))
    return RootCauseResult(**data)
