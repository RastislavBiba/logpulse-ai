import re
import json
from app.config import query_gemini
from app.schemas import RemediationResult, SafetyResult
from app.agents.triage import clean_json_string

# Lokálny deterministický regex guardrail proti deštrukcii
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"drop\s+database",
    r"truncate\s+table",
    r"mkfs",
    r":\(\)\s*\{.*\}\s*;",  # fork bomb
]


def run_safety_agent(remediation: RemediationResult) -> SafetyResult:
    cmd = remediation.remediation_cmd.lower()

    # 1. Deterministická kontrola (okamžitá stopka bez volania LLM)
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return SafetyResult(
                verdict="DANGEROUS",
                risk_score=5,
                warning=f"Príkaz obsahuje zablokovaný deštruktívny vzor: {pattern}"
            )

    # 2. AI oponent na zhodnotenie prevádzkového rizika
    prompt = f"""
    Si Independent Security & Policy Auditor pre produkčné systémy.
    Skontroluj navrhnutý príkaz a posúď, či nie je prehnane riskantný.

    Navrhnutý príkaz:
    {remediation.remediation_cmd}

    Vráť VÝLUČNE validný JSON:
    {{
      "verdict": "SAFE",
      "risk_score": 1,
      "warning": null
    }}
    (Hodnoty verdict: SAFE, REQUIRES_APPROVAL, DANGEROUS)
    """
    try:
        raw_res, _ = query_gemini(prompt)
        data = json.loads(clean_json_string(raw_res))
        return SafetyResult(**data)
    except Exception:
        return SafetyResult(verdict="SAFE", risk_score=1, warning=None)
