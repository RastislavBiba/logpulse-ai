from pydantic import BaseModel, Field

class LogRequest(BaseModel):
    log_text: str = Field(..., min_length=5, description="Surový chybový výpis alebo log")

class TriageResult(BaseModel):
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    stack_category: str = Field(description="Kategória stacku (napr. Elastic Stack, K8s/AKS, Kafka, Database)")
    component: str = Field(description="Presný komponent, napr. Elasticsearch Data Node, Pod, Broker")
    clean_error: str = Field(description="Kľúčový extrahovaný error reťazec")

class RootCauseResult(BaseModel):
    root_cause: str = Field(description="Technické vysvetlenie príčiny v 2-3 vetách")
    sla_risk: str = Field(description="Odhad dopadu na SLA (HIGH, MEDIUM, LOW)")
    failure_domain: str = Field(description="Oblasť zlyhania, napr. Memory, Network, Concurrency")

class RemediationResult(BaseModel):
    remediation_cmd: str = Field(description="Presný terminálový príkaz na opravu")
    runbook_steps: str = Field(description="Stručný postup realizácie opravy")

class SafetyResult(BaseModel):
    verdict: str = Field(description="SAFE, REQUIRES_APPROVAL, DANGEROUS")
    risk_score: int = Field(description="Skóre rizika od 1 (bezpečné) po 5 (deštruktívne)")
    warning: str | None = Field(default=None, description="Varovanie v prípade rizika")

class FinalIncidentReport(BaseModel):
    severity: str
    stack_category: str
    component: str
    sla_risk: str
    root_cause: str
    remediation_cmd: str
    safety_verdict: str
    client_summary: str
    model_used: str
