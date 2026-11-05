import logging
from app.schemas import FinalIncidentReport, RootCauseResult, RemediationResult, SafetyResult
from app.agents.triage import run_triage_agent
from app.agents.root_cause import run_root_cause_agent
from app.agents.remediation import run_remediation_agent
from app.agents.safety import run_safety_agent

logger = logging.getLogger("notix-orchestrator")


def orchestrate_incident(raw_log: str) -> FinalIncidentReport:
    model_used = "unknown"

    # 1. Triage Agent
    try:
        triage, model_used = run_triage_agent(raw_log)
    except Exception as e:
        logger.error(f"Kritická chyba v Triage Agente: {e}")
        from app.schemas import TriageResult
        triage = TriageResult(
            severity="HIGH",
            stack_category="General Infrastructure",
            component="Unknown",
            clean_error=raw_log[:150]
        )

    # 2. Root Cause Agent
    try:
        root_cause = run_root_cause_agent(triage, raw_log)
    except Exception as e:
        logger.error(f"Root Cause Agent zlyhal: {e}")
        root_cause = RootCauseResult(
            root_cause="Automatická diagnostika príčiny zlyhala. Odporúča sa manuálna analýza logov.",
            sla_risk="MEDIUM",
            failure_domain="Unknown"
        )

    # 3. Remediation Agent
    try:
        remediation = run_remediation_agent(triage, root_cause)
    except Exception as e:
        logger.error(f"Remediation Agent zlyhal: {e}")
        remediation = RemediationResult(
            remediation_cmd="# Vyžaduje sa manuálna kontrola inžinierom NOTIX",
            runbook_steps="1. Skontrolovať systémové metriky a procesy manuálne."
        )

    # 4. Safety Guardrail
    try:
        safety = run_safety_agent(remediation)
    except Exception as e:
        logger.error(f"Safety Agent zlyhal: {e}")
        safety = SafetyResult(
            verdict="REQUIRES_APPROVAL",
            risk_score=3,
            warning="Automatická kontrola bezpečnosti bola nedostupná. Spustenie vyžaduje schválenie."
        )

    # 5. Client Summary
    client_summary = (
        f"Zaznamenaný incident na komponente {triage.component} ({triage.stack_category}) "
        f"so závažnosťou {triage.severity}. Príčina: {root_cause.root_cause} "
        f"Bezpečnostné overenie: {safety.verdict}."
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
    )
