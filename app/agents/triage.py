import json
import re
import logging
from app.config import query_gemini
from app.schemas import TriageResult

logger = logging.getLogger("notix-triage")

def extract_and_parse_json(text: str) -> dict:
    """Extrahuje a bezpečne sparsobue JSON z odpovede LLM."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Ak model pridal text pred alebo za JSON, regexom nájdeme prvý blok {...}
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Nepodarilo sa extrahovať validný JSON z textu: {text[:150]}...")

def clean_json_string(text: str) -> str:
    """Spätná kompatibilita pre importy v ostatných agentoch."""
    return json.dumps(extract_and_parse_json(text))

def run_triage_agent(raw_log: str) -> tuple[TriageResult, str]:
    prompt = f"""
    Si Triage & Classification Agent pre NOTIX s.r.o.
    Analyzuj surový log, identifikuj komponent a klasifikuj závažnosť.

    Log:
    {raw_log}

    Vráť VÝLUČNE validný JSON bez markdown syntaxe v tomto formáte:
    {{
      "severity": "CRITICAL",
      "stack_category": "Elastic Stack / SIEM",
      "component": "Elasticsearch Data Node",
      "clean_error": "java.lang.OutOfMemoryError: Java heap space"
    }}
    """
    try:
        raw_res, model = query_gemini(prompt)
        data = extract_and_parse_json(raw_res)
        return TriageResult(**data), model
    except Exception as e:
        logger.error(f"Triage agent zlyhal, použijem bezpečný fallback: {e}")
        return TriageResult(
            severity="HIGH",
            stack_category="General DevOps / Infrastructure",
            component="Unknown Service",
            clean_error=raw_log.strip().split("\n")[-1][:200]
        ), "fallback"
