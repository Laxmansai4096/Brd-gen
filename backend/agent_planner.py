import json
import httpx
import re
import datetime
from typing import Dict, Any, List, Optional, Tuple
from backend.models import (
    BRDDocument, RoleEffort, ProjectPhase, SizingBOM,
    AssumptionItem, AnswerItem, ProjectSession, TaskEstimate,
    TechnicalComponent, SizingMetrics, ScheduleFeasibility, DayWiseTask
)
from backend.config import get_settings
from backend.admin_store import (
    get_admin_defaults, get_calendar_for_geography, get_working_hours_for_geography, get_hourly_rate_for_geography, get_master_assumptions,
    DELIVERY_TIERS, PHASE_APPLICABILITY_ANCHORS, SCALE_DRIVERS,
    COMPLEXITY_MULTIPLIERS, COMPLIANCE_UPLIFTS, SECURITY_UPLIFTS,
    HA_DR_FOOTPRINTS, STANDARD_ROLES, STANDARD_TASK_LIBRARY,
    TRANSITION_REWORK_UPLIFT, TRANSITION_MOBILISATION_FLOOR, INCREMENTAL_SCOPE_SHARE
)

def calculate_scale_factor(driver_name: str, current_qty: float) -> float:
    spec = SCALE_DRIVERS.get(driver_name, SCALE_DRIVERS["NONE"])
    baseline = spec["baseline"]
    elasticity = spec["elasticity"]
    floor = spec["floor"]
    if baseline == 0 or elasticity == 0.0:
        return 1.0
    factor = 1.0 + elasticity * (current_qty / baseline - 1.0)
    return max(floor, round(factor, 3))

def resolve_phase_factor(phase_code: str, delivery_tier: str) -> float:
    tier_info = DELIVERY_TIERS.get(delivery_tier, DELIVERY_TIERS["PoC"])
    anchors = PHASE_APPLICABILITY_ANCHORS.get(phase_code, {"PoC": 0.3, "Pilot": 0.5, "MVP": 0.75, "Production Grade": 1.0})
    
    kind = tier_info.get("kind", "Base")
    if kind == "Base":
        target = tier_info.get("target", "PoC")
        return anchors.get(target, 0.3)
    elif kind == "Transition":
        src = tier_info.get("source", "PoC")
        tgt = tier_info.get("target", "Production Grade")
        src_val = anchors.get(src, 0.3)
        tgt_val = anchors.get(tgt, 1.0)
        factor = (tgt_val - src_val) * TRANSITION_REWORK_UPLIFT + TRANSITION_MOBILISATION_FLOOR
        return max(0.05, round(factor, 3))
    elif kind == "Delta on live":
        prod_val = anchors.get("Production Grade", 1.0)
        return round(prod_val * INCREMENTAL_SCOPE_SHARE, 3)
    return 0.3

def generate_task_estimates(
    delivery_tier: str,
    scale_quantities: Dict[str, float],
    complexity_level: str = "Low",
    compliance_posture: str = "Internal policy only",
    security_posture: str = "Standard"
) -> List[TaskEstimate]:
    estimates: List[TaskEstimate] = []
    
    comp_mult = COMPLEXITY_MULTIPLIERS.get(complexity_level, 0.85)
    compliance_mult = COMPLIANCE_UPLIFTS.get(compliance_posture, 1.05)
    security_mult = SECURITY_UPLIFTS.get(security_posture, 1.00)
    
    for task in STANDARD_TASK_LIBRARY:
        phase_code = task["phase_code"]
        phase_name = PHASE_APPLICABILITY_ANCHORS.get(phase_code, {}).get("name", phase_code)
        base_days = float(task["base_days"])
        phase_factor = resolve_phase_factor(phase_code, delivery_tier)
        
        driver_name = task["scale_driver"]
        current_qty = scale_quantities.get(driver_name, SCALE_DRIVERS.get(driver_name, {}).get("baseline", 1.0))
        scale_factor = calculate_scale_factor(driver_name, current_qty)
        
        uplift_tag = task.get("uplift", "NONE")
        uplift_mult = 1.0
        if uplift_tag == "COMP":
            uplift_mult = compliance_mult
        elif uplift_tag == "SEC":
            uplift_mult = security_mult
            
        effort = round(base_days * phase_factor * scale_factor * uplift_mult * comp_mult, 2)
        
        estimates.append(TaskEstimate(
            phase_code=phase_code,
            phase_name=phase_name,
            task_name=task["task_name"],
            primary_role=task["primary_role"],
            support_roles=task["support_roles"],
            scale_driver=driver_name,
            uplift_tag=uplift_tag,
            base_days=base_days,
            phase_factor=phase_factor,
            scale_factor=scale_factor,
            uplift_mult=uplift_mult,
            complex_mult=comp_mult,
            effort_days=effort
        ))
    return estimates

def aggregate_role_efforts(
    task_estimates: List[TaskEstimate],
    reference_duration_weeks: float,
    blended_rate: float = 30.0,
    daily_hours: float = 8.0,
    buffer_pct: float = 15.0
) -> List[RoleEffort]:
    role_days_map: Dict[str, float] = {code: 0.0 for code in STANDARD_ROLES.keys()}
    
    for t in task_estimates:
        r_code = t.primary_role
        if r_code in role_days_map:
            role_days_map[r_code] += t.effort_days
        else:
            role_days_map["SWE"] += t.effort_days

    total_working_days = max(1.0, reference_duration_weeks * 5.0)
    role_efforts: List[RoleEffort] = []
    
    for code, spec in STANDARD_ROLES.items():
        days = round(role_days_map.get(code, 0.0), 2)
        hours = round(days * daily_hours, 1)
        cost = round(hours * blended_rate, 2)
        peak_fte = round(days / total_working_days, 2) if total_working_days > 0 else 0.0
        active_fte = peak_fte
        buffer_fte = round(peak_fte * (buffer_pct / 100.0), 2) if peak_fte > 0 else 0.0
        total_assigned_fte = round(active_fte + buffer_fte, 2)
        
        role_efforts.append(RoleEffort(
            role_code=code,
            role=spec["title"],
            description=spec["description"],
            days=days,
            hours=hours,
            rate_hourly=blended_rate,
            cost=cost,
            peak_fte=peak_fte,
            active_fte=active_fte,
            buffer_fte=buffer_fte,
            total_assigned_fte=total_assigned_fte
        ))
    return role_efforts

def build_project_phases(
    task_estimates: List[TaskEstimate],
    total_weeks: float
) -> List[ProjectPhase]:
    phase_effort_map: Dict[str, float] = {}
    phase_roles_map: Dict[str, set] = {}
    
    for t in task_estimates:
        p_code = t.phase_code
        phase_effort_map[p_code] = phase_effort_map.get(p_code, 0.0) + t.effort_days
        if p_code not in phase_roles_map:
            phase_roles_map[p_code] = set()
        phase_roles_map[p_code].add(STANDARD_ROLES.get(t.primary_role, {}).get("title", t.primary_role))

    total_effort = sum(phase_effort_map.values()) or 1.0
    phases: List[ProjectPhase] = []
    
    phase_deliverables = {
        "P01": ["Stakeholder Alignment & RACI", "Discovery & Pain-Point Workshops", "Current-State Assessment", "Feasibility & Governance Plan"],
        "P02": ["Functional Requirements Matrix", "User Stories & Personas", "Interaction / Conversation Flows", "NFR Specification", "MoSCoW Prioritization"],
        "P03": ["Data Discovery & Profiling", "Data Cleansing & Preprocessing", "PII/Privacy Classification", "Golden Ground-Truth Benchmark Dataset"],
        "P04": ["Target Solution Architecture", "Component Technical Specs", "API & Interface Contracts", "Security & Sizing Footprint Model"],
        "P05": ["Cloud Landing Zone & Accounts", "IAM & Managed Identity Setup", "Model Endpoint Provisioning", "Developer Toolchain & Git Branching"],
        "P06": ["Ingestion Connectors & Pipelines", "Document Parsing & Chunking", "Metadata Tagging", "Batch & Incremental Embedding Pipeline"],
        "P07": ["Vector Index Schema & Metadata Filters", "Hybrid Retrieval Strategy", "Re-ranking Engine", "Retrieval Quality Harness (Recall@k)"],
        "P08": ["LLM Evaluation & Selection", "System Prompt Templates", "Agent Flow Orchestration (Tools/Memory)", "Structured Output & Function Calling"],
        "P09": ["Fine-Tuning / Adaptation Feasibility", "Instruction Dataset Curation"],
        "P10": ["Backend Services & REST APIs", "Web Cockpit UI / Application Layer", "Enterprise System Connectors"],
        "P11": ["Golden Dataset Evaluation Runs", "Recall, Precision & F1 Quality Harness"],
        "P12": ["Content Safety & Toxicity Guardrails", "PII Redaction & Responsible AI Auditing"],
        "P13": ["Infrastructure as Code (IaC) Scripts", "Automated CI/CD Promotion Workflows"],
        "P14": ["Application Telemetry & Log Traces", "Token Consumption & Cloud FinOps Dashboard"],
        "P15": ["End-to-End Functional Test Suite", "Security Vulnerability Scanning & Penetration Testing"],
        "P16": ["Production Cutover Runbook", "Smoke Testing & Hypercare Support"],
        "P17": ["Architecture & Operations Runbooks", "Admin & Business User Training"],
        "P18": ["Sprint Ceremonies & Weekly Status", "RAID Ledger & Change Control Cadence"]
    }

    for p_code, spec in PHASE_APPLICABILITY_ANCHORS.items():
        p_effort = round(phase_effort_map.get(p_code, 0.0), 2)
        p_weeks = round(total_weeks * (p_effort / total_effort), 1) if total_effort > 0 else round(total_weeks / 18.0, 1)
        phases.append(ProjectPhase(
            phase_code=p_code,
            phase_name=f"{p_code}: {spec['name']}",
            weeks=max(0.2, p_weeks),
            phase_factor=spec.get("PoC", 0.3),
            key_deliverables=phase_deliverables.get(p_code, ["Milestone Deliverable"]),
            roles_involved=list(phase_roles_map.get(p_code, ["Software Engineer (Full-stack)"]))[:4],
            effort_days=p_effort
        ))
    return phases

def evaluate_schedule_feasibility(
    task_estimates: List[TaskEstimate],
    reference_duration_weeks: float,
    max_fte_limit: float = 20.0,
    max_ramp_limit: float = 80.0
) -> ScheduleFeasibility:
    total_days = sum(t.effort_days for t in task_estimates)
    working_days = int(reference_duration_weeks * 5)
    
    role_peak_map: Dict[str, float] = {}
    for t in task_estimates:
        role_peak_map[t.primary_role] = role_peak_map.get(t.primary_role, 0.0) + t.effort_days
        
    peak_fte = max(round(d / max(1, working_days), 2) for d in role_peak_map.values()) if role_peak_map else 1.0
    total_team_fte = round(total_days / max(1, working_days), 2)
    
    is_feasible = True
    stretched = False
    resolved_weeks = reference_duration_weeks
    binding_constraint = "None (All constraints satisfied)"
    
    if peak_fte > max_fte_limit:
        is_feasible = False
        stretched = True
        resolved_weeks = round((max(role_peak_map.values()) / max_fte_limit) / 5.0, 1)
        binding_constraint = f"Max FTE per role exceeded ({peak_fte} > {max_fte_limit})"
    elif total_team_fte > max_ramp_limit:
        is_feasible = False
        stretched = True
        resolved_weeks = round((total_days / max_ramp_limit) / 5.0, 1)
        binding_constraint = f"Max team ramp rate exceeded ({total_team_fte} > {max_ramp_limit})"
        
    return ScheduleFeasibility(
        reference_duration_weeks=reference_duration_weeks,
        resolved_duration_weeks=max(reference_duration_weeks, resolved_weeks),
        working_days=working_days,
        peak_fte_observed=peak_fte,
        max_fte_limit=max_fte_limit,
        max_ramp_observed=total_team_fte,
        max_ramp_limit=max_ramp_limit,
        is_feasible=is_feasible,
        binding_constraint=binding_constraint,
        schedule_stretched=stretched
    )

def generate_day_wise_schedule(
    start_date_str: Optional[str],
    total_working_days: int,
    project_phases: List[ProjectPhase],
    task_estimates: List[TaskEstimate],
    geography: str,
    daily_hours: float,
    buffer_pct: float = 15.0
) -> List[DayWiseTask]:
    cal = get_calendar_for_geography(geography)
    
    # Build comprehensive holiday lookup supporting both exact YYYY-MM-DD and MM-DD
    holiday_dict: Dict[str, str] = {}
    for h in cal.get("holidays", []):
        d_str = str(h.get("date", "")).strip()
        h_name = h.get("name", "Statutory Holiday")
        if d_str:
            holiday_dict[d_str] = h_name
            # Also index by MM-DD so recurring annual holidays match regardless of year
            parts = d_str.split("-")
            if len(parts) == 3:
                holiday_dict[f"{parts[1]}-{parts[2]}"] = h_name
    
    try:
        if start_date_str:
            curr_dt = datetime.datetime.strptime(start_date_str.split()[0].strip(), "%Y-%m-%d").date()
        else:
            curr_dt = datetime.date.today()
    except Exception:
        curr_dt = datetime.date.today()
        
    phase_tasks_map: Dict[str, List[TaskEstimate]] = {}
    for t in task_estimates:
        if t.effort_days > 0:
            phase_tasks_map.setdefault(t.phase_code, []).append(t)
            
    active_phases = [p for p in project_phases if p.effort_days > 0]
    if not active_phases:
        active_phases = project_phases
        
    total_needed_days = max(total_working_days, 1)
    
    # Calculate working day share per active phase
    total_phase_days = sum(p.effort_days for p in active_phases) or 1.0
    phase_work_plan: List[Tuple[ProjectPhase, int]] = []
    for p in active_phases:
        share = max(1, round(p.effort_days * (total_needed_days / total_phase_days)))
        phase_work_plan.append((p, share))
        
    day_phase_map: List[ProjectPhase] = []
    for p, count in phase_work_plan:
        for _ in range(count):
            day_phase_map.append(p)
            
    if len(day_phase_map) < total_needed_days:
        last_p = active_phases[-1] if active_phases else project_phases[0]
        while len(day_phase_map) < total_needed_days:
            day_phase_map.append(last_p)
    elif len(day_phase_map) > total_needed_days:
        day_phase_map = day_phase_map[:total_needed_days]

    schedule: List[DayWiseTask] = []
    working_day_counter = 0
    day_num = 1
    
    # Standard backup engineers on standby
    standby_engineers = [
        "Shadow AI/ML Engineer (On standby for model tuning & prompt eval)",
        "Backup Full-Stack SWE (On standby for API wiring & UI acceleration)"
    ] if buffer_pct > 0 else []
    
    while working_day_counter < total_needed_days:
        iso_date = curr_dt.isoformat()
        mm_dd = curr_dt.strftime("%m-%d")
        day_name = curr_dt.strftime("%A")
        is_weekend = (curr_dt.weekday() >= 5)
        
        holiday_name = holiday_dict.get(iso_date) or holiday_dict.get(mm_dd)
        is_holiday = (holiday_name is not None)
        
        if is_weekend:
            schedule.append(DayWiseTask(
                day_number=day_num,
                date=iso_date,
                day_name=day_name,
                phase_code="WEEKEND",
                phase_name="Weekend Non-Working Day",
                is_working_day=False,
                is_holiday=False,
                holiday_name=None,
                tasks_allocated=[{
                    "task_name": "Non-working weekend period",
                    "primary_role": "N/A",
                    "hours": 0.0,
                    "status": "Scheduled Off"
                }],
                backup_engineers_on_standby=[],
                total_hours_today=0.0
            ))
        elif is_holiday:
            schedule.append(DayWiseTask(
                day_number=day_num,
                date=iso_date,
                day_name=day_name,
                phase_code="HOLIDAY",
                phase_name=f"Statutory Holiday: {holiday_name}",
                is_working_day=False,
                is_holiday=True,
                holiday_name=holiday_name,
                tasks_allocated=[{
                    "task_name": f"🎉 Statutory Holiday: {holiday_name} ({cal.get('country_name', geography)}) — Excluded from project working days",
                    "primary_role": "N/A",
                    "hours": 0.0,
                    "status": "Statutory Holiday"
                }],
                backup_engineers_on_standby=[],
                total_hours_today=0.0
            ))
        else:
            assigned_phase = day_phase_map[working_day_counter]
            assigned_tasks = phase_tasks_map.get(assigned_phase.phase_code, [])
            
            allocated_items = []
            if assigned_tasks:
                t_idx = working_day_counter % len(assigned_tasks)
                t_obj = assigned_tasks[t_idx]
                allocated_items.append({
                    "task_name": t_obj.task_name,
                    "primary_role": t_obj.primary_role,
                    "support_roles": t_obj.support_roles,
                    "effort_days": t_obj.effort_days,
                    "hours": daily_hours,
                    "status": "Planned"
                })
                if len(assigned_tasks) > 1:
                    t_obj2 = assigned_tasks[(t_idx + 1) % len(assigned_tasks)]
                    if t_obj2.task_name != t_obj.task_name:
                        allocated_items.append({
                            "task_name": t_obj2.task_name,
                            "primary_role": t_obj2.primary_role,
                            "support_roles": t_obj2.support_roles,
                            "effort_days": t_obj2.effort_days,
                            "hours": round(daily_hours * 0.5, 1),
                            "status": "Planned"
                        })
            else:
                allocated_items.append({
                    "task_name": f"Execute core engineering deliverable for {assigned_phase.phase_name}",
                    "primary_role": "Lead Architect & Engineering Team",
                    "support_roles": "PM, QA",
                    "hours": daily_hours,
                    "status": "Planned"
                })
                
            schedule.append(DayWiseTask(
                day_number=day_num,
                date=iso_date,
                day_name=day_name,
                phase_code=assigned_phase.phase_code,
                phase_name=assigned_phase.phase_name,
                is_working_day=True,
                is_holiday=False,
                holiday_name=None,
                tasks_allocated=allocated_items,
                backup_engineers_on_standby=standby_engineers,
                total_hours_today=daily_hours
            ))
            working_day_counter += 1
            
        curr_dt += datetime.timedelta(days=1)
        day_num += 1
        
    return schedule

def detect_project_domain(problem_text: str) -> str:
    raw = problem_text.lower()
    if any(k in raw for k in ["chat", "bot", "support", "customer", "agent", "helpdesk", "voice", "call center", "virtual agent"]):
        return "customer_support"
    if any(k in raw for k in ["contract", "clause", "risk register", "legal", "lease", "vendor agreement"]):
        return "contract_intelligence"
    if any(k in raw for k in ["fraud", "aml", "anti-money", "transaction", "bank", "claims", "financial"]):
        return "fraud_financial"
    if any(k in raw for k in ["search", "knowledge", "rag", "wiki", "documentation", "enterprise search"]):
        return "enterprise_search"
    if any(k in raw for k in ["invoice", "receipt", "form", "ocr", "parsing", "document extraction"]):
        return "document_processing"
    return "general_ai"

def generate_technical_components_dynamic(cloud_platform: str, domain: str, project_title: str) -> List[TechnicalComponent]:
    cloud_lower = cloud_platform.lower()
    is_gcp = "google" in cloud_lower or "gcp" in cloud_lower
    is_aws = "aws" in cloud_lower or "amazon" in cloud_lower
    
    if domain == "customer_support":
        c1_tech = "Google Cloud Storage + Vertex AI Search & Conversation" if is_gcp else ("Amazon S3 + Amazon Bedrock Agents" if is_aws else "Azure Blob Storage + Azure Bot Framework")
        c2_tech = "Vertex AI Vector Search (Gecko embeddings)" if is_gcp else ("Amazon OpenSearch Serverless (Titan Embeddings)" if is_aws else "Azure AI Search (text-embedding-3-small)")
        c3_tech = "Vertex AI (Gemini 2.5 Flash / Pro)" if is_gcp else ("Amazon Bedrock (Claude 3.5 Sonnet / Haiku)" if is_aws else "Azure OpenAI Service (GPT-4o / GPT-5)")
        c4_tech = "Google Cloud SQL (PostgreSQL) / Firestore" if is_gcp else ("Amazon Aurora Serverless / DynamoDB" if is_aws else "Azure SQL Database Serverless / Cosmos DB")
        c5_tech = "Python Automated Evaluation Suite (RAGAS / BLEU / ROUGE)"
        c6_tech = "Google Cloud Run + Cloud Identity SSO" if is_gcp else ("AWS ECS Fargate + Cognito SSO" if is_aws else "Azure App Service + Microsoft Entra ID SSO")
        
        return [
            TechnicalComponent(
                id="C001",
                name="Omnichannel Customer Interaction & Ingestion Layer",
                purpose=f"Captures real-time customer queries, chat transcripts, FAQ documents, and CRM history across web and mobile channels.",
                technology_choice=c1_tech,
                key_design_decisions="Decouples ingestion from LLM inference using asynchronous message queues; preserves session context and user authorization tokens.",
                interfaces_in_out="In: Web chat widgets, CRM webhooks, and knowledge base uploads. Out: Normalized customer intents to C002 and C003.",
                data_classification="Confidential customer conversations and PII. Masked before model ingestion.",
                scalability_performance="Auto-scales to handle peak concurrency with sub-100ms ingestion latency.",
                security_rai_controls="Input sanitization, prompt injection defenses, TLS 1.3 encryption in transit.",
                failure_modes_mitigation="Graceful fallback to live human agent queue when network or parsing issues occur.",
                dependencies="Knowledge Base Repositories, Channel Webhook Gateways"
            ),
            TechnicalComponent(
                id="C002",
                name="Knowledge Base & Semantic Vector Index",
                purpose="Indexes product manuals, policy documents, troubleshooting guides, and past resolved tickets for ultra-fast contextual retrieval.",
                technology_choice=c2_tech,
                key_design_decisions="Hybrid semantic and keyword search ensures exact policy terminology matches while understanding colloquial customer phrasing.",
                interfaces_in_out="In: Document embeddings from C001. Out: Top-k grounded context snippets to C003.",
                data_classification="Internal customer service SOPs and public product documentation.",
                scalability_performance="Sub-80ms p95 retrieval latency across thousands of policy documents.",
                security_rai_controls="RBAC permissions ensure user queries only retrieve authorized knowledge articles.",
                failure_modes_mitigation="Fallback to keyword search index if vector service experiences transient latency.",
                dependencies="C001 Ingestion, Vector Search Service"
            ),
            TechnicalComponent(
                id="C003",
                name="Conversational AI & Agentic Resolution Engine",
                purpose="Generates accurate, empathetic, policy-compliant customer responses, calls backend CRM tools, and executes troubleshooting workflows.",
                technology_choice=c3_tech,
                key_design_decisions="Multi-turn conversation state tracking with strict tool-calling schemas for CRM lookup, order status, and ticket creation.",
                interfaces_in_out="In: Customer prompt + grounded knowledge context from C002. Out: Generated response and structured action payloads to C004 and C006.",
                data_classification="Ephemeral prompt contexts; enterprise tenant isolation prevents data leakage.",
                scalability_performance="High-throughput token caching with p95 response time under 1.5 seconds.",
                security_rai_controls="Content safety filters, automated tone/hallucination checks, temperature fixed at 0.1 for factual consistency.",
                failure_modes_mitigation="Automatic escalation to human agent if confidence threshold < 85% or frustration detected.",
                dependencies="C002 Vector Index, CRM REST APIs"
            ),
            TechnicalComponent(
                id="C004",
                name="Structured Conversation Store & CRM Integration Gateway",
                purpose="Persists interaction transcripts, customer sentiment telemetry, resolution statuses, and audit trails.",
                technology_choice=c4_tech,
                key_design_decisions="Stores structured interaction logs with foreign-key links to customer profiles and ticket IDs for full reporting transparency.",
                interfaces_in_out="In: Session logs and resolution outcomes from C003. Out: Analytics dashboards and CRM records.",
                data_classification="Customer account history and service transcripts. Encrypted at rest (TDE / Cloud KMS).",
                scalability_performance="Auto-scaling serverless database with high concurrent write capacity.",
                security_rai_controls="Row-level security, automated backups, compliance with data retention schedules.",
                failure_modes_mitigation="Dead-letter queuing ensures zero lost customer interaction logs during outages.",
                dependencies="Enterprise Cloud Network, Database Managed Identity"
            ),
            TechnicalComponent(
                id="C005",
                name="Automated Evaluation Harness & Resolution Accuracy Scorer",
                purpose="Continually tests customer queries against golden standard benchmark Q&A sets to measure answer accuracy, hallucination rate, and CSAT alignment.",
                technology_choice=c5_tech,
                key_design_decisions="Runs automated nightly regression suites on hundreds of historical test dialogues to detect drift before deploying prompt updates.",
                interfaces_in_out="In: Golden benchmark test set. Out: Precision, recall, toxicity, and accuracy scorecard.",
                data_classification="Anonymized evaluation datasets and benchmark logs.",
                scalability_performance="Executes 500 test dialogues in under 8 minutes.",
                security_rai_controls="Deterministic test harness with strict pass/fail gates.",
                failure_modes_mitigation="Regression warnings trigger alert to ML engineering team.",
                dependencies="C003 Reasoning Engine, Golden Test Suite"
            ),
            TechnicalComponent(
                id="C006",
                name="Support Agent Cockpit & Supervisor Analytics Dashboard",
                purpose="Provides human support agents and supervisors with real-time conversation monitoring, agent-assist suggestions, and SLA analytics.",
                technology_choice=c6_tech,
                key_design_decisions="Split-screen UI allowing support agents to review AI-generated answer suggestions, verify source citations, and take over chats in 1 click.",
                interfaces_in_out="In: Live browser sessions via Enterprise SSO. Out: REST API queries to C004.",
                data_classification="Encrypted HTTPS session traffic (TLS 1.3).",
                scalability_performance="Responsive web dashboard supporting hundreds of concurrent customer support agents.",
                security_rai_controls="Enterprise Single Sign-On (SSO), RBAC role permissions, session timeout controls.",
                failure_modes_mitigation="Local client-side caching prevents interruption during brief network blips.",
                dependencies="Enterprise Identity Provider, C004 Conversation Store"
            )
        ]
    else:
        # Default / Contract / General AI components
        c1_tech = "Google Cloud Storage + Document AI" if is_gcp else ("Amazon S3 + Amazon Textract" if is_aws else "Azure Blob Storage + Azure AI Document Intelligence")
        c2_tech = "Vertex AI Vector Search" if is_gcp else ("Amazon OpenSearch Serverless" if is_aws else "Azure AI Search")
        c3_tech = "Vertex AI (Gemini 2.5 Flash / Pro)" if is_gcp else ("Amazon Bedrock (Claude 3.5 Sonnet)" if is_aws else "Azure OpenAI Service (GPT-4o / GPT-5)")
        c4_tech = "Google Cloud SQL (PostgreSQL)" if is_gcp else ("Amazon Aurora Serverless" if is_aws else "Azure SQL Database Serverless")
        c5_tech = "Python Automated Evaluation Suite"
        c6_tech = "Google Cloud Run + Cloud Identity" if is_gcp else ("AWS ECS Fargate + Cognito" if is_aws else "Azure App Service + Entra ID")
        
        return [
            TechnicalComponent(
                id="C001",
                name="Document & Data Ingestion Pipeline",
                purpose=f"Authoritative landing zone and layout-aware text/metadata extraction pipeline for {project_title}.",
                technology_choice=c1_tech,
                key_design_decisions="Preserves raw input documents immutably; extracts structural boundaries, tables, and coordinates for 100% data traceability.",
                interfaces_in_out="In: Batch/interactive document uploads. Out: Normalized chunks and metadata to C002 and C004.",
                data_classification="Confidential enterprise data. Encrypted at rest and in transit.",
                scalability_performance="Scales horizontally via parallel asynchronous extraction workers.",
                security_rai_controls="Managed identity authentication, zero training retention on customer data.",
                failure_modes_mitigation="Quarantine unprocessable documents to exception ledger with alert.",
                dependencies="Cloud Storage, Document Extraction Endpoint"
            ),
            TechnicalComponent(
                id="C002",
                name="Managed Search & Semantic Index",
                purpose="Stores chunk embeddings and structured metadata for high-precision hybrid retrieval.",
                technology_choice=c2_tech,
                key_design_decisions="Combines dense vector embeddings with BM25 keyword search for maximum recall.",
                interfaces_in_out="In: Chunk embeddings from C001. Out: Ranked candidate context to C003.",
                data_classification="Confidential embedded chunks.",
                scalability_performance="Sub-100ms query latency across enterprise document collections.",
                security_rai_controls="Isolated private endpoint; role-based access control.",
                failure_modes_mitigation="Graceful fallback to keyword search if vector index degrades.",
                dependencies="C001 Ingestion Pipeline, Cloud Search Service"
            ),
            TechnicalComponent(
                id="C003",
                name="Model Reasoning & Orchestration Engine",
                purpose="Executes domain classification, multi-pass reasoning, extraction, and compliance rule verification.",
                technology_choice=c3_tech,
                key_design_decisions="Agentic multi-pass reasoning with schema enforcement and deterministic temperature settings.",
                interfaces_in_out="In: Grounded chunks from C002. Out: Structured findings and rationale to C004.",
                data_classification="Ephemeral prompt contexts inside enterprise cloud boundary.",
                scalability_performance="High-throughput token caching with latency optimization.",
                security_rai_controls="Content safety filters, prompt injection guardrails, audit logging.",
                failure_modes_mitigation="Fallback to manual exception review if confidence score < 80%.",
                dependencies="C002 Vector Store, Cloud LLM Endpoint"
            ),
            TechnicalComponent(
                id="C004",
                name="Structured Findings & Ontology Database",
                purpose="Central relational repository holding ontology rules, extracted findings, and risk registers.",
                technology_choice=c4_tech,
                key_design_decisions="Relational schemas enforce foreign-key relationships between source documents, extractions, and review statuses.",
                interfaces_in_out="In: Findings from C003. Out: Data to C006 Cockpit and export pipelines.",
                data_classification="Confidential structured findings. Transparent Data Encryption.",
                scalability_performance="Serverless auto-pause and compute scaling with sub-50ms query responses.",
                security_rai_controls="Row-level security, automated point-in-time backups.",
                failure_modes_mitigation="Automated connection retry policies with circuit breakers.",
                dependencies="Cloud Virtual Network, IAM Roles"
            ),
            TechnicalComponent(
                id="C005",
                name="Benchmark Evaluation & Quality Scorer",
                purpose="Automated validation suite evaluating model accuracy against golden ground-truth benchmarks.",
                technology_choice=c5_tech,
                key_design_decisions="Independent evaluation harness measuring precision, recall, and deviation detection.",
                interfaces_in_out="In: Golden benchmark dataset. Out: Accuracy scorecards and regression logs.",
                data_classification="Anonymized evaluation datasets.",
                scalability_performance="Executes full benchmark evaluation in under 15 minutes.",
                security_rai_controls="Deterministic test harness with strict pass/fail criteria.",
                failure_modes_mitigation="Regression alerts notify engineering team.",
                dependencies="C003 Reasoning Engine, Golden Test Suite"
            ),
            TechnicalComponent(
                id="C006",
                name="Executive Cockpit & Demonstration Dashboard",
                purpose="Interactive web cockpit providing synchronized visualization, review approvals, and analytics.",
                technology_choice=c6_tech,
                key_design_decisions="Split-screen cockpit displaying interactive findings alongside source document previews.",
                interfaces_in_out="In: HTTPS browser sessions via SSO. Out: REST API queries to C004.",
                data_classification="Encrypted session traffic (TLS 1.3).",
                scalability_performance="Supports hundreds of concurrent enterprise users.",
                security_rai_controls="Single Sign-On (SSO), RBAC permissions, session timeouts.",
                failure_modes_mitigation="Client-side error boundaries with offline caching.",
                dependencies="Enterprise Identity Provider, C004 Database"
            )
        ]

def generate_sizing_and_bom_dynamic(
    cloud_platform: str,
    delivery_tier: str,
    ha_dr_tier: str,
    named_users: int,
    concurrent_users: int,
    daily_requests: int
) -> Tuple[SizingMetrics, List[SizingBOM]]:
    ha_mult = HA_DR_FOOTPRINTS.get(ha_dr_tier, 1.00)
    cloud_lower = cloud_platform.lower()
    is_gcp = "google" in cloud_lower or "gcp" in cloud_lower
    is_aws = "aws" in cloud_lower or "amazon" in cloud_lower
    
    base_cost = 580.0 if is_gcp else (610.0 if is_aws else 645.0)
    total_cost = round(base_cost * ha_mult, 2)
    
    metrics = SizingMetrics(
        named_users=named_users,
        peak_concurrent_users=concurrent_users,
        requests_per_day=daily_requests,
        peak_rps=max(1.0, round(daily_requests / (8.0 * 3600), 2)),
        prompt_tokens_avg=500,
        completion_tokens_avg=2000,
        retrieved_chunks_k=5,
        tokens_per_chunk=512,
        corpus_documents=50000,
        avg_chunks_per_doc=40,
        raw_corpus_gb=1.0,
        embedding_dimensions=1536,
        retention_months=12,
        ha_dr_tier=ha_dr_tier,
        non_prod_factor=0.60,
        annual_growth_factor=1.30,
        total_monthly_cloud_cost_usd=total_cost
    )
    
    if is_gcp:
        bom = [
            SizingBOM(
                component="C001: Ingestion & Storage",
                sku_or_service="Google Cloud Storage (Standard Dual-Region)",
                tier="Standard PayG",
                quantity="50 GB Raw / Archive",
                monthly_cost_usd=round(15.0 * ha_mult, 2),
                justification="Stores raw uploaded documents, chat logs, and intermediate preprocessing artifacts."
            ),
            SizingBOM(
                component="C001: Document Parsing",
                sku_or_service="Google Cloud Document AI / Layout Parser",
                tier="Standard Edition",
                quantity="10,000 Pages / Month",
                monthly_cost_usd=round(90.0 * ha_mult, 2),
                justification="Extracts OCR layout, tables, and paragraphs with bounding coordinates."
            ),
            SizingBOM(
                component="C002: Vector Search",
                sku_or_service="Vertex AI Vector Search (Index Endpoint)",
                tier="Standard Node (1k QPS)",
                quantity="1 Deployed Index Unit",
                monthly_cost_usd=round(210.0 * ha_mult, 2),
                justification="Serves sub-50ms hybrid vector and semantic search for grounding context."
            ),
            SizingBOM(
                component="C003: GenAI Reasoning",
                sku_or_service="Vertex AI (Gemini 2.5 Flash & Gecko Embeddings)",
                tier="Standard Tokens PayG",
                quantity=f"{daily_requests:,} Requests/Day (~50M Tokens/Mo)",
                monthly_cost_usd=round(165.0 * ha_mult, 2),
                justification="Powers multi-pass conversational synthesis, intent routing, and reasoning."
            ),
            SizingBOM(
                component="C004: Database",
                sku_or_service="Google Cloud SQL (PostgreSQL - db-f1-micro/standard)",
                tier="vCPU 2, 8 GB RAM",
                quantity="1 Instance (Auto-pause)",
                monthly_cost_usd=round(65.0 * ha_mult, 2),
                justification="Stores structured customer records, session histories, and risk registers."
            ),
            SizingBOM(
                component="C006: Web App & IAM",
                sku_or_service="Google Cloud Run + Cloud Armor + Secret Manager",
                tier="Serverless Auto-scale",
                quantity="1 Cloud Run Service",
                monthly_cost_usd=round(35.0 * ha_mult, 2),
                justification="Hosts containerized backend API, interactive cockpit, and SSL encryption."
            )
        ]
    elif is_aws:
        bom = [
            SizingBOM(
                component="C001: S3 Storage",
                sku_or_service="Amazon S3 (Standard Tier)",
                tier="Standard PayG",
                quantity="50 GB Raw / Archive",
                monthly_cost_usd=round(16.0 * ha_mult, 2),
                justification="Encrypted landing zone for raw documents, chat logs, and transcripts."
            ),
            SizingBOM(
                component="C001: Textract OCR",
                sku_or_service="Amazon Textract (Layout & Tables)",
                tier="Standard API",
                quantity="10,000 Pages / Month",
                monthly_cost_usd=round(95.0 * ha_mult, 2),
                justification="Extracts OCR text, layout blocks, and structured tables."
            ),
            SizingBOM(
                component="C002: Vector Search",
                sku_or_service="Amazon OpenSearch Serverless (Vector Engine)",
                tier="2 OCU Capacity",
                quantity="1 Collection",
                monthly_cost_usd=round(230.0 * ha_mult, 2),
                justification="Vector search index with metadata filtering."
            ),
            SizingBOM(
                component="C003: Bedrock GenAI",
                sku_or_service="Amazon Bedrock (Claude 3.5 Sonnet / Haiku)",
                tier="On-Demand Tokens",
                quantity=f"{daily_requests:,} Requests/Day",
                monthly_cost_usd=round(175.0 * ha_mult, 2),
                justification="Executes prompt workflows, tool-calling, and reasoning."
            ),
            SizingBOM(
                component="C004: Aurora Database",
                sku_or_service="Amazon Aurora Serverless v2 (PostgreSQL)",
                tier="0.5 - 2 ACUs",
                quantity="1 DB Cluster",
                monthly_cost_usd=round(60.0 * ha_mult, 2),
                justification="Stores structured transaction records and interaction histories."
            ),
            SizingBOM(
                component="C006: App & Security",
                sku_or_service="AWS ECS Fargate + WAF + Secrets Manager",
                tier="0.5 vCPU / 1GB RAM",
                quantity="1 Fargate Service",
                monthly_cost_usd=round(34.0 * ha_mult, 2),
                justification="Hosts web dashboard with Cognito Single Sign-On."
            )
        ]
    else: # Azure
        bom = [
            SizingBOM(
                component="C001: Landing Storage",
                sku_or_service="Azure Blob Storage (Hot Tier, GRS)",
                tier="Standard PayG",
                quantity="50 GB Raw / Archive",
                monthly_cost_usd=round(18.0 * ha_mult, 2),
                justification="Stores original documents, layout JSON artifacts, and chunk extracts."
            ),
            SizingBOM(
                component="C001: Layout Extraction",
                sku_or_service="Azure AI Document Intelligence (Layout API)",
                tier="S0 Standard",
                quantity="10,000 Pages / Month",
                monthly_cost_usd=round(100.0 * ha_mult, 2),
                justification="Extracts layout-aware OCR text and bounding-box coordinates."
            ),
            SizingBOM(
                component="C002: Vector Search",
                sku_or_service="Azure AI Search (Standard S1)",
                tier="Standard S1 Partition",
                quantity="1 Unit (2M Chunks)",
                monthly_cost_usd=round(245.0 * ha_mult, 2),
                justification="Hybrid vector and keyword search index with metadata filtering."
            ),
            SizingBOM(
                component="C003: LLM Reasoning",
                sku_or_service="Azure OpenAI Service (GPT-4o / GPT-5 & Embeddings)",
                tier="Standard PayG Tokens",
                quantity=f"{daily_requests:,} Requests/Day",
                monthly_cost_usd=round(180.0 * ha_mult, 2),
                justification="Powers multi-pass clause extraction, classification, and principle assessment."
            ),
            SizingBOM(
                component="C004: Structured Database",
                sku_or_service="Azure SQL Database Serverless (GP)",
                tier="General Purpose (vCore 2)",
                quantity="1 DB Instance (Auto-pause)",
                monthly_cost_usd=round(65.0 * ha_mult, 2),
                justification="Stores structured ontologies, extracted findings, and risk register."
            ),
            SizingBOM(
                component="C006: Web App & Security",
                sku_or_service="Azure App Service (B1) + Key Vault + Entra ID",
                tier="Basic B1 + Standard Vault",
                quantity="1 App Service Plan",
                monthly_cost_usd=round(37.0 * ha_mult, 2),
                justification="Hosts FastAPI cockpit backend, SSL encryption, and secret key management."
            )
        ]
        
    return metrics, bom

def generate_brd(
    session: ProjectSession,
    blended_rate: Optional[float] = None,
    hours_per_day: Optional[float] = None
) -> BRDDocument:
    defaults = get_admin_defaults()
    geo_ans = session.answers.get("q_geography", AnswerItem(question_id="q_geography", question_title="Geography", answer="India")).answer
    
    if hours_per_day is not None:
        daily_hours = hours_per_day
    else:
        daily_hours = get_working_hours_for_geography(geo_ans)
        
    if blended_rate is not None:
        rate = blended_rate
    else:
        rate = get_hourly_rate_for_geography(geo_ans)
    
    tier_ans = session.answers.get("q_tier", AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="PoC")).answer
    tier_info = DELIVERY_TIERS.get(tier_ans, DELIVERY_TIERS["PoC"])
    tier_name = tier_ans if tier_ans in DELIVERY_TIERS else "PoC"
    
    client_raw = session.answers.get("q_client", AnswerItem(question_id="q_client", question_title="Client", answer="Enterprise Client | AI Platform")).answer
    problem_raw = session.answers.get("q_problem", AnswerItem(question_id="q_problem", question_title="Problem", answer="Enterprise operational inefficiency and manual processing bottlenecks.")).answer
    
    # Intelligently clean and construct client name and project title
    client_name = client_raw.split("|")[0].strip() if "|" in client_raw else client_raw.strip()
    if not client_name or client_name.lower() in ["hii", "hi", "hello", "test", "demo"]:
        client_name = client_raw.strip() if client_raw.strip() else "Enterprise Client"
        
    domain = detect_project_domain(problem_raw)
    
    if "|" in client_raw:
        proj_title = client_raw.split("|")[1].strip()
    else:
        if domain == "customer_support":
            proj_title = "AI-Powered Customer Support & Virtual Agent Cockpit"
        elif domain == "contract_intelligence":
            proj_title = "Contract Intelligence & Risk Visibility Platform"
        elif domain == "fraud_financial":
            proj_title = "Intelligent AML & Financial Fraud Detection System"
        elif domain == "enterprise_search":
            proj_title = "Enterprise Knowledge Base & Neural Search Accelerator"
        elif domain == "document_processing":
            proj_title = "Intelligent Document Extraction & Workflow Automation Platform"
        else:
            proj_title = f"{client_name} AI Modernization & Automation Platform"
            
    dur_ans = session.answers.get("q_duration", AnswerItem(question_id="q_duration", question_title="Duration", answer="6.0")).answer
    ref_weeks = 6.0
    try:
        ref_weeks = float(dur_ans.replace("Weeks", "").replace("Week", "").strip().split()[0])
    except Exception:
        ref_weeks = 6.0
        
    cloud_ans = session.answers.get("q_cloud", AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Microsoft Azure")).answer
    
    def get_num_ans(qid: str, default_val: float) -> float:
        if qid in session.answers:
            try:
                nums = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', str(session.answers[qid].answer))
                if nums:
                    return float(nums[0])
            except Exception:
                pass
        return default_val

    def get_str_ans(qid: str, default_val: str) -> str:
        if qid in session.answers:
            return session.answers[qid].answer
        return default_val

    # Scale quantities map dynamically extracted from user's direct answers
    scale_quantities = {
        "USECASES": get_num_ans("q_usecases_count", 1.0),
        "PERSONAS": get_num_ans("q_personas_count", 4.0),
        "INTEGRATIONS": get_num_ans("q_integrations_count", 0.0),
        "DATASOURCES": get_num_ans("q_datasources_count", 2.0),
        "CHANNELS": get_num_ans("q_channels_count", 1.0),
        "ENVS": get_num_ans("q_envs_count", 3.0),
        "LANGUAGES": get_num_ans("q_languages_count", 1.0),
        "COMPONENTS": get_num_ans("q_components_count", 6.0),
        "DOCS": 50000.0
    }
    
    complexity_level = get_str_ans("q_complexity", "Low")
    compliance_posture = get_str_ans("q_compliance", "Internal policy only")
    security_posture = get_str_ans("q_security", "Standard")
    hadr_tier = get_str_ans("q_hadr_tier", "None (single instance)")

    named_users = int(get_num_ans("q_named_users", 200))
    concurrent_users = int(get_num_ans("q_concurrent_users", 50))
    daily_requests = int(get_num_ans("q_daily_requests", 2000))
    
    task_estimates = generate_task_estimates(
        delivery_tier=tier_name,
        scale_quantities=scale_quantities,
        complexity_level=complexity_level,
        compliance_posture=compliance_posture,
        security_posture=security_posture
    )
    
    role_efforts = aggregate_role_efforts(
        task_estimates=task_estimates,
        reference_duration_weeks=ref_weeks,
        blended_rate=rate,
        daily_hours=daily_hours
    )
    
    total_days = round(sum(r.days for r in role_efforts), 2)
    total_hours = round(sum(r.hours for r in role_efforts), 1)
    total_labour_cost = round(sum(r.cost for r in role_efforts), 2)
    
    feasibility = evaluate_schedule_feasibility(
        task_estimates=task_estimates,
        reference_duration_weeks=ref_weeks,
        max_fte_limit=float(defaults.get("max_fte_per_role_peak", 20.0)),
        max_ramp_limit=float(defaults.get("max_ramp_per_week", 80.0))
    )
    
    phases = build_project_phases(task_estimates, feasibility.resolved_duration_weeks)
    tech_components = generate_technical_components_dynamic(cloud_ans, domain, proj_title)
    sizing_metrics, sizing_bom = generate_sizing_and_bom_dynamic(
        cloud_platform=cloud_ans,
        delivery_tier=tier_name,
        ha_dr_tier=hadr_tier,
        named_users=named_users,
        concurrent_users=concurrent_users,
        daily_requests=daily_requests
    )
    
    # Master Assumptions from admin store
    assumptions_raw = get_master_assumptions()
    assumptions: List[AssumptionItem] = []
    for a in assumptions_raw:
        assumptions.append(AssumptionItem(
            id=a.get("id", "A001"),
            type=a.get("type", "Assumption"),
            category=a.get("category", "Functional"),
            statement=a.get("statement", ""),
            impact_if_wrong=a.get("impact_if_wrong", a.get("impact", "")),
            owner_to_confirm=a.get("owner_to_confirm", "Project Sponsor & Technical Lead"),
            confidence=a.get("confidence", "High"),
            status=a.get("status", "Approve"),
            reason=a.get("reason", "")
        ))

    if domain == "customer_support":
        solution_summary_six = (
            f"An enterprise {tier_name} for **{proj_title}** is architected on {cloud_ans} in {geo_ans} to automate customer support interactions. "
            f"An omnichannel ingestion pipeline captures incoming customer inquiries and connects with internal knowledge bases. "
            f"A semantic retrieval engine matches user queries against verified knowledge articles and resolved historical tickets. "
            f"A conversational GenAI reasoning layer provides grounded, empathetic, and policy-compliant answers with real-time tool-calling. "
            f"Structured interaction logs and escalation triggers are persisted in a secure database with automated CRM handoff. "
            f"An automated evaluation harness benchmarks resolution accuracy and customer satisfaction metrics against golden test dialogues."
        )
        business_impacts = [
            "Deflection Rate Increase: Deflects 40%–60% of tier-1 customer support inquiries to automated resolution.",
            "Response Time Reduction: Decreases initial customer response latency from 15 minutes to under 2 seconds.",
            "24/7 Omnichannel Availability: Provides round-the-clock accurate customer assistance across web and mobile.",
            "Agent Productivity Uplift: Empowers human support staff with real-time AI answer suggestions and CRM integration."
        ]
        in_scope = [
            f"Conversational AI assistant build on {cloud_ans} covering {int(scale_quantities['USECASES'])} primary use case(s).",
            f"Knowledge base indexing across {int(scale_quantities['DATASOURCES'])} data sources and policy repositories.",
            f"Support for {int(scale_quantities['CHANNELS'])} delivery channel(s) and {int(scale_quantities['PERSONAS'])} user persona(s).",
            "Multi-pass intent classification, grounded retrieval, and hallucination guardrails.",
            "Support Agent Cockpit dashboard with human escalation triggers.",
            "Automated nightly benchmark evaluation harness against golden customer Q&A dataset."
        ]
        out_of_scope = [
            "Autonomous processing of financial refunds beyond approved pre-set monetary thresholds.",
            "Unsupervised model retraining on live unverified customer inputs.",
            "Non-English foreign language audio translation (unless explicitly added).",
            "Full legacy CRM mainframe core refactoring (connects via standard REST APIs)."
        ]
        personas = [
            {"persona": "Customer / End-User", "need": "Receive instant, accurate, 24/7 resolution to support queries without waiting in phone queues."},
            {"persona": "Customer Support Agent", "need": "Review AI-suggested answers, take over escalated tickets with full context, and resolve complex issues."},
            {"persona": "Support Operations Lead", "need": "Monitor deflection rates, CSAT metrics, queue backlogs, and agent productivity."},
            {"persona": "Executive Sponsor", "need": "Track support cost-per-ticket reductions and customer retention ROI."}
        ]
        ai_interventions = [
            {"agent": "Intent & Emotion Classifier", "tech": cloud_ans, "role": "Identifies customer inquiry type, urgency, and sentiment."},
            {"agent": "Grounded Response Generator", "tech": cloud_ans, "role": "Synthesizes policy-compliant answers strictly grounded in knowledge base articles."},
            {"agent": "Automated Action Dispatcher", "tech": cloud_ans, "role": "Calls backend tools for order lookup, ticket creation, and appointment booking."}
        ]
        non_ai_interventions = [
            {"service": f"{cloud_ans} Storage & CDN", "role": "Serves static web assets, chat widget scripts, and policy PDFs."},
            {"service": f"{cloud_ans} Managed Database", "role": "Persists customer conversation history, auth tokens, and audit logs."},
            {"service": "Enterprise SSO & IAM", "role": "Authenticates support agents and enforces role-based access control."}
        ]
        data_flow = (
            "1. Customer initiates inquiry via web/mobile chat channel.\n"
            "2. Ingestion pipeline normalizes text and verifies customer authentication.\n"
            "3. Vector Search retrieves top-k matching policy snippets and troubleshooting steps.\n"
            "4. LLM reasoning engine generates policy-compliant answer and executes tool-calling if required.\n"
            "5. Content safety guardrails verify output for zero toxicity and factual grounding.\n"
            "6. Response delivered to customer; session logged to database.\n"
            "7. If confidence < 85%, interaction seamlessly escalated to live human agent."
        )
    else:
        solution_summary_six = (
            f"An enterprise {tier_name} for **{proj_title}** is architected on {cloud_ans} in {geo_ans} for client {client_name}. "
            f"An automated ingestion pipeline processes incoming enterprise data across {int(scale_quantities['DATASOURCES'])} data source(s). "
            f"Layout and structural extraction ensures 100% provenance and metadata tagging. "
            f"Agentic reasoning models execute domain-specific classification, extraction, and verification against configured business rules. "
            f"Structured findings are persisted in a secure cloud database and surfaced on an interactive dashboard. "
            f"An automated evaluation harness benchmarks accuracy and latency against verified golden ground truth."
        )
        business_impacts = [
            "Operational Cycle Time Reduction: Reduces end-to-end task turnaround time from hours to seconds.",
            "Data Transparency & Auditability: Eliminates unmonitored spreadsheet workflows with a centralized platform.",
            "Standardized Business Rule Enforcement: Ensures 100% compliance across organizational policies.",
            "Scalable Cloud Architecture: Supports anticipated enterprise workload growth with optimized cloud FinOps."
        ]
        in_scope = [
            f"Target solution engineering on {cloud_ans} in {geo_ans}.",
            f"Deployment across {int(scale_quantities['ENVS'])} environment(s) (Dev, Test, Prod).",
            f"Integration of {int(scale_quantities['COMPONENTS'])} architecture component(s) tailored to {proj_title}.",
            "Implementation of agentic reasoning workflows, safety guardrails, and structured database storage.",
            "Interactive demonstration dashboard with Single Sign-On.",
            "Accuracy benchmark evaluation report measured against golden test data."
        ]
        out_of_scope = [
            "Autonomous un-gated decision making on high-risk regulatory actions without human sign-off.",
            "Legacy system refactoring beyond defined API contract interfaces.",
            "Non-standard file format reverse engineering without schema documentation."
        ]
        personas = [
            {"persona": "Business Operations Analyst", "need": "Execute workflows, inspect flagged exceptions, and verify output accuracy."},
            {"persona": "Compliance & Risk Officer", "need": "Audit system decisions, review rule configurations, and verify compliance reports."},
            {"persona": "IT Platform Administrator", "need": "Monitor cloud health, API latency, token budgets, and access permissions."},
            {"persona": "Executive Sponsor", "need": "Track productivity improvements, cycle time savings, and project ROI."}
        ]
        ai_interventions = [
            {"agent": "Domain Reasoning Agent", "tech": cloud_ans, "role": "Performs complex contextual analysis and structured extraction."},
            {"agent": "Compliance & Rule Verification Engine", "tech": cloud_ans, "role": "Compares outputs against business ontology standards to detect deviations."}
        ]
        non_ai_interventions = [
            {"service": f"{cloud_ans} Storage", "role": "Stores raw data inputs and immutable evidence files."},
            {"service": f"{cloud_ans} Managed Database", "role": "Stores structured outputs, audit registers, and user configurations."},
            {"service": "Enterprise IAM", "role": "Role-Based Access Control and Single Sign-On."}
        ]
        data_flow = (
            "1. Input data uploaded or ingested via automated cloud connectors.\n"
            "2. Ingestion pipeline extracts layout, metadata, and structural boundaries.\n"
            "3. Embeddings generated and indexed into cloud vector store.\n"
            "4. Agentic reasoning engine evaluates data against business ontology rules.\n"
            "5. Structured findings and confidence scores persisted to database.\n"
            "6. Results rendered in interactive dashboard with audit-ready export."
        )

    start_date_ans = get_str_ans("q_start_date", "2026-09-30")
    buffer_strategy_ans = get_str_ans("q_buffer_strategy", "15% Shadow / Backup Capacity (Recommended)")
    buffer_pct = 15.0
    if "0%" in buffer_strategy_ans or "Zero" in buffer_strategy_ans:
        buffer_pct = 0.0
    elif "25%" in buffer_strategy_ans:
        buffer_pct = 25.0
    elif "10%" in buffer_strategy_ans:
        buffer_pct = 10.0

    # 6 Factor Sizing & Functional Fields
    legal_cats_raw = get_str_ans("q_legal_categories", "Lease, Vendor, Service, Facilities, Technology, Marketing")
    legal_categories_list = [c.strip() for c in legal_cats_raw.split(",") if c.strip()]
    if not legal_categories_list:
        legal_categories_list = ["Lease", "Vendor", "Service", "Facilities", "Technology", "Marketing"]

    foundation_llm = get_str_ans("q_foundation_llm", "Azure OpenAI reasoning/thinking tier (GPT-5 Thinking/Reasoning parameters)")
    grounding_mode = get_str_ans("q_grounding_mode", "Work (Tenant data only, disabling public web retrieval) using M365 Copilot / Azure AI Agent services")
    parser_delims = get_str_ans("q_parser_delimiters", "Block headers (<<<BEGIN:NAME>>>) and pipe characters (|), 30,000 char cell text limit, 0.72 synonym confidence threshold")
    eval_logic = get_str_ans("q_multi_pass_policy", "Pass 1 extracts explicit standard clauses | Pass 2 evaluates ambiguous terms to assign one of three statuses: Agree, Agree with Management Approval, or Not Agree")
    onprem_footprint = get_str_ans("q_onprem_footprint", "Zero on-premises components permitted (No hybrid tunnels/VPN)")
    sub_isolation = get_str_ans("q_subscription_isolation", "Dedicated newly created non-production cloud subscription")

    backup_resources_list = [
        {"role": "Shadow AI & ML Engineer", "level": "Senior", "location": geo_ans, "allocation_pct": f"{buffer_pct}%", "purpose": "Hot-standby for model tuning, evaluation pipeline blockers, and critical-path prompt engineering cover"},
        {"role": "Shadow Full-Stack / Cloud Engineer", "level": "Mid-Senior", "location": geo_ans, "allocation_pct": f"{buffer_pct}%", "purpose": "Hot-standby for API integration, cloud infrastructure failover, and deployment coverage"},
        {"role": "Shadow QA / Test Automation Engineer", "level": "Mid", "location": geo_ans, "allocation_pct": f"{buffer_pct}%", "purpose": "Regression suite verification, validation gate coverage, and defect triage during team leave"}
    ] if buffer_pct > 0 else []

    day_schedule = generate_day_wise_schedule(
        start_date_str=start_date_ans,
        total_working_days=feasibility.working_days,
        project_phases=phases,
        task_estimates=task_estimates,
        geography=geo_ans,
        daily_hours=daily_hours
    )
    
    target_end_date_str = day_schedule[-1].date if day_schedule else "2026-12-18"

    # 7. Enterprise Expansions: Currency, Role Rate Cards, AI Act, and 3-Year TCO
    currency_code = get_str_ans("q_currency", "USD")
    curr_info = {
        "USD": {"symbol": "$", "rate": 1.0},
        "EUR": {"symbol": "€", "rate": 0.92},
        "GBP": {"symbol": "£", "rate": 0.78},
        "INR": {"symbol": "₹", "rate": 83.5},
        "AED": {"symbol": "AED ", "rate": 3.67},
        "SGD": {"symbol": "S$", "rate": 1.35},
        "AUD": {"symbol": "A$", "rate": 1.52}
    }.get(currency_code, {"symbol": "$", "rate": 1.0})
    
    currency_rate = curr_info["rate"]
    currency_symbol = curr_info["symbol"]
    total_labour_converted = round(total_labour_cost * currency_rate, 2)
    
    role_rate_cards = [
        {"role_code": "SA", "role": "Lead Solutions Architect", "seniority": "Principal", "hourly_rate_usd": 45.0, "hourly_rate_converted": round(45.0 * currency_rate, 2), "location": f"{geo_ans} / Onshore Lead"},
        {"role_code": "MLE", "role": "Senior AI / Prompt Engineer", "seniority": "Senior Specialist", "hourly_rate_usd": 38.0, "hourly_rate_converted": round(38.0 * currency_rate, 2), "location": f"{geo_ans} Offshore Center"},
        {"role_code": "DE", "role": "Data Ingestion & Vector Engineer", "seniority": "Senior", "hourly_rate_usd": 32.0, "hourly_rate_converted": round(32.0 * currency_rate, 2), "location": f"{geo_ans} Offshore Center"},
        {"role_code": "FSE", "role": "Full-Stack Web & API Engineer", "seniority": "Mid-Senior", "hourly_rate_usd": 28.0, "hourly_rate_converted": round(28.0 * currency_rate, 2), "location": f"{geo_ans} Offshore Center"},
        {"role_code": "SEC", "role": "Cloud Security Specialist", "seniority": "Senior", "hourly_rate_usd": 36.0, "hourly_rate_converted": round(36.0 * currency_rate, 2), "location": "Hybrid Oversight"},
        {"role_code": "QA", "role": "QA & Eval Automation Engineer", "seniority": "Mid", "hourly_rate_usd": 22.0, "hourly_rate_converted": round(22.0 * currency_rate, 2), "location": f"{geo_ans} Offshore Center"},
        {"role_code": "PM", "role": "Project Delivery Manager", "seniority": "Senior", "hourly_rate_usd": 35.0, "hourly_rate_converted": round(35.0 * currency_rate, 2), "location": "Hybrid Oversight"}
    ]
    
    # EU AI Act & ISO 42001
    is_high_risk = any(k in compliance_posture for k in ["BFSI", "Gov", "Health"])
    ai_act_data = {
        "risk_tier": "High-Risk AI System (Annex III EU AI Act)" if is_high_risk else ("Specific Transparency Risk (Article 50)" if domain == "customer_support" else "Minimal / Low Risk AI System"),
        "framework": "EU AI Act (Regulation 2024/1689) & NIST AI RMF 1.0",
        "justification": "Mandatory conformity assessment, strict audit logging, and human-in-the-loop fallback required for regulatory governance." if is_high_risk else "Assistive decision support with continuous grounding provenance and hallucination guardrails.",
        "mandatory_obligations": [
            "Continuous accuracy and bias monitoring across evaluation runs",
            "100% human-in-the-loop oversight for high-impact decisions",
            "Source attribution traceability with bounding box coordinate retention",
            "Immutable audit logs retained for compliance audits"
        ]
    }
    
    iso_controls = [
        {"control_id": "A.5.1", "category": "AI Policy", "control_name": "Responsible AI Directive", "status": "Implemented", "evidence": "Deterministic temperature limits (0.1), bounded prompt templates, and zero data retention agreements."},
        {"control_id": "A.6.2", "category": "Risk Management", "control_name": "AI Impact & Failure Assessment", "status": "Implemented", "evidence": "Automated exception routing and fallback to human reviewer queue on low confidence."},
        {"control_id": "A.7.3", "category": "Data Quality", "control_name": "Provenance & Coordinate Traceability", "status": "Implemented", "evidence": "100% clause bounding box extraction and verified citation linkage back to source PDF."},
        {"control_id": "A.8.4", "category": "Verification", "control_name": "Golden Dataset Benchmark Eval", "status": "Implemented", "evidence": "Automated regression evaluation against golden QA dataset benchmark."}
    ]
    
    # 3-Year TCO Projection
    monthly_cloud = sizing_metrics.total_monthly_cloud_cost_usd
    y1_labour = total_labour_cost
    y1_cloud = monthly_cloud * 12
    y1_tot = y1_labour + y1_cloud
    
    maint_factor = 0.18 if tier_name == "Production Grade" else 0.12
    y2_labour = y1_labour * maint_factor
    y2_cloud = y1_cloud * 1.10
    y2_tot = y2_labour + y2_cloud
    
    y3_labour = y2_labour * 1.05
    y3_cloud = y2_cloud * 1.10
    y3_tot = y3_labour + y3_cloud
    
    tco_data = {
        "year1_build_usd": round(y1_tot, 2),
        "year1_labour_usd": round(y1_labour, 2),
        "year1_cloud_usd": round(y1_cloud, 2),
        "year2_run_usd": round(y2_tot, 2),
        "year2_labour_usd": round(y2_labour, 2),
        "year2_cloud_usd": round(y2_cloud, 2),
        "year3_run_usd": round(y3_tot, 2),
        "year3_labour_usd": round(y3_labour, 2),
        "year3_cloud_usd": round(y3_cloud, 2),
        "total_3year_tco_usd": round(y1_tot + y2_tot + y3_tot, 2),
        "payg_advantage_pct": 46.5,
        "finops_recommendation": "Pay-as-you-go serverless model delivers optimal cost-efficiency for current volume. Transition to Provisioned Throughput (PTU) when request volume exceeds 15,000/day."
    }

    brd = BRDDocument(
        project_title=proj_title,
        client_name=client_name,
        delivery_tier=tier_name,
        tier_kind=tier_info.get("kind", "Base"),
        headline_weight=tier_info.get("headline_weight", 0.289),
        complexity_level=complexity_level,
        complexity_multiplier=COMPLEXITY_MULTIPLIERS.get(complexity_level, 0.85),
        compliance_posture=compliance_posture,
        compliance_multiplier=COMPLIANCE_UPLIFTS.get(compliance_posture, 1.05),
        security_posture=security_posture,
        security_multiplier=SECURITY_UPLIFTS.get(security_posture, 1.00),
        ha_dr_tier=hadr_tier,
        
        start_date=start_date_ans,
        target_end_date=target_end_date_str,
        buffer_capacity_pct=buffer_pct,
        backup_resources=backup_resources_list,
        delivery_model=f"Blended Delivery Model ({geo_ans} Regional Calendar & statutory holidays respected, {daily_hours}h daily working capacity, {buffer_pct}% standby buffer)",
        
        currency_code=currency_code,
        currency_symbol=currency_symbol,
        currency_exchange_rate=currency_rate,
        total_labour_cost_converted=total_labour_converted,
        role_rate_cards=role_rate_cards,
        tco_projection=tco_data,
        ai_act_classification=ai_act_data,
        iso_42001_controls=iso_controls,
        
        executive_summary=(
            f"This Business Requirements Document (BRD) and Engineering Plan establishes the deterministic scope, "
            f"architecture, 12-discipline resource allocation, and cloud infrastructure Bill of Materials for **{proj_title}** "
            f"({tier_name} Tier) for **{client_name}**. Operating on a blended rate of ${rate:.2f}/hour ({currency_symbol}{rate*currency_rate:.2f}/hr {currency_code}), this solution "
            f"leverages {cloud_ans} in {geo_ans} across {int(scale_quantities['ENVS'])} environment(s) to deliver production-grade AI automation. "
            f"Project kick-off is scheduled for **{start_date_ans}** with targeted completion on **{target_end_date_str}**, incorporating {buffer_pct}% standby buffer resource protection."
        ),
        problem_statement=problem_raw,
        solution_summary_six_sentences=solution_summary_six,
        business_impacts=business_impacts,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        ai_interventions=ai_interventions,
        non_ai_interventions=non_ai_interventions,
        user_personas=personas,
        target_architecture_narrative=(
            f"The architecture is a scalable cloud pipeline hosted on {cloud_ans} in the {geo_ans} region. "
            f"It deploys across {int(scale_quantities['ENVS'])} environments using {int(scale_quantities['COMPONENTS'])} "
            f"core microservice components. Model execution is grounded via vector search and structured databases, "
            f"and rendered to {int(scale_quantities['PERSONAS'])} user persona(s) behind Enterprise Single Sign-On."
        ),
        azure_services_used=[{"service": b.sku_or_service, "sku": b.tier, "purpose": b.justification} for b in sizing_bom],
        data_flow_narrative=data_flow,
        responsible_ai_governance=[
            "100% Human-in-the-Loop oversight; AI outputs are assistive recommendations requiring human review for high-impact actions.",
            "Source attribution & provenance: every model response links directly to verified source documentation.",
            "Zero client data retention for foundation model training within the enterprise tenant boundary.",
            "Deterministic temperature controls and automated content safety guardrails."
        ],
        security_compliance=[
            f"Data strictly retained within the regional cloud residency boundary ({geo_ans}).",
            "Managed identity and secret-less authentication between all cloud services (HTTPS / Azure Managed Identities).",
            "Transparent Data Encryption (TDE / Azure Key Vault platform-managed keys) at rest and TLS 1.3 in transit.",
            "Role-Based Access Control (RBAC) integrated with Microsoft Entra ID SSO."
        ],
        risks_mitigations=[
            {"risk": "Data quality or knowledge base gaps degrade response accuracy", "mitigation": "Automated ingestion validation and fallback to human exception queue."},
            {"risk": "User prompt injection or unauthorized access attempts", "mitigation": "Input sanitization, content safety guardrails, and strict RBAC authorization."},
            {"risk": "Scope expansion beyond agreed use cases", "mitigation": "Scope frozen strictly to defined capabilities with formal change control procedures."}
        ],
        legal_categories=legal_categories_list,
        foundation_llm_architecture=foundation_llm,
        grounding_surface_mode=grounding_mode,
        parser_delimiters=parser_delims,
        evaluation_decision_logic=eval_logic,
        technical_components=tech_components,
        sizing_metrics=sizing_metrics,
        sizing_bom=sizing_bom,
        total_duration_weeks=feasibility.resolved_duration_weeks,
        reference_duration_weeks=ref_weeks,
        total_person_days=total_days,
        total_person_hours=total_hours,
        total_labour_cost_usd=total_labour_cost,
        blended_hourly_rate=rate,
        daily_working_hours=daily_hours,
        role_efforts=role_efforts,
        project_phases=phases,
        task_estimates=task_estimates,
        schedule_feasibility=feasibility,
        day_wise_schedule=day_schedule,
        assumptions=assumptions,
        assumption_gate_passed=all(a.status == "Approve" for a in assumptions)
    )
    
    session.brd = brd
    return brd
