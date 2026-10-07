import json
import httpx
import re
import datetime
from typing import Dict, Any, List, Optional, Tuple
from backend.models import (
    BRDDocument, RoleEffort, ProjectPhase, SizingBOM,
    AssumptionItem, AnswerItem, ProjectSession, TaskEstimate,
    TechnicalComponent, SizingMetrics, ScheduleFeasibility, DayWiseTask,
    RequirementItem, CapabilityItem, DataFlowItem, CalculationLedgerItem, HITLGates
)
from backend.config import get_settings
from backend.llm_gateway import LLMGateway
from backend.canonical_generator import (
    build_canonical_requirements, build_capabilities_catalog,
    build_canonical_data_flows, build_calculation_ledger
)
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
    # 1. Computer Vision
    if any(k in raw for k in ["defect", "surface inspection", "manufacturing quality", "wafer", "pcb", "crack", "industrial vision"]):
        return "cv_defect_detection"
    if any(k in raw for k in ["camera", "video stream", "surveillance", "traffic", "yolo", "cctv", "object detection", "tracking", "face recognition", "biometric"]):
        return "cv_object_detection"
    if any(k in raw for k in ["invoice", "receipt", "form", "ocr", "layoutlm", "scanned document", "document extraction"]):
        return "cv_ocr_document"
        
    # 2. Deep Learning & Speech/Voice
    if any(k in raw for k in ["speech", "voice", "transcription", "asr", "whisper", "call recording", "audio", "tts", "speech-to-text"]):
        return "dl_speech_voice"
    if any(k in raw for k in ["deep learning", "neural network", "transformer model", "custom embedding", "signal processing"]):
        return "dl_custom_neural"
        
    # 3. Classical Machine Learning
    if any(k in raw for k in ["forecast", "time-series", "timeseries", "demand planning", "inventory prediction", "prophet", "arima"]):
        return "ml_forecasting_timeseries"
    if any(k in raw for k in ["fraud", "aml", "anti-money", "transaction risk", "claims anomaly", "anomaly detection", "credit default"]):
        return "ml_fraud_anomaly"
    if any(k in raw for k in ["recommend", "personalization", "collaborative filter", "two-tower", "ranking", "upsell"]):
        return "ml_recommendation"
    if any(k in raw for k in ["churn", "lead score", "propensity", "regression", "classification", "tabular", "xgboost", "random forest"]):
        return "ml_predictive_tabular"
        
    # 4. Natural Language Processing
    if any(k in raw for k in ["ner", "entity recognition", "sentiment", "topic modeling", "translation", "spacy", "deberta", "bert"]):
        return "nlp_text_analytics"
        
    # 5. Generative AI
    if any(k in raw for k in ["contract", "clause", "risk register", "legal", "lease", "vendor agreement"]):
        return "contract_intelligence"
    if any(k in raw for k in ["chat", "bot", "support", "customer", "virtual agent", "helpdesk", "faq"]):
        return "customer_support"
    if any(k in raw for k in ["copilot", "code generation", "developer assistant", "unit test", "code review"]):
        return "genai_code_copilot"
    if any(k in raw for k in ["agentic", "multi-agent", "autonomous agent", "langgraph", "crewai", "autogen", "react"]):
        return "genai_agentic_workflow"
    if any(k in raw for k in ["search", "knowledge", "rag", "wiki", "documentation", "enterprise search", "semantic search"]):
        return "genai_rag_knowledge"
        
    return "general_ai"

def generate_technical_components_dynamic(cloud_platform: str, domain: str, project_title: str) -> List[TechnicalComponent]:
    cloud_lower = cloud_platform.lower()
    is_gcp = "google" in cloud_lower or "gcp" in cloud_lower
    is_aws = "aws" in cloud_lower or "amazon" in cloud_lower
    is_ibm = "ibm" in cloud_lower or "watson" in cloud_lower
    is_onprem = "on-prem" in cloud_lower or "hybrid" in cloud_lower or "private" in cloud_lower or "local" in cloud_lower
    
    # -------------------------------------------------------------
    # 1. Computer Vision (Defect Detection & Object Vision)
    # -------------------------------------------------------------
    if domain in ["cv_defect_detection", "cv_object_detection"]:
        if is_aws:
            c1_tech = "Amazon S3 + AWS IoT Greengrass / Kinesis Video Streams"
            c2_tech = "Amazon SageMaker Feature Store + OpenSearch Serverless"
            c3_tech = "Amazon SageMaker Endpoint (YOLOv8 / RT-DETR on g5.xlarge GPU)"
            c4_tech = "Amazon DynamoDB / Aurora Serverless v2"
            c5_tech = "Custom Python CV Evaluation Harness (mAP50, IoU, Recall & Precision Scorer)"
            c6_tech = "AWS ECS Fargate + Amazon Cognito SSO + CloudWatch"
        elif is_gcp:
            c1_tech = "Google Cloud Storage + Cloud Video Intelligence / Vertex AI Vision"
            c2_tech = "Vertex AI Feature Store + Vertex AI Vector Search"
            c3_tech = "Vertex AI Custom Model Endpoint (NVIDIA L4 / A100 GPU)"
            c4_tech = "Google Cloud SQL (PostgreSQL) / Firestore"
            c5_tech = "Automated Visual Inspection Scorer & Confusion Matrix Evaluator"
            c6_tech = "Google Cloud Run + Cloud Identity SSO"
        elif is_ibm:
            c1_tech = "IBM Cloud Object Storage + IBM Maximo Visual Inspection"
            c2_tech = "IBM Cloud Pak for Data Feature Catalog"
            c3_tech = "WatsonX.ai / Custom Vision Inference Container on Red Hat OpenShift"
            c4_tech = "IBM Cloud Databases for PostgreSQL"
            c5_tech = "Automated Defect & Object Accuracy Benchmark Suite"
            c6_tech = "IBM Cloud Code Engine / OpenShift Dashboard + IBM Cloud IAM"
        elif is_onprem:
            c1_tech = "Local RTSP Camera Feed / Edge Buffer + MinIO S3 Object Storage"
            c2_tech = "Milvus / Qdrant Vector Store on Kubernetes"
            c3_tech = "Triton Inference Server with NVIDIA TensorRT (H100 / L40S Local GPU)"
            c4_tech = "PostgreSQL 16 Enterprise Cluster with High Availability"
            c5_tech = "Automated Frame-by-Frame mAP & IoU Benchmark Evaluation Suite"
            c6_tech = "On-Premises React/FastAPI Cockpit + Keycloak OIDC SSO"
        else: # Azure
            c1_tech = "Azure Blob Storage + Azure Video Indexer / IoT Edge"
            c2_tech = "Azure AI Search + Azure Cosmos DB Metadata Store"
            c3_tech = "Azure Machine Learning Managed GPU Endpoint (Standard_NC6s_v3)"
            c4_tech = "Azure SQL Database Serverless / Azure Table Storage"
            c5_tech = "Automated Vision Evaluation Harness (mAP, F1-Score & False Alarm Scorer)"
            c6_tech = "Azure App Service / Container Apps + Microsoft Entra ID SSO"

        return [
            TechnicalComponent(
                id="C001",
                name="High-Throughput Vision Data Ingestion & Frame Preprocessing Layer",
                purpose=f"Captures high-resolution camera feeds, image snapshots, and video frames, performing normalization, resizing, and optical calibration.",
                technology_choice=c1_tech,
                key_design_decisions="Decoupled edge ingestion pipeline with zero dropped frames; lossless compressed landing store.",
                interfaces_in_out="In: Industrial camera feeds, RTSP streams, and batch uploads. Out: Normalized tensor arrays to C002 and C003.",
                data_classification="Internal industrial images and inspection frames (Confidential).",
                scalability_performance="Processes up to 60 FPS real-time video streams with sub-30ms frame intake latency.",
                security_rai_controls="Device certificate authentication (mTLS), tamper-evident stream logging.",
                failure_modes_mitigation="Local disk buffering on network drops with automatic spooling upon reconnect.",
                dependencies="Camera Edge Hardware, Secure Network Gateway"
            ),
            TechnicalComponent(
                id="C002",
                name="Visual Feature & Metadata Indexing Store",
                purpose="Indexes image embeddings, bounding box coordinates, camera identifiers, and timestamp metadata for historical analytics.",
                technology_choice=c2_tech,
                key_design_decisions="Stores multi-dimensional feature vectors with temporal partitioning for instant retrospective defect analysis.",
                interfaces_in_out="In: Frame features from C001. Out: Historical match candidates to C003.",
                data_classification="Inspection feature vectors and metadata (Confidential).",
                scalability_performance="Sub-50ms query latency over millions of visual event records.",
                security_rai_controls="Role-based access controls; isolated private network endpoints.",
                failure_modes_mitigation="Automatic index replica failover.",
                dependencies="C001 Ingestion Store"
            ),
            TechnicalComponent(
                id="C003",
                name="Deep Computer Vision Inference & Anomaly Detection Engine",
                purpose="Executes real-time object detection, segmentation, and surface defect classification with millimeter-level bounding boxes.",
                technology_choice=c3_tech,
                key_design_decisions="Optimized TensorRT / ONNX GPU runtime ensuring low latency and deterministic inference throughput.",
                interfaces_in_out="In: Preprocessed image tensors from C001. Out: Classified bounding boxes, defect tags, and confidence scores to C004.",
                data_classification="Inference payloads and prediction confidence scores (Confidential).",
                scalability_performance="High-concurrency GPU batching with sub-25ms per-frame inference latency.",
                security_rai_controls="Strict confidence gating (≥95% precision threshold); low-confidence frames routed to human QA.",
                failure_modes_mitigation="Circuit breaker routes transient GPU spikes to secondary inference pool.",
                dependencies="C001 Frame Preprocessing, GPU Inference Hardware"
            ),
            TechnicalComponent(
                id="C004",
                name="Inspection Findings, Defect Ledger & Analytics Database",
                purpose="Persists defect records, bounding box coordinates, production line telemetry, and operator sign-off audit logs.",
                technology_choice=c4_tech,
                key_design_decisions="Relational schema with spatial/bounding box coordinates and foreign keys to source image storage.",
                interfaces_in_out="In: Detection events from C003. Out: Telemetry to C006 Cockpit.",
                data_classification="Production quality audit data (Confidential).",
                scalability_performance="High-write throughput supporting continuous manufacturing shifts.",
                security_rai_controls="Transparent Data Encryption (TDE), immutable audit trail.",
                failure_modes_mitigation="Write-ahead logging and point-in-time recovery.",
                dependencies="Enterprise Cloud Network, Managed Identity"
            ),
            TechnicalComponent(
                id="C005",
                name="Automated Vision Benchmark & Quality Scorer",
                purpose="Evaluates model precision, recall, mAP50, and false positive rates against curated golden ground-truth defect benchmarks.",
                technology_choice=c5_tech,
                key_design_decisions="Automated nightly regression suite validating accuracy against edge cases before model promotion.",
                interfaces_in_out="In: Golden benchmark image datasets. Out: Confusion matrix and mAP scorecard.",
                data_classification="Anonymized evaluation datasets.",
                scalability_performance="Evaluates 1,000 benchmark images in under 5 minutes.",
                security_rai_controls="Deterministic test harness with strict pass/fail quality gates.",
                failure_modes_mitigation="Regression warnings halt deployment pipeline.",
                dependencies="C003 Vision Engine, Golden Test Suite"
            ),
            TechnicalComponent(
                id="C006",
                name="Quality Inspection Cockpit & Operator Review Dashboard",
                purpose="Provides plant operators and quality engineers with real-time visual inspection alerts, overlay bounding boxes, and sign-offs.",
                technology_choice=c6_tech,
                key_design_decisions="Split-screen UI showing live video stream alongside detected defect overlays and 1-click manual verification.",
                interfaces_in_out="In: HTTPS browser sessions via SSO. Out: REST API queries to C004.",
                data_classification="Encrypted session traffic (TLS 1.3).",
                scalability_performance="Supports simultaneous multi-line operator stations with sub-second alert rendering.",
                security_rai_controls="Corporate SSO, RBAC operator privileges, session timeouts.",
                failure_modes_mitigation="Local client cache prevents interruption during brief network blips.",
                dependencies="Enterprise Identity Provider, C004 Database"
            )
        ]

    # -------------------------------------------------------------
    # 2. Classical Machine Learning (Predictive Tabular, Churn, Forecasting, Fraud)
    # -------------------------------------------------------------
    elif domain in ["ml_predictive_tabular", "ml_forecasting_timeseries", "ml_fraud_anomaly", "ml_recommendation", "fraud_financial"]:
        if is_aws:
            c1_tech = "Amazon S3 + AWS Glue ETL / Amazon Kinesis Data Streams"
            c2_tech = "Amazon SageMaker Feature Store + Amazon OpenSearch"
            c3_tech = "Amazon SageMaker Real-Time Endpoint (XGBoost / LightGBM / Prophet)"
            c4_tech = "Amazon Aurora Serverless v2 (PostgreSQL) / DynamoDB"
            c5_tech = "SageMaker Model Monitor & Python Evaluation Suite (AUC-ROC / RMSE / F1)"
            c6_tech = "AWS ECS Fargate + Cognito SSO + CloudWatch"
        elif is_gcp:
            c1_tech = "Google Cloud Storage + Cloud Dataflow / BigQuery"
            c2_tech = "Vertex AI Feature Store"
            c3_tech = "Vertex AI Prediction Endpoint / BigQuery ML (AutoML & Custom XGBoost)"
            c4_tech = "Google Cloud SQL (PostgreSQL) / BigQuery Datastore"
            c5_tech = "Vertex AI Model Monitoring & Automated Backtesting Harness"
            c6_tech = "Google Cloud Run + Cloud Identity SSO"
        elif is_ibm:
            c1_tech = "IBM Cloud Object Storage + DataStage ETL"
            c2_tech = "IBM Cloud Pak for Data Feature Catalog"
            c3_tech = "Watson Machine Learning (AutoAI / Custom Python ML Models)"
            c4_tech = "IBM Cloud Databases for PostgreSQL"
            c5_tech = "Watson OpenScale Model Drift & Accuracy Monitor"
            c6_tech = "IBM Cloud Code Engine / OpenShift Dashboard + IBM Cloud IAM"
        elif is_onprem:
            c1_tech = "Kafka / Spark Streaming + MinIO Object Storage"
            c2_tech = "Feast Feature Store on Kubernetes"
            c3_tech = "Triton Inference Server / FastAPI Python ML Model Server"
            c4_tech = "PostgreSQL 16 Enterprise Cluster"
            c5_tech = "Evidently AI / MLflow Drift & Accuracy Evaluation Suite"
            c6_tech = "On-Premises React/FastAPI Cockpit + Keycloak SSO"
        else: # Azure
            c1_tech = "Azure Blob Storage + Azure Data Factory ETL / Event Hubs"
            c2_tech = "Azure Machine Learning Feature Store"
            c3_tech = "Azure Machine Learning Managed Online Endpoint (XGBoost / CatBoost / ARIMA)"
            c4_tech = "Azure SQL Database Serverless / Cosmos DB"
            c5_tech = "Azure ML Model Data Collector & Automated Backtesting Harness"
            c6_tech = "Azure App Service / Container Apps + Microsoft Entra ID SSO"

        return [
            TechnicalComponent(
                id="C001",
                name="Data Ingestion, Schema Validation & Feature Extraction Pipeline",
                purpose=f"Ingests batch historical datasets and real-time event streams, performing automated data cleaning, type validation, and feature transformations.",
                technology_choice=c1_tech,
                key_design_decisions="Automated data drift checks at ingestion; decoupled batch and streaming ingestion paths.",
                interfaces_in_out="In: Batch CSV/Parquet uploads, ERP/CRM database connectors, and event streams. Out: Clean feature matrices to C002 and C003.",
                data_classification="Enterprise financial/operational data (Confidential). Encrypted in transit and at rest.",
                scalability_performance="Processes multi-gigabyte feature tables in under 10 minutes.",
                security_rai_controls="Column-level data masking, TLS 1.3 encryption, IAM managed identities.",
                failure_modes_mitigation="Quarantine corrupted input records to error dead-letter queue with alert.",
                dependencies="Data Warehouse / Data Lake, ETL Pipelines"
            ),
            TechnicalComponent(
                id="C002",
                name="Central Feature Store & Historical Training Store",
                purpose="Maintains curated, point-in-time correct online and offline feature tables to prevent training-serving skew.",
                technology_choice=c2_tech,
                key_design_decisions="Low-latency online feature retrieval coupled with scalable offline time-travel feature logging.",
                interfaces_in_out="In: Features from C001. Out: Online feature vectors to C003 inference engine.",
                data_classification="Calculated feature metrics and entity profiles (Confidential).",
                scalability_performance="Sub-15ms online feature lookup latency.",
                security_rai_controls="Fine-grained RBAC permissions on feature groups.",
                failure_modes_mitigation="Fallback to last-known feature snapshot if online store sync encounters delay.",
                dependencies="C001 Feature Pipeline, Cloud Network"
            ),
            TechnicalComponent(
                id="C003",
                name="Predictive ML Model Inference & Scoring Engine",
                purpose="Generates real-time predictions, probability scores, SHAP feature attributions, and anomaly flags.",
                technology_choice=c3_tech,
                key_design_decisions="Ensemble architecture combining gradient boosting with calibrated probability estimators and SHAP explainability.",
                interfaces_in_out="In: Online feature vector from C002. Out: Risk scores, forecasts, and feature attributions to C004.",
                data_classification="Inference requests and output predictions (Confidential).",
                scalability_performance="Auto-scales compute endpoints with sub-50ms p95 prediction latency.",
                security_rai_controls="Explainable AI (SHAP/LIME) on every output; automated thresholding prevents ungrounded predictions.",
                failure_modes_mitigation="Graceful fallback to baseline heuristic scoring model during endpoint maintenance.",
                dependencies="C002 Feature Store, Cloud ML Compute"
            ),
            TechnicalComponent(
                id="C004",
                name="Prediction Store, Decision Ledger & Audit Repository",
                purpose="Stores prediction outcomes, confidence scores, explainability attributions, and business review statuses.",
                technology_choice=c4_tech,
                key_design_decisions="Relational schema with point-in-time timestamping for complete auditability and compliance verification.",
                interfaces_in_out="In: Predictions from C003. Out: Data feeds to C006 Cockpit and downstream CRM/ERP.",
                data_classification="Scored transactions, risk registers, and decision records (Confidential).",
                scalability_performance="High-concurrency indexed relational queries.",
                security_rai_controls="Row-level security, automated encrypted backups.",
                failure_modes_mitigation="Automated connection retry policies and transactional rollback.",
                dependencies="Cloud Database, IAM Role Assignment"
            ),
            TechnicalComponent(
                id="C005",
                name="Model Performance, Drift Monitor & Backtesting Harness",
                purpose="Continuously evaluates model performance, tracking AUC-ROC, precision/recall, RMSE, and feature distribution drift.",
                technology_choice=c5_tech,
                key_design_decisions="Automated scheduled backtesting against realized ground-truth outcomes; drift detection triggers automated retraining alerts.",
                interfaces_in_out="In: Ground-truth realized outcomes and prediction logs from C004. Out: Performance scorecards and drift alerts.",
                data_classification="Aggregated model telemetry and benchmark scorecards.",
                scalability_performance="Executes full backtest against 100k records in under 3 minutes.",
                security_rai_controls="Strict statistical confidence intervals with automated alert thresholds.",
                failure_modes_mitigation="Drift alerts proactively dispatched to ML engineering team.",
                dependencies="C004 Prediction Store, Evaluation Harness"
            ),
            TechnicalComponent(
                id="C006",
                name="Predictive Analytics Cockpit & Business Decision Dashboard",
                purpose="Provides business stakeholders and risk analysts with interactive dashboards, feature importance breakdowns, and review actions.",
                technology_choice=c6_tech,
                key_design_decisions="Interactive split-screen dashboard displaying top risk factors, prediction confidence, and 1-click decision approvals.",
                interfaces_in_out="In: HTTPS browser sessions via Enterprise SSO. Out: REST API queries to C004.",
                data_classification="Encrypted HTTPS session traffic (TLS 1.3).",
                scalability_performance="Responsive web dashboard supporting hundreds of concurrent business users.",
                security_rai_controls="Corporate SSO (Entra ID / Cognito / Okta), RBAC permissions, audit logging.",
                failure_modes_mitigation="Client-side caching ensures dashboard accessibility during transient network blips.",
                dependencies="Enterprise Identity Provider, C004 Store"
            )
        ]

    # -------------------------------------------------------------
    # 3. Deep Learning & Speech / Voice AI
    # -------------------------------------------------------------
    elif domain in ["dl_speech_voice", "dl_custom_neural"]:
        if is_aws:
            c1_tech = "Amazon S3 + Amazon Transcribe / Bedrock Whisper"
            c2_tech = "Amazon OpenSearch Serverless (Titan Embeddings)"
            c3_tech = "Amazon Bedrock (Claude 3.5 Sonnet) / SageMaker GPU Endpoint"
            c4_tech = "Amazon Aurora Serverless v2 (PostgreSQL)"
            c5_tech = "Automated WER (Word Error Rate) & Intent Accuracy Scorer"
            c6_tech = "AWS ECS Fargate + Cognito SSO"
        elif is_gcp:
            c1_tech = "Google Cloud Storage + Cloud Speech-to-Text / Chirp"
            c2_tech = "Vertex AI Vector Search"
            c3_tech = "Vertex AI (Gemini 2.5 Flash Multimodal Audio)"
            c4_tech = "Google Cloud SQL (PostgreSQL)"
            c5_tech = "Automated Speech Transcription & Intent Benchmark Suite"
            c6_tech = "Google Cloud Run + Cloud Identity SSO"
        elif is_ibm:
            c1_tech = "IBM Cloud Object Storage + Watson Speech to Text"
            c2_tech = "Watson Discovery Index"
            c3_tech = "WatsonX.ai (Granite / Llama Models)"
            c4_tech = "IBM Cloud Databases for PostgreSQL"
            c5_tech = "Watson Speech Quality & WER Scorer"
            c6_tech = "IBM Cloud OpenShift / Code Engine + IBM Cloud IAM"
        elif is_onprem:
            c1_tech = "Local Audio Ingestion + MinIO Object Storage"
            c2_tech = "Qdrant / Milvus Vector Store on Kubernetes"
            c3_tech = "Whisper.cpp / Faster-Whisper on NVIDIA Local GPUs + vLLM"
            c4_tech = "PostgreSQL 16 Enterprise Cluster"
            c5_tech = "Automated Word Error Rate (WER) & ROUGE Scorer Harness"
            c6_tech = "On-Premises React Dashboard + Keycloak SSO"
        else: # Azure
            c1_tech = "Azure Blob Storage + Azure Speech Services / Azure OpenAI Whisper"
            c2_tech = "Azure AI Search (text-embedding-3-small)"
            c3_tech = "Azure OpenAI Service (GPT-4o / GPT-5 Audio & Reasoning)"
            c4_tech = "Azure SQL Database Serverless"
            c5_tech = "Automated Speech Accuracy & Transcription Evaluation Suite"
            c6_tech = "Azure App Service + Microsoft Entra ID SSO"

        return [
            TechnicalComponent(
                id="C001",
                name="Audio Ingestion, Speech-to-Text & Diarization Pipeline",
                purpose=f"Ingests real-time call audio and batch voice recordings, performing noise reduction, speaker diarization, and time-aligned transcription.",
                technology_choice=c1_tech,
                key_design_decisions="Multi-channel audio separation with speaker timestamping; raw audio encrypted and archived for compliance.",
                interfaces_in_out="In: Telephony SIP feeds, WAV/MP3 uploads. Out: Time-aligned transcripts with speaker tags to C002 and C003.",
                data_classification="Voice recordings and customer conversational PII (Confidential). PII redacted before downstream processing.",
                scalability_performance="Transcribes 60-minute audio files in under 45 seconds with sub-5% Word Error Rate (WER).",
                security_rai_controls="Automated PII scrubbing, TLS 1.3 audio streaming, platform-managed encryption.",
                failure_modes_mitigation="Automatic retry on noisy audio packets with fallback to conservative acoustic model.",
                dependencies="Telephony Gateway, Cloud Speech Service"
            ),
            TechnicalComponent(
                id="C002",
                name="Transcript Search & Conversational Embedding Index",
                purpose="Indexes voice transcripts, utterance embeddings, customer sentiments, and call metadata for fast semantic search.",
                technology_choice=c2_tech,
                key_design_decisions="Dense conversational embeddings paired with metadata filters on agent ID, call outcome, and duration.",
                interfaces_in_out="In: Transcripts from C001. Out: Relevant conversational context to C003.",
                data_classification="Conversational transcripts and semantic embeddings (Confidential).",
                scalability_performance="Sub-60ms semantic search latency across hundreds of thousands of historical calls.",
                security_rai_controls="Role-based call access control; private virtual network endpoints.",
                failure_modes_mitigation="Index replica failover.",
                dependencies="C001 Speech Ingestion Pipeline"
            ),
            TechnicalComponent(
                id="C003",
                name="Voice Intelligence, Intent Extraction & Sentiment Reasoning Engine",
                purpose="Extracts customer intents, compliance adherence, sentiment progression, and action items from call transcripts.",
                technology_choice=c3_tech,
                key_design_decisions="Structured prompt templates with deterministic schema output for compliance checklist validation.",
                interfaces_in_out="In: Clean transcripts from C001. Out: Compliance scores, intent tags, and summaries to C004.",
                data_classification="Call analysis findings and compliance scorecards (Confidential).",
                scalability_performance="Processes multi-turn dialogue analysis with p95 response time under 1.2 seconds.",
                security_rai_controls="Guardrails against hallucinations; 100% sentence-level citation back to audio timestamp.",
                failure_modes_mitigation="Low-confidence intent classifications flagged for supervisor review.",
                dependencies="C001 Transcripts, Cloud LLM Endpoint"
            ),
            TechnicalComponent(
                id="C004",
                name="Call Telemetry, Compliance Ledger & Analytics Database",
                purpose="Central structured database storing call metadata, compliance verdicts, sentiment scores, and agent QA metrics.",
                technology_choice=c4_tech,
                key_design_decisions="Relational schema linking audio files, transcripts, timestamps, and compliance findings.",
                interfaces_in_out="In: Insights from C003. Out: Data to C006 Cockpit.",
                data_classification="Structured call QA findings (Confidential).",
                scalability_performance="High-concurrency indexed relational queries.",
                security_rai_controls="Transparent Data Encryption (TDE), automated retention lifecycle.",
                failure_modes_mitigation="Automated connection pool retry policies.",
                dependencies="Cloud Database, Managed Identity"
            ),
            TechnicalComponent(
                id="C005",
                name="Automated WER & Transcription Benchmark Scorer",
                purpose="Evaluates Word Error Rate (WER), speaker attribution accuracy, and intent classification against golden audio benchmarks.",
                technology_choice=c5_tech,
                key_design_decisions="Nightly benchmark suite testing accuracy against varied accents, background noises, and acoustic conditions.",
                interfaces_in_out="In: Golden transcribed audio datasets. Out: WER and BLEU accuracy reports.",
                data_classification="Anonymized evaluation audio datasets.",
                scalability_performance="Evaluates 100 hours of benchmark audio in under 20 minutes.",
                security_rai_controls="Deterministic test harness with strict pass/fail gates.",
                failure_modes_mitigation="Regression alerts dispatched to engineering team.",
                dependencies="C003 Reasoning Engine, Golden Audio Suite"
            ),
            TechnicalComponent(
                id="C006",
                name="Voice Analytics Cockpit & QA Supervisor Dashboard",
                purpose="Interactive web application for contact center supervisors, providing audio playback with synchronized transcript highlighting and QA scoring.",
                technology_choice=c6_tech,
                key_design_decisions="Audio waveform player synchronized with transcript text and 1-click compliance validation.",
                interfaces_in_out="In: HTTPS browser sessions via SSO. Out: REST API queries to C004.",
                data_classification="Encrypted HTTPS session traffic (TLS 1.3).",
                scalability_performance="Supports hundreds of concurrent supervisor sessions.",
                security_rai_controls="Corporate SSO, RBAC supervisor roles, session timeouts.",
                failure_modes_mitigation="Client-side error boundaries with offline state recovery.",
                dependencies="Enterprise Identity Provider, C004 Database"
            )
        ]

    # -------------------------------------------------------------
    # 4. Generative AI, RAG, Agentic & Customer Support (Default)
    # -------------------------------------------------------------
    elif domain == "customer_support":
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
    elif domain == "contract_intelligence":
        c1_tech = "Azure Blob Storage + Azure AI Document Intelligence" if not (is_gcp or is_aws) else ("Google Cloud Storage + Document AI" if is_gcp else "Amazon S3 + Amazon Textract")
        c2_tech = "Managed search and vector store native to Microsoft Azure (Azure AI Search)" if not (is_gcp or is_aws) else ("Vertex AI Vector Search" if is_gcp else "Amazon OpenSearch Serverless")
        c3_tech = "Azure OpenAI Service (GPT-4o / GPT-5 Thinking / Reasoning)" if not (is_gcp or is_aws) else ("Vertex AI (Gemini 2.5 Flash / Pro)" if is_gcp else "Amazon Bedrock (Claude 3.5 Sonnet)")
        c4_tech = "Azure-native managed structured / relational store (Azure SQL / PostgreSQL)" if not (is_gcp or is_aws) else ("Google Cloud SQL" if is_gcp else "Amazon Aurora Serverless")
        c5_tech = "Azure-native dashboard & Python automated evaluation harness"
        c6_tech = "Microsoft Entra ID SSO + Azure Key Vault + Landing Zone Resource Groups" if not (is_gcp or is_aws) else ("Google Cloud Identity + Secret Manager" if is_gcp else "AWS Cognito + Secrets Manager")

        return [
            TechnicalComponent(
                id="C001",
                name="Contract Landing Store and Ingestion Pipeline",
                purpose=f"Holds authoritative contract samples supplied in Azure Blob Storage and drives layout extraction, chunking, and embedding.",
                technology_choice=c1_tech,
                key_design_decisions="Preserves raw input documents immutably; extracts layout boundaries, page numbers, and bounding-box coordinates for 100% clause-level traceability.",
                interfaces_in_out="In: Legal operations uploads to Blob container. Out: Calls Document Intelligence; writes chunks and embeddings to C002 and document records to C004.",
                data_classification="Executed commercial contracts (Confidential under internal policy).",
                scalability_performance="Scales via asynchronous batch workers; bounded by Document Intelligence request throughput in India region.",
                security_rai_controls="Read-only landing container access; managed identities preferred over shared keys; platform-managed encryption.",
                failure_modes_mitigation="Unprocessable layouts quarantined to exceptions list on dashboard; pipeline resumes from last completed document and pass.",
                dependencies="C002 Vector Store, C004 Store, Azure Blob Storage"
            ),
            TechnicalComponent(
                id="C002",
                name="Clause Index and Retrieval Layer",
                purpose="Stores clause-level chunks with embeddings and metadata, serving targeted retrieval to classification, extraction passes, and assessment.",
                technology_choice=c2_tech,
                key_design_decisions="Hybrid retrieval combining keyword and vector matching; metadata carries document ID, category, clause type, page, and coordinates.",
                interfaces_in_out="In: C001 writes chunks, embeddings, and metadata. Out: Ranked candidate chunks with provenance metadata to C003.",
                data_classification="Clause-level text fragments and embeddings (Confidential).",
                scalability_performance="Sub-100ms retrieval latency across contract clause chunks.",
                security_rai_controls="Restricted to project managed identities; mandatory provenance metadata on every chunk.",
                failure_modes_mitigation="Graceful retry on transient index latency; poor recall detected per clause type by evaluation harness.",
                dependencies="C001 Ingestion Pipeline, Azure AI Search"
            ),
            TechnicalComponent(
                id="C003",
                name="Classification, Multi-Pass Extraction & Principle Assessment Engine",
                purpose="Classifies contracts into 6 categories, extracts agreed clauses across multi-pass runs, and assesses clauses against contracting principles.",
                technology_choice=c3_tech,
                key_design_decisions="Multi-pass extraction: pass 1 extracts standard clauses; follow-up targeted passes resolve vague or negotiated terms. Assessment produces Agree / Agree with Management Approval / Not Agree.",
                interfaces_in_out="In: Document text & chunks from C002. Out: Structured clause records, assessment rationales, and pass provenance to C004.",
                data_classification="Contract clause prompts and structured assessment outputs (Confidential).",
                scalability_performance="Parallel document and clause-item processing; token quota managed with backoff retries.",
                security_rai_controls="No automated un-gated decision making; ungrounded findings flagged unsupported; zero data retention for training.",
                failure_modes_mitigation="Model throttling handled with exponential backoff; runaway loops prevented by agreed maximum pass count.",
                dependencies="C002 Retrieval Layer, Azure OpenAI Service, C004 Store"
            ),
            TechnicalComponent(
                id="C004",
                name="Ontology, Principle Configuration and Risk Register Store",
                purpose="Stores contract ontologies, contracting principles, extracted clause records with pass provenance, exceptions, and risk registers.",
                technology_choice=c4_tech,
                key_design_decisions="Ontology and principles stored as configuration data (not hardcoded); risk register schema extends existing spreadsheet format with clause-level deep links.",
                interfaces_in_out="In: C001 writes document records, C003 writes clause records and assessments. Out: C005 reads for dashboard and file exports.",
                data_classification="Structured risk registers, ontologies, and exception records (Confidential).",
                scalability_performance="Relational schema with index optimization; 12-month retention enforcement.",
                security_rai_controls="Access restricted to named project team; mandatory source clause, page, and coordinate references.",
                failure_modes_mitigation="Partial writes rejected at write time; each record stamped with configuration version for reproducibility.",
                dependencies="Azure Database / Cosmos DB, Managed Identity"
            ),
            TechnicalComponent(
                id="C005",
                name="Evaluation Harness, Dashboard and Operational Telemetry",
                purpose="Scores classification and extraction against legal-confirmed benchmark sets, presents risk visibility dashboards, and tracks token costs.",
                technology_choice=c5_tech,
                key_design_decisions="Evaluation harness runs outside runtime path; splits first-pass and multi-pass accuracy metrics; dashboard surfaces risk by category, deviations, and exceptions.",
                interfaces_in_out="In: Reads findings and pass provenance from C004; reads legal benchmark ground truth. Out: Renders dashboard and produces accuracy reports.",
                data_classification="Risk findings and benchmark scorecards.",
                scalability_performance="Lightweight dashboard serving validation reviewers; evaluation runs benchmark set in under 15 minutes.",
                security_rai_controls="Read-only dashboard behind corporate SSO; all displayed findings link back to exact source clause and page.",
                failure_modes_mitigation="Dashboard downtime mitigated by direct risk register file exports; incomplete benchmarks flagged loudly.",
                dependencies="C004 Store, Azure App Service / Dashboard"
            ),
            TechnicalComponent(
                id="C006",
                name="Identity, Secrets and Environment Landing Zone",
                purpose="Provides corporate Single Sign-On, manages secrets and encryption keys, and provisions Dev, Test, and UAT resource groups in non-production.",
                technology_choice=c6_tech,
                key_design_decisions="Dedicated resource groups in existing non-production subscription; managed identities preferred over shared keys; platform-managed encryption.",
                interfaces_in_out="In: SSO authentication requests. Out: Issues tokens and managed identities to C001-C005; secrets to project identities.",
                data_classification="Identity claims and secret connection strings.",
                scalability_performance="Scales with named project user group.",
                security_rai_controls="Single Sign-On (SSO) with access limited to named project group; secrets never stored in code or config files.",
                failure_modes_mitigation="Scripted environment provisioning prevents environment drift across Dev, Test, and UAT.",
                dependencies="Azure Subscription, Corporate Identity Provider"
            )
        ]
    else:
        # Default Universal General AI / Enterprise RAG components
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
    is_ibm = "ibm" in cloud_lower or "watson" in cloud_lower
    is_onprem = "on-prem" in cloud_lower or "hybrid" in cloud_lower or "private" in cloud_lower or "local" in cloud_lower
    
    if is_onprem:
        base_cost = 450.0
    elif is_ibm:
        base_cost = 620.0
    elif is_gcp:
        base_cost = 580.0
    elif is_aws:
        base_cost = 610.0
    else:
        base_cost = 645.0 # Azure baseline
        
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
    elif is_ibm:
        bom = [
            SizingBOM(
                component="C001: Object Storage",
                sku_or_service="IBM Cloud Object Storage (Standard)",
                tier="Standard PayG",
                quantity="50 GB Raw / Archive",
                monthly_cost_usd=round(17.0 * ha_mult, 2),
                justification="Secure object landing storage for raw corpora, datasets, and documents."
            ),
            SizingBOM(
                component="C002: Watson Discovery Index",
                sku_or_service="IBM Watson Discovery (Plus Plan)",
                tier="Plus Tier",
                quantity="1 Index Collection",
                monthly_cost_usd=round(220.0 * ha_mult, 2),
                justification="Semantic document indexing, enrichment, and NLP entity extraction."
            ),
            SizingBOM(
                component="C003: WatsonX.ai GenAI",
                sku_or_service="IBM WatsonX.ai (Granite 20b & Llama 3.3)",
                tier="Standard Tokens PayG",
                quantity=f"{daily_requests:,} Requests/Day",
                monthly_cost_usd=round(185.0 * ha_mult, 2),
                justification="Powers domain reasoning, summarization, and compliance analysis."
            ),
            SizingBOM(
                component="C004: Cloud Databases",
                sku_or_service="IBM Cloud Databases for PostgreSQL",
                tier="Standard (2 vCPU, 8 GB RAM)",
                quantity="1 Database Cluster",
                monthly_cost_usd=round(68.0 * ha_mult, 2),
                justification="Stores structured finding registers, ontologies, and user sessions."
            ),
            SizingBOM(
                component="C006: OpenShift / Code Engine",
                sku_or_service="IBM Cloud Code Engine + Secrets Manager + IAM",
                tier="Serverless Compute",
                quantity="1 Code Engine App",
                monthly_cost_usd=round(30.0 * ha_mult, 2),
                justification="Hosts containerized discovery cockpit and enterprise SSO integration."
            )
        ]
    elif is_onprem:
        bom = [
            SizingBOM(
                component="C001: MinIO Storage",
                sku_or_service="MinIO S3-Compatible Storage on Kubernetes",
                tier="On-Premises Infrastructure",
                quantity="1 TB Local NVMe Volume",
                monthly_cost_usd=round(45.0 * ha_mult, 2),
                justification="Local S3-compatible object landing zone and artifact repository."
            ),
            SizingBOM(
                component="C002: Milvus Vector DB",
                sku_or_service="Milvus / Qdrant Distributed on Kubernetes",
                tier="Local Cluster (4 Pods)",
                quantity="1 Deployed Vector Cluster",
                monthly_cost_usd=round(80.0 * ha_mult, 2),
                justification="Ultra-fast local semantic vector search and metadata filtering."
            ),
            SizingBOM(
                component="C003: GPU Inference Server",
                sku_or_service="Triton Inference Server / vLLM on NVIDIA L40S/A100 GPU",
                tier="Dedicated Private GPU",
                quantity="1 GPU Node Allocated",
                monthly_cost_usd=round(210.0 * ha_mult, 2),
                justification="Private air-gapped model inference for LLMs, Computer Vision, or ML models."
            ),
            SizingBOM(
                component="C004: PostgreSQL Cluster",
                sku_or_service="PostgreSQL 16 Enterprise with pgvector on Kubernetes",
                tier="High-Availability Pod Pair",
                quantity="1 HA Database Instance",
                monthly_cost_usd=round(75.0 * ha_mult, 2),
                justification="Stores risk findings, ontologies, audit trails, and review statuses."
            ),
            SizingBOM(
                component="C006: Web App & Keycloak SSO",
                sku_or_service="FastAPI Cockpit + Keycloak OIDC SSO on Kubernetes",
                tier="Container Ingress",
                quantity="1 Ingress Service",
                monthly_cost_usd=round(40.0 * ha_mult, 2),
                justification="Hosts web dashboard and integrates with corporate Active Directory / LDAP."
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
    proj_title = None
    if "|" in client_raw:
        parts = client_raw.split("|")
        client_name = parts[0].strip()
        proj_title = parts[1].strip()
    elif " — " in client_raw:
        parts = client_raw.split(" — ")
        client_name = parts[0].strip()
        proj_title = parts[1].strip()
    elif " – " in client_raw:
        parts = client_raw.split(" – ")
        client_name = parts[0].strip()
        proj_title = parts[1].strip()
    elif " - " in client_raw and not client_raw.startswith("q_"):
        parts = client_raw.split(" - ")
        client_name = parts[0].strip()
        proj_title = parts[1].strip()
    elif ":" in client_raw:
        parts = client_raw.split(":")
        client_name = parts[0].strip()
        proj_title = parts[1].strip()
    else:
        client_name = client_raw.strip() if client_raw.strip() else "Enterprise Client"
        
    domain = detect_project_domain(problem_raw)
    if not proj_title:
        if domain == "customer_support":
            proj_title = f"{client_name} AI Customer Support & Virtual Assistant"
        elif domain == "contract_intelligence":
            proj_title = f"{client_name} Contract Intelligence & Risk Visibility Platform"
        elif domain == "fraud_financial":
            proj_title = f"{client_name} Intelligent AML & Fraud Detection System"
        elif domain == "enterprise_search":
            proj_title = f"{client_name} Enterprise Knowledge Base & Neural Search"
        elif domain == "document_processing":
            proj_title = f"{client_name} Intelligent Document Extraction & Workflow Automation"
        else:
            proj_title = f"{client_name} AI Modernization & Automation Platform"


            
    def get_num_ans(qid: str, default_val: float) -> float:
        if qid in session.answers:
            try:
                clean_str = str(session.answers[qid].answer).replace(',', '')
                nums = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', clean_str)
                if nums:
                    return float(nums[0])
            except Exception:
                pass
        return default_val

    def get_str_ans(qid: str, default_val: str) -> str:
        if qid in session.answers:
            return session.answers[qid].answer
        return default_val

    dur_ans = get_str_ans("q_duration", "6.0")
    ref_weeks = 6.0
    try:
        ref_weeks = float(dur_ans.replace("Weeks", "").replace("Week", "").strip().split()[0])
    except Exception:
        ref_weeks = 6.0
        
    cloud_ans = get_str_ans("q_cloud", "Microsoft Azure")
    geo_ans = get_str_ans("q_geography", "India")
    start_date_ans = get_str_ans("q_start_date", "2026-09-30")
    
    daily_hours = get_working_hours_for_geography(geo_ans)
    rate = get_hourly_rate_for_geography(geo_ans)
    
    buffer_strategy_ans = get_str_ans("q_buffer_strategy", "15% Shadow / Backup Capacity (Recommended)")
    buffer_pct = 15.0
    if "0%" in buffer_strategy_ans or "Zero" in buffer_strategy_ans:
        buffer_pct = 0.0
    elif "25%" in buffer_strategy_ans:
        buffer_pct = 25.0
    elif "10%" in buffer_strategy_ans:
        buffer_pct = 10.0

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
    
    # 1. Base Task Effort (sum of 98 tasks: delivery P01-P17 + PM P18)
    delivery_task_days = round(sum(t.effort_days for t in task_estimates if t.phase_code != "P18"), 2)
    pm_task_days = round(sum(t.effort_days for t in task_estimates if t.phase_code == "P18"), 2)
    base_task_days = round(delivery_task_days + pm_task_days, 2)
    
    # 2. PM Overhead on delivery (12% per Sheet 01 Config)
    pm_overhead_pct = float(defaults.get("pm_governance_overhead_pct", 12.0))
    pm_overhead_days = round(delivery_task_days * (pm_overhead_pct / 100.0), 2)
    
    # 3. Contingency (10% per Sheet 01 Config)
    contingency_pct = float(defaults.get("contingency_pct", 10.0))
    contingency_days = round((base_task_days + pm_overhead_days) * (contingency_pct / 100.0), 2)
    
    # 4. Total Effort (Delivery + P18 + PM Overhead + Contingency) = 127.1 person-days
    total_days = round(base_task_days + pm_overhead_days + contingency_days, 1)
    total_hours = round(total_days * daily_hours, 1)
    total_labour_cost = round(total_hours * rate, 2)
    
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
    
    # Master Assumptions strictly from user inputs and admin default store (Zero Hallucination)
    assumptions: List[AssumptionItem] = [
        AssumptionItem(
            id="ASM-001",
            type="Constraint",
            category="Technical",
            statement=f"Solution executes exclusively on {cloud_ans} in {geo_ans} region within dedicated non-production cloud subscription with zero unauthorized external egress.",
            impact_if_wrong="Cloud architecture redesign, resource relocation, and network perimeter reconfiguration.",
            owner_to_confirm="Principal Solutions Architect & Client Cloud Lead",
            confidence="High",
            status="Approve"
        ),
        AssumptionItem(
            id="ASM-002",
            type="Assumption",
            category="Commercial",
            statement=f"Delivery baseline calibrated for {tier_name} tier over {ref_weeks} reference weeks ({feasibility.working_days} working days) at blended rate ${rate:.2f}/hr with {buffer_pct}% shadow standby engineering protection.",
            impact_if_wrong="Schedule timeline adjustment, sprint re-estimation, and resource loading revisions.",
            owner_to_confirm="Senior Delivery PM & Client Sponsor",
            confidence="High",
            status="Approve"
        ),
        AssumptionItem(
            id="ASM-003",
            type="Assumption",
            category="Scale",
            statement=f"Workload sizing dimensioned for {named_users} named users, {concurrent_users} peak concurrent sessions, and {daily_requests} daily requests across {int(scale_quantities['ENVS'])} environment(s).",
            impact_if_wrong="Cloud infrastructure resizing and provisioned throughput SKU adjustment.",
            owner_to_confirm="Enterprise Architect & Infrastructure Lead",
            confidence="High",
            status="Approve"
        ),
        AssumptionItem(
            id="ASM-004",
            type="Prerequisite",
            category="Data",
            statement=f"Client provides representative digital training & test sample data across {int(scale_quantities['DATASOURCES'])} connected data source(s) prior to Sprint 1 kick-off.",
            impact_if_wrong="Model grounding delay and validation dataset dependency blocker.",
            owner_to_confirm="Client Data Owner & ML Engineer",
            confidence="High",
            status="Approve"
        ),
        AssumptionItem(
            id="ASM-005",
            type="Constraint",
            category="Governance",
            statement=f"Responsible AI governance enforces 100% human-in-the-loop review for high-impact outputs and zero client data retention for public foundation model training.",
            impact_if_wrong="Compliance audit exception and regulatory governance escalation.",
            owner_to_confirm="AI Ethics Board & Compliance Officer",
            confidence="High",
            status="Approve"
        )
    ]
    
    # Append any custom admin master assumptions from store
    for a in get_master_assumptions():
        if not any(ex.statement == a.get("statement") for ex in assumptions):
            assumptions.append(AssumptionItem(
                id=a.get("id", f"ASM-{len(assumptions)+1:03d}"),
                type=a.get("type", "Assumption"),
                category=a.get("category", "Functional"),
                statement=a.get("statement", ""),
                impact_if_wrong=a.get("impact_if_wrong", a.get("impact", "")),
                owner_to_confirm=a.get("owner_to_confirm", "Project Sponsor & Technical Lead"),
                confidence=a.get("confidence", "High"),
                status=a.get("status", "Approve"),
                reason=a.get("reason", "")
            ))

    if domain == "contract_intelligence":
        solution_summary_six = (
            f"A throwaway {tier_name} for **{proj_title}** is architected on {cloud_ans} in an India region inside the existing non-production subscription for {client_name}, "
            f"processing a representative sample of previously executed English digital contracts placed into {cloud_ans} storage. "
            f"An ingestion and enrichment pipeline uses Azure AI Document Intelligence to recover layout-aware text, section boundaries, and page coordinates for 100% clause traceability. "
            f"Clause extraction executes as a multi-pass process: a first pass extracts standard category clauses, and targeted follow-up passes resolve ambiguous or heavily negotiated terms. "
            f"Extracted clauses are evaluated against category-specific contracting principles, producing Agree, Agree with Management Approval, or Not Agree with cited rationale. "
            f"Findings are aggregated into a contract risk register following existing spreadsheet structures with clause deep-links, surfaced on a demonstration dashboard with SSO."
        )
        business_impacts = [
            "Contract Review Cycle Time: Reduces manual clause audit turnaround time from days to minutes per contract.",
            "Contractual Risk Visibility: Replaces fragmented spreadsheets with a centralized, searchable risk register.",
            "Standardized Contracting Principle Enforcement: Consistently identifies deviations requiring management approval.",
            "100% Clause-Level Traceability: Eliminates audit ambiguity by linking every risk finding directly to source page coordinates."
        ]
        in_scope = [
            f"Processing representative sample of historical contracts across 6 categories (Lease, Vendor, Service, Facilities, Tech, Marketing).",
            f"Definition of contract categories, ontologies, and legal validation of contracting principles.",
            f"Multi-pass clause extraction capability across {int(scale_quantities['USECASES'])} core use case(s) and {int(scale_quantities['PERSONAS'])} user persona(s).",
            "Principle assessment framework classifying findings into Agree, Agree with Management Approval, or Not Agree.",
            "Contract risk register generation and demonstration risk visibility dashboard with Corporate SSO.",
            "Accuracy and risk assessment report benchmarked against legal-confirmed ground-truth contracts."
        ]
        out_of_scope = [
            "Workflow automation, approval routing, and approval management (Phase 2 scope).",
            "Production system-to-system integrations with ERP or legacy document stores (manual Blob storage upload).",
            "Scanned, photographed, or handwritten contract OCR tuning (digital machine-readable contracts in PoC).",
            "Review of unexecuted draft contracts (deferred to production phase).",
            "Non-English foreign language contract translation."
        ]
        personas = [
            {"persona": "Legal Reviewer", "need": "Review extracted clauses, validate principle assessments, and arbitrate ambiguous terms."},
            {"persona": "Procurement Reviewer", "need": "Inspect vendor contract deviations and verify commercial terms against policy."},
            {"persona": "Business Function Owner", "need": "View read-only dashboards highlighting contractual risks in their operational domain."},
            {"persona": "Management Approver", "need": "Review consolidated risk registers and approve deviations requiring executive sign-off."}
        ]
        ai_interventions = [
            {"agent": "Contract Classifier & Clause Extractor", "tech": cloud_ans, "role": "Identifies contract category and performs multi-pass clause extraction."},
            {"agent": "Principle Assessment & Risk Engine", "tech": cloud_ans, "role": "Evaluates extracted clauses against ontology rules to determine approval status."}
        ]
        non_ai_interventions = [
            {"service": f"{cloud_ans} Blob Landing Container", "role": "Authoritative storage for uploaded contract sample files."},
            {"service": f"{cloud_ans} Structured Findings Database", "role": "Stores ontologies, principle rules, clause records, and risk registers."},
            {"service": "Corporate Single Sign-On (SSO)", "role": "Authenticates project team members with role-based access control."}
        ]
        data_flow = (
            "1. PVR INOX places sample contract files into Azure Blob Storage landing container.\n"
            "2. Ingestion pipeline invokes Azure AI Document Intelligence for layout extraction and coordinate mapping.\n"
            "3. Document is chunked along clause boundaries; embeddings generated and indexed into Azure AI Search.\n"
            "4. Classification engine identifies contract category from 6 supported domains.\n"
            "5. Multi-pass extraction retrieves standard and vague clauses, stamping each record with pass provenance.\n"
            "6. Principle assessment evaluates clauses against configured rules to assign Agree/Management Approval/Not Agree.\n"
            "7. Structured findings populate contract risk register with deep-links to source pages.\n"
            "8. Exceptions and unresolvable clauses routed to dashboard exceptions queue for human reviewer."
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

    # Default Structured Point-by-Point Executive Summary
    default_exec_summary = (
        f"• **Scope & Objective:** Deterministic engineering scope, architecture, 12-discipline resource loading, and cloud infrastructure Bill of Materials for **{proj_title}** ({tier_name} Tier) for **{client_name}**.\n"
        f"• **Commercial Baseline:** Standardized blended rate of ${rate:.2f}/hour ({currency_symbol}{rate*currency_rate:.2f}/hr {currency_code}).\n"
        f"• **Cloud Platform & Region:** Built on {cloud_ans} in {geo_ans} across {int(scale_quantities['ENVS'])} environment(s) delivering production-grade AI automation.\n"
        f"• **Schedule & Protection:** Kick-off scheduled for **{start_date_ans}** with targeted completion on **{target_end_date_str}**, incorporating {buffer_pct}% standby buffer resource protection."
    )

    # Live Real-Time Multi-Cloud AI Narrative Synthesis
    live_narratives = LLMGateway.synthesize_narratives(
        client_name=client_name,
        project_title=proj_title,
        problem_statement=problem_raw,
        delivery_tier=tier_name,
        cloud_platform=cloud_ans,
        scope_in=in_scope,
        scope_out=out_of_scope
    )
    if live_narratives:
        exec_summary_text = live_narratives.get("executive_summary") or default_exec_summary
        if live_narratives.get("solution_summary_six_sentences"):
            solution_summary_six = live_narratives["solution_summary_six_sentences"]
        target_arch_narrative = live_narratives.get("target_architecture_narrative") or (
            f"The architecture is a scalable cloud pipeline hosted on {cloud_ans} in the {geo_ans} region. "
            f"It deploys across {int(scale_quantities['ENVS'])} environments using {int(scale_quantities['COMPONENTS'])} "
            f"core microservice components. Model execution is grounded via vector search and structured databases, "
            f"and rendered to {int(scale_quantities['PERSONAS'])} user persona(s) behind Enterprise Single Sign-On."
        )
        if live_narratives.get("data_flow_narrative"):
            data_flow = live_narratives["data_flow_narrative"]
    else:
        exec_summary_text = default_exec_summary
        target_arch_narrative = (
            f"The architecture is a scalable cloud pipeline hosted on {cloud_ans} in the {geo_ans} region. "
            f"It deploys across {int(scale_quantities['ENVS'])} environments using {int(scale_quantities['COMPONENTS'])} "
            f"core microservice components. Model execution is grounded via vector search and structured databases, "
            f"and rendered to {int(scale_quantities['PERSONAS'])} user persona(s) behind Enterprise Single Sign-On."
        )
        target_arch_narrative = (
            f"The architecture is a scalable cloud pipeline hosted on {cloud_ans} in the {geo_ans} region. "
            f"It deploys across {int(scale_quantities['ENVS'])} environments using {int(scale_quantities['COMPONENTS'])} "
            f"core microservice components. Model execution is grounded via vector search and structured databases, "
            f"and rendered to {int(scale_quantities['PERSONAS'])} user persona(s) behind Enterprise Single Sign-On."
        )

    # Build Canonical Items per reference.txt
    canonical_reqs = build_canonical_requirements(
        client_name=client_name,
        project_title=proj_title,
        delivery_tier=tier_name,
        domain=domain,
        cloud_platform=cloud_ans,
        geography=geo_ans,
        compliance_posture=compliance_posture
    )
    capabilities_catalog = build_capabilities_catalog(domain=domain, cloud_platform=cloud_ans)
    canonical_data_flows = build_canonical_data_flows(domain=domain, cloud_platform=cloud_ans)
    calc_ledger = build_calculation_ledger(
        tier_name=tier_name,
        task_estimates=task_estimates,
        role_efforts=role_efforts,
        feasibility=feasibility,
        sizing_bom=sizing_bom,
        hourly_rate=rate
    )
    hitl_gates = getattr(session, "hitl_gates", None) or HITLGates()

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
        cloud_platform=cloud_ans,
        
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
        
        executive_summary=exec_summary_text,
        problem_statement=problem_raw,
        solution_summary_six_sentences=solution_summary_six,
        business_impacts=business_impacts,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        ai_interventions=ai_interventions,
        non_ai_interventions=non_ai_interventions,
        user_personas=personas,
        target_architecture_narrative=target_arch_narrative,
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
        canonical_requirements=canonical_reqs,
        capabilities=capabilities_catalog,
        data_flows=canonical_data_flows,
        calculation_ledger=calc_ledger,
        hitl_gates=hitl_gates,
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
        delivery_task_days=delivery_task_days,
        pm_task_days=pm_task_days,
        pm_overhead_days=pm_overhead_days,
        contingency_days=contingency_days,
        base_task_days=base_task_days,
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

