import json
from app.config import query_gemini
from app.schemas import TriageResult

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
    raw_res, model = query_gemini(prompt)
    data = json.loads(clean_json_string(raw_res))
    return TriageResult(**data), model

def clean_json_string(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()
