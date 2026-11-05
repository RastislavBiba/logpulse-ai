import re
from app.config import query_gemini
from app.schemas import RemediationResult, SafetyResult
from app.agents.triage import extract_and_parse_json

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"drop\s+database",
    r"truncate\s+table",
    r"mkfs",
]


def run_safety_agent(remediation: RemediationResult) -> tuple[SafetyResult, int, int]:
    cmd = remediation.remediation_cmd.lower()

    # Deterministický regex guard (0 tokenov)
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return SafetyResult(
                verdict="DANGEROUS",
                risk_score=5,
                warning=f"Zablokovaný deštruktívny vzor: {pattern}"
            ), 0, 0

    prompt = f"""
    Si Independent Security & Policy Auditor pre produkčné systémy.
    Skontroluj navrhnutý príkaz:
    {remediation.remediation_cmd}

    Vráť VÝLUČNE validný JSON:
    {{
      "verdict": "SAFE",
      "risk_score": 1,
      "warning": null
    }}
    """
    try:
        raw_res, _, p_tokens, o_tokens, _ = query_gemini(prompt)
        data = extract_and_parse_json(raw_res)
        return SafetyResult(**data), p_tokens, o_tokens
    except Exception:
        return SafetyResult(verdict="SAFE", risk_score=1, warning=None), 0, 0
