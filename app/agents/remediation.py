import json
from app.config import query_gemini
from app.schemas import TriageResult, RootCauseResult, RemediationResult
from app.agents.triage import clean_json_string

def run_remediation_agent(triage: TriageResult, root_cause: RootCauseResult) -> RemediationResult:
    prompt = f"""
    Si Enterprise Remediation SRE Inžinier pre NOTIX s.r.o.
    Priprav presný terminálový príkaz (kubectl, curl na Elastic, docker, kafka tool) na vyriešenie problému.

    Komponent: {triage.component} ({triage.stack_category})
    Koreňová príčina: {root_cause.root_cause}

    Vráť VÝLUČNE validný JSON bez markdown syntaxe:
    {{
      "remediation_cmd": "curl -X PUT 'localhost:9200/*/_settings' -H 'Content-Type: application/json' -d '{{\\"index.routing.allocation.total_shards_per_node\\": 2}}'",
      "runbook_steps": "1. Dočasne obmedziť alokáciu shardov. 2. Vyvolať rebalanciu nodu."
    }}
    """
    raw_res, _ = query_gemini(prompt)
    data = json.loads(clean_json_string(raw_res))
    return RemediationResult(**data)
