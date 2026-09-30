from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
    category: str  # "Scope", "Scale", "Technical", "Sizing", "Governance"
    priority: str = "Medium"  # "Blocker", "High", "Medium"
    help_text: Optional[str] = None

class AnswerItem(BaseModel):
    question_id: str
    question_title: str
    answer: str
    is_default: bool = False
    ambiguity_count: int = 0
    hitl_confirmed: bool = False
    notes: Optional[str] = None

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

class TechnicalComponent(BaseModel):
    id: str  # C001 - C006
    name: str
    purpose: str
    technology_choice: str
    key_design_decisions: str
    interfaces_in_out: str
    data_classification: str
    scalability_performance: str
    security_rai_controls: str
    failure_modes_mitigation: str
    dependencies: str

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
    
    # Project Timing & Backup Staffing
    start_date: str = "2026-10-05"
    target_end_date: str = ""
    buffer_capacity_pct: float = 15.0
    backup_resources: List[Dict[str, Any]] = []
    delivery_model: str = "Global Delivery Model (Onshore Oversight + Offshore Execution)"
    
    # Narratives
    executive_summary: str
    problem_statement: str
    solution_summary_six_sentences: str
    business_impacts: List[str]
    in_scope: List[str]
    out_of_scope: List[str]
    ai_interventions: List[Dict[str, Any]]
    non_ai_interventions: List[Dict[str, Any]]
    user_personas: List[Dict[str, str]]
    target_architecture_narrative: str
    azure_services_used: List[Dict[str, str]]
    data_flow_narrative: str
    responsible_ai_governance: List[str]
    security_compliance: List[str]
    risks_mitigations: List[Dict[str, str]]
    
    # Technical Components (6 Components)
    technical_components: List[TechnicalComponent] = []
    
    # Sizing & Infrastructure
    sizing_metrics: SizingMetrics = SizingMetrics()
    sizing_bom: List[SizingBOM] = []
    
    # Estimation & Resource Loading
    total_duration_weeks: float
    reference_duration_weeks: float
    total_person_days: float
    total_person_hours: float
    total_labour_cost_usd: float
    blended_hourly_rate: float = 30.0
    daily_working_hours: float = 8.0
    
    # 12 Disciplines & 18 Phases & Tasks
    role_efforts: List[RoleEffort]
    project_phases: List[ProjectPhase]
    task_estimates: List[TaskEstimate] = []
    
    # Schedule Feasibility & Day-Wise Plan
    schedule_feasibility: ScheduleFeasibility
    day_wise_schedule: List[DayWiseTask] = []
    
    # Assumptions Gate
    assumptions: List[AssumptionItem]
    assumption_gate_passed: bool = True

class ChatMessage(BaseModel):
    sender: str  # "agent", "user", "system"
    content: str
    timestamp: str
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
    uploaded_files: List[Dict[str, Any]] = []
    messages: List[ChatMessage] = []
    brd: Optional[BRDDocument] = None
    handoff_dossier: Optional[Dict[str, Any]] = None
