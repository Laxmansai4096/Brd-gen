import datetime
from typing import List, Dict, Any, Optional
from backend.models import (
    RequirementItem, CapabilityItem, DataFlowItem, CalculationLedgerItem,
    HITLGates, TaskEstimate, RoleEffort, ScheduleFeasibility, SizingBOM
)

def build_canonical_requirements(
    client_name: str,
    project_title: str,
    delivery_tier: str,
    domain: str,
    cloud_platform: str,
    geography: str,
    compliance_posture: str
) -> List[RequirementItem]:
    """
    Builds the 17 Canonical Requirements per Section 8 & 9 of reference.txt.
    Covers Functional, Non-functional, Business, Technical, Data, Integration,
    Security, Compliance, AI, Responsible AI, Operational, Deployment, Reporting,
    UX, Availability, Performance, and DR.
    """
    reqs: List[RequirementItem] = [
        RequirementItem(
            requirement_id="FR-001",
            type="FUNCTIONAL",
            statement=f"The solution must ingest, classify, and extract structured business attributes for {project_title} with 100% field provenance.",
            actor="Solution Engine",
            capability="CAP-DATA-INGEST",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Ingests all supported digital formats", "Extracts key attributes with confidence score > 85%"],
            dependencies=[],
            impacts=["Data Pipeline", "WBS Phase P06"]
        ),
        RequirementItem(
            requirement_id="FR-002",
            type="FUNCTIONAL",
            statement="The solution must evaluate extracted data against configured business ontology principles to produce multi-tier status recommendations.",
            actor="AI Reasoning Engine",
            capability="CAP-AI-EVAL",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Produces 3-tier outcome (Agree, Agree with Mgmt, Not Agree)", "Generates grounded explanatory rationale"],
            dependencies=["FR-001"],
            impacts=["AI Orchestration", "WBS Phase P08"]
        ),
        RequirementItem(
            requirement_id="NFR-001",
            type="NON_FUNCTIONAL",
            statement="System must deliver sub-2.5 second conversational inference latency and process batch document workloads predictably without memory leaks.",
            actor="Platform Infrastructure",
            capability="CAP-PLAT-PERF",
            priority="MUST",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["P95 latency < 2.5s", "Batch processing handles burst requests without degradation"],
            dependencies=[],
            impacts=["Infrastructure", "WBS Phase P15"]
        ),
        RequirementItem(
            requirement_id="BUS-001",
            type="BUSINESS",
            statement=f"Eliminate manual operational bottlenecks for {client_name}, reducing end-to-end processing turnaround time by at least 60%.",
            actor="Business Stakeholders",
            capability="CAP-BIZ-WORKFLOW",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Executive dashboard tracks time savings", "Review queue throughput doubles"],
            dependencies=[],
            impacts=["Business Operations", "WBS Phase P02"]
        ),
        RequirementItem(
            requirement_id="TECH-001",
            type="TECHNICAL",
            statement=f"The architecture must be deployed on {cloud_platform} utilizing native cloud services, serverless execution, and containerized microservices.",
            actor="Lead Solutions Architect",
            capability="CAP-PLAT-CLOUD",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=[f"Hosted in {cloud_platform}", "All components use infrastructure as code templates"],
            dependencies=[],
            impacts=["Architecture", "WBS Phase P04"]
        ),
        RequirementItem(
            requirement_id="DATA-001",
            type="DATA",
            statement="Document text chunks, layout bounding boxes, and embeddings must be stored with parent document metadata for 100% auditability.",
            actor="Data Engineer",
            capability="CAP-DATA-PERSIST",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Every finding links to exact source page and coordinates", "Zero ungrounded hallucinations"],
            dependencies=["FR-001"],
            impacts=["Data Architecture", "WBS Phase P06"]
        ),
        RequirementItem(
            requirement_id="INT-001",
            type="INTEGRATION",
            statement="Authenticate all user interactions through corporate Enterprise Single Sign-On (SSO / OAuth 2.0 / SAML).",
            actor="Security Engineer",
            capability="CAP-APP-AUTH",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Users authenticate via corporate IdP", "RBAC roles restrict admin functions"],
            dependencies=[],
            impacts=["Security Architecture", "WBS Phase P10"]
        ),
        RequirementItem(
            requirement_id="SEC-001",
            type="SECURITY",
            statement="All data at rest must use AES-256 platform-managed encryption; in-transit traffic must enforce TLS 1.3 with secret-less service identities.",
            actor="Security Officer",
            capability="CAP-PLAT-SEC",
            priority="MUST",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["TLS 1.3 enforced on all endpoints", "Managed identities used between cloud services"],
            dependencies=[],
            impacts=["Cloud Foundation", "WBS Phase P05"]
        ),
        RequirementItem(
            requirement_id="COMP-001",
            type="COMPLIANCE",
            statement=f"Strict compliance with regional data residency guidelines in {geography} with zero external cross-border data leakage.",
            actor="Compliance Lead",
            capability="CAP-PLAT-COMP",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=[f"All storage & compute located in {geography}", "Compliance audit logging enabled"],
            dependencies=[],
            impacts=["Governance", "WBS Phase P12"]
        ),
        RequirementItem(
            requirement_id="AI-001",
            type="AI",
            statement="Foundation models must use deterministic temperature controls (<= 0.2), schema-enforced JSON outputs, and hybrid semantic retrieval.",
            actor="AI Engineer",
            capability="CAP-AI-MODEL",
            priority="MUST",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["Zero JSON schema validation failures", "Retrieval combines keyword and vector embeddings"],
            dependencies=[],
            impacts=["AI Modeling", "WBS Phase P08"]
        ),
        RequirementItem(
            requirement_id="RAI-001",
            type="RESPONSIBLE_AI",
            statement="Human-in-the-loop oversight is mandatory; AI serves as an assistive copilot and cannot commit autonomous binding approvals without human review.",
            actor="Responsible AI Officer",
            capability="CAP-AI-GOVERN",
            priority="MUST",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["High-impact decisions require HITL sign-off", "Confidence scores displayed on all recommendations"],
            dependencies=["AI-001"],
            impacts=["Governance", "WBS Phase P12"]
        ),
        RequirementItem(
            requirement_id="OPS-001",
            type="OPERATIONAL",
            statement="Unhandled document formats, low-confidence extractions, or model timeouts must route to an exceptions queue without pipeline crash.",
            actor="Operations Team",
            capability="CAP-APP-OPS",
            priority="SHOULD",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["Dead-letter queue captures failed files", "Exception queue visible in admin cockpit"],
            dependencies=[],
            impacts=["Operations", "WBS Phase P14"]
        ),
        RequirementItem(
            requirement_id="DEP-001",
            type="DEPLOYMENT",
            statement="Support automated infrastructure provisioning and code deployment across Dev, Test, and UAT non-production environments.",
            actor="DevOps / SRE",
            capability="CAP-PLAT-DEPLOY",
            priority="SHOULD",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["Environments isolated in dedicated resource groups", "Automated deployment scripts tested"],
            dependencies=[],
            impacts=["MLOps / IaC", "WBS Phase P13"]
        ),
        RequirementItem(
            requirement_id="REP-001",
            type="REPORTING",
            statement="Provide real-time visibility and exportable reports (DOCX, PDF, PPTX, CSV) for audit compliance and management reviews.",
            actor="Business Analyst",
            capability="CAP-BIZ-REPORT",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["1-click DOCX, PDF, and PPTX export", "Export accurately reflects approved canonical data"],
            dependencies=[],
            impacts=["Document Generation", "WBS Phase P17"]
        ),
        RequirementItem(
            requirement_id="UX-001",
            type="UX",
            statement="Interactive, responsive web workbench with multi-tab navigation, live Gantt chart, role-loading breakdown, and admin controls.",
            actor="Frontend UX Engineer",
            capability="CAP-APP-UX",
            priority="MUST",
            source="CLIENT",
            status="CLIENT_CONFIRMED",
            acceptance_criteria=["Responsive across desktop resolutions", "Zero layout shift during live chat"],
            dependencies=[],
            impacts=["Application Frontend", "WBS Phase P10"]
        ),
        RequirementItem(
            requirement_id="AVAIL-001",
            type="AVAILABILITY",
            statement=f"Service availability targeted per delivery tier: single-instance for PoC; zone-redundant high availability for MVP/Production.",
            actor="SRE / Cloud Architect",
            capability="CAP-PLAT-HA",
            priority="SHOULD",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["Meets delivery tier uptime target", "Automated health check endpoints active"],
            dependencies=[],
            impacts=["Infrastructure", "WBS Phase P05"]
        ),
        RequirementItem(
            requirement_id="DR-001",
            type="DR",
            statement="Batch processing states must checkpoint intermediate progress so that transient disruptions allow resumption from the last processed record.",
            actor="Data / SRE Engineer",
            capability="CAP-PLAT-DR",
            priority="SHOULD",
            source="DEFAULT",
            status="DEFAULT",
            acceptance_criteria=["Batch jobs restart from last successful chunk", "Zero duplicate writes to findings store"],
            dependencies=["DATA-001"],
            impacts=["Resilience", "WBS Phase P14"]
        )
    ]
    return reqs

def build_capabilities_catalog(domain: str, cloud_platform: str) -> List[CapabilityItem]:
    """
    Builds the Reusable Capability Catalog per Section 12 & 13 of reference.txt.
    Categories: Business, Application, Data, AI, Platform.
    Scope Status: IN_SCOPE, OUT_OF_SCOPE, FUTURE, CONDITIONAL.
    """
    return [
        CapabilityItem(
            capability_id="CAP-BIZ-WORKFLOW",
            category="Business",
            name="Workflow & Decision Orchestration",
            description="Manages state transitions, reviews, and decision routing across business processes.",
            scope_status="IN_SCOPE",
            architecture_components=["C001", "C006"],
            applicable_wbs_tasks=["T002", "T005"]
        ),
        CapabilityItem(
            capability_id="CAP-BIZ-APPROVAL",
            category="Business",
            name="Automated Enterprise Approval Routing",
            description="End-to-end multi-tier corporate sign-off routing into live ERP/Procurement systems.",
            scope_status="OUT_OF_SCOPE",
            architecture_components=[],
            applicable_wbs_tasks=[]
        ),
        CapabilityItem(
            capability_id="CAP-BIZ-REPORT",
            category="Business",
            name="Executive Dashboards & Document Exports",
            description="Surfaces analytics, risk metrics, and multi-format document generation (DOCX, PDF, PPTX).",
            scope_status="IN_SCOPE",
            architecture_components=["C005", "C006"],
            applicable_wbs_tasks=["T017", "T018"]
        ),
        CapabilityItem(
            capability_id="CAP-APP-UX",
            category="Application",
            name="Interactive Discovery & Estimation Workbench",
            description="Web-based responsive UI with real-time AI chat, Gantt scheduling, and admin configuration.",
            scope_status="IN_SCOPE",
            architecture_components=["C006"],
            applicable_wbs_tasks=["T010", "T015"]
        ),
        CapabilityItem(
            capability_id="CAP-APP-AUTH",
            category="Application",
            name="Enterprise SSO & Identity Access",
            description="Single Sign-On authentication and Role-Based Access Control integration.",
            scope_status="IN_SCOPE",
            architecture_components=["C006"],
            applicable_wbs_tasks=["T010"]
        ),
        CapabilityItem(
            capability_id="CAP-DATA-INGEST",
            category="Data",
            name="Multi-Format Document Ingestion",
            description="Cloud blob intake and layout-aware text extraction with coordinate bounding boxes.",
            scope_status="IN_SCOPE",
            architecture_components=["C001", "C002"],
            applicable_wbs_tasks=["T003", "T006"]
        ),
        CapabilityItem(
            capability_id="CAP-DATA-PERSIST",
            category="Data",
            name="Hybrid Search Index & Structured Storage",
            description="Persistent storage for vector embeddings, keyword indexes, and structured finding registers.",
            scope_status="IN_SCOPE",
            architecture_components=["C004"],
            applicable_wbs_tasks=["T007"]
        ),
        CapabilityItem(
            capability_id="CAP-AI-MODEL",
            category="AI",
            name="Agentic Multi-Pass LLM Extraction & Reasoning",
            description="Cloud foundation model invocation with multi-pass schema validation and deterministic parameters.",
            scope_status="IN_SCOPE",
            architecture_components=["C003"],
            applicable_wbs_tasks=["T008", "T009"]
        ),
        CapabilityItem(
            capability_id="CAP-AI-GOVERN",
            category="AI",
            name="Responsible AI & Grounding Guardrails",
            description="Hallucination verification, content safety filtering, and human-in-the-loop oversight.",
            scope_status="IN_SCOPE",
            architecture_components=["C003", "C005"],
            applicable_wbs_tasks=["T012"]
        ),
        CapabilityItem(
            capability_id="CAP-AI-FINETUNE",
            category="AI",
            name="Custom Model Pretraining & Deep Fine-Tuning",
            description="Training custom open-weights foundation models from scratch on client private corpus.",
            scope_status="OUT_OF_SCOPE",
            architecture_components=[],
            applicable_wbs_tasks=[]
        ),
        CapabilityItem(
            capability_id="CAP-PLAT-CLOUD",
            category="Platform",
            name="Cloud Landing Zone & Managed Foundation",
            description=f"Isolated non-production resource group and cloud networking on {cloud_platform}.",
            scope_status="IN_SCOPE",
            architecture_components=["C001", "C006"],
            applicable_wbs_tasks=["T005", "T013"]
        ),
        CapabilityItem(
            capability_id="CAP-PLAT-HA",
            category="Platform",
            name="Multi-Region Active-Active DR Replication",
            description="Real-time geo-replication with automated cross-region DNS failover.",
            scope_status="FUTURE",
            architecture_components=[],
            applicable_wbs_tasks=[]
        )
    ]

def build_canonical_data_flows(domain: str, cloud_platform: str) -> List[DataFlowItem]:
    """
    Builds the structured End-to-End Data Flows per Section 15 of reference.txt.
    """
    return [
        DataFlowItem(
            flow_id="DF-001",
            name="Document & Raw Data Intake",
            source="Client Authorized Cloud Storage / User Upload",
            target="Ingestion & Extraction Service (C001)",
            data_objects=["Raw PDF/Word documents", "Document metadata manifest"],
            protocol="HTTPS / Cloud SDK",
            frequency="On-Demand / Batch",
            volume={"daily_files": 100, "avg_file_size_mb": 2.5},
            security={"encryption": "TLS 1.3 / AES-256", "auth": "Cloud Managed Identity"},
            transformation=["File validation", "MIME type verification", "Virus scan"],
            failure_handling="Quarantine container, dead-letter queue, and notification alert"
        ),
        DataFlowItem(
            flow_id="DF-002",
            name="Layout-Aware Parsing & Chunking",
            source="Ingestion Service (C001)",
            target="Document Intelligence & Vector Store (C002 & C004)",
            data_objects=["Layout text tokens", "Page coordinates", "Bounding boxes", "Vector embeddings"],
            protocol="Internal Microservice API / gRPC",
            frequency="Event-Driven per file",
            volume={"chunks_per_doc": 40, "vector_dim": 1536},
            security={"encryption": "Private Cloud VNet", "auth": "Token-based IAM"},
            transformation=["Section boundary chunking", "Embedding generation", "Metadata tagging"],
            failure_handling="Retry with exponential backoff; fallback to OCR plain text"
        ),
        DataFlowItem(
            flow_id="DF-003",
            name="Agentic Reasoning & Principle Evaluation",
            source="Vector Store (C004) & Ontology Rules",
            target="Multi-Cloud LLM Gateway & Reasoning Engine (C003)",
            data_objects=["Retrieved context chunks", "Principle guidelines", "Prompt schema"],
            protocol="HTTPS / REST API",
            frequency="Real-Time / Multi-Pass",
            volume={"avg_input_tokens": 1200, "avg_output_tokens": 600},
            security={"encryption": "TLS 1.3", "auth": "Server-side API Key / SigV4"},
            transformation=["Prompt template hydration", "Schema enforcement", "Temperature bounding"],
            failure_handling="Fallback to targeted pass 2 or route to human exception queue"
        ),
        DataFlowItem(
            flow_id="DF-004",
            name="Structured Finding Persistence & Presentation",
            source="Reasoning Engine (C003)",
            target="Findings Database & Web Cockpit (C005 & C006)",
            data_objects=["Risk register entries", "Agree/Not-Agree status", "Citation links"],
            protocol="PostgreSQL / HTTPS REST",
            frequency="Continuous persistence",
            volume={"records_per_doc": 25},
            security={"encryption": "Encrypted at rest (TDE)", "auth": "Enterprise SSO"},
            transformation=["Format normalization", "Export serialization (DOCX/PDF/PPTX)"],
            failure_handling="Transactional rollback and audit log warning"
        )
    ]

def build_calculation_ledger(
    tier_name: str,
    task_estimates: List[TaskEstimate],
    role_efforts: List[RoleEffort],
    feasibility: ScheduleFeasibility,
    sizing_bom: List[SizingBOM],
    hourly_rate: float
) -> List[CalculationLedgerItem]:
    """
    Builds the Calculation Ledger per Section 54 of reference.txt.
    Logs every calculation with formula, inputs, results, and timestamp.
    """
    ts = datetime.datetime.now().isoformat()
    total_days = round(sum(r.days for r in role_efforts), 2)
    total_hours = round(sum(r.hours for r in role_efforts), 1)
    total_cost = round(sum(r.cost for r in role_efforts), 2)
    monthly_bom = round(sum(b.monthly_cost_usd for b in sizing_bom), 2)

    ledger: List[CalculationLedgerItem] = [
        CalculationLedgerItem(
            calculation_id="CALC-001",
            calculation_type="DELIVERY_TIER_RIGOUR",
            inputs={"delivery_tier": tier_name},
            formula="PhaseEffort = BaseDays * PhaseRigour[phase, tier]",
            result={"applied_tier": tier_name, "total_tasks_estimated": len(task_estimates)},
            engine_version="1.0.0",
            timestamp=ts
        ),
        CalculationLedgerItem(
            calculation_id="CALC-002",
            calculation_type="TASK_EFFORT_DETERMINISTIC",
            inputs={"hourly_rate": hourly_rate, "tasks_count": len(task_estimates)},
            formula="E_task = BaseDays * PhaseFactor * ScaleFactor * Complexity * Compliance * Security",
            result={"total_person_days": total_days, "total_person_hours": total_hours},
            engine_version="1.0.0",
            timestamp=ts
        ),
        CalculationLedgerItem(
            calculation_id="CALC-003",
            calculation_type="RESOURCE_ALLOCATION_COST",
            inputs={"blended_rate": hourly_rate, "total_hours": total_hours, "roles_count": len(role_efforts)},
            formula="LaborCost_r = Hours_r * Rate_r; TotalLabor = sum(LaborCost_r)",
            result={"total_labour_cost_usd": total_cost, "currency": "USD"},
            engine_version="1.0.0",
            timestamp=ts
        ),
        CalculationLedgerItem(
            calculation_id="CALC-004",
            calculation_type="SCHEDULE_FEASIBILITY_CHECK",
            inputs={
                "ref_weeks": feasibility.reference_duration_weeks,
                "working_days": feasibility.working_days,
                "peak_fte_observed": feasibility.peak_fte_observed,
                "max_fte_limit": feasibility.max_fte_limit,
                "max_ramp_observed": feasibility.max_ramp_observed,
                "max_ramp_limit": feasibility.max_ramp_limit
            },
            formula="Capacity_d = Hours * Utilisation * Efficiency; min d st sum(Capacity) >= Effort",
            result={
                "is_feasible": feasibility.is_feasible,
                "resolved_duration_weeks": feasibility.resolved_duration_weeks,
                "schedule_stretched": feasibility.schedule_stretched,
                "binding_constraint": feasibility.binding_constraint
            },
            engine_version="1.0.0",
            timestamp=ts
        ),
        CalculationLedgerItem(
            calculation_id="CALC-005",
            calculation_type="CLOUD_BOM_SIZING",
            inputs={"bom_items_count": len(sizing_bom)},
            formula="TotalCost = sum(MonthlyCost_i) * FootprintMultiplier(HA_DR)",
            result={"total_monthly_cloud_cost_usd": monthly_bom, "annual_cloud_cost_usd": round(monthly_bom * 12, 2)},
            engine_version="1.0.0",
            timestamp=ts
        )
    ]
    return ledger
