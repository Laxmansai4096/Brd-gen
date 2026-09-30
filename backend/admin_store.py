import os
import json
import csv
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

ADMIN_DATA_DIR = "admin_data"
CALENDARS_FILE = os.path.join(ADMIN_DATA_DIR, "calendars.json")
ASSUMPTIONS_FILE = os.path.join(ADMIN_DATA_DIR, "master_assumptions.json")
DEFAULTS_FILE = os.path.join(ADMIN_DATA_DIR, "system_defaults.json")
TASK_LIBRARY_FILE = os.path.join(ADMIN_DATA_DIR, "task_library.json")
MULTIPLIERS_FILE = os.path.join(ADMIN_DATA_DIR, "multipliers.json")

os.makedirs(ADMIN_DATA_DIR, exist_ok=True)

class HolidayEntry(BaseModel):
    date: str
    name: str
    type: str = "Statutory"  # "Statutory", "Floating", "Bank Holiday", "Regional"

class LocationCalendar(BaseModel):
    country_code: str
    country_name: str
    currency_code: str = "USD"
    currency_symbol: str = "$"
    working_days_per_week: int = 5
    daily_working_hours: float = 8.0
    hourly_rate: float = 30.0          # Base USD rate
    hourly_rate_local: float = 30.0    # Rate in native location currency
    annual_holiday_allowance: int = 12
    holidays: List[HolidayEntry] = []

# --- 11 DELIVERY TIERS ---
DELIVERY_TIERS = {
    "PoC": {
        "kind": "Base", "source": "", "target": "PoC", "headline_weight": 0.289, "src_idx": 0, "tgt_idx": 1,
        "description": "Proof of Concept. Throwaway build that answers one question: is this technically feasible? Happy path only, synthetic or sampled data, no NFRs, no security review, no CI/CD, single environment, demo-only UI. Not deployed to real users."
    },
    "Pilot": {
        "kind": "Base", "source": "", "target": "Pilot", "headline_weight": 0.525, "src_idx": 0, "tgt_idx": 2,
        "description": "Limited live trial with a controlled user cohort on real data. Basic auth, basic logging, manual operations, light NFRs, time-boxed. Refactor expected before scale-up. Usually runs in a non-production or ring-fenced environment."
    },
    "MVP": {
        "kind": "Base", "source": "", "target": "MVP", "headline_weight": 0.778, "src_idx": 0, "tgt_idx": 3,
        "description": "Minimum Viable Product. Smallest releasable product slice with a real user base. Production-grade hardening on the critical path, automated deployment, core security and Responsible AI controls, documented runbooks, but deliberately reduced scope, limited HA/DR, and accepted technical debt logged."
    },
    "Production Grade": {
        "kind": "Base", "source": "", "target": "Production Grade", "headline_weight": 1.000, "src_idx": 0, "tgt_idx": 4,
        "description": "Full production readiness. Complete functional scope, enforced NFRs (performance, availability, HA/DR), full security and Responsible AI gates, infrastructure as code, CI/CD, observability, cost governance, load and UAT testing, formal cutover, hypercare and operational handover."
    },
    "PoC to Pilot": {
        "kind": "Transition", "source": "PoC", "target": "Pilot", "headline_weight": 0.320, "src_idx": 1, "tgt_idx": 2,
        "description": "Uplift of an existing PoC to a controlled live trial. Charges only the delta between PoC and Pilot rigour, plus a rework uplift because PoC artefacts are rarely reusable as-is, plus a mobilisation floor for re-discovery and re-baselining."
    },
    "PoC to MVP": {
        "kind": "Transition", "source": "PoC", "target": "MVP", "headline_weight": 0.612, "src_idx": 1, "tgt_idx": 3,
        "description": "Uplift of an existing PoC directly to a releasable MVP. Charges the PoC-to-MVP rigour delta plus rework uplift and mobilisation floor. Expect substantial re-architecture as PoC shortcuts are unwound."
    },
    "PoC to Production Grade": {
        "kind": "Transition", "source": "PoC", "target": "Production Grade", "headline_weight": 0.867, "src_idx": 1, "tgt_idx": 4,
        "description": "Uplift of an existing PoC straight to full production readiness. Charges the full rigour delta plus rework uplift and mobilisation floor. Highest-risk transition: most PoC code is replaced rather than extended."
    },
    "Pilot to MVP": {
        "kind": "Transition", "source": "Pilot", "target": "MVP", "headline_weight": 0.342, "src_idx": 2, "tgt_idx": 3,
        "description": "Uplift of a running pilot into a releasable MVP. Charges the Pilot-to-MVP rigour delta plus rework uplift and mobilisation floor. Pilot learnings usually reduce requirement churn."
    },
    "Pilot to Production Grade": {
        "kind": "Transition", "source": "Pilot", "target": "Production Grade", "headline_weight": 0.597, "src_idx": 2, "tgt_idx": 4,
        "description": "Uplift of a running pilot to full production readiness. Charges the Pilot-to-Production rigour delta plus rework uplift and mobilisation floor. Dominated by NFR, security, HA/DR and operational readiness work."
    },
    "MVP to Production Grade": {
        "kind": "Transition", "source": "MVP", "target": "Production Grade", "headline_weight": 0.305, "src_idx": 3, "tgt_idx": 4,
        "description": "Hardening of a live MVP to full production grade. Charges the MVP-to-Production rigour delta plus rework uplift and mobilisation floor. Dominated by scale, resilience, full Responsible AI certification and technical-debt paydown."
    },
    "Incremental Production Grade": {
        "kind": "Delta on live", "source": "Production Grade (live)", "target": "Production Grade", "headline_weight": 0.300, "src_idx": 4, "tgt_idx": 4,
        "description": "A delta release onto an existing, already-live production solution. Effort covers only the incremental change plus mandatory regression, impact assessment, re-certification of affected controls and release management. Platform, CI/CD and observability already exist and are reused."
    }
}

# --- 18 PHASES APPLICABILITY MATRIX (Base Rigour Anchors) ---
PHASE_APPLICABILITY_ANCHORS = {
    "P01": {"name": "Mobilisation & Discovery", "PoC": 1.00, "Pilot": 1.00, "MVP": 1.00, "Production Grade": 1.00},
    "P02": {"name": "Requirements & Use Cases", "PoC": 0.40, "Pilot": 0.65, "MVP": 0.85, "Production Grade": 1.00},
    "P03": {"name": "Data Discovery, Prep & Ingestion", "PoC": 0.30, "Pilot": 0.60, "MVP": 0.80, "Production Grade": 1.00},
    "P04": {"name": "Solution & Technical Architecture", "PoC": 0.35, "Pilot": 0.60, "MVP": 0.80, "Production Grade": 1.00},
    "P05": {"name": "Environment, Landing Zone & Infra", "PoC": 0.25, "Pilot": 0.50, "MVP": 0.75, "Production Grade": 1.00},
    "P06": {"name": "Data Pipeline, Chunking & Indexing", "PoC": 0.40, "Pilot": 0.65, "MVP": 0.85, "Production Grade": 1.00},
    "P07": {"name": "Retrieval / Index / Knowledge Store", "PoC": 0.50, "Pilot": 0.70, "MVP": 0.85, "Production Grade": 1.00},
    "P08": {"name": "Model Selection, Prompting & LLM Config", "PoC": 0.55, "Pilot": 0.75, "MVP": 0.90, "Production Grade": 1.00},
    "P09": {"name": "Fine-tuning / Model Adaptation", "PoC": 0.20, "Pilot": 0.40, "MVP": 0.70, "Production Grade": 1.00},
    "P10": {"name": "Application, API & Integration Dev", "PoC": 0.25, "Pilot": 0.50, "MVP": 0.75, "Production Grade": 1.00},
    "P11": {"name": "Evaluation, Benchmarking & Ground Truth", "PoC": 0.25, "Pilot": 0.50, "MVP": 0.80, "Production Grade": 1.00},
    "P12": {"name": "Responsible AI, Safety & Guardrails", "PoC": 0.10, "Pilot": 0.35, "MVP": 0.70, "Production Grade": 1.00},
    "P13": {"name": "MLOps / LLMOps, IaC & CI/CD", "PoC": 0.05, "Pilot": 0.30, "MVP": 0.70, "Production Grade": 1.00},
    "P14": {"name": "Observability, Cost & FinOps", "PoC": 0.10, "Pilot": 0.35, "MVP": 0.70, "Production Grade": 1.00},
    "P15": {"name": "Testing (Functional, Perf, Security)", "PoC": 0.15, "Pilot": 0.40, "MVP": 0.75, "Production Grade": 1.00},
    "P16": {"name": "Deployment, Cutover & Launch", "PoC": 0.05, "Pilot": 0.30, "MVP": 0.65, "Production Grade": 1.00},
    "P17": {"name": "Documentation, Training & Handover", "PoC": 0.15, "Pilot": 0.40, "MVP": 0.70, "Production Grade": 1.00},
    "P18": {"name": "Project Management & Governance", "PoC": 0.35, "Pilot": 0.55, "MVP": 0.75, "Production Grade": 1.00}
}

# --- SCALE DRIVERS & ELASTICITY ---
SCALE_DRIVERS = {
    "NONE": {"baseline": 1, "elasticity": 0.00, "floor": 0.50},
    "USECASES": {"baseline": 1, "elasticity": 0.70, "floor": 0.50},
    "INTEGRATIONS": {"baseline": 2, "elasticity": 0.65, "floor": 0.50},
    "DATASOURCES": {"baseline": 2, "elasticity": 0.60, "floor": 0.50},
    "PERSONAS": {"baseline": 2, "elasticity": 0.45, "floor": 0.50},
    "CHANNELS": {"baseline": 1, "elasticity": 0.60, "floor": 0.50},
    "ENVS": {"baseline": 3, "elasticity": 0.40, "floor": 0.50},
    "LANGUAGES": {"baseline": 1, "elasticity": 0.50, "floor": 0.50},
    "COMPONENTS": {"baseline": 6, "elasticity": 0.55, "floor": 0.50},
    "DOCS": {"baseline": 50000, "elasticity": 0.30, "floor": 0.50}
}

# --- MULTIPLIERS & COEFFICIENTS ---
COMPLEXITY_MULTIPLIERS = {
    "Low": 0.85,
    "Medium": 1.00,
    "High": 1.25,
    "Very High": 1.50
}

COMPLIANCE_UPLIFTS = {
    "None": 1.00,
    "Internal policy only": 1.05,
    "Regulated - moderate": 1.15,
    "Regulated - high (BFSI/Health/Gov)": 1.30
}

SECURITY_UPLIFTS = {
    "Standard": 1.00,
    "Enhanced": 1.12,
    "Restricted / Air-gapped": 1.30
}

HA_DR_FOOTPRINTS = {
    "None (single instance)": 1.00,
    "Zone redundant": 1.35,
    "Region pair - active/passive": 1.60,
    "Region pair - active/active": 2.00
}

TRANSITION_REWORK_UPLIFT = 1.15
TRANSITION_MOBILISATION_FLOOR = 0.05
INCREMENTAL_SCOPE_SHARE = 0.30

# --- 12 STANDARD DISCIPLINES (ROLES) ---
STANDARD_ROLES = {
    "PM": {
        "title": "Project / Delivery Manager",
        "description": "Plan, scope, RAID, governance, status, stakeholder management, commercial change control",
        "hourly_rate": 30.0
    },
    "BA": {
        "title": "Business Analyst",
        "description": "Requirement elicitation, process mapping, acceptance criteria, UAT coordination, traceability",
        "hourly_rate": 30.0
    },
    "SA": {
        "title": "Solution Architect",
        "description": "End-to-end architecture, technology selection, NFR ownership, design authority, sizing, architecture decision records",
        "hourly_rate": 30.0
    },
    "AIE": {
        "title": "AI / ML Engineer",
        "description": "Prompt engineering, RAG pipeline, orchestration, agents, fine-tuning, model evaluation harness",
        "hourly_rate": 30.0
    },
    "DE": {
        "title": "Data Engineer",
        "description": "Ingestion, transformation, chunking, embedding pipelines, data quality, lineage",
        "hourly_rate": 30.0
    },
    "MLO": {
        "title": "MLOps / LLMOps Engineer",
        "description": "IaC, CI/CD, model and prompt registry, deployment pipelines, environment promotion, drift monitoring",
        "hourly_rate": 30.0
    },
    "SWE": {
        "title": "Software Engineer (Full-stack)",
        "description": "APIs, integration layer, application UI wiring, business logic, SDKs",
        "hourly_rate": 30.0
    },
    "UX": {
        "title": "UX / UI Designer",
        "description": "Journey design, wireframes, conversational UX, accessibility, usability testing",
        "hourly_rate": 30.0
    },
    "QA": {
        "title": "QA / Test Engineer",
        "description": "Test strategy, functional and regression tests, evaluation-set testing, performance testing, defect management",
        "hourly_rate": 30.0
    },
    "SEC": {
        "title": "Security Engineer",
        "description": "Threat modelling, identity, secrets, data protection, penetration test coordination, control evidence",
        "hourly_rate": 30.0
    },
    "SRE": {
        "title": "SRE / Platform Engineer",
        "description": "Landing zone, networking, observability, capacity, reliability, incident readiness, DR drills",
        "hourly_rate": 30.0
    },
    "RAI": {
        "title": "Responsible AI / Compliance Lead",
        "description": "Impact assessment, fairness and safety evaluation, guardrail policy, regulatory mapping, model cards",
        "hourly_rate": 30.0
    }
}

# --- MASTER TASK LIBRARY (18 Phases, Production Base Days) ---
STANDARD_TASK_LIBRARY = [
    # P01: Mobilisation & Discovery
    {"phase_code": "P01", "task_name": "Engagement kick-off, stakeholder map and RACI", "primary_role": "PM", "support_roles": "SA, BA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P01", "task_name": "Discovery workshops: business problem, value hypothesis, success metrics", "primary_role": "BA", "support_roles": "SA, PM", "base_days": 4.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P01", "task_name": "Current-state landscape, systems and constraints assessment", "primary_role": "SA", "support_roles": "BA", "base_days": 3.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P01", "task_name": "Feasibility assessment and go/no-go recommendation", "primary_role": "SA", "support_roles": "AIE", "base_days": 2.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P01", "task_name": "Delivery plan, RAID log and governance cadence set-up", "primary_role": "PM", "support_roles": "SA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P02: Requirements & Use Cases
    {"phase_code": "P02", "task_name": "Functional requirement elicitation and user story writing", "primary_role": "BA", "support_roles": "UX, SA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P02", "task_name": "Non-functional requirement definition (performance, availability, retention, SLA)", "primary_role": "SA", "support_roles": "SRE, BA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P02", "task_name": "Persona definition and user journey mapping", "primary_role": "UX", "support_roles": "BA", "base_days": 3.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P02", "task_name": "Acceptance criteria and requirements traceability matrix", "primary_role": "BA", "support_roles": "QA", "base_days": 3.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P02", "task_name": "Conversational / interaction design and wireframes", "primary_role": "UX", "support_roles": "BA, SWE", "base_days": 5.0, "scale_driver": "CHANNELS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P02", "task_name": "Scope baseline, MoSCoW prioritisation and change-control agreement", "primary_role": "PM", "support_roles": "BA, SA", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P03: Data Discovery, Prep & Ingestion
    {"phase_code": "P03", "task_name": "Data source discovery, profiling and quality assessment", "primary_role": "DE", "support_roles": "BA", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P03", "task_name": "Data access, entitlement and data-sharing agreement facilitation", "primary_role": "DE", "support_roles": "SEC, PM", "base_days": 3.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"phase_code": "P03", "task_name": "Data classification, PII/PHI identification and masking strategy", "primary_role": "SEC", "support_roles": "DE, RAI", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"phase_code": "P03", "task_name": "Data governance, lineage and retention design", "primary_role": "DE", "support_roles": "SEC", "base_days": 3.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "COMP"},
    {"phase_code": "P03", "task_name": "Corpus curation, de-duplication and content-quality remediation", "primary_role": "DE", "support_roles": "AIE", "base_days": 5.0, "scale_driver": "DOCS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P03", "task_name": "Ground-truth / golden dataset construction with SME validation", "primary_role": "AIE", "support_roles": "BA, QA", "base_days": 7.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},

    # P04: Solution & Technical Architecture
    {"phase_code": "P04", "task_name": "Target solution architecture and component decomposition", "primary_role": "SA", "support_roles": "AIE, SRE", "base_days": 5.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P04", "task_name": "Technical component design specification per component", "primary_role": "SA", "support_roles": "AIE, SWE, DE", "base_days": 3.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P04", "task_name": "Integration and interface design (contracts, auth, error handling)", "primary_role": "SA", "support_roles": "SWE", "base_days": 3.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P04", "task_name": "Architecture Decision Records and design authority review", "primary_role": "SA", "support_roles": "PM", "base_days": 2.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P04", "task_name": "Capacity, sizing and platform footprint model", "primary_role": "SA", "support_roles": "SRE", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P04", "task_name": "Security architecture, identity and network design", "primary_role": "SEC", "support_roles": "SA, SRE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "SEC"},
    {"phase_code": "P04", "task_name": "HA/DR, resilience and business continuity design", "primary_role": "SRE", "support_roles": "SA", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P05: Environment, Landing Zone & Infra
    {"phase_code": "P05", "task_name": "Subscription / account, landing zone and network foundation", "primary_role": "SRE", "support_roles": "SEC", "base_days": 5.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "SEC"},
    {"phase_code": "P05", "task_name": "Identity, RBAC, managed identity and secret management set-up", "primary_role": "SEC", "support_roles": "SRE", "base_days": 4.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "SEC"},
    {"phase_code": "P05", "task_name": "AI platform / model endpoint provisioning and quota management", "primary_role": "MLO", "support_roles": "SRE, AIE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P05", "task_name": "Vector store / search index provisioning and configuration", "primary_role": "MLO", "support_roles": "DE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P05", "task_name": "Data platform and storage provisioning", "primary_role": "SRE", "support_roles": "DE", "base_days": 3.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P05", "task_name": "Developer workstation, repository, branch policy and toolchain set-up", "primary_role": "MLO", "support_roles": "SWE", "base_days": 2.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P06: Data Pipeline, Chunking & Indexing
    {"phase_code": "P06", "task_name": "Ingestion connector build per source system", "primary_role": "DE", "support_roles": "SWE", "base_days": 5.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Document parsing, OCR and layout extraction pipeline", "primary_role": "DE", "support_roles": "AIE", "base_days": 6.0, "scale_driver": "DOCS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Chunking strategy design, implementation and tuning", "primary_role": "AIE", "support_roles": "DE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Metadata enrichment and taxonomy tagging", "primary_role": "DE", "support_roles": "BA", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Embedding pipeline build, batch and incremental", "primary_role": "DE", "support_roles": "AIE, MLO", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Data transformation, cleansing and validation rules", "primary_role": "DE", "support_roles": "QA", "base_days": 5.0, "scale_driver": "DATASOURCES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P06", "task_name": "Change data capture / refresh and re-index scheduling", "primary_role": "DE", "support_roles": "MLO", "base_days": 4.0, "scale_driver": "DATASOURCES", "applies_to": "AI", "uplift": "NONE"},

    # P07: Retrieval / Index / Knowledge Store
    {"phase_code": "P07", "task_name": "Index schema, field and filter design", "primary_role": "AIE", "support_roles": "DE", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P07", "task_name": "Retrieval strategy build (hybrid, semantic, keyword, filters)", "primary_role": "AIE", "support_roles": "DE", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P07", "task_name": "Re-ranking and relevance tuning against the golden set", "primary_role": "AIE", "support_roles": "QA", "base_days": 5.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P07", "task_name": "Retrieval quality measurement harness (recall@k, MRR, nDCG)", "primary_role": "AIE", "support_roles": "QA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P08: Model Selection, Prompting & LLM Config
    {"phase_code": "P08", "task_name": "Model selection, benchmarking and trade-off analysis", "primary_role": "AIE", "support_roles": "SA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "System prompt and prompt-template engineering", "primary_role": "AIE", "support_roles": "BA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "Orchestration / agent flow implementation (tools, routing, memory)", "primary_role": "AIE", "support_roles": "SWE", "base_days": 8.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "Structured output, function calling and schema enforcement", "primary_role": "AIE", "support_roles": "SWE", "base_days": 4.0, "scale_driver": "INTEGRATIONS", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "Grounding, citation and source-attribution implementation", "primary_role": "AIE", "support_roles": "SWE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "Prompt versioning, registry and A/B experiment framework", "primary_role": "MLO", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P08", "task_name": "Token, latency and cost optimisation (caching, routing, truncation)", "primary_role": "AIE", "support_roles": "SA", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P09: Fine-tuning / Model Adaptation
    {"phase_code": "P09", "task_name": "Fine-tuning / adaptation feasibility and dataset preparation", "primary_role": "AIE", "support_roles": "DE", "base_days": 6.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P10: Application, API & Integration Dev
    {"phase_code": "P10", "task_name": "Backend service and REST API implementation", "primary_role": "SWE", "support_roles": "SA", "base_days": 8.0, "scale_driver": "COMPONENTS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P10", "task_name": "User interface / presentation layer implementation", "primary_role": "SWE", "support_roles": "UX", "base_days": 8.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P10", "task_name": "External system integration connectors", "primary_role": "SWE", "support_roles": "DE", "base_days": 6.0, "scale_driver": "INTEGRATIONS", "applies_to": "BOTH", "uplift": "NONE"},

    # P11: Evaluation, Benchmarking & Ground Truth
    {"phase_code": "P11", "task_name": "Evaluation dataset curation and golden standard benchmarking", "primary_role": "AIE", "support_roles": "BA, QA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "AI", "uplift": "NONE"},
    {"phase_code": "P11", "task_name": "Automated evaluation pipeline execution and reporting", "primary_role": "QA", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P12: Responsible AI, Safety & Guardrails
    {"phase_code": "P12", "task_name": "Responsible AI impact assessment and safety policy configuration", "primary_role": "RAI", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "COMP"},
    {"phase_code": "P12", "task_name": "Content filtering, jailbreak detection, and toxicity guardrails", "primary_role": "RAI", "support_roles": "AIE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "SEC"},

    # P13: MLOps / LLMOps, IaC & CI/CD
    {"phase_code": "P13", "task_name": "Infrastructure as Code (IaC / Bicep / Terraform) automation", "primary_role": "MLO", "support_roles": "SRE", "base_days": 6.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P13", "task_name": "CI/CD deployment pipeline configuration across environments", "primary_role": "MLO", "support_roles": "SWE", "base_days": 5.0, "scale_driver": "ENVS", "applies_to": "BOTH", "uplift": "NONE"},

    # P14: Observability, Cost & FinOps
    {"phase_code": "P14", "task_name": "Application telemetry, tracing, and log analytics setup", "primary_role": "SRE", "support_roles": "MLO", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P14", "task_name": "Token usage and cloud FinOps cost monitoring dashboard", "primary_role": "SRE", "support_roles": "PM", "base_days": 3.0, "scale_driver": "NONE", "applies_to": "AI", "uplift": "NONE"},

    # P15: Testing (Functional, Perf, Security)
    {"phase_code": "P15", "task_name": "End-to-end functional and regression testing", "primary_role": "QA", "support_roles": "SWE, BA", "base_days": 6.0, "scale_driver": "USECASES", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P15", "task_name": "Security vulnerability scanning and threat assessment", "primary_role": "SEC", "support_roles": "QA", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "SEC"},

    # P16: Deployment, Cutover & Launch
    {"phase_code": "P16", "task_name": "Production environment cutover, smoke tests, and hypercare", "primary_role": "SRE", "support_roles": "PM, SWE", "base_days": 5.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},

    # P17: Documentation, Training & Handover
    {"phase_code": "P17", "task_name": "Operations runbooks, architectural documentation, and user guides", "primary_role": "BA", "support_roles": "SA, SWE", "base_days": 4.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"},
    {"phase_code": "P17", "task_name": "Operational handover and SME training sessions", "primary_role": "PM", "support_roles": "BA, SA", "base_days": 3.0, "scale_driver": "PERSONAS", "applies_to": "BOTH", "uplift": "NONE"},

    # P18: Project Management & Governance
    {"phase_code": "P18", "task_name": "Ongoing project management, sprint ceremonies, status reporting", "primary_role": "PM", "support_roles": "SA", "base_days": 8.0, "scale_driver": "NONE", "applies_to": "BOTH", "uplift": "NONE"}
]

# --- MASTER ASSUMPTIONS ALIGNED TO WORKBOOK ---
DEFAULT_MASTER_ASSUMPTIONS = [
    {
        "id": "A001",
        "type": "Assumption",
        "category": "Functional",
        "statement": "We assume the list of clauses and contract details to be extracted for each of the six categories is agreed in the first workshop and then frozen, because no list exists in the inputs today.",
        "impact_if_wrong": "If the list is not frozen, extraction is built against a moving target, the accuracy metrics have no stable denominator and every clause added after freeze is rework to the schema, prompts and evaluation set.",
        "owner_to_confirm": "Legal and Procurement leadership",
        "confidence": "Medium",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A002",
        "type": "Assumption",
        "category": "Data",
        "statement": "We assume PVR INOX provides around 100 contracts for each of the six categories, and that each set genuinely contains standard, negotiated and known-problem contracts rather than standard templates only.",
        "impact_if_wrong": "If only standard templates are supplied, the principle assessment framework cannot be shown to detect any deviation, and the decision gate has no evidence on the capability the phase exists to prove.",
        "owner_to_confirm": "Legal Operations team",
        "confidence": "Medium",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A003",
        "type": "Assumption",
        "category": "Data",
        "statement": "We assume the representative sample processed in this phase is materially smaller than the 50,000-document live corpus, because that figure describes the eventual live service.",
        "impact_if_wrong": "If the full live corpus must be processed in this phase, the ingestion, indexing and model consumption profile changes entirely and the PoC tier scope no longer holds.",
        "owner_to_confirm": "Project sponsor and IT lead",
        "confidence": "High",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A004",
        "type": "Assumption",
        "category": "Data",
        "statement": "We assume every contract supplied in this phase is a digital, machine-readable file, so no scanned images, photographs of signed paper or handwritten documents appear in the sample. It is noted that in the production phase scanned documents are a possibility.",
        "impact_if_wrong": "If scanned documents appear in this phase, optical recognition and its tuning become necessary work that is not in scope, and layout and coordinate accuracy for traceability degrades.",
        "owner_to_confirm": "Legal Operations team",
        "confidence": "High",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A005",
        "type": "Assumption",
        "category": "Data",
        "statement": "We assume the contract copies PVR INOX places in cloud storage are the final executed versions for this phase, so no separate check against an authoritative source system is needed. It is noted that in the production phase only draft contracts will be received, because the expectation is to identify and act before it is too late.",
        "impact_if_wrong": "If drafts are mixed into this phase's sample, findings will be raised against text that was never executed, and the accuracy comparison against the legal-confirmed benchmark becomes meaningless.",
        "owner_to_confirm": "Legal Operations team",
        "confidence": "High",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A006",
        "type": "Assumption",
        "category": "Functional",
        "statement": "We assume each document is assessed on its own, and that amendments, addenda and side letters are not linked back to their parent contract in this phase.",
        "impact_if_wrong": "If amendment linkage is required, a document relationship model and a merged-contract assessment path must be built, which is new design and new evaluation logic.",
        "owner_to_confirm": "Legal leadership",
        "confidence": "High",
        "status": "Approve",
        "reason": ""
    },
    {
        "id": "A007",
        "type": "Assumption",
        "category": "Functional",
        "statement": "We assume contract files are placed into cloud storage with a folder and naming convention that identifies category and sample type, agreed at kick-off.",
        "impact_if_wrong": "If files arrive without the convention, category ground truth for evaluation is unavailable and a separate manifest or manual labelling exercise is needed before ingestion can run.",
        "owner_to_confirm": "Legal and Procurement operations",
        "confidence": "High",
        "status": "Approve",
        "reason": ""
    }
]

# --- CALENDARS ---
DEFAULT_CALENDARS: Dict[str, LocationCalendar] = {
    "IN": LocationCalendar(
        country_code="IN",
        country_name="India",
        currency_code="INR",
        currency_symbol="₹",
        working_days_per_week=5,
        daily_working_hours=9.0,
        hourly_rate=25.0,
        hourly_rate_local=2100.0,
        annual_holiday_allowance=12,
        holidays=[
            HolidayEntry(date="2026-01-26", name="Republic Day", type="Statutory"),
            HolidayEntry(date="2026-08-15", name="Independence Day", type="Statutory"),
            HolidayEntry(date="2026-10-02", name="Mahatma Gandhi Jayanti", type="Statutory"),
            HolidayEntry(date="2026-03-04", name="Holi", type="Floating"),
            HolidayEntry(date="2026-03-21", name="Eid ul-Fitr", type="Floating"),
            HolidayEntry(date="2026-10-20", name="Dussehra", type="Floating"),
            HolidayEntry(date="2026-11-08", name="Diwali", type="Floating"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
        ]
    ),
    "UK": LocationCalendar(
        country_code="UK",
        country_name="United Kingdom",
        currency_code="GBP",
        currency_symbol="£",
        working_days_per_week=5,
        daily_working_hours=7.0,
        hourly_rate=65.0,
        hourly_rate_local=52.0,
        annual_holiday_allowance=8,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Bank Holiday"),
            HolidayEntry(date="2026-04-03", name="Good Friday", type="Bank Holiday"),
            HolidayEntry(date="2026-04-06", name="Easter Monday", type="Bank Holiday"),
            HolidayEntry(date="2026-05-04", name="Early May Bank Holiday", type="Bank Holiday"),
            HolidayEntry(date="2026-05-25", name="Spring Bank Holiday", type="Bank Holiday"),
            HolidayEntry(date="2026-08-31", name="Summer Bank Holiday", type="Bank Holiday"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Bank Holiday"),
            HolidayEntry(date="2026-12-28", name="Boxing Day (Observed)", type="Bank Holiday"),
        ]
    ),
    "US": LocationCalendar(
        country_code="US",
        country_name="United States",
        currency_code="USD",
        currency_symbol="$",
        working_days_per_week=5,
        daily_working_hours=8.0,
        hourly_rate=85.0,
        hourly_rate_local=85.0,
        annual_holiday_allowance=11,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-01-19", name="Martin Luther King Jr. Day", type="Floating"),
            HolidayEntry(date="2026-05-25", name="Memorial Day", type="Floating"),
            HolidayEntry(date="2026-06-19", name="Juneteenth", type="Statutory"),
            HolidayEntry(date="2026-07-04", name="Independence Day", type="Statutory"),
            HolidayEntry(date="2026-09-07", name="Labor Day", type="Floating"),
            HolidayEntry(date="2026-11-26", name="Thanksgiving Day", type="Floating"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
        ]
    ),
    "EU": LocationCalendar(
        country_code="EU",
        country_name="European Union",
        currency_code="EUR",
        currency_symbol="€",
        working_days_per_week=5,
        daily_working_hours=7.5,
        hourly_rate=60.0,
        hourly_rate_local=55.0,
        annual_holiday_allowance=10,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-05-01", name="Labour Day", type="Statutory"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
        ]
    ),
    "SG": LocationCalendar(
        country_code="SG",
        country_name="Singapore",
        currency_code="SGD",
        currency_symbol="S$",
        working_days_per_week=5,
        daily_working_hours=8.5,
        hourly_rate=50.0,
        hourly_rate_local=68.0,
        annual_holiday_allowance=11,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-02-17", name="Chinese New Year", type="Floating"),
            HolidayEntry(date="2026-05-01", name="Labour Day", type="Statutory"),
            HolidayEntry(date="2026-08-09", name="National Day", type="Statutory"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
        ]
    ),
    "AE": LocationCalendar(
        country_code="AE",
        country_name="United Arab Emirates",
        currency_code="AED",
        currency_symbol="AED ",
        working_days_per_week=5,
        daily_working_hours=8.0,
        hourly_rate=45.0,
        hourly_rate_local=165.0,
        annual_holiday_allowance=14,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-03-21", name="Eid Al Fitr", type="Floating"),
            HolidayEntry(date="2026-05-27", name="Arafat Day", type="Floating"),
            HolidayEntry(date="2026-05-28", name="Eid Al Adha", type="Floating"),
            HolidayEntry(date="2026-12-01", name="Commemoration Day", type="Statutory"),
            HolidayEntry(date="2026-12-02", name="National Day", type="Statutory"),
        ]
    ),
    "AU": LocationCalendar(
        country_code="AU",
        country_name="Australia",
        currency_code="AUD",
        currency_symbol="A$",
        working_days_per_week=5,
        daily_working_hours=7.5,
        hourly_rate=55.0,
        hourly_rate_local=82.0,
        annual_holiday_allowance=11,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-01-26", name="Australia Day", type="Statutory"),
            HolidayEntry(date="2026-04-25", name="Anzac Day", type="Statutory"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
            HolidayEntry(date="2026-12-26", name="Boxing Day", type="Statutory"),
        ]
    ),
    "CA": LocationCalendar(
        country_code="CA",
        country_name="Canada",
        currency_code="CAD",
        currency_symbol="C$",
        working_days_per_week=5,
        daily_working_hours=8.0,
        hourly_rate=65.0,
        hourly_rate_local=88.0,
        annual_holiday_allowance=10,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-07-01", name="Canada Day", type="Statutory"),
            HolidayEntry(date="2026-12-25", name="Christmas Day", type="Statutory"),
        ]
    ),
    "JP": LocationCalendar(
        country_code="JP",
        country_name="Japan",
        currency_code="JPY",
        currency_symbol="¥",
        working_days_per_week=5,
        daily_working_hours=8.0,
        hourly_rate=70.0,
        hourly_rate_local=10500.0,
        annual_holiday_allowance=16,
        holidays=[
            HolidayEntry(date="2026-01-01", name="New Year's Day", type="Statutory"),
            HolidayEntry(date="2026-02-11", name="National Foundation Day", type="Statutory"),
            HolidayEntry(date="2026-04-29", name="Showa Day", type="Statutory"),
            HolidayEntry(date="2026-05-03", name="Constitution Day", type="Statutory"),
            HolidayEntry(date="2026-05-04", name="Greenery Day", type="Statutory"),
        ]
    )
}

def get_working_hours_for_geography(geo_name_or_code: str) -> float:
    cal = get_calendar_for_geography(geo_name_or_code)
    return float(cal.get("daily_working_hours", 8.0))

def get_hourly_rate_for_geography(geo_name_or_code: str) -> float:
    cal = get_calendar_for_geography(geo_name_or_code)
    return float(cal.get("hourly_rate", 30.0))

# --- SYSTEM DEFAULTS ---
DEFAULT_SYSTEM_DEFAULTS = {
    "blended_hourly_rate": 30.0,
    "currency": "USD",
    "currency_symbol": "$",
    "hours_per_day": 8.0,
    "working_days_per_week": 5,
    "default_delivery_tier": "PoC",
    "default_reference_duration": "6.0",
    "default_cloud_platform": "Microsoft Azure",
    "default_primary_location": "India",
    "max_fte_per_role_peak": 20.0,
    "max_ramp_per_week": 80.0,
    "phase_overlap_fraction": 0.50,
    "min_fte_granularity": 0.25,
    "productive_utilisation_pct": 100.0,
    "leave_and_buffer_pct": 0.0,
    "contingency_pct": 10.0,
    "pm_governance_overhead_pct": 12.0
}

def get_admin_defaults() -> Dict[str, Any]:
    if os.path.exists(DEFAULTS_FILE):
        try:
            with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(DEFAULT_SYSTEM_DEFAULTS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_SYSTEM_DEFAULTS)

def save_admin_defaults(defaults: Dict[str, Any]) -> Dict[str, Any]:
    curr = get_admin_defaults()
    curr.update(defaults)
    with open(DEFAULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(curr, f, indent=2)
    return curr

def get_calendars() -> Dict[str, Any]:
    defaults_dict = {k: v.model_dump() for k, v in DEFAULT_CALENDARS.items()}
    if os.path.exists(CALENDARS_FILE):
        try:
            with open(CALENDARS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for code, cal in defaults_dict.items():
                    if code in saved:
                        merged_cal = dict(cal)
                        merged_cal.update(saved[code])
                        if "hourly_rate" not in saved[code] or saved[code]["hourly_rate"] is None:
                            merged_cal["hourly_rate"] = cal.get("hourly_rate", 30.0)
                        if "hourly_rate_local" not in saved[code] or saved[code]["hourly_rate_local"] is None:
                            merged_cal["hourly_rate_local"] = cal.get("hourly_rate_local", 30.0)
                        if "currency_code" not in saved[code] or saved[code]["currency_code"] is None:
                            merged_cal["currency_code"] = cal.get("currency_code", "USD")
                        if "currency_symbol" not in saved[code] or saved[code]["currency_symbol"] is None:
                            merged_cal["currency_symbol"] = cal.get("currency_symbol", "$")
                        defaults_dict[code] = merged_cal
                    else:
                        defaults_dict[code] = cal
                for code, cal in saved.items():
                    if code not in defaults_dict:
                        defaults_dict[code] = cal
                return defaults_dict
        except Exception:
            pass
    return defaults_dict

def save_calendars(calendars: Dict[str, Any]):
    with open(CALENDARS_FILE, "w", encoding="utf-8") as f:
        json.dump(calendars, f, indent=2)

def get_calendar_for_geography(geo_name_or_code: str) -> Dict[str, Any]:
    cals = get_calendars()
    lookup = geo_name_or_code.strip().lower()
    for code, cal in cals.items():
        if code.lower() == lookup:
            return cal
    for code, cal in cals.items():
        cname = cal.get("country_name", "").lower()
        if lookup in cname or cname in lookup:
            return cal
    return cals.get("IN", {
        "country_code": "IN",
        "country_name": "India",
        "currency_code": "INR",
        "currency_symbol": "₹",
        "working_days_per_week": 5,
        "daily_working_hours": 9.0,
        "hourly_rate": 25.0,
        "hourly_rate_local": 2100.0,
        "annual_holiday_allowance": 12,
        "holidays": []
    })

def upsert_calendar(country_code: str, country_name: str, working_days: int = 5, daily_working_hours: float = 8.0, hourly_rate: float = 30.0, hourly_rate_local: Optional[float] = None, currency_code: str = "USD", currency_symbol: str = "$", annual_allowance: int = 12) -> Dict[str, Any]:
    cals = get_calendars()
    code = country_code.strip().upper()
    existing = cals.get(code, {})
    holidays = existing.get("holidays", [])
    
    local_rate = hourly_rate_local if hourly_rate_local is not None else float(hourly_rate)
    
    cal = {
        "country_code": code,
        "country_name": country_name.strip() or existing.get("country_name", code),
        "currency_code": currency_code or existing.get("currency_code", "USD"),
        "currency_symbol": currency_symbol or existing.get("currency_symbol", "$"),
        "working_days_per_week": int(working_days),
        "daily_working_hours": float(daily_working_hours),
        "hourly_rate": float(hourly_rate),
        "hourly_rate_local": float(local_rate),
        "annual_holiday_allowance": int(annual_allowance),
        "holidays": holidays
    }
    cals[code] = cal
    save_calendars(cals)
    return cal

def add_holiday_to_calendar(country_code: str, date: str, name: str, holiday_type: str = "Statutory") -> Dict[str, Any]:
    cals = get_calendars()
    code = country_code.strip().upper()
    if code not in cals:
        cals[code] = {
            "country_code": code,
            "country_name": code,
            "working_days_per_week": 5,
            "annual_holiday_allowance": 12,
            "holidays": []
        }
    holidays = cals[code].get("holidays", [])
    holidays = [h for h in holidays if h.get("date") != date]
    holidays.append({
        "date": date.strip(),
        "name": name.strip(),
        "type": holiday_type.strip() or "Statutory"
    })
    holidays.sort(key=lambda x: x.get("date", ""))
    cals[code]["holidays"] = holidays
    save_calendars(cals)
    return cals[code]

def delete_holiday_from_calendar(country_code: str, holiday_index: int) -> Dict[str, Any]:
    cals = get_calendars()
    code = country_code.strip().upper()
    if code in cals and "holidays" in cals[code]:
        holidays = cals[code]["holidays"]
        if 0 <= holiday_index < len(holidays):
            holidays.pop(holiday_index)
            cals[code]["holidays"] = holidays
            save_calendars(cals)
    return cals.get(code, {})

def update_holiday_in_calendar(country_code: str, holiday_index: int, date: str, name: str, holiday_type: str = "Statutory") -> Dict[str, Any]:
    cals = get_calendars()
    code = country_code.strip().upper()
    if code in cals and "holidays" in cals[code]:
        holidays = cals[code]["holidays"]
        if 0 <= holiday_index < len(holidays):
            holidays[holiday_index] = {
                "date": date.strip(),
                "name": name.strip(),
                "type": holiday_type.strip() or "Statutory"
            }
            holidays.sort(key=lambda x: x.get("date", ""))
            cals[code]["holidays"] = holidays
            save_calendars(cals)
    return cals.get(code, {})

def delete_calendar(country_code: str) -> bool:
    cals = get_calendars()
    code = country_code.strip().upper()
    if code in cals:
        del cals[code]
        save_calendars(cals)
        return True
    return False

def get_master_assumptions() -> List[Dict[str, Any]]:
    if os.path.exists(ASSUMPTIONS_FILE):
        try:
            with open(ASSUMPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_MASTER_ASSUMPTIONS

def save_master_assumptions(assumptions: List[Dict[str, Any]]):
    with open(ASSUMPTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(assumptions, f, indent=2)

def parse_holiday_sheet(file_path: str, country_code: str, country_name: str) -> Dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    holidays: List[Dict[str, str]] = []
    
    if ext == ".csv":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    d_str, name = row[0].strip(), row[1].strip()
                    htype = row[2].strip() if len(row) > 2 else "Statutory"
                    if d_str.lower() not in ["date", "day", "holiday"]:
                        holidays.append({"date": d_str, "name": name, "type": htype})
    elif ext in [".txt", ".json"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "date" in item and "name" in item:
                            holidays.append({
                                "date": item["date"],
                                "name": item["name"],
                                "type": item.get("type", "Statutory")
                            })
            except Exception:
                f.seek(0)
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        holidays.append({"date": parts[0].strip(), "name": parts[1].strip(), "type": "Statutory"})
                    
    code = country_code.strip().upper()
    cals = get_calendars()
    cal = {
        "country_code": code,
        "country_name": country_name.strip() or code,
        "working_days_per_week": 5,
        "annual_holiday_allowance": len(holidays) or 12,
        "holidays": holidays
    }
    cals[code] = cal
    save_calendars(cals)
    return cal
