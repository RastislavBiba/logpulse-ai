from app.config import query_gemini
from app.schemas import TriageResult, RootCauseResult
from app.agents.triage import extract_and_parse_json


def run_root_cause_agent(triage: TriageResult, raw_log: str) -> tuple[RootCauseResult, int, int]:
    prompt = f"""
    Si Senior Root Cause Diagnostics Specialist pre NOTIX s.r.o.
    Na základe triage analýzy presne urči príčinu incidentu a dopad na SLA.

    Triage:
    Komponent: {triage.component} ({triage.stack_category})
    Chyba: {triage.clean_error}

    Log:
    {raw_log[:1500]}

    Vráť VÝLUČNE validný JSON:
    {{
      "root_cause": "Node OOM killed kvôli preťaženiu JVM heap pamäte.",
      "sla_risk": "HIGH",
      "failure_domain": "Memory"
    }}
    """
    raw_res, _, p_tokens, o_tokens, _ = query_gemini(prompt)
    data = extract_and_parse_json(raw_res)
    return RootCauseResult(**data), p_tokens, o_tokens
