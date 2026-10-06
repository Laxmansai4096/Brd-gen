"""
Comprehensive Worked Example Data for PVR INOX Contract Intelligence & Risk Visibility Platform
Extracted directly from the Master Solution Effort Estimation Calculator reference workbook.
"""

from typing import Dict, List, Any

# --- 01 CONFIGURATION DATA ---
COPILOT_SESSION_CONFIG = {
    "llm_model": "GPT-5 Thinking / Reasoning",
    "grounding_mode": "Work",
    "copilot_surface": "M365 Copilot Chat",
    "licence_attested": True,
    "prompt_response_folder": "",
    "estimation_unit": "Person-Days",
    "hours_per_person_day": 9.0,
    "working_days_per_week": 5,
    "story_points_ratio": 1.0,
    "productive_utilisation_pct": 100.0,
    "leave_buffer_pct": 0.0,
    "contingency_pct": 10.0,
    "pm_governance_overhead_pct": 12.0,
    "max_fte_per_role": 20.0,
    "max_ramp_per_week": 80.0,
    "phase_overlap_fraction": 0.50,
    "min_fte_granularity": 0.25,
    "day_level_cutoff_weeks": 999,
    "max_rows_daywise": 30000,
    "max_prompt_chars": 500000,
    "max_response_chars": 1000000,
    "sheet_chunk_size": 30000,
    "field_delimiter": "|",
    "not_provided_token": "NOT PROVIDED",
    "header_match_threshold": 0.72,
    "max_field_chars": 32000,
    "run_state": {
        "environment_validated": True,
        "inputs_validated": True,
        "questions_imported": True,
        "questions_answered": True,
        "solution_imported": True,
        "assumption_gate": "PASSED",
        "estimate_built": True,
        "schedule_generated": True,
        "last_action": "Step 12 schedule: 6 weeks, 441 day-rows, 0 role(s) flagged"
    }
}

# --- 02 INPUTS DATA ---
ENGAGEMENT_INPUTS = {
    "client_name": "PVR INOX",
    "engagement_name": "Contract Intelligence & Risk Visibility Platform",
    "functionality_required": """PVR INOX manages contracts across multiple categories, each governed by specific commercial, legal, and operational requirements.
Key challenges include:
• Contracts are received and maintained in multiple formats and layouts.
• Manual review of contractual clauses is time-consuming and dependent on subject matter expertise.
• Different categories of contracts require evaluation against different contracting principles.
• Deviations from approved contracting standards may not be consistently identified.

Assumptions:
• PVR INOX will provide representative contract samples across agreed contract categories, including lease, vendor, service, facilities, technology, and marketing contracts.
• Contracting principles, approval criteria, and risk assessment guidelines will be provided and validated by business and legal stakeholders.
• Contract documents will be available in digital formats suitable for AI-based processing and clause extraction.
• Business and legal SMEs will be available for workshops, validation activities, and acceptance reviews.
• Phase 1 is intended to validate feasibility using historical contract samples and does not include workflow automation, approval management, or production integrations.
• Final contract approval, legal interpretation, and risk acceptance decisions will remain the responsibility of PVR INOX business and legal teams.

Prerequisites:
• Availability of representative contract samples covering all in-scope contract categories in Azure Blob Storage.
• Availability of approved contracting principles, clause standards, and risk-rating criteria in Azure Blob Storage.
• Access to benchmark contract reviews confirmed by legal for accuracy validation.
• Availability of Legal, Procurement, Business, and IT stakeholders for sign-off.
• Provisioning of required Azure services (Azure Blob Storage, Document Intelligence, Azure OpenAI Service).
• Completion of data access, security, compliance, and governance approvals within Azure India region.
• Agreement on success metrics, assessment categories (Agree, Agree with Management Approval, Not Agree), and validation approach before Phase 1.

Objective:
Validate the technical, operational, and commercial viability of automated contract classification, clause extraction, principle assessment, and risk identification using representative contract samples.

Scope:
• Process historical contract samples.
• Define contract categories.
• Configure contract ontologies.
• Configure contracting principles.
• Build contract classification capability.
• Build clause extraction capability.
• Build principle assessment framework.
• Generate contract risk register.
• Create risk visibility dashboards.

Deliverables:
• Working proof-of-concept solution.
• Contract classification framework.
• Contract ontology definitions.
• Clause extraction capability.
• Principle assessment framework.
• Contract risk register.
• Risk visibility dashboard.
• Accuracy and risk assessment report.
• Target-state architecture.
• Azure deployment roadmap.
• Estimated Azure operating costs.

Decision Gate:
At the conclusion of Phase 1, PVR INOX will review:
• Classification performance
• Clause extraction performance
• Principle assessment effectiveness
• Risk register quality
• Business usability
• Target architecture
Upon acceptance of Phase 1 deliverables, PVR INOX may elect to proceed with Phase 2.""",
    "delivery_tier": "PoC",
    "reference_duration_weeks": 6.0,
    "planned_start_date": "2026-10-05",
    "delivery_geography": "India",
    "solution_domain": "AI / GenAI",
    "scale_drivers": {
        "use_cases": 1,
        "user_personas": 4,
        "system_integrations": 0,
        "data_sources": 2,
        "delivery_channels": 1,
        "languages": 1,
        "environments": 3,
        "architecture_components": 6,
        "technical_complexity": "Low",
        "compliance_posture": "Internal policy only",
        "security_posture": "Standard"
    },
    "platform_preference": {
        "primary_cloud": "Microsoft Azure",
        "secondary_cloud": "Microsoft Azure",
        "deployment_region": "India",
        "on_premises_required": False
    },
    "sizing_drivers": {
        "named_users": 200,
        "peak_concurrent_users": 50,
        "requests_per_day": 2000,
        "peak_rps": 3.00,
        "avg_user_prompt_tokens": 500,
        "avg_completion_tokens": 2000,
        "retrieved_chunks_top_k": 5,
        "tokens_per_chunk": 512,
        "documents_in_corpus": 50000,
        "avg_chunks_per_doc": 40,
        "raw_corpus_gb": 1.0,
        "embedding_dimensions": 1536,
        "data_retention_months": 12,
        "avg_cpu_ms_per_request": 120,
        "ha_dr_tier": "None (single instance)",
        "non_prod_factor": 0.60,
        "annual_growth_factor": 1.30
    },
    "technical_success_metrics": [
        {"metric": "Processing Completeness", "target": "100%", "description": "100% processing of agreed contract datasets"},
        {"metric": "Classification Accuracy", "target": "≥95%", "description": "≥95% contract classification accuracy across 6 legal categories"},
        {"metric": "Clause Extraction Accuracy", "target": "≥95%", "description": "≥95% extraction accuracy for agreed clauses and attributes"},
        {"metric": "Source Traceability", "target": "100%", "description": "100% traceability between risk assessments and source contract clauses"},
        {"metric": "Workflow Execution", "target": "≥95%", "description": "≥95% successful execution of assessment workflows"}
    ],
    "business_success_metrics": [
        {"metric": "Principle Coverage", "target": "100%", "description": "100% assessment of identified clauses against applicable contracting principles"},
        {"metric": "Three-Tier Classification", "target": "100%", "description": "100% classification into Agree, Agree with Management Approval, or Not Agree"},
        {"metric": "Risk Register Generation", "target": "100%", "description": "Generation of contract risk registers for all processed contracts"},
        {"metric": "Dashboard Visibility", "target": "100%", "description": "Dashboard visibility into risk exposure, deviations, and approval requirements"},
        {"metric": "Audit Traceability", "target": "100%", "description": "Clause-level traceability and auditability for legal inspection"}
    ]
}

# --- 04 COMPLETE 98-TASK MASTER LIBRARY (From Sheet 04 & Sheet 20) ---
MASTER_TASK_LIBRARY_98 = [
    # P01: Mobilisation & Discovery
    {"task_id": "T001", "phase_code": "P01", "phase_name": "Mobilisation & Discovery", "task_name": "Engagement kick-off, stakeholder map and RACI", "primary_role": "PM", "support_roles": "SA, BA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T002", "phase_code": "P01", "phase_name": "Mobilisation & Discovery", "task_name": "Discovery workshops: business problem, value hypothesis, success metrics", "primary_role": "BA", "support_roles": "SA, PM", "base_days": 4.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T003", "phase_code": "P01", "phase_name": "Mobilisation & Discovery", "task_name": "Current-state landscape, systems and constraints assessment", "primary_role": "SA", "support_roles": "BA", "base_days": 3.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T004", "phase_code": "P01", "phase_name": "Mobilisation & Discovery", "task_name": "Feasibility assessment and go/no-go recommendation", "primary_role": "SA", "support_roles": "AIE", "base_days": 2.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T005", "phase_code": "P01", "phase_name": "Mobilisation & Discovery", "task_name": "Delivery plan, RAID log and governance cadence set-up", "primary_role": "PM", "support_roles": "SA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P02: Requirements & Use Case Definition
    {"task_id": "T006", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Functional requirement elicitation and user story writing", "primary_role": "BA", "support_roles": "UX, SA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T007", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Non-functional requirement definition (performance, availability, retention, SLA)", "primary_role": "SA", "support_roles": "SRE, BA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T008", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Persona definition and user journey mapping", "primary_role": "UX", "support_roles": "BA", "base_days": 3.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T009", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Acceptance criteria and requirements traceability matrix", "primary_role": "BA", "support_roles": "QA", "base_days": 3.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T010", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Conversational / interaction design and wireframes", "primary_role": "UX", "support_roles": "BA, SWE", "base_days": 5.0, "scale_driver": "CHANNELS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T011", "phase_code": "P02", "phase_name": "Requirements & Use Case Definition", "task_name": "Scope baseline, MoSCoW prioritisation and change-control agreement", "primary_role": "PM", "support_roles": "BA, SA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P03: Data Discovery, Prep & Governance
    {"task_id": "T012", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Data source discovery, profiling and quality assessment", "primary_role": "DE", "support_roles": "BA", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T013", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Data access, entitlement and data-sharing agreement facilitation", "primary_role": "DE", "support_roles": "SEC, PM", "base_days": 3.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"task_id": "T014", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Data classification, PII/PHI identification and masking strategy", "primary_role": "SEC", "support_roles": "DE, RAI", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"task_id": "T015", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Data governance, lineage and retention design", "primary_role": "DE", "support_roles": "SEC", "base_days": 3.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"task_id": "T016", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Corpus curation, de-duplication and content-quality remediation", "primary_role": "DE", "support_roles": "AIE", "base_days": 6.0, "scale_driver": "DOCS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T017", "phase_code": "P03", "phase_name": "Data Discovery, Prep & Governance", "task_name": "Ground-truth / golden dataset construction with SME validation", "primary_role": "AIE", "support_roles": "BA, QA", "base_days": 7.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},

    # P04: Solution & Technical Architecture
    {"task_id": "T018", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Target solution architecture and component decomposition", "primary_role": "SA", "support_roles": "AIE, SRE", "base_days": 5.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T019", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Technical component design specification per component", "primary_role": "SA", "support_roles": "AIE, SWE, DE", "base_days": 3.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T020", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Integration and interface design (contracts, auth, error handling)", "primary_role": "SA", "support_roles": "SWE", "base_days": 3.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T021", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Architecture Decision Records and design authority review", "primary_role": "SA", "support_roles": "PM", "base_days": 2.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T022", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Capacity, sizing and platform footprint model", "primary_role": "SA", "support_roles": "SRE", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T023", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "Security architecture, identity and network design", "primary_role": "SEC", "support_roles": "SA, SRE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T024", "phase_code": "P04", "phase_name": "Solution & Technical Architecture", "task_name": "HA/DR, resilience and business continuity design", "primary_role": "SRE", "support_roles": "SA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P05: Environment, Landing Zone & Platform Setup
    {"task_id": "T025", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "Subscription / account, landing zone and network foundation", "primary_role": "SRE", "support_roles": "SEC", "base_days": 5.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T026", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "Identity, RBAC, managed identity and secret management set-up", "primary_role": "SEC", "support_roles": "SRE", "base_days": 4.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T027", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "AI platform / model endpoint provisioning and quota management", "primary_role": "MLO", "support_roles": "SRE, AIE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T028", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "Vector store / search index provisioning and configuration", "primary_role": "MLO", "support_roles": "DE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T029", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "Data platform and storage provisioning", "primary_role": "SRE", "support_roles": "DE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T030", "phase_code": "P05", "phase_name": "Environment, Landing Zone & Platform Setup", "task_name": "Developer workstation, repository, branch policy and toolchain set-up", "primary_role": "MLO", "support_roles": "SWE", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P06: Data Pipeline, Chunking & Embedding
    {"task_id": "T031", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Ingestion connector build per source system", "primary_role": "DE", "support_roles": "SWE", "base_days": 5.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T032", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Document parsing, OCR and layout extraction pipeline", "primary_role": "DE", "support_roles": "AIE", "base_days": 6.0, "scale_driver": "DOCS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T033", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Chunking strategy design, implementation and tuning", "primary_role": "AIE", "support_roles": "DE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T034", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Metadata enrichment and taxonomy tagging", "primary_role": "DE", "support_roles": "BA", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T035", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Embedding pipeline build, batch and incremental", "primary_role": "DE", "support_roles": "AIE, MLO", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T036", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Data transformation, cleansing and validation rules", "primary_role": "DE", "support_roles": "QA", "base_days": 5.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T037", "phase_code": "P06", "phase_name": "Data Pipeline, Chunking & Embedding", "task_name": "Change data capture / refresh and re-index scheduling", "primary_role": "DE", "support_roles": "MLO", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "AI", "uplift": "NONE"},

    # P07: Retrieval / Index / Knowledge Build
    {"task_id": "T038", "phase_code": "P07", "phase_name": "Retrieval / Index / Knowledge Build", "task_name": "Index schema, field and filter design", "primary_role": "AIE", "support_roles": "DE", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T039", "phase_code": "P07", "phase_name": "Retrieval / Index / Knowledge Build", "task_name": "Retrieval strategy build (hybrid, semantic, keyword, filters)", "primary_role": "AIE", "support_roles": "DE", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T040", "phase_code": "P07", "phase_name": "Retrieval / Index / Knowledge Build", "task_name": "Re-ranking and relevance tuning against the golden set", "primary_role": "AIE", "support_roles": "QA", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T041", "phase_code": "P07", "phase_name": "Retrieval / Index / Knowledge Build", "task_name": "Retrieval quality measurement harness (recall@k, MRR, nDCG)", "primary_role": "AIE", "support_roles": "QA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P08: Model Selection, Prompting & Orchestration
    {"task_id": "T042", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Model selection, benchmarking and trade-off analysis", "primary_role": "AIE", "support_roles": "SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T043", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "System prompt and prompt-template engineering", "primary_role": "AIE", "support_roles": "BA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T044", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Orchestration / agent flow implementation (tools, routing, memory)", "primary_role": "AIE", "support_roles": "SWE", "base_days": 8.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T045", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Structured output, function calling and schema enforcement", "primary_role": "AIE", "support_roles": "SWE", "base_days": 4.0, "scale_driver": "INTEGRATIONS", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T046", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Grounding, citation and source-attribution implementation", "primary_role": "AIE", "support_roles": "SWE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T047", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Prompt versioning, registry and A/B experiment framework", "primary_role": "MLO", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T048", "phase_code": "P08", "phase_name": "Model Selection, Prompting & Orchestration", "task_name": "Token, latency and cost optimisation (caching, routing, truncation)", "primary_role": "AIE", "support_roles": "SA", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P09: Fine-tuning / Model Adaptation
    {"task_id": "T049", "phase_code": "P09", "phase_name": "Fine-tuning / Model Adaptation", "task_name": "Fine-tuning / adaptation feasibility and dataset preparation", "primary_role": "AIE", "support_roles": "DE", "base_days": 6.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T050", "phase_code": "P09", "phase_name": "Fine-tuning / Model Adaptation", "task_name": "Fine-tune execution, hyperparameter sweep and checkpoint selection", "primary_role": "AIE", "support_roles": "MLO", "base_days": 6.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T051", "phase_code": "P09", "phase_name": "Fine-tuning / Model Adaptation", "task_name": "Adapted model evaluation against baseline and promotion decision", "primary_role": "AIE", "support_roles": "QA, SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P10: Application, API & Integration Layer
    {"task_id": "T052", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "API layer and service implementation", "primary_role": "SWE", "support_roles": "SA", "base_days": 8.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T053", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Front-end / channel implementation", "primary_role": "SWE", "support_roles": "UX", "base_days": 10.0, "scale_driver": "CHANNELS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T054", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Downstream / upstream system integration build", "primary_role": "SWE", "support_roles": "DE", "base_days": 5.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T055", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Authentication, authorisation and session handling in the application", "primary_role": "SWE", "support_roles": "SEC", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T056", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Business rules, workflow and exception handling", "primary_role": "SWE", "support_roles": "BA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T057", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Localisation and multi-language enablement", "primary_role": "SWE", "support_roles": "UX", "base_days": 3.0, "scale_driver": "LANGUAGES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T058", "phase_code": "P10", "phase_name": "Application, API & Integration Layer", "task_name": "Accessibility conformance implementation and audit", "primary_role": "UX", "support_roles": "SWE, QA", "base_days": 3.0, "scale_driver": "CHANNELS", "applies_to": "BOTH", "uplift": "COMP"},

    # P11: Evaluation, Benchmarking & Golden Sets
    {"task_id": "T059", "phase_code": "P11", "phase_name": "Evaluation, Benchmarking & Golden Sets", "task_name": "Evaluation framework design (metrics, rubrics, thresholds)", "primary_role": "AIE", "support_roles": "QA, RAI", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T060", "phase_code": "P11", "phase_name": "Evaluation, Benchmarking & Golden Sets", "task_name": "Automated evaluation harness build and CI wiring", "primary_role": "AIE", "support_roles": "MLO, QA", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T061", "phase_code": "P11", "phase_name": "Evaluation, Benchmarking & Golden Sets", "task_name": "Groundedness, faithfulness and hallucination-rate measurement", "primary_role": "AIE", "support_roles": "RAI, QA", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T062", "phase_code": "P11", "phase_name": "Evaluation, Benchmarking & Golden Sets", "task_name": "Human-in-the-loop review process and SME evaluation rounds", "primary_role": "BA", "support_roles": "AIE, RAI", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T063", "phase_code": "P11", "phase_name": "Evaluation, Benchmarking & Golden Sets", "task_name": "Regression evaluation baseline and drift thresholds", "primary_role": "AIE", "support_roles": "MLO", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P12: Responsible AI, Safety & Security
    {"task_id": "T064", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Responsible AI impact assessment and regulatory mapping", "primary_role": "RAI", "support_roles": "SA, SEC", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "COMP"},
    {"task_id": "T065", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Content safety, guardrail and jailbreak-resistance implementation", "primary_role": "RAI", "support_roles": "AIE, SEC", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "SEC"},
    {"task_id": "T066", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Bias, fairness and representational-harm testing", "primary_role": "RAI", "support_roles": "AIE, QA", "base_days": 4.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "COMP"},
    {"task_id": "T067", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Threat modelling including prompt injection and data exfiltration", "primary_role": "SEC", "support_roles": "AIE, SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "SEC"},
    {"task_id": "T068", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Security testing, VAPT coordination and remediation", "primary_role": "SEC", "support_roles": "SWE, QA", "base_days": 6.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T069", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Model card, transparency note and audit evidence pack", "primary_role": "RAI", "support_roles": "SA, BA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "COMP"},
    {"task_id": "T070", "phase_code": "P12", "phase_name": "Responsible AI, Safety & Security", "task_name": "Privacy review, DPIA and data residency conformance", "primary_role": "SEC", "support_roles": "RAI, DE", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},

    # P13: MLOps / LLMOps, IaC & CI-CD
    {"task_id": "T071", "phase_code": "P13", "phase_name": "MLOps / LLMOps, IaC & CI-CD", "task_name": "Infrastructure as Code modules and parameterisation", "primary_role": "MLO", "support_roles": "SRE", "base_days": 6.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T072", "phase_code": "P13", "phase_name": "MLOps / LLMOps, IaC & CI-CD", "task_name": "CI/CD pipeline build with quality and security gates", "primary_role": "MLO", "support_roles": "SWE, SEC", "base_days": 6.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "SEC"},
    {"task_id": "T073", "phase_code": "P13", "phase_name": "MLOps / LLMOps, IaC & CI-CD", "task_name": "Environment promotion, configuration and release strategy", "primary_role": "MLO", "support_roles": "SRE, PM", "base_days": 4.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T074", "phase_code": "P13", "phase_name": "MLOps / LLMOps, IaC & CI-CD", "task_name": "Model / prompt registry, versioning and rollback mechanism", "primary_role": "MLO", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T075", "phase_code": "P13", "phase_name": "MLOps / LLMOps, IaC & CI-CD", "task_name": "Automated re-index / retraining trigger pipeline", "primary_role": "MLO", "support_roles": "DE, AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P14: Observability, Cost & FinOps
    {"task_id": "T076", "phase_code": "P14", "phase_name": "Observability, Cost & FinOps", "task_name": "Telemetry, tracing and structured logging implementation", "primary_role": "SRE", "support_roles": "SWE, AIE", "base_days": 5.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T077", "phase_code": "P14", "phase_name": "Observability, Cost & FinOps", "task_name": "Dashboards, alerting and SLO definition", "primary_role": "SRE", "support_roles": "SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T078", "phase_code": "P14", "phase_name": "Observability, Cost & FinOps", "task_name": "Token and cost telemetry, budget alerts and FinOps guardrails", "primary_role": "SRE", "support_roles": "SA, MLO", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T079", "phase_code": "P14", "phase_name": "Observability, Cost & FinOps", "task_name": "Quality and drift monitoring in production", "primary_role": "MLO", "support_roles": "AIE, RAI", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T080", "phase_code": "P14", "phase_name": "Observability, Cost & FinOps", "task_name": "Feedback capture loop and continuous-improvement backlog", "primary_role": "BA", "support_roles": "AIE, UX", "base_days": 3.0, "scale_driver": "CHANNELS", "applies_to": "AI", "uplift": "NONE"},

    # P15: Testing (Functional, Performance, UAT)
    {"task_id": "T081", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "Test strategy, test plan and test environment data set-up", "primary_role": "QA", "support_roles": "BA, MLO", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T082", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "Functional and integration test design and execution", "primary_role": "QA", "support_roles": "SWE", "base_days": 8.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T083", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "Automated regression suite build", "primary_role": "QA", "support_roles": "SWE", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T084", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "Performance, load and soak testing", "primary_role": "QA", "support_roles": "SRE, SA", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T085", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "Resilience, failover and DR test execution", "primary_role": "SRE", "support_roles": "QA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T086", "phase_code": "P15", "phase_name": "Testing (Functional, Performance, UAT)", "task_name": "UAT facilitation, defect triage and sign-off", "primary_role": "BA", "support_roles": "QA, PM", "base_days": 6.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},

    # P16: Deployment, Cutover & Hypercare
    {"task_id": "T087", "phase_code": "P16", "phase_name": "Deployment, Cutover & Hypercare", "task_name": "Cutover plan, runbook and rollback procedure", "primary_role": "SRE", "support_roles": "PM, SA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T088", "phase_code": "P16", "phase_name": "Deployment, Cutover & Hypercare", "task_name": "Production deployment execution and smoke validation", "primary_role": "MLO", "support_roles": "SRE, QA", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T089", "phase_code": "P16", "phase_name": "Deployment, Cutover & Hypercare", "task_name": "Go-live command centre and hypercare support", "primary_role": "SRE", "support_roles": "SWE, AIE, PM", "base_days": 8.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T090", "phase_code": "P16", "phase_name": "Deployment, Cutover & Hypercare", "task_name": "Service transition, SLA agreement and operational readiness review", "primary_role": "PM", "support_roles": "SRE, SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P17: Documentation, Training & Handover
    {"task_id": "T091", "phase_code": "P17", "phase_name": "Documentation, Training & Handover", "task_name": "Solution, architecture and operations documentation", "primary_role": "SA", "support_roles": "SWE, SRE", "base_days": 5.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T092", "phase_code": "P17", "phase_name": "Documentation, Training & Handover", "task_name": "Admin, prompt-maintenance and content-curation guides", "primary_role": "BA", "support_roles": "AIE", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"task_id": "T093", "phase_code": "P17", "phase_name": "Documentation, Training & Handover", "task_name": "End-user training material and enablement sessions", "primary_role": "BA", "support_roles": "UX", "base_days": 4.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T094", "phase_code": "P17", "phase_name": "Documentation, Training & Handover", "task_name": "Knowledge transfer to the run team and shadowing", "primary_role": "SA", "support_roles": "SRE, SWE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P18: Project Management & Governance
    {"task_id": "T095", "phase_code": "P18", "phase_name": "Project Management & Governance", "task_name": "Programme management, reporting and stakeholder governance", "primary_role": "PM", "support_roles": "SA", "base_days": 10.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T096", "phase_code": "P18", "phase_name": "Project Management & Governance", "task_name": "Risk, issue, dependency and assumption management", "primary_role": "PM", "support_roles": "SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T097", "phase_code": "P18", "phase_name": "Project Management & Governance", "task_name": "Vendor, licence and procurement coordination", "primary_role": "PM", "support_roles": "SA, SEC", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"task_id": "T098", "phase_code": "P18", "phase_name": "Project Management & Governance", "task_name": "Quality assurance of deliverables and phase-gate reviews", "primary_role": "PM", "support_roles": "QA, SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"}
]

# --- 11 SOLUTION NARRATIVE SECTIONS (S001 to S015 From Sheet 11) ---
MASTER_SOLUTION_SECTIONS = [
    {
        "sid": "S001",
        "section": "Problem restated in business terms",
        "content": "PVR INOX signs contracts across lease, vendor, service, facilities, technology and marketing categories, each governed by different commercial, legal and operational rules. Contracts arrive in varied formats and layouts, and review depends on scarce legal and procurement expertise reading each document manually. Because each category is judged against different contracting principles, deviations from approved standards are not caught consistently. Findings live in spreadsheets and disconnected documents, so there is no consolidated view of contractual risk exposure, no reliable list of deviations needing management approval, and no traceability from a finding back to the clause that caused it. The business question for this phase is narrow: can automated classification, clause extraction, principle assessment and risk registration be made to work well enough on representative historical contracts to justify building a production service.",
        "depends_on": "Q013/Q023/Q024/Q047/A010",
        "confidence": "High"
    },
    {
        "sid": "S002",
        "section": "Solution summary in six sentences or fewer",
        "content": "A throwaway proof of concept is built on Microsoft Azure in an India region inside the existing non-production subscription, processing a representative sample of previously executed English digital contracts that PVR INOX places into Azure Blob Storage. An ingestion and enrichment pipeline uses Azure AI Document Intelligence to recover layout-aware text and page coordinates, then classifies each contract into one of the six agreed categories using Azure OpenAI Service. Clause extraction runs as a multi-pass process rather than one pass per document: a first pass extracts the well-defined clauses and attributes for the category, and additional targeted extraction passes are run for vague, open-textured or negotiated terms that a single pass cannot resolve reliably. Extracted clauses are assessed against category-specific contracting principles configured as a structured ontology and principle rule set, producing an outcome of Agree, Agree with Management Approval or Not Agree with a supporting rationale and a pointer to the source clause and page. Findings are written to a contract risk register that follows the existing spreadsheet review structure, extended with a clause-level link back into the source document, and surfaced on a demonstration dashboard behind corporate single sign-on. An evaluation harness scores classification and extraction against a legal-confirmed benchmark set so the decision gate can be judged on measured numbers rather than impressions.",
        "depends_on": "Q001/Q002/Q007/Q008/Q027/Q036/A051/A052",
        "confidence": "High"
    },
    {
        "sid": "S003",
        "section": "Scope - what is in",
        "content": "Processing of the agreed representative sample of historical contracts drawn from the six in-scope categories, at an indicative 100 contracts per category. Definition of contract categories and configuration of contract ontologies per category. Elicitation, configuration and legal validation of contracting principles, clause standards and risk-rating criteria for each category. A contract classification capability across the six categories. A multi-pass clause and contractual attribute extraction capability against the clause list frozen in the first workshop, including additional targeted passes for vague or ambiguous terms. A principle assessment framework producing Agree, Agree with Management Approval or Not Agree per assessed clause. Generation of a contract risk register per processed contract in the existing review structure, extended with clause-level links. A read-only risk visibility dashboard plus an exceptions list for unprocessable contracts. An accuracy and risk assessment report measured against the legal-confirmed benchmark contracts. A target-state architecture that anticipates scanned-document intake and draft-contract review in the production phase, an Azure deployment roadmap and an assumption-based estimate of Azure operating costs against the stated volume and usage figures. Dev, Test and UAT environments in non-production. Corporate single sign-on for the demonstration interface, restricted to a named project group.",
        "depends_on": "Q011/Q013/Q014/Q019/Q024/A051/A053/A054",
        "confidence": "High"
    },
    {
        "sid": "S004",
        "section": "Scope - what is explicitly out",
        "content": "Workflow automation, approval routing and approval management. Production integrations and any system-to-system connection to a contract management, ERP or document management system - PVR INOX places files into Blob Storage manually. Scanned, photographed or handwritten originals and any optical recognition tuning for them, which are noted as a production-phase requirement but are not built or tested here. Review of unexecuted draft contracts, which is noted as the production-phase expectation but is not exercised in this phase. Non-English contracts. Linking amendments, addenda and side letters to parent contracts, and assessment of a contract as amended. Function-level or row-level access restriction between user groups. Masking or redaction of personal data in contract text. Customer-managed encryption keys. Formal security review or penetration testing. Failover, disaster recovery and backup arrangements. Production deployment, CI/CD pipelines, a production support model and any service level commitment. Processing-time commitments or performance tuning against the live-scale figures. Any automated decision making - the solution does not approve, reject or interpret a contract.",
        "depends_on": "Q028/Q031/Q037/Q038/Q041/Q042/Q043/A005/A006",
        "confidence": "High"
    },
    {
        "sid": "S005",
        "section": "Target architecture narrative",
        "content": "The design is a single-platform, single-region, batch-oriented pipeline on Microsoft Azure in India, with a thin read-only presentation layer. A landing zone in the existing non-production subscription hosts one resource group per environment for Dev, Test and UAT. Contract samples arrive in Azure Blob Storage in a controlled container that PVR INOX writes to and the project team reads from. An orchestration layer drives the document journey: layout-aware extraction through Azure AI Document Intelligence, chunking and embedding, classification, multi-pass clause extraction, and principle assessment through Azure OpenAI Service. The orchestration layer is explicitly pass-aware - it tracks which clause items in the category clause list remain unresolved after the first extraction pass and schedules further targeted passes for them, so extraction cost and duration vary by document rather than being fixed. A managed search and vector store capability native to Azure holds clause-level chunks with their document, category, page and coordinate metadata so that every downstream finding can be traced back to the exact text it came from. A structured store holds the ontology, the principle rule set, the extracted clause records with their pass provenance and the risk register findings, and is the single source for both the register export and the dashboard. The dashboard is a demonstration-grade read-only surface behind corporate single sign-on. An evaluation harness runs outside the runtime path, replaying the benchmark set and scoring classification and extraction against the legal-confirmed answers, reporting first-pass and multi-pass results separately. Secrets are held in a managed secrets store, component-to-component authentication uses platform managed identities rather than keys where the service supports it, and platform-managed encryption is relied on throughout. Observability is basic platform telemetry plus token and cost capture sufficient to produce the operating cost estimate, not a production monitoring stack. The target-state view carries two forward-looking notes for Phase 2: an optical recognition intake path for scanned contracts, and a draft-contract review path where assessment happens before execution. Six primary components carry the solution; the count is held at the architect's expectation and no production-only tier is introduced.",
        "depends_on": "Q002/Q003/Q008/Q011/Q051/A051/A053/A054/A055",
        "confidence": "High"
    },
    {
        "sid": "S006",
        "section": "Data flow, end to end",
        "content": "PVR INOX legal operations places the authorised contract sample into the agreed Azure Blob Storage container, and those copies are treated as the authoritative executed versions for this phase. The ingestion pipeline picks up each document, records a document identifier and its source path, and calls Azure AI Document Intelligence to produce layout-aware text with page and coordinate references. The document is chunked along clause and section boundaries, embeddings are generated, and chunks plus metadata are written to the managed search and vector index. Classification runs next, assigning the document to one of the six categories and writing a confidence signal alongside it. The category determines which ontology and which clause list apply; a first extraction pass retrieves candidate chunks and returns structured clause records and contractual attributes for the well-defined items. Any clause item that returns empty, low confidence, or a value the schema cannot validate - typically the vague or heavily negotiated terms - is queued for one or more targeted follow-up extraction passes that narrow retrieval to that clause item alone, and each record carries the pass number that produced it. Each extracted clause is then evaluated against the applicable contracting principles, producing an assessment outcome of Agree, Agree with Management Approval or Not Agree, a rationale and a risk rating, all written to the findings store. Findings are aggregated into a per-contract risk register in the existing spreadsheet structure plus a clause-level link, and surfaced on the dashboard by category, by approval requirement and by outcome. Any document that fails extraction or classification, and any clause item still unresolved after the agreed maximum number of passes, is written to an exceptions list visible on the dashboard and routed to the nominated legal operations contact for manual handling. Every finding in this phase is reviewed by a person before it is treated as reliable. All documents, indexes and findings remain in the India region and are retained for twelve months, then deleted or returned on request.",
        "depends_on": "Q022/Q029/Q034/Q035/A051/A052/A056",
        "confidence": "High"
    },
    {
        "sid": "S007",
        "section": "Model and retrieval strategy",
        "content": "Only models available through Azure OpenAI Service in an India-eligible configuration are used; no third-party model provider is introduced and no fine-tuning is performed in this phase, so P09 carries no build. Classification is prompt-based over a bounded set of six known categories using the document's opening sections and structural signals, because the category count is small and fixed and a trained classifier cannot be justified before the sample is seen. Clause extraction is retrieval-augmented and multi-pass: the clause list for the category drives a first broad pass, and unresolved or vague clause items each drive their own narrow pass with clause-specific retrieval and a clause-specific prompt, because a single combined pass produces confident-looking but ungrounded values for open-textured terms. Retrieval is hybrid - keyword matching catches the fixed legal phrasing that makes contract language searchable, vector similarity catches the negotiated rewordings that keyword matching misses. Chunking follows clause and section boundaries rather than fixed character windows, because a clause split across two chunks produces an assessment that cannot be traced to a single source location. Principle assessment is a separate model call from extraction, taking the extracted clause and the applicable principle as input, so that an extraction error and an assessment error can be told apart during evaluation. Every model output carries the chunk identifier, page, coordinates and extraction pass number that produced it, satisfying the 100 percent traceability metric. Prompts, the clause schema, the pass policy and the principle set are versioned so that an accuracy figure can be attributed to a specific configuration. NEED-VERIFY: availability of specific Azure OpenAI models and their context window sizes in India regions. NEED-VERIFY: retrieval and index tier limits of the managed vector store capability. NEED-VERIFY: Azure OpenAI request and token quota headroom for repeated multi-pass evaluation runs.",
        "depends_on": "Q006/Q008/Q026/A019/A051/A057/A058",
        "confidence": "Medium"
    },
    {
        "sid": "S008",
        "section": "Integration approach",
        "content": "No system-to-system integration is built in this phase, consistent with the stated integration count of zero. PVR INOX is responsible for placing all contract samples into the agreed Azure Blob Storage container, and the solution reads from that container only. The only inbound dependency is therefore a storage handover, governed by a naming and folder convention agreed at kick-off so that category and sample-type can be identified without a separate manifest. Outbound, the risk register is produced as a file export in the existing spreadsheet structure so that legal and procurement can work with it in tools they already use, and the dashboard reads directly from the findings store. A nominated IT applications contact is named at kick-off as the single point for any access request should a connection become necessary, but building such a connection would be a change to scope. Identity is the one platform integration in scope: corporate single sign-on fronts the demonstration interface. The target architecture flags that a Phase 2 draft-contract review path would require an inbound connection to wherever drafts are authored or circulated, which does not exist in this phase.",
        "depends_on": "Q038/Q039/A034/A035/A050/A054",
        "confidence": "High"
    },
    {
        "sid": "S009",
        "section": "Security and identity approach",
        "content": "Access to the demonstration interface uses corporate single sign-on and is limited to a named project group; no local accounts are created. All authorised users in this phase can see every processed contract, because function-level restriction is explicitly deferred. Contracts are treated as confidential under internal policy, and the control relied on is restriction of access to the named project team rather than redaction - contracts may contain counterparty contact details and no masking is applied in this phase. Platform-managed encryption is used for data at rest and in transit, with a managed secrets store holding any keys, connection strings and credentials; customer-managed keys are deferred to the production phase. Component-to-component authentication uses platform managed identities in preference to shared keys wherever the service supports it. All data and processing stay inside India regions, signed off by the PVR INOX legal function before any sample is uploaded. No formal security review or penetration test is performed, per the tier definition, so the environment is kept closed: non-production subscription, no public data paths beyond the authenticated dashboard, and no real user population. Internal policy applies only; no external regulatory obligation has been stated. The target architecture notes that draft contracts in a production phase are commercially sensitive before signature and would warrant tighter access control than this phase applies.",
        "depends_on": "Q007/Q009/Q031/Q032/Q033/Q036/Q037/Q043/A006",
        "confidence": "High"
    },
    {
        "sid": "S010",
        "section": "Responsible AI approach and human oversight",
        "content": "The solution is positioned as an assistant, not a decision maker. Every finding produced in this phase is reviewed by a person before it is treated as reliable, and final contract approval, legal interpretation and risk acceptance remain with PVR INOX business and legal teams. Where business and legal views differ on whether a clause is Agree, Agree with Management Approval or Not Agree, a nominated legal lead at PVR INOX is the final arbiter. Traceability is the primary responsible AI control: no assessment is displayed without a link to the exact clause text, page and document that produced it, so a reviewer can always check the machine against the source. Assessments carry a stated rationale, and where the model cannot ground an assessment in retrieved clause text the finding is marked unsupported rather than asserted. Vague clause items that remain unresolved after the agreed maximum number of extraction passes are shown as unresolved rather than filled with a best guess, because an invented value for an open-textured term is the most damaging failure this design can produce. Contracts that cannot be read or classified are not silently dropped - they go to a visible exceptions list routed to a nominated legal operations contact. Accuracy is measured openly against a benchmark set confirmed correct by the PVR INOX legal team, and the accuracy and risk assessment report states where the solution failed as plainly as where it succeeded. No content safety tuning, bias testing or adversarial testing beyond this is performed at PoC tier.",
        "depends_on": "Q018/Q021/Q022/A014/A015/A051/A052",
        "confidence": "High"
    },
    {
        "sid": "S011",
        "section": "Non-functional approach - performance, availability, resilience",
        "content": "No processing-time commitment applies in this phase; batches run without a fixed completion window, so the pipeline is optimised for correctness and traceability rather than throughput. This matters more after the move to multi-pass extraction, because the number of model calls per contract is now variable and driven by how many clause items need follow-up passes. A single instance with no failover is accepted - if the environment becomes unavailable, processing pauses until it is restored, and the batch resumes from the last completed document and pass rather than restarting. The named-user, concurrency and request-rate figures in the sizing drivers describe the eventual live service and are used only to produce the assumption-based operating cost estimate; the phase itself serves a small group of reviewers using the dashboard concurrently during validation sessions. The 50,000-document corpus figure is likewise the eventual live size, not this phase's workload - this phase processes the agreed representative sample. Three environments exist, Dev, Test and UAT, all non-production. Resilience is limited to restartable batch processing and retention of intermediate extraction output so that a re-run does not require re-reading every document from scratch or repeating passes that already succeeded. No load testing, no capacity testing and no NFR acceptance criteria apply at this tier. The binding constraint in practice is Azure OpenAI request and token quota in the non-production subscription, because multi-pass extraction and repeated benchmark replays both consume it.",
        "depends_on": "Q040/Q041/Q042/A020/A031/A032/A033/A051/A057",
        "confidence": "Medium"
    },
    {
        "sid": "S012",
        "section": "Operating model after go-live",
        "content": "There is no go-live in this phase. The proof of concept is supported by the delivery team on a best-effort basis for an agreed handover window, and no production support model is established. Data is retained for the twelve-month period stated in the engagement inputs and then deleted or returned on request. At the decision gate a nominated executive sponsor at PVR INOX, Nithin Arora, reviews classification performance, clause extraction performance, principle assessment effectiveness, risk register quality, business usability and the target architecture, and signs off acceptance. The executive sponsor also decides any trade-off between higher accuracy and additional human review effort or a longer timeline, advised by legal - a decision that now includes how many extraction passes are worth running for vague terms. Jitender Verma acts as the single point of contact for all queries during the engagement. Target architecture and the Azure deployment roadmap are written on the basis that Phase 2 adds workflow automation, approval management and production integrations, and additionally that Phase 2 must handle scanned documents and draft rather than executed contracts, so the Phase 1 build is deliberately throwaway where a production design would differ. Handover duration is agreed prior to closure.",
        "depends_on": "Q010/Q035/Q044/Q045/Q046/Q051/A005/A006/A043",
        "confidence": "High"
    },
    {
        "sid": "S013",
        "section": "Key risks and how the design mitigates them",
        "content": "The clause and attribute list per category is not yet agreed, and extraction cannot be built against a moving target - the design fixes the list in the first workshop and freezes it before build, and the accuracy metrics are measured only against the frozen list. Vague and open-textured clause terms now drive additional extraction passes, and the number of such terms is unknown until the clause list is frozen, so extraction effort and model consumption per contract cannot be bounded in advance - the design mitigates this with an agreed maximum pass count per clause item and by routing anything still unresolved to the exceptions list rather than letting passes run indefinitely. Contracting principles exist in documented form for some categories only and must be elicited in workshops for the rest, which loads the early phases with SME-dependent work - the design separates the ontology and principle configuration from the model logic so that late principle changes are configuration, not code. The 95 percent classification and extraction accuracy bar is an acceptance condition set before any sample has been seen - the evaluation harness scores per category and per clause type so a shortfall can be isolated rather than sinking the whole gate, and the sponsor holds the accuracy versus effort trade-off decision. Sample quality is a risk: if the provided contracts are all standard and contain no negotiated or known-deviation examples, the assessment framework cannot be shown to detect deviations at all - the design calls for standard, negotiated and known-problem contracts in each category. Benchmark availability is a hard dependency; without legal-confirmed manual reviews there is no denominator for any accuracy claim. Assessment of each document in isolation means a clause superseded by an amendment may be reported as a live risk - this is stated as a known limitation of the phase, not a defect. Non-production Azure OpenAI quota is a real constraint because multi-pass extraction multiplied by repeated benchmark replays raises consumption materially above a single-pass design. Phase 1 evidence will be based on executed, machine-readable contracts while production is expected to bring scanned documents and unsigned drafts, so Phase 1 accuracy figures will not transfer unchanged to production - this is recorded as a stated limitation and reflected in the target architecture. SME availability remains the single largest schedule risk given workshops, validation and acceptance all depend on the same small group, mitigated by a named SPOC and an agreed weekly commitment.",
        "depends_on": "A003/A005/A006/A016/A017/A020/A051/A052/A053/A054",
        "confidence": "High"
    },
    {
        "sid": "S014",
        "section": "Options considered and rejected, with the reason",
        "content": "Single-pass extraction of the whole clause list per document was rejected by the reviewer and is no longer part of the design, because vague or negotiated terms require separate targeted extraction runs to be resolved reliably. Fine-tuning or training a dedicated classification model was rejected because six categories with a limited sample give too little training data to beat prompt-based classification, and the phase must answer feasibility, not optimise a model. A third-party or self-hosted model was rejected because only models available through the named cloud provider are in play. Building a connector to a contract management or document store was rejected because PVR INOX places files into cloud storage directly and no integration is in scope. Pure vector retrieval was rejected in favour of hybrid retrieval because contract language contains fixed legal phrasing that exact matching finds more reliably than similarity alone. Fixed-size chunking was rejected because clauses split across chunk boundaries break the clause-level traceability the phase must demonstrate. A single combined prompt performing extraction and assessment together was rejected because it makes an extraction failure indistinguishable from an assessment failure during evaluation. Unbounded retry of extraction passes was rejected in favour of an agreed maximum pass count, because unbounded passes consume quota without a stopping rule and hide a genuine extraction failure. Optical character recognition tuning for scanned originals was rejected for this phase because contracts in scope are digital and machine-readable, while being recorded in the target architecture as a production-phase requirement. Function-level access control, personal-data masking, customer-managed keys, CI/CD and failover were all considered and deliberately excluded as production concerns outside the PoC tier definition. Building the dashboard as a bespoke application was rejected in favour of a demonstration-grade read-only surface, because the phase evaluates business usability of the findings, not of a product.",
        "depends_on": "A002 rejected/A005/A006/A051",
        "confidence": "High"
    },
    {
        "sid": "S015",
        "section": "Changes in this revision",
        "content": "Change 1 - forced by the rejection of A002. Single-pass clause extraction per document is removed from the design. Extraction is now multi-pass: a first broad pass over the category clause list, then one or more narrow targeted passes for vague, open-textured or negotiated clause items that the first pass leaves empty, low-confidence or schema-invalid. Sections S002, S003, S005, S006, S007 and component C003 are rewritten to describe pass-aware orchestration, per-clause-item pass tracking and pass provenance on every extracted record. New assumptions A051 and A052 replace the rejected A002, covering the multi-pass approach and the agreed maximum pass count. Change 2 - consequence of Change 1 on non-functional and risk sections. S011 and S013 now state that model calls per contract are variable rather than fixed and that Azure OpenAI quota in the non-production subscription is the binding constraint, because multi-pass extraction and repeated benchmark replays compound consumption. New assumption A057 records the quota headroom dependency arising from the NEED-VERIFY in S007. Change 3 - consequence of Change 1 on evaluation and oversight. C005 now reports first-pass and multi-pass accuracy separately so the sponsor can see what the extra passes bought, and S010 now states that clause items unresolved after the maximum pass count are shown as unresolved and routed to the exceptions list rather than filled with a best guess. Change 4 - forced by the correction to A005. The statement that contracts are digital and machine-readable is retained for this phase, with the reviewer's note that scanned documents are a possibility in the production phase. S004 now records scanned intake as a production-phase requirement rather than a flat exclusion, S005 adds an optical recognition intake path to the target-state view, S013 states that Phase 1 accuracy figures will not transfer unchanged to a scanned corpus, and new assumption A053 captures this. Change 5 - forced by the correction to A006. Cloud-stored copies remain the authoritative executed versions for this phase, with the reviewer's note that the production expectation is review of draft contracts so that risks are identified before signature. S004, S005, S008, S009 and S012 now carry the draft-contract implication for Phase 2, including that a draft path would need an inbound connection and tighter access control, and new assumption A054 captures this. Change 6 - housekeeping. The NEED-INPUT on pipeline compute form factor in C001 is now carried as assumption A055, and the NEED-VERIFY on managed vector store tier limits is now carried as assumption A058. All approved assumptions A001 and A003 to A050 are carried forward unchanged with their original identifiers and wording; A002 is deleted and not reused.",
        "depends_on": "A002/A005/A006/A051/A052/A053/A054/A055/A057/A058",
        "confidence": "High"
    }
]

# --- 12 ARCHITECTURE COMPONENTS (C001 to C006 From Sheet 12) ---
MASTER_COMPONENTS_6 = [
    {
        "id": "C001",
        "name": "Contract Landing Store and Ingestion Pipeline",
        "type": "Data Ingestion & Extraction",
        "technology": "Azure Blob Storage & Azure AI Document Intelligence",
        "technology_choice": "Azure Blob Storage landing container + Azure-native orchestration & compute; Azure AI Document Intelligence for layout extraction.",
        "purpose": "Holds authoritative contract samples supplied by PVR INOX and drives each document through layout extraction, chunking, and embedding. Preserves execution provenance.",
        "responsibility": "Ingest digital contracts, extract bounding-box coordinates, execute layout-aware chunking along clause boundaries, and feed downstream indexing.",
        "key_design_decisions": "Documents are read-only and never modified in place. Layout-aware extraction preserves page/coordinate references for 100% traceability. Chunking follows clause/section boundaries rather than fixed character tokens. Batch pipeline is restartable per document and pass.",
        "interfaces_in_out": "In: PVR INOX legal operations writes contract files to Blob container. Out: Calls Azure AI Document Intelligence over HTTPS via Managed Identity; writes chunks to C002 and document records to C004.",
        "data_classification": "Confidential (PVR INOX Internal Policy). Full commercial contract text, counterparty details. No masking in PoC phase.",
        "scalability_performance": "Parallel document batch processing. Throughput bound by Document Intelligence India quota and embedding rate limits.",
        "security_rai_controls": "Read-only access for delivery team. Azure Managed Identities for all service-to-service calls. Platform-managed encryption at rest/transit.",
        "failure_modes_mitigation": "Layout extraction errors routed to C004 exceptions record and displayed on dashboard. Pipeline crashes resume from last completed document/pass.",
        "dependencies": "C002 (Clause Index), C004 (Structured Store), C006 (Landing Zone), Azure Blob Storage container.",
        "environment": ["Dev", "Test", "UAT"]
    },
    {
        "id": "C002",
        "name": "Clause Index and Retrieval Layer",
        "type": "Search & Vector Database",
        "technology": "Azure AI Search / Managed Vector Store",
        "technology_choice": "Azure native managed search and vector store supporting hybrid BM25 + dense vector indexing.",
        "purpose": "Stores clause-level chunks with 1536-dim embeddings and metadata; serves targeted retrieval to classification, multi-pass extraction, and principle assessment.",
        "responsibility": "Index 40 chunks/doc across corpus with coordinate metadata; execute hybrid keyword and vector retrieval queries for targeted clause passes.",
        "key_design_decisions": "Hybrid retrieval combining BM25 keyword matching (for fixed legal terminology) and cosine vector similarity (for negotiated rewordings). Metadata carries document ID, category, clause type, page, and coordinates. Scoped per environment (Dev, Test, UAT).",
        "interfaces_in_out": "In: C001 writes chunks, embeddings, and metadata. In/Out: C003 issues retrieval queries per pass and receives ranked chunks with provenance.",
        "data_classification": "Confidential (PVR INOX Internal Policy). Clause text fragments, embeddings, coordinate metadata.",
        "scalability_performance": "Sized for 2,000,000 vectors (23.76 GB searchable index). Query rate scales with multi-pass extraction passes.",
        "security_rai_controls": "Restricted to project Managed Identities. No public endpoint. Mandatory provenance metadata attached to every retrieved chunk.",
        "failure_modes_mitigation": "Index unavailable causes pipeline pause and resume. Low recall detected by evaluation harness in C005. Chunk boundaries tuned in P06.",
        "dependencies": "C001 (Ingestion), C003 (Extraction Engine), C006 (Secrets & Network).",
        "environment": ["Dev", "Test", "UAT"]
    },
    {
        "id": "C003",
        "name": "Classification, Multi-Pass Extraction & Principle Assessment Engine",
        "type": "Core AI Reasoning & Orchestration",
        "technology": "Azure OpenAI Service (GPT-5 Reasoning / GPT-4o)",
        "technology_choice": "Azure OpenAI Service in India-eligible configuration invoked via Azure native orchestration.",
        "purpose": "Classifies contracts into 6 categories, extracts agreed clauses/attributes via multi-pass pipeline, and evaluates clauses against contracting principles.",
        "responsibility": "Prompt-based classification over 6 categories; Pass 1 broad extraction; Pass 2 targeted extraction for vague terms; separate 3-tier principle assessment (Agree, Agree with Mgmt, Not Agree).",
        "key_design_decisions": "Multi-pass extraction explicitly decouples broad extraction from vague/negotiated term passes. Principle assessment runs as an independent model call to isolate extraction defects from assessment logic. Structured JSON schema enforcement with pass provenance tracking. Maximum pass count ceiling prevents infinite loops.",
        "interfaces_in_out": "In: Invoked by orchestrator after C001 ingestion. Out: Queries C002 for context; calls Azure OpenAI via Managed Identity; writes structured assessments and pass provenance to C004.",
        "data_classification": "Confidential. Contract clause text in prompt payloads, structured evaluation results in responses. Confined to India region.",
        "scalability_performance": "Variable model calls per contract. Non-production Azure OpenAI TPM/RPM quota is the primary sizing constraint during evaluation replays.",
        "security_rai_controls": "No automated decision making (assistant role only). Unresolved vague terms marked as exceptions rather than hallucinated guesses. Grounding verification on all findings.",
        "failure_modes_mitigation": "Quota throttling handled via exponential backoff. Schema-invalid outputs re-queued as follow-up pass or routed to exception list. Infinite loops blocked by pass ceiling.",
        "dependencies": "C002 (Index), C004 (Store), C006 (Landing Zone), Azure OpenAI Service.",
        "environment": ["Dev", "Test", "UAT"]
    },
    {
        "id": "C004",
        "name": "Ontology, Principle Configuration & Risk Register Store",
        "type": "Structured Persistence & Risk Repository",
        "technology": "Azure SQL Database / Managed PostgreSQL",
        "technology_choice": "Azure native managed relational/structured database within non-production India region.",
        "purpose": "Stores contract ontologies, contracting principles, extracted clause records with pass provenance, exceptions, and the consolidated contract risk register.",
        "responsibility": "Persist configuration data (categories, principles, schemas) and operational results; serve data exports and dashboard aggregation queries.",
        "key_design_decisions": "Ontologies and principle rule sets stored as configuration rather than hardcoded in prompts. Register schema mirrors PVR INOX spreadsheet review layout extended with clause deep links. Exceptions are first-class records. 12-month data retention enforced.",
        "interfaces_in_out": "In: C001 writes document metadata; C003 writes clause records and assessments; legal team loads principle configs. Out: C005 reads for dashboard rendering and CSV/Excel register export.",
        "data_classification": "Confidential. Clause text, assessment outcomes, rationales, risk ratings, ontology configurations, exception records.",
        "scalability_performance": "Sized for 32.26 GB total persistent storage across all environments. Low concurrency during PoC validation.",
        "security_rai_controls": "Access limited to named project group via Azure AD SSO. Platform-managed encryption at rest (TDE). Strict foreign-key traceability.",
        "failure_modes_mitigation": "Database outage causes pipeline pause/resume. Record versioning prevents mid-run schema drift. Unprovenanced writes rejected at schema level.",
        "dependencies": "C001 (Ingestion), C003 (Engine), C005 (Dashboard), C006 (Security).",
        "environment": ["Dev", "Test", "UAT"]
    },
    {
        "id": "C005",
        "name": "Evaluation Harness, Dashboard & Operational Telemetry",
        "type": "Presentation, Analytics & Quality Assurance",
        "technology": "Azure Web App / React + Azure Monitor & Python Evaluation Harness",
        "technology_choice": "Read-only web cockpit behind Azure AD SSO + automated evaluation harness and platform telemetry.",
        "purpose": "Scores classification and extraction against legal-confirmed benchmark sets, provides risk visibility dashboard and exceptions list, and tracks token/cost metrics.",
        "responsibility": "Render 3 key business views (Risk by category, Mgmt approvals required, Outcome distribution); display exceptions list; report Pass 1 vs Multi-Pass accuracy; log FinOps telemetry.",
        "key_design_decisions": "Evaluation harness runs out-of-band to prevent interference with runtime pipeline. Dashboard is demonstration-grade and strictly read-only. First-pass vs multi-pass accuracy reported separately. Token and cost extrapolation clearly marked assumption-based.",
        "interfaces_in_out": "In: Reads findings, exceptions, and pass provenance from C004; reads benchmark golden answers; reads platform cost telemetry. Out: Renders UI to authenticated stakeholders; generates accuracy reports.",
        "data_classification": "Confidential (Contract Findings & Benchmark Answers). Operational telemetry is Internal.",
        "scalability_performance": "Serves small concurrent reviewer cohort (5-10 users) during validation sessions. Evaluation replay scales with benchmark set size.",
        "security_rai_controls": "Protected by corporate SSO (Azure AD) restricted to named project group. 100% clause-level deep links. Transparent failure reporting.",
        "failure_modes_mitigation": "Dashboard downtime mitigated by CSV/Excel register exports. Missing benchmark data reported as unmeasurable rather than guessed.",
        "dependencies": "C004 (Store), C006 (Identity), Legal Benchmark Answer Key.",
        "environment": ["Dev", "Test", "UAT"]
    },
    {
        "id": "C006",
        "name": "Identity, Secrets & Environment Landing Zone",
        "type": "Cloud Foundation & Security",
        "technology": "Microsoft Entra ID (Azure AD), Azure Key Vault, Azure Resource Manager",
        "technology_choice": "Azure AD for corporate SSO, Azure Key Vault for secrets management, dedicated resource groups in existing non-prod subscription.",
        "purpose": "Provides corporate single sign-on, securely manages keys and credentials, and provisions isolated Dev, Test, and UAT resource groups in India region.",
        "responsibility": "Federate corporate SSO; issue and enforce Managed Identities; store configuration secrets; enforce network isolation.",
        "key_design_decisions": "Deploys into existing non-production subscription. 3 isolated environments (Dev, Test, UAT) created as separate resource groups. Managed Identities preferred over shared connection strings. Customer-managed keys deferred to production.",
        "interfaces_in_out": "In: Stakeholders authenticate via corporate SSO. Out: Issues tokens and Managed Identities consumed by C001-C005; provides secrets from Key Vault.",
        "data_classification": "Confidential (Identity claims, API credentials, connection strings). No contract content passes through.",
        "scalability_performance": "Sized for named project group (20-50 users). Zero throughput bottleneck.",
        "security_rai_controls": "Strict RBAC. No local user accounts. All secrets stored in Key Vault with access auditing. All resources in Azure India region.",
        "failure_modes_mitigation": "SSO federation delay mitigated by early prerequisite checklist (P011). Key Vault rotation automated via Managed Identities.",
        "dependencies": "Existing Azure non-production subscription, PVR INOX Corporate Identity Provider.",
        "environment": ["Dev", "Test", "UAT"]
    }
]

# --- 13 MASTER ASSUMPTIONS (A001-A058) & PREREQUISITES (P001-P025) (Sheet 13) ---
MASTER_ASSUMPTIONS_ALL = [
    {"id": "A001", "type": "Assumption", "category": "Functional", "statement": "We assume the list of clauses and contract details to be extracted for each of the six categories is agreed in the first workshop and then frozen, because no list exists in the inputs today.", "impact_if_wrong": "If the list is not frozen, extraction is built against a moving target, the accuracy metrics have no stable denominator and every clause added after freeze is rework to the schema, prompts and evaluation set.", "owner_to_confirm": "Legal and Procurement leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A003", "type": "Assumption", "category": "Data", "statement": "We assume PVR INOX provides around 100 contracts for each of the six categories, and that each set genuinely contains standard, negotiated and known-problem contracts rather than standard templates only.", "impact_if_wrong": "If only standard templates are supplied, the principle assessment framework cannot be shown to detect any deviation, and the decision gate has no evidence on the capability the phase exists to prove.", "owner_to_confirm": "Legal Operations team", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A004", "type": "Assumption", "category": "Data", "statement": "We assume the representative sample processed in this phase is materially smaller than the 50,000-document live corpus, because that figure describes the eventual live service.", "impact_if_wrong": "If the full live corpus must be processed in this phase, the ingestion, indexing and model consumption profile changes entirely and the PoC tier scope no longer holds.", "owner_to_confirm": "Project sponsor and IT governance owner", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A005", "type": "Assumption", "category": "Data", "statement": "We assume every contract supplied in this phase is a digital, machine-readable file, so no scanned images, photographs of signed paper or handwritten documents appear in the sample. It is noted that in the production phase scanned documents are a possibility.", "impact_if_wrong": "If scanned documents appear in this phase, optical recognition and its tuning become necessary work that is not in scope, and layout and coordinate accuracy for traceability degrades.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": "Do note, in Production phase, scanned documents is a possibility"},
    {"id": "A006", "type": "Assumption", "category": "Data", "statement": "We assume the contract copies PVR INOX places in cloud storage are the final executed versions for this phase, so no separate check against an authoritative source system is needed. It is noted that in the production phase only draft contracts will be received, because the expectation is to identify and act before it is too late.", "impact_if_wrong": "If drafts are mixed into this phase's sample, findings will be raised against text that was never executed, and the accuracy comparison against the legal-confirmed benchmark becomes meaningless.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": "Do note in production phase, we will only get draft contracts as expectation is identify and act before too late"},
    {"id": "A007", "type": "Assumption", "category": "Functional", "statement": "We assume each document is assessed on its own, and that amendments, addenda and side letters are not linked back to their parent contract in this phase.", "impact_if_wrong": "If amendment linkage is required, a document relationship model and a merged-contract assessment path must be built, which is new design and new evaluation logic.", "owner_to_confirm": "Legal leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A008", "type": "Assumption", "category": "Data", "statement": "We assume contract files are placed into cloud storage with a folder and naming convention that identifies category and sample type, agreed at kick-off.", "impact_if_wrong": "If files arrive without the convention, category ground truth for evaluation is unavailable and a separate manifest or manual labelling exercise is needed before classification can be scored.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A009", "type": "Assumption", "category": "Functional", "statement": "We assume documented contracting principles and risk-rating criteria exist for some categories, and that the remainder can be elicited and legally validated in workshops inside this engagement.", "impact_if_wrong": "If principles cannot be elicited for a category, that category cannot be assessed at all and must be dropped from the assessment scope, reducing what the decision gate can judge.", "owner_to_confirm": "Legal leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A010", "type": "Assumption", "category": "Functional", "statement": "We assume the existing spreadsheet review format is stable and can be used as the starting structure for the risk register, extended with a link to the source clause.", "impact_if_wrong": "If the format is unstable or disputed, the register schema, the export and the dashboard fields must be redesigned after build rather than agreed before it.", "owner_to_confirm": "Legal and Procurement leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A011", "type": "Assumption", "category": "Functional", "statement": "We assume the dashboard needs to answer only three questions on day one - risk exposure by category, deviations requiring management approval, and count of findings by assessment outcome - plus show the exceptions list.", "impact_if_wrong": "If more questions are required, additional aggregation logic and dashboard surfaces are needed that were not sized as demonstration-grade output.", "owner_to_confirm": "Business function owners", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A012", "type": "Assumption", "category": "Functional", "statement": "We assume all four user groups - legal reviewer, procurement reviewer, business function owner and management approver - use the same dashboard, with only the two reviewer groups having anything beyond read-only access.", "impact_if_wrong": "If separate interfaces or per-group capability are required, multiple surfaces and a permission model must be built, which the PoC tier excludes.", "owner_to_confirm": "Business function owners", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A013", "type": "Assumption", "category": "Functional", "statement": "We assume every contract in scope is in English, so no translation or multilingual handling is needed.", "impact_if_wrong": "If non-English contracts appear, extraction prompts, the clause schema and the benchmark set must all be extended per language, and accuracy for those documents is unproven.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A014", "type": "Assumption", "category": "Responsible AI", "statement": "We assume a person reviews every finding before it is treated as reliable, so the solution is never relied on as a decision maker in this phase.", "impact_if_wrong": "If findings are acted on without review, the business takes contractual risk on unvalidated machine output, which the design explicitly does not support.", "owner_to_confirm": "Legal leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A015", "type": "Assumption", "category": "Governance", "statement": "We assume the nominated PVR INOX legal lead resolves any disagreement over whether a clause is Agree, Agree with Management Approval or Not Agree, and is available throughout validation.", "impact_if_wrong": "If no arbiter is available, disputed assessments stay open, the benchmark cannot be finalised and the accuracy report cannot be signed off.", "owner_to_confirm": "Legal leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A016", "type": "Assumption", "category": "Functional", "statement": "We assume the 95 percent classification and extraction accuracy bar is measurable against the legal-confirmed benchmark set and is treated as the acceptance condition for this phase.", "impact_if_wrong": "If the bar is not measurable as stated, the decision gate has no objective pass condition and acceptance becomes a matter of opinion.", "owner_to_confirm": "Project sponsor", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A017", "type": "Assumption", "category": "Data", "statement": "We assume the benchmark contracts confirmed by legal cover all six categories, not just a subset.", "impact_if_wrong": "If a category has no benchmark, accuracy for that category cannot be reported and that part of the scope cannot be accepted at the decision gate.", "owner_to_confirm": "Legal leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A018", "type": "Assumption", "category": "Technical", "statement": "We assume a managed search and vector store capability native to Azure meets the retrieval needs of this design, since the product selection is open.", "impact_if_wrong": "If it does not, retrieval design must be reworked mid-build and the clause-level traceability model depends on whatever replacement is chosen.", "owner_to_confirm": "Solution Architect and IT architecture team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A019", "type": "Assumption", "category": "Technical", "statement": "We assume the language models available through the chosen cloud provider in India regions can process a full contract clause set within a single request without splitting each document into many requests.", "impact_if_wrong": "If context capacity is smaller than assumed, each document must be split across many more requests, raising model consumption and extending processing time for the sample.", "owner_to_confirm": "IT architecture team", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A020", "type": "Assumption", "category": "Technical", "statement": "We assume service quota available in the non-production subscription is sufficient to process the sample and to replay the benchmark set repeatedly during evaluation cycles.", "impact_if_wrong": "If quota is insufficient, evaluation cycles are serialised or throttled and the number of accuracy iterations before the decision gate is reduced.", "owner_to_confirm": "IT governance owner", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A051", "type": "Assumption", "category": "Functional", "statement": "We assume clause extraction runs as more than one pass per contract - a first pass covering well-defined clause items, then separate targeted passes for vague or heavily negotiated terms - rather than a single extraction run per document.", "impact_if_wrong": "Model calls and processing time become variable. Multi-pass extraction increases quota consumption during validation replays.", "owner_to_confirm": "Legal leadership and Solution Architect", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A052", "type": "Assumption", "category": "Functional", "statement": "We assume the clause items that count as vague and need follow-up passes, and the maximum pass ceiling per item, are agreed in the first workshop alongside the clause list freeze.", "impact_if_wrong": "Without an agreed ceiling, extraction either retries indefinitely and consumes unbounded model quota, or stops too early and misses vague clauses.", "owner_to_confirm": "Legal leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A053", "type": "Assumption", "category": "Architecture", "statement": "We assume scanned documents are a production-phase possibility only, so the target architecture must show an optical recognition intake path while no such path is built or tested in this phase.", "impact_if_wrong": "If scanned handling must be proven now, OCR tuning becomes in-scope work and reported accuracy metrics must cover scanned documents.", "owner_to_confirm": "Legal Operations team and Solution Architect", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A054", "type": "Assumption", "category": "Architecture", "statement": "We assume the production expectation is to review draft contracts before signature, so the target architecture must show a draft-review path, while this phase is proven only on executed contracts.", "impact_if_wrong": "If draft review must be demonstrated in this phase, an inbound route for unsigned drafts, tighter access control and a different benchmark basis are required.", "owner_to_confirm": "Legal leadership and Solution Architect", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A055", "type": "Assumption", "category": "Technical", "statement": "We assume the compute form factor for the ingestion and orchestration pipeline is selected during architecture definition.", "impact_if_wrong": "If delayed, pipeline build cannot start and ingestion work sits idle.", "owner_to_confirm": "Solution Architect", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "A056", "type": "Assumption", "category": "Functional", "statement": "We assume clause items still unresolved after the maximum number of extraction passes are recorded as exceptions on the dashboard rather than reported as absent from the contract.", "impact_if_wrong": "If reported as absent, reviewers read a missing clause where a vague clause exists, creating false negatives on high-risk terms.", "owner_to_confirm": "Legal leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "A057", "type": "Assumption", "category": "Technical", "statement": "We assume Azure OpenAI request and token quota in the existing non-production subscription has enough headroom for multi-pass extraction across the full sample plus repeated benchmark replays.", "impact_if_wrong": "If headroom is short, evaluation cycles must be serialised or the sample reduced.", "owner_to_confirm": "IT governance owner", "confidence": "Low", "status": "Approve", "reason": ""},
    {"id": "A058", "type": "Assumption", "category": "Technical", "statement": "We assume the retrieval and index tier limits of the managed search and vector store capability accommodate the sample index size and higher query rate from multi-pass extraction.", "impact_if_wrong": "If limits bind, a higher tier must be provisioned or sample size reduced.", "owner_to_confirm": "Solution Architect and IT architecture team", "confidence": "Low", "status": "Approve", "reason": ""},

    # Prerequisites (P001 - P025)
    {"id": "P001", "type": "Prerequisite", "category": "Compliance", "statement": "PVR INOX legal function formally signs off that India-region hosting satisfies data residency obligations before any contract sample is uploaded.", "impact_if_wrong": "No contract sample may be uploaded, blocking ingestion and downstream build.", "owner_to_confirm": "Legal and Compliance function", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P002", "type": "Prerequisite", "category": "Governance", "statement": "All data access, security, compliance and governance approvals listed in engagement prerequisites are completed before planned start date.", "impact_if_wrong": "Environment provisioning and data access are blocked from start date.", "owner_to_confirm": "IT governance team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P003", "type": "Prerequisite", "category": "Data", "statement": "A nominated legal operations owner authorises release of the contract sample set to the delivery team before planned start date.", "impact_if_wrong": "No corpus exists, blocking ingestion, classification and extraction.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P004", "type": "Prerequisite", "category": "Data", "statement": "Representative contract samples covering all six in-scope categories (including standard, negotiated, and known deviations) are placed in Azure Blob Storage.", "impact_if_wrong": "Deviation detection cannot be demonstrated and framework cannot be evidenced at decision gate.", "owner_to_confirm": "Legal Operations team", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P005", "type": "Prerequisite", "category": "Data", "statement": "Approved contracting principles, clause standards, risk-rating criteria and management approval guidelines for each category are provided in Azure Blob Storage.", "impact_if_wrong": "Principle assessment cannot be configured, blocking P08 and removing category from scope.", "owner_to_confirm": "Legal and Procurement leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P006", "type": "Prerequisite", "category": "Data", "statement": "A benchmark set of manually reviewed contracts per category is confirmed as correct by PVR INOX legal team before testing begins.", "impact_if_wrong": "Accuracy cannot be measured, preventing decision gate evidence generation.", "owner_to_confirm": "Legal leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P007", "type": "Prerequisite", "category": "Functional", "statement": "The agreed list of clauses and contractual attributes to be extracted per category is confirmed in the first workshop and frozen before build.", "impact_if_wrong": "Extraction schemas and prompts cannot be finalised, blocking P07/P08.", "owner_to_confirm": "Legal and Procurement leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P008", "type": "Prerequisite", "category": "Governance", "statement": "Success metrics, assessment categories (Agree, Agree with Management Approval, Not Agree), and validation approach agreed prior to Phase 1 commencement.", "impact_if_wrong": "Decision gate has no agreed pass condition, making acceptance disputable.", "owner_to_confirm": "Project sponsor", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P009", "type": "Prerequisite", "category": "Environment", "statement": "Azure Blob Storage, Document Intelligence, and Azure OpenAI Service are provisioned in India region within non-production subscription with sufficient quota.", "impact_if_wrong": "No pipeline or evaluation can run, blocking P05 onwards.", "owner_to_confirm": "IT governance team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P010", "type": "Prerequisite", "category": "Environment", "statement": "Dev, Test and UAT environments are created as separate resource groups in existing non-production subscription.", "impact_if_wrong": "Build, test and validation cannot be separated, risking contamination.", "owner_to_confirm": "IT governance team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P011", "type": "Prerequisite", "category": "Security", "statement": "Corporate single sign-on federated to project environment and named project group created for dashboard access.", "impact_if_wrong": "Users cannot sign in to dashboard, blocking validation sessions.", "owner_to_confirm": "IT identity team", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P012", "type": "Prerequisite", "category": "Access", "statement": "Delivery team granted read access to contract landing container and write access to project resource groups.", "impact_if_wrong": "Team cannot read contracts or deploy components.", "owner_to_confirm": "IT governance team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P013", "type": "Prerequisite", "category": "Resourcing", "statement": "Named legal, procurement, business and IT stakeholders confirmed with agreed weekly time commitment, with Jitender Verma acting as SPOC.", "impact_if_wrong": "Workshops, principle elicitation and validation stall.", "owner_to_confirm": "Legal and Procurement leadership", "confidence": "Medium", "status": "Approve", "reason": ""},
    {"id": "P014", "type": "Prerequisite", "category": "Governance", "statement": "A nominated legal lead is appointed as final arbiter for assessment classification disputes during this phase.", "impact_if_wrong": "Disputed assessments stay open and accuracy report cannot be finalised.", "owner_to_confirm": "Legal leadership", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P015", "type": "Prerequisite", "category": "Governance", "statement": "A nominated legal operations contact is appointed to receive contracts and unresolved clause items routed to exceptions list.", "impact_if_wrong": "Exceptions accumulate with no owner.", "owner_to_confirm": "Legal Operations team", "confidence": "High", "status": "Approve", "reason": ""},
    {"id": "P017", "type": "Prerequisite", "category": "Governance", "statement": "Nithin Arora confirmed as executive sponsor and single signatory for decision gate acceptance and accuracy trade-offs.", "impact_if_wrong": "Decision gate cannot be signed off and trade-off decisions stall.", "owner_to_confirm": "Project sponsor office", "confidence": "High", "status": "Approve", "reason": ""}
]

# --- 21 RESOURCE LOADING WEEKS (W1 to W6 From Sheet 21) ---
MASTER_RESOURCE_LOADING = {
    "reference_duration_weeks": 6.0,
    "resolved_duration_weeks": 6.0,
    "stretch_applied_weeks": 0.0,
    "roles_flagged_infeasible": 0,
    "role_weekly_fte": [
        {"role_code": "PM", "role": "Project / Delivery Manager", "total_days": 10.5, "peak_fte": 1.35, "status": "OK", "w1": 0.67, "w2": 0.19, "w3": 0.0, "w4": 0.0, "w5": 0.0, "w6": 1.35},
        {"role_code": "BA", "role": "Business Analyst", "total_days": 10.0, "peak_fte": 0.91, "status": "OK", "w1": 0.91, "w2": 0.44, "w3": 0.0, "w4": 0.0, "w5": 0.33, "w6": 0.41},
        {"role_code": "SA", "role": "Solution Architect", "total_days": 9.5, "peak_fte": 0.94, "status": "OK", "w1": 0.63, "w2": 0.94, "w3": 0.18, "w4": 0.0, "w5": 0.0, "w6": 0.24},
        {"role_code": "AIE", "role": "AI / ML Engineer", "total_days": 30.3, "peak_fte": 2.45, "status": "OK", "w1": 0.08, "w2": 0.34, "w3": 1.40, "w4": 2.45, "w5": 2.09, "w6": 0.0},
        {"role_code": "DE", "role": "Data Engineer", "total_days": 14.0, "peak_fte": 1.48, "status": "OK", "w1": 0.17, "w2": 0.99, "w3": 1.48, "w4": 0.30, "w5": 0.0, "w6": 0.0},
        {"role_code": "MLO", "role": "MLOps / LLMOps Engineer", "total_days": 5.1, "peak_fte": 0.44, "status": "OK", "w1": 0.0, "w2": 0.24, "w3": 0.16, "w4": 0.20, "w5": 0.44, "w6": 0.03},
        {"role_code": "SWE", "role": "Software Engineer (Full-stack)", "total_days": 7.1, "peak_fte": 1.20, "status": "OK", "w1": 0.0, "w2": 0.0, "w3": 0.0, "w4": 0.30, "w5": 1.20, "w6": 0.0},
        {"role_code": "UX", "role": "UX / UI Designer", "total_days": 3.8, "peak_fte": 0.33, "status": "OK", "w1": 0.33, "w2": 0.33, "w3": 0.0, "w4": 0.03, "w5": 0.11, "w6": 0.0},
        {"role_code": "QA", "role": "QA / Test Engineer", "total_days": 2.9, "peak_fte": 0.46, "status": "OK", "w1": 0.0, "w2": 0.0, "w3": 0.0, "w4": 0.0, "w5": 0.15, "w6": 0.46},
        {"role_code": "SEC", "role": "Security Engineer", "total_days": 4.3, "peak_fte": 0.50, "status": "OK", "w1": 0.04, "w2": 0.50, "w3": 0.11, "w4": 0.0, "w5": 0.25, "w6": 0.0},
        {"role_code": "SRE", "role": "SRE / Platform Engineer", "total_days": 4.6, "peak_fte": 0.39, "status": "OK", "w1": 0.0, "w2": 0.39, "w3": 0.16, "w4": 0.0, "w5": 0.24, "w6": 0.18},
        {"role_code": "RAI", "role": "Responsible AI / Compliance Lead", "total_days": 1.5, "peak_fte": 0.32, "status": "OK", "w1": 0.0, "w2": 0.0, "w3": 0.0, "w4": 0.0, "w5": 0.32, "w6": 0.0}
    ],
    "team_total_fte": [2.83, 4.36, 3.49, 3.28, 5.13, 2.67]
}

# --- 30 BILL OF MATERIALS (B001 to B025 From Sheet 30) ---
MASTER_BOM_25 = [
    {"bid": "B001", "category": "AI and model services", "component": "Azure OpenAI Service generative model deployment", "purpose": "Runs contract classification, first-pass and follow-up clause extraction passes, and principle assessment calls for C003", "platform": "Microsoft Azure", "sku_name": "Azure OpenAI GPT-5 Reasoning / GPT-4o (India Region)", "quantity": "238,040,000.00", "unit": "tokens/month", "sizing_basis": "Total tokens per month", "environment": "Non-production", "lead_time": "Quota increase request required for multi-pass runs (3-day lead time)"},
    {"bid": "B002", "category": "AI and model services", "component": "Azure OpenAI Service embedding model deployment", "purpose": "Generates 1536-dimension clause chunk embeddings for the clause index in C002", "platform": "Microsoft Azure", "sku_name": "text-embedding-3-small (1536 dims, India Region)", "quantity": "150,040,000.00", "unit": "tokens/month", "sizing_basis": "Input tokens per month", "environment": "Non-production", "lead_time": "Standard provisioning via Managed Identity"},
    {"bid": "B003", "category": "AI and model services", "component": "Azure AI Document Intelligence", "purpose": "Recovers layout-aware text with page and coordinate references from contract documents in C001", "platform": "Microsoft Azure", "sku_name": "Azure AI Document Intelligence (Layout Model Tier S0)", "quantity": "2,000.00", "unit": "requests/day", "sizing_basis": "Requests per day", "environment": "Non-production", "lead_time": "Provisioned in India Central region"},
    {"bid": "B004", "category": "Vector and search services", "component": "Managed vector and search index", "purpose": "Holds clause-level chunks with document, category, clause type, page and coordinate metadata and serves hybrid retrieval", "platform": "Microsoft Azure", "sku_name": "Azure AI Search (Standard S1 Tier, Hybrid Search Enabled)", "quantity": "23.76", "unit": "GB", "sizing_basis": "Searchable index including HA/DR", "environment": "All", "lead_time": "One index per environment (Dev, Test, UAT)"},
    {"bid": "B005", "category": "Data platform and storage", "component": "Azure Blob Storage contract landing container", "purpose": "Holds the authoritative contract samples PVR INOX places for this phase; read-only to delivery team", "platform": "Microsoft Azure", "sku_name": "Azure Blob Storage (Hot LRS, India Central)", "quantity": "1.00", "unit": "GB", "sizing_basis": "Raw corpus", "environment": "Non-production", "lead_time": "Pre-configured landing container"},
    {"bid": "B006", "category": "Data platform and storage", "component": "Structured store for ontology, principles, clause records and risk register", "purpose": "Single source for register export and dashboard, holding ontology, principle rule set, clause records, exceptions, findings", "platform": "Microsoft Azure", "sku_name": "Azure SQL Database (General Purpose Serverless, 2 vCore)", "quantity": "32.26", "unit": "GB", "sizing_basis": "Total storage all environments", "environment": "All", "lead_time": "12-month retention configured"},
    {"bid": "B007", "category": "Data platform and storage", "component": "Processed corpus and intermediate extraction output store", "purpose": "Retains layout-extracted text, chunks and per-pass intermediate output so a re-run does not repeat passes that already succeeded", "platform": "Microsoft Azure", "sku_name": "Azure Blob Storage (Cool LRS)", "quantity": "1.40", "unit": "GB", "sizing_basis": "Processed corpus", "environment": "Non-production", "lead_time": "Non-production retention"},
    {"bid": "B008", "category": "Compute and hosting", "component": "Pipeline orchestration and compute for ingestion and pass-aware extraction", "purpose": "Drives document journey through layout extraction, chunking, embedding, classification, multi-pass extraction and assessment", "platform": "Microsoft Azure", "sku_name": "Azure Container Apps / Azure Functions Premium (EP1)", "quantity": "4.00", "unit": "instances", "sizing_basis": "Total instances all environments", "environment": "All", "lead_time": "Serverless container compute"},
    {"bid": "B009", "category": "Compute and hosting", "component": "Application and API hosting for findings service and dashboard surface", "purpose": "Hosts API layer over findings store, register export, and read-only dashboard surface", "platform": "Microsoft Azure", "sku_name": "Azure App Service (Linux Basic B1 / P0v3)", "quantity": "2.00", "unit": "instances", "sizing_basis": "Instances per production environment", "environment": "Non-production", "lead_time": "Standard App Service Plan"},
    {"bid": "B010", "category": "Compute and hosting", "component": "Application compute footprint", "purpose": "Serves demonstration dashboard and API at small concurrent reviewer group during validation sessions", "platform": "Microsoft Azure", "sku_name": "Compute Core Allocation", "quantity": "1.00", "unit": "vCPU", "sizing_basis": "Application vCPU at peak", "environment": "Non-production", "lead_time": "Peak concurrency 5-10 reviewers"},
    {"bid": "B013", "category": "Identity", "component": "Corporate single sign-on for demonstration interface", "purpose": "Authenticates named project group into dashboard; no local accounts created", "platform": "Microsoft Azure", "sku_name": "Microsoft Entra ID (PVR INOX Existing Corporate Tenant)", "quantity": "20.00", "unit": "seats", "sizing_basis": "Named Project Group", "environment": "All", "lead_time": "App registration and security group assignment"},
    {"bid": "B014", "category": "Secrets and key management", "component": "Managed secrets store", "purpose": "Holds keys, connection strings and credentials; Managed Identities preferred over shared keys", "platform": "Microsoft Azure", "sku_name": "Azure Key Vault (Standard Tier)", "quantity": "1.00", "unit": "instances", "sizing_basis": "Central Secrets Store", "environment": "All", "lead_time": "Zero lead time"},
    {"bid": "B015", "category": "Networking and private connectivity", "component": "Closed non-production network boundary", "purpose": "Keeps environment closed with no public data paths beyond authenticated dashboard", "platform": "Microsoft Azure", "sku_name": "Azure Virtual Network & NSGs", "quantity": "1.00", "unit": "instances", "sizing_basis": "Network Boundary", "environment": "Non-production", "lead_time": "Confined to India region"},
    {"bid": "B016", "category": "Observability", "component": "Platform telemetry, structured logging and tracing", "purpose": "Captures pipeline traces, per-pass token consumption and document volume feeding operating cost estimate", "platform": "Microsoft Azure", "sku_name": "Azure Log Analytics & Application Insights", "quantity": "6.34", "unit": "GB", "sizing_basis": "Logs and traces at retention", "environment": "All", "lead_time": "Standard monitoring workspace"},
    {"bid": "B017", "category": "Observability", "component": "Cost and token metering for operating cost estimate", "purpose": "Captures metered consumption so Azure operating cost estimate is derived from measured PoC usage", "platform": "Microsoft Azure", "sku_name": "Azure Cost Management & Billing API", "quantity": "1.00", "unit": "instances", "sizing_basis": "Subscription Metering", "environment": "All", "lead_time": "Requires billing reader role from IT owner"},
    {"bid": "B018", "category": "CI/CD and source control", "component": "Source control repository and branch policy", "purpose": "Holds pipeline code, prompts, clause schema, pass policy and ontology configuration under version control", "platform": "Microsoft Azure", "sku_name": "Azure DevOps Repos / GitHub Enterprise", "quantity": "5.00", "unit": "seats", "sizing_basis": "Developer Seats", "environment": "All", "lead_time": "Scripted provisioning"},
    {"bid": "B020", "category": "Security tooling", "component": "Platform-native access control and audit logging", "purpose": "Restricts access to named project team and records access to confidential contract content", "platform": "Microsoft Azure", "sku_name": "Azure RBAC & Activity Logs", "quantity": "1.00", "unit": "instances", "sizing_basis": "Platform Controls", "environment": "All", "lead_time": "Standard Azure RBAC"},
    {"bid": "B023", "category": "Non-cloud items", "component": "Benchmark review effort and annotation of legal-confirmed answer key", "purpose": "PVR INOX legal effort to confirm manually reviewed benchmark contracts against which accuracy is measured", "platform": "Client Non-Cloud", "sku_name": "Legal Benchmark Annotation Effort", "quantity": "100.00", "unit": "contracts/category", "sizing_basis": "Benchmark Dataset", "environment": "Client Estate", "lead_time": "Confirmed before testing begins"}
]

# --- 31 SIZING MODEL 34 METRICS (Sheet 31) ---
MASTER_SIZING_METRICS_34 = {
    "workload": {
        "requests_per_day": {"value": 2000.0, "unit": "requests", "derivation": "Input"},
        "requests_per_month": {"value": 44000.0, "unit": "requests", "derivation": "Daily requests x 22 working days/month"},
        "peak_rps": {"value": 3.00, "unit": "req/s", "derivation": "Input peak rate"},
        "retrieved_context_tokens_per_req": {"value": 2560.0, "unit": "tokens", "derivation": "top-k (5) x tokens per chunk (512)"},
        "total_input_tokens_per_req": {"value": 3410.0, "unit": "tokens", "derivation": "User prompt (500) + retrieved context (2560) + system prompt (350)"},
        "output_tokens_per_req": {"value": 2000.0, "unit": "tokens", "derivation": "Input avg completion tokens"},
        "input_tokens_per_month": {"value": 150040000.0, "unit": "tokens/month", "derivation": "Total input tokens per req x 44,000 monthly reqs"},
        "output_tokens_per_month": {"value": 88000000.0, "unit": "tokens/month", "derivation": "Output tokens per req x 44,000 monthly reqs"},
        "total_tokens_per_month": {"value": 238040000.0, "unit": "tokens/month", "derivation": "Sum of input and output tokens (238.04M)"},
        "peak_tokens_per_minute": {"value": 973800.0, "unit": "tokens/min", "derivation": "Peak TPS (3) x 60s x tokens per req (5410) = 973.8k TPM reservation"}
    },
    "knowledge": {
        "vector_count": {"value": 2000000.0, "unit": "vectors", "derivation": "50,000 documents x 40 chunks/doc = 2.0M vectors"},
        "raw_vector_payload_gb": {"value": 12.29, "unit": "GB", "derivation": "Vectors (2M) x dimensions (1536) x 4 bytes (float32)"},
        "vector_index_footprint_gb": {"value": 19.66, "unit": "GB", "derivation": "Raw payload x index overhead factor (1.60)"},
        "chunk_text_metadata_gb": {"value": 4.10, "unit": "GB", "derivation": "Chunk text stored alongside vectors (approx 4 bytes/token)"},
        "searchable_index_total_gb": {"value": 23.76, "unit": "GB", "derivation": "Vector index footprint + chunk text & metadata"}
    },
    "storage": {
        "raw_corpus_gb": {"value": 1.00, "unit": "GB", "derivation": "Input raw corpus size"},
        "processed_corpus_gb": {"value": 1.40, "unit": "GB", "derivation": "Raw corpus x processed-to-raw ratio (1.40)"},
        "logs_and_traces_gb": {"value": 6.34, "unit": "GB", "derivation": "Monthly requests x 12,000 bytes x 12 months retention"},
        "conversation_history_gb": {"value": 11.43, "unit": "GB", "derivation": "Monthly requests x tokens x 4 bytes x 12 months retention"},
        "total_persistent_storage_gb": {"value": 20.16, "unit": "GB", "derivation": "Sum of raw, processed, logs, and conversation history"}
    },
    "compute": {
        "application_vcpu_peak": {"value": 1.00, "unit": "vCPU", "derivation": "Peak TPS (3) x 120ms / 1000 / 0.65 target utilisation = 0.55 floored at 1.0"},
        "application_ram_peak_gb": {"value": 4.00, "unit": "GB", "derivation": "vCPU (1.0) x 4.0 GB RAM per vCPU"},
        "instances_per_prod_env": {"value": 2.00, "unit": "instances", "derivation": "vCPU demand / 4 vCPU per instance, floored at minimum 2 instances"}
    },
    "resilience": {
        "ha_dr_multiplier": {"value": 1.00, "unit": "x", "derivation": "None (single instance) from inputs"},
        "production_instances": {"value": 2.00, "unit": "instances", "derivation": "2 instances x 1.0 HA/DR factor"},
        "production_storage_gb": {"value": 20.16, "unit": "GB", "derivation": "20.16 GB x 1.0 HA/DR factor"},
        "searchable_index_gb": {"value": 23.76, "unit": "GB", "derivation": "23.76 GB x 1.0 HA/DR factor"}
    },
    "environments": {
        "non_prod_factor": {"value": 0.60, "unit": "x", "derivation": "Dev + Test footprint (60% of production)"},
        "total_instances_all_envs": {"value": 4.00, "unit": "instances", "derivation": "Production instances (2) x (1 + 0.60) = 3.2 floored at 4.0"},
        "total_storage_all_envs_gb": {"value": 32.26, "unit": "GB", "derivation": "Production storage (20.16 GB) x 1.60 = 32.26 GB"}
    },
    "growth_year_2": {
        "annual_growth_factor": {"value": 1.30, "unit": "x", "derivation": "30% projected annual volume increase"},
        "year_2_tokens_per_month": {"value": 309452000.0, "unit": "tokens/month", "derivation": "Year 1 tokens (238.04M) x 1.30 = 309.45M tokens/mo"},
        "year_2_searchable_index_gb": {"value": 30.88, "unit": "GB", "derivation": "Year 1 index (23.76 GB) x 1.30 = 30.88 GB"},
        "year_2_total_storage_gb": {"value": 41.94, "unit": "GB", "derivation": "Year 1 storage (32.26 GB) x 1.30 = 41.94 GB"},
        "year_2_instances": {"value": 6.00, "unit": "instances", "derivation": "Year 1 instances (4) x 1.30 = 5.2 floored at 6 instances"}
    }
}

# --- 10 CLARIFICATION QUESTIONS (Q001-Q052 From Sheet 10) ---
MASTER_CLARIFICATION_QUESTIONS_52 = [
    {"qid": "Q001", "category": "Key Decision", "question": "Which cloud platforms are approved for this work, and is one of them mandated as the main one?", "why_it_matters": "A second approved platform changes how many deployment patterns must be designed and tested.", "who_answers": "Enterprise Architecture / IT leadership at PVR INOX", "priority": "Blocker", "answer": "Microsoft Azure is the only approved platform for both primary hosting and any secondary use, as stated in the engagement inputs.", "status": "Answered"},
    {"qid": "Q002", "category": "Key Decision", "question": "Is there an existing company cloud account or subscription that this solution must be built inside, or will a new one be created?", "why_it_matters": "Deploying into existing environment means inheriting approval queues; new one means initial setup lead time.", "who_answers": "IT Infrastructure / Cloud Platform team at PVR INOX", "priority": "Blocker", "answer": "Existing Account is present. It's PoC so we are going to use only non-production subscription.", "status": "Answered"},
    {"qid": "Q003", "category": "Key Decision", "question": "Is there any contract data or processing that must remain on your own premises or inside a specific country for legal or policy reasons?", "why_it_matters": "Determines whether processing can run entirely in cloud region or must be split on-premises.", "who_answers": "Legal and Compliance at PVR INOX", "priority": "Blocker", "answer": "All contract data and processing remain within the India region of the chosen cloud; no on-premises components are required.", "status": "Answered"},
    {"qid": "Q004", "category": "Key Decision", "question": "If more than one cloud platform ends up in use: which one owns sign-in, storage, and AI services?", "why_it_matters": "Splitting responsibilities adds multi-cloud latency, networking, and permission complexity.", "who_answers": "Enterprise Architecture at PVR INOX", "priority": "High", "answer": "A single platform (Microsoft Azure) provides sign-in, data storage and AI services for this phase.", "status": "Answered"},
    {"qid": "Q005", "category": "Key Decision", "question": "If two clouds are involved, does a private network link already exist, and which budget absorbs transfer costs?", "why_it_matters": "Private cross-cloud links have long lead times and data egress costs.", "who_answers": "IT Networking and Finance at PVR INOX", "priority": "Medium", "answer": "No cross-cloud connectivity is required because the solution is single-platform; no cross-cloud transfer costs arise.", "status": "Answered"},
    {"qid": "Q006", "category": "Key Decision", "question": "Is the choice of AI model limited by an existing vendor agreement or approved model list?", "why_it_matters": "A restricted model list rules out specific vision/reasoning models.", "who_answers": "Legal, Procurement and IT Security at PVR INOX", "priority": "Blocker", "answer": "Models available through Azure OpenAI Service in India-eligible configuration are used, with no third-party model providers introduced.", "status": "Answered"},
    {"qid": "Q007", "category": "Key Decision", "question": "Which country or regions satisfy your data residency obligations for in-scope contracts, and who signs off?", "why_it_matters": "Residency limits cloud region availability; unnamed approver delays upload.", "who_answers": "Legal / Data Protection Officer at PVR INOX", "priority": "Blocker", "answer": "India-based regions only, signed off by the PVR INOX legal function before any contract sample is uploaded.", "status": "Answered"},
    {"qid": "Q008", "category": "Key Decision", "question": "Is there an approved product you require us to use for searching contract text, or is selection open?", "why_it_matters": "Mandated search products constrain indexing and coordinate retrieval.", "who_answers": "Enterprise Architecture at PVR INOX", "priority": "High", "answer": "The selection is open, and a managed search and vector store capability native to Azure (Azure AI Search) is used.", "status": "Answered"},
    {"qid": "Q009", "category": "Non-Functional", "question": "What is your approved way of storing passwords, keys and encryption material, and do you require CMKs?", "why_it_matters": "Customer-managed keys add setup, rotation and recovery work.", "who_answers": "IT Security at PVR INOX", "priority": "High", "answer": "Platform-managed encryption with Azure Key Vault is used for this phase; customer-managed keys are deferred to the production phase.", "status": "Answered"},
    {"qid": "Q010", "category": "Key Decision", "question": "Who will run and support this solution after it is handed over, and does that team already support Azure?", "why_it_matters": "Determines required handover depth and operational training.", "who_answers": "IT Operations leadership at PVR INOX", "priority": "High", "answer": "The proof of concept is supported by the delivery team on a best-effort basis for an agreed handover window; no production support model is established in this phase.", "status": "Answered"},
    {"qid": "Q011", "category": "Key Decision", "question": "Which environments must exist for this work - dev, test, staging, production, DR?", "why_it_matters": "Each additional environment adds infrastructure and validation effort.", "who_answers": "IT Platform team at PVR INOX", "priority": "Blocker", "answer": "Dev, Test and UAT environments are needed in non-production subscription.", "status": "Answered"},
    {"qid": "Q012", "category": "Key Decision", "question": "Are there any purchasing, contracting or licence approval steps with a waiting period that would delay start?", "why_it_matters": "Procurement lead times sit outside delivery team control.", "who_answers": "Procurement at PVR INOX", "priority": "High", "answer": "Waiting time is 3 Days. Completed before planned start date.", "status": "Answered"},
    {"qid": "Q013", "category": "Functional", "question": "Which specific contract categories are in scope for this phase?", "why_it_matters": "Every additional category needs its own ontology, principles and assessment rules.", "who_answers": "Legal and Procurement leads at PVR INOX", "priority": "Blocker", "answer": "The six categories named in the engagement inputs - lease, vendor, service, facilities, technology and marketing - are the complete scope.", "status": "Answered"},
    {"qid": "Q014", "category": "Functional", "question": "How many sample contracts will you provide for each category?", "why_it_matters": "Need problem contracts to prove deviation detection.", "who_answers": "Legal and Procurement leads at PVR INOX", "priority": "Blocker", "answer": "100 for each category (approx 600 total), covering standard, negotiated, and known deviation examples.", "status": "Answered"},
    {"qid": "Q015", "category": "Functional", "question": "Is the corpus figure of 50,000 documents the set to be processed in this phase or eventual live size?", "why_it_matters": "Full corpus vs validation sample changes processing run time and quota.", "who_answers": "Engagement sponsor at PVR INOX", "priority": "Blocker", "answer": "The 50,000-document figure describes the eventual live corpus; this phase processes an agreed representative sample only.", "status": "Answered"},
    {"qid": "Q016", "category": "Functional", "question": "Which contract clauses and contract details must be extracted for each category?", "why_it_matters": "The clause list defines what is built and what 95% accuracy is measured against.", "who_answers": "Legal team at PVR INOX", "priority": "Blocker", "answer": "An agreed clause list per category is confirmed in the first workshop and frozen before build begins.", "status": "Answered"},
    {"qid": "Q017", "category": "Functional", "question": "Do written contracting principles and risk-rating criteria already exist for each category?", "why_it_matters": "Undocumented principles require workshop elicitation before assessment logic can be built.", "who_answers": "Legal and Procurement leads at PVR INOX", "priority": "Blocker", "answer": "Principles exist in documented form for some categories and must be elicited in workshops for the remainder, with legal validation.", "status": "Answered"},
    {"qid": "Q018", "category": "Functional", "question": "Who has authority to decide whether a clause is Agree, Agree with Management Approval, or Not Agree?", "why_it_matters": "Single named arbiter avoids validation stalls on unresolved disagreements.", "who_answers": "Legal leadership at PVR INOX", "priority": "High", "answer": "A nominated legal lead at PVR INOX is the final arbiter for assessment classification during this phase.", "status": "Answered"},
    {"qid": "Q019", "category": "Functional", "question": "What does an acceptable result look like in practice?", "why_it_matters": "Converts numeric targets into business judgement for proceeding to Phase 2.", "who_answers": "Engagement sponsor at PVR INOX", "priority": "High", "answer": "The technical success metrics stated in the engagement inputs (≥95% accuracy, 100% traceability) measured against benchmark set.", "status": "Answered"},
    {"qid": "Q020", "category": "Functional", "question": "Which manually reviewed contracts will serve as the benchmark that results are compared against?", "why_it_matters": "Accuracy cannot be claimed without an agreed benchmark answer key.", "who_answers": "Legal team at PVR INOX", "priority": "Blocker", "answer": "An agreed set of previously reviewed contracts per category, confirmed as correct by the PVR INOX legal team before testing begins.", "status": "Answered"},
    {"qid": "Q025", "category": "Functional", "question": "Who are the four groups of people who will use this solution?", "why_it_matters": "Drives how many views and permission levels must be demonstrated.", "who_answers": "Engagement sponsor at PVR INOX", "priority": "High", "answer": "The four groups are legal reviewer, procurement reviewer, business function owner and management approver, with read-only dashboard access for all but reviewers.", "status": "Answered"},
    {"qid": "Q027", "category": "Functional", "question": "Will contracts be provided as searchable digital files or scanned images/photos?", "why_it_matters": "Scanned paper originals require OCR tuning not in scope for PoC.", "who_answers": "Legal operations at PVR INOX", "priority": "Blocker", "answer": "Contracts are digital and machine-readable, as stated in assumptions; scanned or handwritten originals are out of scope for this phase.", "status": "Answered"},
    {"qid": "Q044", "category": "Key Decision", "question": "Who is the single person who signs off that this phase has passed its decision gate?", "why_it_matters": "A decision gate without a named approver causes completed engagements to remain open.", "who_answers": "Engagement sponsor at PVR INOX", "priority": "Blocker", "answer": "Nithin Arora is the executive sponsor and single signatory for decision gate acceptance.", "status": "Answered"},
    {"qid": "Q045", "category": "Key Decision", "question": "Which named legal and business subject matter experts will be available for workshops?", "why_it_matters": "Expert availability determines whether timeline holds.", "who_answers": "Legal and Business leadership at PVR INOX", "priority": "Blocker", "answer": "For all queries Jitender Verma will act as the SPOC, coordinating legal and procurement SME availability.", "status": "Answered"},
    {"qid": "Q052", "category": "Other", "question": "Who at PVR INOX is responsible for obtaining data access, security and governance approvals?", "why_it_matters": "Prerequisites without a named owner cause start-date delays.", "who_answers": "IT Governance at PVR INOX", "priority": "Blocker", "answer": "Gaurav is the SPOC for IT governance, security, and data access approvals.", "status": "Answered"}
]

# --- 92 QA PARSE LOG AUDIT ENTRIES (Sheet 92) ---
MASTER_QA_LOGS = [
    {"timestamp": "2026-09-24 14:42:00", "step": "Step 13", "block": "QA", "severity": "INFO", "message": "QA run started. Every check below is re-run from scratch."},
    {"timestamp": "2026-09-24 14:42:01", "step": "Step 13", "block": "NAMES", "severity": "PASS", "message": "All 83 required named ranges resolve."},
    {"timestamp": "2026-09-24 14:42:02", "step": "Step 13", "block": "PATHS", "severity": "PASS", "message": "Prompt and response files defaulted to workspace directory."},
    {"timestamp": "2026-09-24 14:42:03", "step": "Step 13", "block": "LIBRARY", "severity": "PASS", "message": "98 library task(s) included for domain 'AI / GenAI'."},
    {"timestamp": "2026-09-24 14:42:04", "step": "Step 13", "block": "FORMULAS", "severity": "PASS", "message": "No formula errors anywhere in the estimation engine."},
    {"timestamp": "2026-09-24 14:42:05", "step": "Step 13", "block": "ESTIMATE", "severity": "PASS", "message": "98 task row(s), no duplicates, all role and phase codes valid. Sum of effort: 127.1 person-days (97.5 delivery + 11.7 PM + 11.6 contingency)."},
    {"timestamp": "2026-09-24 14:42:06", "step": "Step 13", "block": "RECONCILE", "severity": "PASS", "message": "Resource loading reconciles to the estimate (127.1 vs 127.1 person-days)."},
    {"timestamp": "2026-09-24 14:42:07", "step": "Step 13", "block": "RECONCILE", "severity": "PASS", "message": "Day-wise tasks reconcile to the estimate."},
    {"timestamp": "2026-09-24 14:42:08", "step": "Step 13", "block": "GATE", "severity": "PASS", "message": "The assumption gate has PASSED (83/83 rows approved)."},
    {"timestamp": "2026-09-24 14:42:09", "step": "Step 13", "block": "QUESTIONS", "severity": "PASS", "message": "No Blocker-priority questions are outstanding (0 blockers outstanding)."},
    {"timestamp": "2026-09-24 14:42:10", "step": "Step 13", "block": "SIZING", "severity": "PASS", "message": "34 sizing metrics all compute to a non-negative number."},
    {"timestamp": "2026-09-24 14:42:11", "step": "Step 13", "block": "CONFIG", "severity": "PASS", "message": "Configuration values are all within sane bounds."},
    {"timestamp": "2026-09-24 14:42:12", "step": "Step 13", "block": "QA", "severity": "INFO", "message": "QA run finished. 12 passed, 0 errors. Ready for executive sign-off."}
]
