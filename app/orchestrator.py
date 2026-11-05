import time
import logging
from app.schemas import (
    FinalIncidentReport,
    RootCauseResult,
    RemediationResult,
    SafetyResult,
    TriageResult,
    LLMOpsMetrics
)
from app.agents.triage import run_triage_agent
from app.agents.root_cause import run_root_cause_agent
from app.agents.remediation import run_remediation_agent
from app.agents.safety import run_safety_agent

logger = logging.getLogger("notix-orchestrator")


def orchestrate_incident(raw_log: str) -> FinalIncidentReport:
    start_total_time = time.perf_counter()

    total_prompt_tokens = 0
    total_output_tokens = 0
    calls_count = 0
    model_used = "unknown"

    # 1. Triage Agent
    try:
        triage, model_used, p_tok, o_tok = run_triage_agent(raw_log)
        total_prompt_tokens += p_tok
        total_output_tokens += o_tok
        calls_count += 1
    except Exception as e:
        logger.error(f"Triage agent zlyhal: {e}")
        triage = TriageResult(
            severity="HIGH",
            stack_category="General Infrastructure",
            component="Unknown",
            clean_error=raw_log[:150]
        )

    # 2. Root Cause Agent
    try:
        root_cause, p_tok, o_tok = run_root_cause_agent(triage, raw_log)
        total_prompt_tokens += p_tok
        total_output_tokens += o_tok
        calls_count += 1
    except Exception as e:
        logger.error(f"Root Cause Agent zlyhal: {e}")
        root_cause = RootCauseResult(
            root_cause="Automatická diagnostika príčiny zlyhala.",
            sla_risk="MEDIUM",
            failure_domain="Unknown"
        )

    # 3. Remediation Agent
    try:
        remediation, p_tok, o_tok = run_remediation_agent(triage, root_cause)
        total_prompt_tokens += p_tok
        total_output_tokens += o_tok
        calls_count += 1
    except Exception as e:
        logger.error(f"Remediation Agent zlyhal: {e}")
        remediation = RemediationResult(
            remediation_cmd="# Vyžaduje sa manuálna kontrola inžinierom NOTIX",
            runbook_steps="1. Skontrolovať systém manuálne."
        )

    # 4. Safety Guardrail
    try:
        safety, p_tok, o_tok = run_safety_agent(remediation)
        total_prompt_tokens += p_tok
        total_output_tokens += o_tok
        calls_count += 1
    except Exception as e:
        logger.error(f"Safety Agent zlyhal: {e}")
        safety = SafetyResult(
            verdict="REQUIRES_APPROVAL",
            risk_score=3,
            warning="Bezpečnostná kontrola nebola dostupná."
        )

    # 5. Client Summary
    client_summary = (
        f"Zaznamenaný incident na komponente {triage.component} ({triage.stack_category}) "
        f"so závažnosťou {triage.severity}. Príčina: {root_cause.root_cause} "
        f"Bezpečnostné overenie: {safety.verdict}."
    )

    # 6. LLMOps Výpočet (Cena a Latencia)
    total_latency = round(time.perf_counter() - start_total_time, 2)
    total_tokens = total_prompt_tokens + total_output_tokens

    # Sadzba Gemini Flash (veľmi presný odhad v USD)
    cost = (total_prompt_tokens * 0.000000075) + (total_output_tokens * 0.00000030)
    estimated_cost_usd = round(cost, 6)

    llmops = LLMOpsMetrics(
        total_prompt_tokens=total_prompt_tokens,
        total_output_tokens=total_output_tokens,
        total_tokens=total_tokens,
        total_latency_seconds=total_latency,
        estimated_cost_usd=estimated_cost_usd,
        agent_calls_count=calls_count
    )

    return FinalIncidentReport(
        severity=triage.severity,
        stack_category=triage.stack_category,
        component=triage.component,
        sla_risk=root_cause.sla_risk,
        root_cause=root_cause.root_cause,
        remediation_cmd=remediation.remediation_cmd,
        safety_verdict=safety.verdict,
        client_summary=client_summary,
        model_used=model_used,
        llmops=llmops
    )
