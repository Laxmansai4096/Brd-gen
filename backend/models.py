from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Section 10: Dynamic Question Model ---
class QuestionOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None

class QuestionItem(BaseModel):
    id: str
    title: str
    prompt: str
    type: str  # "dropdown", "text", "number", "multi_choice"
    options: Optional[List[QuestionOption]] = None
    default_value: str
    category: str  # "Scope", "Scale", "Technical", "Sizing", "Governance", "KEY_DECISION"
    priority: str = "Medium"  # "Blocker", "High", "Medium"
    owner_persona: str = "CLIENT"  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"
    help_text: Optional[str] = None
    ask_when: Optional[List[Dict[str, Any]]] = None  # Conditional display rules e.g. [{"question_id": "q_cloud", "equals": "multi-cloud"}]
    dependencies: Optional[List[str]] = None
    resolves: Optional[List[str]] = None
    stakeholder: Optional[str] = None
    why_it_matters: Optional[str] = None
    downstream_impacts: Optional[List[str]] = None

class AnswerItem(BaseModel):
    question_id: str
    question_title: str
    answer: str
    is_default: bool = False
    ambiguity_count: int = 0
    hitl_confirmed: bool = False
    notes: Optional[str] = None

# --- Section 8 & 9: Canonical Requirements Model ---
class RequirementItem(BaseModel):
    requirement_id: str  # e.g. "FR-001", "NFR-001", "SEC-001", "AI-001"
    type: str  # "FUNCTIONAL", "NON_FUNCTIONAL", "BUSINESS", "TECHNICAL", "DATA", "INTEGRATION", "SECURITY", "COMPLIANCE", "AI", "RESPONSIBLE_AI", "OPERATIONAL", "DEPLOYMENT", "REPORTING", "UX", "AVAILABILITY", "PERFORMANCE", "DR", "AUDIT"
    statement: str
    actor: str = "System"
    capability: str = "General"
    priority: str = "MUST"  # "MUST", "SHOULD", "COULD", "WONT"
    source: str = "CLIENT"  # "CLIENT", "AI_INFERRED", "DEFAULT"
    status: str = "CLIENT_CONFIRMED"  # "CLIENT_PROVIDED", "CLIENT_CONFIRMED", "DEFAULT", "PROJECT_OVERRIDE", "INFERRED", "PENDING_CONFIRMATION", "CONFLICT", "SCOPE_CONSTRAINT", "DEPENDENCY", "RESOLVED", "REJECTED"
    acceptance_criteria: List[str] = []
    dependencies: List[str] = []
    impacts: List[str] = []

# --- Section 12 & 13: Capability & Scope Catalog ---
class CapabilityItem(BaseModel):
    capability_id: str  # e.g. "CAP-001"
    category: str  # "Business", "Application", "Data", "AI", "Platform"
    name: str
    description: str
    scope_status: str = "IN_SCOPE"  # "IN_SCOPE", "OUT_OF_SCOPE", "FUTURE", "CONDITIONAL"
    architecture_components: List[str] = []
    applicable_wbs_tasks: List[str] = []

# --- Section 14: Structured Technical Component ---
class TechnicalComponent(BaseModel):
    id: str  # C001 - C006
    name: str
    type: str = "Service"
    technology: str = ""
    technology_choice: str = ""
    purpose: str = ""
    responsibility: str = ""
    key_design_decisions: str = ""
    interfaces_in_out: str = ""
    data_classification: str = "Confidential"
    scalability_performance: str = "Auto-scaling"
    security_rai_controls: str = "RBAC, TLS 1.3, Data Redaction"
    failure_modes_mitigation: str = "Retry with exponential backoff, dead-letter queue"
    dependencies: str = "None"
    environment: List[str] = ["Dev", "Test", "UAT"]

# --- Section 15: End-to-End Data Flow Model ---
class DataFlowItem(BaseModel):
    flow_id: str  # DF-001
    name: str
    source: str
    target: str
    data_objects: List[str] = []
    protocol: str = "HTTPS/REST"
    frequency: str = "Batch / On-Demand"
    volume: Dict[str, Any] = {}
    security: Dict[str, Any] = {"encryption": "TLS 1.3", "auth": "OAuth 2.0 / Managed Identity"}
    transformation: List[str] = []
    failure_handling: str = "DLQ, structured exception logging, alert routing"

# --- Section 54: Calculation Ledger Audit Trail ---
class CalculationLedgerItem(BaseModel):
    calculation_id: str  # CALC-001
    calculation_type: str  # "TASK_EFFORT", "SCALE_FACTOR", "RESOURCE_COST", "SCHEDULE_FEASIBILITY", "BOM_COST"
    inputs: Dict[str, Any] = {}
    formula: str = ""
    result: Dict[str, Any] = {}
    engine_version: str = "1.0.0"
    timestamp: str = ""

# --- Section 50: Deterministic Impact Analysis ---
class ImpactAnalysisResult(BaseModel):
    parameter_changed: str
    old_value: Any
    new_value: Any
    affected_dimensions: Dict[str, Any] = {}  # Capacity, Architecture, Infrastructure, Testing, Schedule, Cost, FTE
    unaffected_dimensions: List[str] = []
    narrative_explanation: str = ""
    delta_days: float = 0.0
    delta_cost_usd: float = 0.0
    delta_fte: float = 0.0
    base_duration_weeks: float = 0.0
    base_person_days: float = 0.0
    base_cost_usd: float = 0.0
    base_fte: float = 0.0
    base_monthly_cloud_usd: float = 0.0
    sim_duration_weeks: float = 0.0
    sim_person_days: float = 0.0
    sim_cost_usd: float = 0.0
    sim_fte: float = 0.0
    sim_monthly_cloud_usd: float = 0.0

# --- Section 51: 4 HITL Approval Gates & 3-Persona Collaborative Workflow ---
class PersonaReview(BaseModel):
    persona: str  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"
    satisfied: bool = False
    status: str = "PENDING"  # "PENDING", "APPROVED", "CHANGES_REQUESTED"
    feedback: Optional[str] = None
    timestamp: Optional[str] = None
    signature_name: Optional[str] = None

class TripartyMessage(BaseModel):
    id: str
    sender_persona: str  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER", "AI_AGENT"
    sender_name: str
    message: str
    timestamp: str
    resolved: bool = False
    action_taken: Optional[str] = None

class PMQueryItem(BaseModel):
    id: str
    topic: str
    query_text: str
    addressed_to: str = "ALL"  # "CLIENT", "SOLUTIONS_ARCHITECT", "ALL"
    client_response: Optional[str] = None
    architect_response: Optional[str] = None
    status: str = "OPEN"  # "OPEN", "RESOLVED"

class EscalatedTopicItem(BaseModel):
    id: str
    question_id: str
    topic_title: str
    question_text: str
    why_needed: str
    client_context: str
    category: str = "Technical Architecture"
    options: List[Dict[str, str]] = []
    default_recommendation: str = ""
    status: str = "PENDING_ARCHITECT"  # "PENDING_ARCHITECT", "RESOLVED"
    architect_answer: Optional[str] = None
    architect_notes: Optional[str] = None
    escalated_at: Optional[str] = None
    resolved_at: Optional[str] = None

class WorkflowState(BaseModel):
    stage: str = "IDEATION"  # "IDEATION", "DISCOVERY", "DUAL_REVIEW", "PM_REVIEW", "FINAL_APPROVED"
    current_stage: Optional[str] = "IDEATION"
    active_persona: str = "CLIENT"  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"
    confidence_score: float = 0.0  # 0 to 100
    confidence_threshold: float = 95.0
    is_confidence_reached: bool = False
    
    # Stage 1: Ideation Data
    ideation_client_idea: Optional[str] = None
    ideation_architect_feedback: Optional[str] = None
    ideation_agreed_project: Optional[str] = None
    
    # Stage 2: Architect Escalation Queue
    escalated_topics: List[EscalatedTopicItem] = []
    
    # Stage 3: Dual Review
    client_review: PersonaReview = PersonaReview(persona="CLIENT", signature_name="Client Business Lead")
    architect_review: PersonaReview = PersonaReview(persona="SOLUTIONS_ARCHITECT", signature_name="Principal Solutions Architect")
    dual_review_iterations: int = 0
    
    # Stage 4: PM Review & Triparty Consensus
    pm_review: PersonaReview = PersonaReview(persona="PROJECT_MANAGER", signature_name="Senior Delivery PM")
    pm_queries: List[PMQueryItem] = []
    triparty_messages: List[TripartyMessage] = []
    
    # Stage 5: Final Distribution
    final_signoff_timestamp: Optional[str] = None
    final_shared_with: List[str] = ["Client", "Solutions Architect", "Project Manager"]

class HITLGates(BaseModel):
    gate1_requirements_approved: bool = False
    gate1_notes: Optional[str] = None
    gate2_solution_approved: bool = False
    gate2_notes: Optional[str] = None
    gate3_estimate_approved: bool = False
    gate3_notes: Optional[str] = None
    gate4_brd_approved: bool = False
    gate4_notes: Optional[str] = None
    
    # Persona-specific Sign-offs
    client_business_approved: bool = False
    client_approval_timestamp: Optional[str] = None
    client_notes: Optional[str] = None
    
    architect_tech_approved: bool = False
    architect_approval_timestamp: Optional[str] = None
    architect_notes: Optional[str] = None
    
    manager_estimate_approved: bool = False
    manager_approval_timestamp: Optional[str] = None
    manager_notes: Optional[str] = None

class DimensionScore(BaseModel):
    name: str
    category: str
    weight: float
    score: float
    status: str  # "GROUNDED", "PARTIAL", "MISSING"
    captured_value: Optional[str] = None
    impact: str = "High"

class DiscoveryConfidence(BaseModel):
    score: float = 0.0  # 0 to 100
    is_ready_for_brd: bool = False  # True when >= 95.0
    threshold: float = 95.0
    dimensions: List[DimensionScore] = []
    missing_items: List[str] = []
    recommendation: str = ""
    next_question: Optional[QuestionItem] = None
    summary_dossier: Optional[Dict[str, Any]] = None

# --- Existing Core Estimation & Schedule Models ---
class AssumptionItem(BaseModel):
    id: str
    type: str = "Assumption"  # "Assumption", "Prerequisite", "Constraint"
    category: str  # "Functional", "Data", "Technical", "Commercial", "Governance"
    statement: str
    impact_if_wrong: str
    owner_to_confirm: str
    confidence: str = "Medium"  # "High", "Medium", "Low"
    status: str = "Approve"  # "Approve", "Correct", "Reject"
    reason: Optional[str] = None
    can_override: bool = True

class TaskEstimate(BaseModel):
    phase_code: str  # P01 - P18
    phase_name: str
    task_name: str
    primary_role: str
    support_roles: str
    scale_driver: str
    uplift_tag: str
    base_days: float
    phase_factor: float
    scale_factor: float
    uplift_mult: float
    complex_mult: float
    effort_days: float

class RoleEffort(BaseModel):
    role_code: str
    role: str
    description: str
    days: float
    hours: float
    rate_hourly: float = 30.0
    cost: float
    peak_fte: float = 1.0
    active_fte: float = 1.0
    buffer_fte: float = 0.2
    total_assigned_fte: float = 1.2

class ProjectPhase(BaseModel):
    phase_code: str  # P01 - P18
    phase_name: str
    weeks: float
    phase_factor: float
    key_deliverables: List[str]
    roles_involved: List[str]
    effort_days: float

class SizingBOM(BaseModel):
    component: str
    sku_or_service: str
    tier: str
    quantity: str
    monthly_cost_usd: float
    justification: str

class SizingMetrics(BaseModel):
    named_users: int = 200
    peak_concurrent_users: int = 50
    requests_per_day: int = 2000
    peak_rps: float = 3.0
    prompt_tokens_avg: int = 500
    completion_tokens_avg: int = 2000
    retrieved_chunks_k: int = 5
    tokens_per_chunk: int = 512
    corpus_documents: int = 50000
    avg_chunks_per_doc: int = 40
    raw_corpus_gb: float = 1.0
    embedding_dimensions: int = 1536
    retention_months: int = 12
    ha_dr_tier: str = "None (single instance)"
    non_prod_factor: float = 0.60
    annual_growth_factor: float = 1.30
    total_monthly_cloud_cost_usd: float = 645.0

class DayWiseTask(BaseModel):
    day_number: int
    date: str
    day_name: str
    phase_code: str
    phase_name: str
    is_working_day: bool = True
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    tasks_allocated: List[Dict[str, Any]] = []
    backup_engineers_on_standby: List[str] = []
    total_hours_today: float = 0.0

class ScheduleFeasibility(BaseModel):
    reference_duration_weeks: float
    resolved_duration_weeks: float
    working_days: int
    peak_fte_observed: float
    max_fte_limit: float = 20.0
    max_ramp_observed: float
    max_ramp_limit: float = 80.0
    is_feasible: bool = True
    binding_constraint: str = "None (All constraints satisfied)"
    schedule_stretched: bool = False

class BRDDocument(BaseModel):
    project_title: str
    client_name: str
    delivery_tier: str  # One of 11 tiers
    tier_kind: str = "Base"  # "Base", "Transition", "Delta on live"
    headline_weight: float = 0.289
    complexity_level: str = "Low"
    complexity_multiplier: float = 0.85
    compliance_posture: str = "Internal policy only"
    compliance_multiplier: float = 1.05
    security_posture: str = "Standard"
    security_multiplier: float = 1.00
    ha_dr_tier: str = "None (single instance)"
    cloud_platform: str = "Microsoft Azure"
    
    # Timing & Delivery
    start_date: str = "2026-10-05"
    target_end_date: str = ""
    buffer_capacity_pct: float = 15.0
    backup_resources: List[Dict[str, Any]] = []
    delivery_model: str = "Global Delivery Model (Onshore Oversight + Offshore Execution)"
    version: str = "1.0.0"
    
    # Narratives
    executive_summary: str
    problem_statement: str
    solution_summary_six_sentences: str
    business_impacts: List[str]
    in_scope: List[str]
    out_of_scope: List[str]
    ai_interventions: List[Dict[str, Any]] = []
    non_ai_interventions: List[Dict[str, Any]] = []
    user_personas: List[Dict[str, str]] = []
    target_architecture_narrative: str
    azure_services_used: List[Dict[str, str]] = []
    data_flow_narrative: str
    responsible_ai_governance: List[str] = []
    security_compliance: List[str] = []

    # Canonical Model Arrays per reference.txt
    canonical_requirements: List[RequirementItem] = []
    capabilities: List[CapabilityItem] = []
    data_flows: List[DataFlowItem] = []
    calculation_ledger: List[CalculationLedgerItem] = []
    hitl_gates: HITLGates = HITLGates()

    # Functional Scope & Settings
    legal_categories: List[str] = ["Lease", "Vendor", "Service", "Facilities", "Technology", "Marketing"]
    foundation_llm_architecture: str = "Azure OpenAI / Google Gemini reasoning tier"
    grounding_surface_mode: str = "Work (Tenant data only, no public web retrieval)"
    parser_delimiters: str = "Block headers (<<<BEGIN:NAME>>>) and pipe delimiters (|)"
    evaluation_decision_logic: str = "Pass 1: Clause Extraction | Pass 2: Three-Tier Status [Agree, Agree with Mgmt, Not Agree]"

    # Technical Components
    technical_components: List[TechnicalComponent] = []
    
    # Sizing & Infrastructure
    sizing_metrics: SizingMetrics = SizingMetrics()
    sizing_bom: List[SizingBOM] = []
    
    # Enterprise & Rate Cards
    currency_code: str = "USD"
    currency_symbol: str = "$"
    currency_exchange_rate: float = 1.0
    total_labour_cost_converted: float = 0.0
    role_rate_cards: List[Dict[str, Any]] = []
    tco_projection: Dict[str, Any] = {}
    ai_act_classification: Dict[str, Any] = {}
    iso_42001_controls: List[Dict[str, Any]] = []
    
    # Estimation & Resource Loading
    total_duration_weeks: float
    reference_duration_weeks: float
    delivery_task_days: float = 97.5
    pm_task_days: float = 6.3
    pm_overhead_days: float = 11.7
    contingency_days: float = 11.6
    base_task_days: float = 103.7
    total_person_days: float
    total_person_hours: float
    total_labour_cost_usd: float
    blended_hourly_rate: float = 30.0
    daily_working_hours: float = 8.0
    
    # Disciplines & Phases
    role_efforts: List[RoleEffort]
    project_phases: List[ProjectPhase]
    task_estimates: List[TaskEstimate] = []
    
    # Feasibility & Day-Wise Plan
    schedule_feasibility: ScheduleFeasibility
    day_wise_schedule: List[DayWiseTask] = []
    
    # Assumptions
    assumptions: List[AssumptionItem] = []
    assumption_gate_passed: bool = True

class RevisionSnapshot(BaseModel):
    revision_id: str
    revision_number: int
    timestamp: str
    tier: str
    duration_weeks: float
    person_days: float
    labour_cost_usd: float
    summary_change: str
    trigger_reason: Optional[str] = None
    total_duration_weeks: Optional[float] = None
    total_person_days: Optional[float] = None
    total_labour_cost: Optional[float] = None
    monthly_cloud_cost: Optional[float] = None
    currency_code: str = "USD"
    currency_symbol: str = "$"
    brd_snapshot: Dict[str, Any]

class ChatMessage(BaseModel):
    sender: str  # "agent", "user", "system", "architect", "manager", "client"
    content: str
    timestamp: str
    persona: Optional[str] = None  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER", "AI_AGENT"
    persona_badge: Optional[str] = None
    is_architect_input: bool = False
    is_pm_input: bool = False
    question_context: Optional[QuestionItem] = None
    is_ambiguity_warning: bool = False
    ambiguity_strike: int = 0
    is_hitl_confirmation: bool = False
    hitl_default_value: Optional[str] = None
    hitl_options: Optional[List[Dict[str, str]]] = None

class ProjectSession(BaseModel):
    session_id: str
    current_question_index: int = 0
    answers: Dict[str, AnswerItem] = {}
    ambiguity_tracker: Dict[str, int] = {}
    clarification_state: Optional[Dict[str, Any]] = None
    uploaded_files: List[Dict[str, Any]] = []
    revisions: List[RevisionSnapshot] = []
    messages: List[ChatMessage] = []
    brd: Optional[BRDDocument] = None
    handoff_dossier: Optional[Dict[str, Any]] = None
    hitl_gates: HITLGates = HITLGates()
    workflow: WorkflowState = Field(default_factory=WorkflowState)
    confidence: Optional[DiscoveryConfidence] = None
