from app.config import query_gemini
from app.schemas import TriageResult, RootCauseResult, RemediationResult
from app.agents.triage import extract_and_parse_json

def run_remediation_agent(triage: TriageResult, root_cause: RootCauseResult) -> tuple[RemediationResult, int, int]:
    prompt = f"""
    Si Enterprise Remediation SRE Inžinier pre NOTIX s.r.o.
    Priprav presný terminálový príkaz na vyriešenie problému.

    Komponent: {triage.component} ({triage.stack_category})
    Príčina: {root_cause.root_cause}

    Vráť VÝLUČNE validný JSON:
    {{
      "remediation_cmd": "curl -X PUT 'localhost:9200/*/_settings' -H 'Content-Type: application/json' -d '...'",
      "runbook_steps": "1. Vyvolať rebalanciu nodu."
    }}
    """
    raw_res, _, p_tokens, o_tokens, _ = query_gemini(prompt)
    data = extract_and_parse_json(raw_res)
    return RemediationResult(**data), p_tokens, o_tokens
