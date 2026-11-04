import logging
from app.schemas import FinalIncidentReport
from app.agents.triage import run_triage_agent
from app.agents.root_cause import run_root_cause_agent
from app.agents.remediation import run_remediation_agent
from app.agents.safety import run_safety_agent

logger = logging.getLogger("notix-orchestrator")


def orchestrate_incident(raw_log: str) -> FinalIncidentReport:
    # 1. Triage
    triage, model_used = run_triage_agent(raw_log)

    # 2. Root Cause
    root_cause = run_root_cause_agent(triage, raw_log)

    # 3. Remediation
    remediation = run_remediation_agent(triage, root_cause)

    # 4. Safety Guardrail
    safety = run_safety_agent(remediation)

    # 5. Client Summary
    client_summary = (
        f"Zaznamenaný incident na komponente {triage.component} ({triage.stack_category}) "
        f"so závažnosťou {triage.severity}. Príčina: {root_cause.root_cause} "
        f"Navrhnuté opatrenie bolo overené Safety filtrom s výsledkom {safety.verdict}."
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
