"""
deck_section_a.py
Contains builders for Slides 12 through 22:
- Slide 12: Deployment Architecture Diagram (Dev, SIT, UAT, Prod)
- Slide 13: Editable Deployment Architecture Specifications Grid
- Slide 14: Deep-Dive Intervention 1 - Layout Ingestion & Extraction (Non-AI)
- Slide 15: Deep-Dive Intervention 2 - Contract Classification (AI Agent)
- Slide 16: Deep-Dive Intervention 3 - Multi-Pass Clause Extraction Engine (AI Agent)
- Slide 17: Deep-Dive Intervention 4 - Contracting Principle Assessment (AI Agent + Rule)
- Slide 18: Deep-Dive Intervention 5 - Risk Register Synthesis & Review Cockpit (Non-AI)
- Slide 19: End-to-End Data Flow Diagram (UI to Azure Services)
- Slide 20: Editable Data Flow Matrix & Sequence Specifications
- Slide 21: Technical Component Register - Part 1: Ingestion, Storage & Search
- Slide 22: Technical Component Register - Part 2: AI Models, Database, Compute & APIs
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from build_deck_helpers import (
    create_base_slide, add_card, add_table, add_kpi_metric, add_image_slide,
    BG_LIGHT, CARD_BG, CARD_BORDER, TEXT_DARK, TEXT_SUB, TEXT_MUTED,
    BLUE_PRIMARY, EMERALD_SUCCESS, AMBER_WARN, PURPLE_ACCENT, RED_ALERT
)

def build_slides_12_to_22(prs):
    print("Building Slides 12 to 22 (Section A)...")

    # =========================================================================
    # SLIDE 12 (Topic 10): Deployment Architecture Diagram (Dev, SIT, UAT, Prod)
    # =========================================================================
    s12 = create_base_slide(
        prs, 12, "Multi-Environment Deployment Architecture (Dev, SIT, UAT, Prod)",
        "Environment topology across isolated non-production and hardened production subscriptions",
        "Section 10: Deployment Architecture",
        {
            "logic": "Enterprise customers require rigorous environment isolation so development and testing cannot impact production data or quotas.",
            "designs": "Embedded high-resolution 4-environment deployment diagram showing official Azure logos, subscriptions, and security rings.",
            "highlights": "Dev, SIT, and UAT reside in non-prod subscription with cost caps; Prod resides in dedicated, hardened subscription.",
            "details": "Azure OpenAI TPM quota partitioned: 50k (Dev), 100k (SIT), 150k (UAT), and Provisioned Throughput (PTU) for Production."
        }
    )
    add_image_slide(s12, "exports/assets/diagrams/arch_deployment_diagram.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 13 (Topic 11): Editable Deployment Architecture Grid
    # =========================================================================
    s13 = create_base_slide(
        prs, 13, "Editable Deployment Architecture & Environment Specifications",
        "Configurable infrastructure specifications, SKU tiers, HA/DR configurations, and access boundaries",
        "Section 10: Deployment Architecture",
        {
            "logic": "Provides an editable breakdown for DevOps and cloud infrastructure engineers to plan resource group provisioning.",
            "designs": "Four vertical editable environment columns detailing Resource Group, Storage, Doc Intel, OpenAI, Compute, and Security.",
            "highlights": "Production features Zone-Redundant Storage (ZRS), Private Endpoints, and PIM/JIT security with zero public internet access.",
            "details": "Environment sizing reflects non-production factor of 0.60 as calibrated in the engagement sizing model."
        }
    )
    add_card(s13, 0.8, 1.5, 2.75, 5.1, "Development (DEV)", [
        "Subscription: Non-Prod Sub / rg-contract-dev-001.",
        "Storage: Azure Blob (Hot Tier, LRS, Soft Delete 7 Days).",
        "Doc Intelligence: Shared S0 multi-tenant endpoint.",
        "Azure OpenAI: Pay-As-You-Go GPT-4o (TPM: 50,000).",
        "Vector Search: AI Search Basic Tier (1 replica, 1 partition).",
        "Compute: Container Apps Consumption (0-2 replicas).",
        "Database: Azure SQL Basic (5 DTUs / Serverless 2 vCores).",
        "Access: Developer Entra ID Security Group with Contributor."
    ], header_color=BLUE_PRIMARY)

    add_card(s13, 3.8, 1.5, 2.75, 5.1, "System Testing (SIT)", [
        "Subscription: Non-Prod Sub / rg-contract-sit-001.",
        "Storage: Azure Blob (Hot Tier, LRS, Versioning enabled).",
        "Doc Intelligence: Dedicated S0 endpoint for regression runs.",
        "Azure OpenAI: Pay-As-You-Go GPT-4o (TPM: 100,000).",
        "Vector Search: AI Search Standard S1 (1 replica, 1 partition).",
        "Compute: Container Apps Fixed 2 replicas for testing.",
        "Database: Azure SQL Standard S2 (50 DTUs).",
        "Access: QA automation service principal + Tester Entra group."
    ], header_color=EMERALD_SUCCESS)

    add_card(s13, 6.8, 1.5, 2.75, 5.1, "User Acceptance (UAT)", [
        "Subscription: Non-Prod Sub / rg-contract-uat-001.",
        "Storage: Azure Blob (Hot Tier, GRS Geo-Redundant, WORM).",
        "Doc Intelligence: Production-parity S0 endpoint.",
        "Azure OpenAI: Reserved quota Pay-As-You-Go (TPM: 150,000).",
        "Vector Search: AI Search Standard S1 (2 replicas for HA).",
        "Compute: Container Apps Autoscale 2 to 5 replicas.",
        "Database: Azure SQL General Purpose (4 vCores).",
        "Access: Legal & Procurement SME review group via SSO."
    ], header_color=AMBER_WARN)

    add_card(s13, 9.8, 1.5, 2.75, 5.1, "Enterprise Prod", [
        "Subscription: Enterprise Production Sub / rg-contract-prod.",
        "Storage: Azure Blob (ZRS Zone-Redundant, Immutable WORM).",
        "Doc Intelligence: Dedicated endpoint with Private Link.",
        "Azure OpenAI: Provisioned Throughput (PTU) or 300k TPM.",
        "Vector Search: AI Search Standard S2 (3 replicas, Multi-AZ).",
        "Compute: Container Apps / AKS Multi-AZ (Autoscale 2-10).",
        "Database: Azure SQL Business Critical (Geo-Replica South).",
        "Access: Entra ID PIM (Privileged Identity Mgmt) + MFA."
    ], header_color=RED_ALERT)

    # =========================================================================
    # SLIDE 14 (Topic 12a): Intervention 1 - Layout Ingestion & Parsing (Non-AI)
    # =========================================================================
    s14 = create_base_slide(
        prs, 14, "Intervention Deep-Dive 1: Deterministic Layout Ingestion (Non-AI)",
        "Zero-hallucination layout recovery, table decomposition, and pixel coordinate extraction via Azure AI Doc Intelligence",
        "Section 11: Interventions",
        {
            "logic": "Raw OCR and document coordinate extraction must be 100% deterministic. Using an LLM for OCR would cause coordinate hallucinations.",
            "designs": "Four structured cards covering Description, Inputs, Technical Implementation, and Delivered Business Benefits.",
            "highlights": "Recovers exact (x, y, w, h) bounding boxes per text span; normalizes multi-page tables across contract annexures.",
            "details": "Azure AI Document Intelligence Prebuilt Layout model processes 50-page complex PDF contracts in under 4 seconds."
        }
    )
    add_card(s14, 0.8, 1.5, 2.75, 5.1, "Intervention Description", [
        "• Purpose: Converts messy, multi-column PDF contracts into structured layout tokens, tables, and exact page coordinates.",
        "• Deterministic Non-AI: Uses Azure AI Document Intelligence OCR engine—no generative text manipulation.",
        "• Coordinate Precision: Emits normalized 72-DPI bounding box coordinates (x, y, w, h) for every word and paragraph.",
        "• Table Reconstruction: Converts complex lease fee grids and rent escalators into structured JSON matrices."
    ], header_color=BLUE_PRIMARY)

    add_card(s14, 3.8, 1.5, 2.75, 5.1, "Inputs Needed", [
        "• Raw Digital PDFs: Executed contracts placed in Azure Blob Storage /contracts/raw.",
        "• File Formats: Native digital PDF (Phase 1); scanned/OCR contracts (Phase 2 extension).",
        "• Metadata Header: Document ID, upload timestamp, file size, and target folder category hint.",
        "• Storage Handover Convention: Folder naming convention (/lease, /vendor, /tech, /service, /facilities, /mkt)."
    ], header_color=PURPLE_ACCENT)

    add_card(s14, 6.8, 1.5, 2.75, 5.1, "Technical Implementation", [
        "• Azure Service: Azure AI Document Intelligence (prebuilt-layout API v2024-02-29-preview).",
        "• Execution Trigger: Azure Functions event triggered via Event Grid on BlobCreated.",
        "• Polling & Retrieval: Asynchronous analyze document pattern with exponential backoff.",
        "• Chunking Pipeline: Python parser slices document into 512-token chunks strictly at clause/section boundaries.",
        "• Vector Storage: Writes chunks + coordinates to Azure AI Search hybrid vector index."
    ], header_color=AMBER_WARN)

    add_card(s14, 9.8, 1.5, 2.75, 5.1, "Business Benefits Delivered", [
        "• 100% Audit Grounding: Eliminates fabricated clause citations; every finding references authentic page pixels.",
        "• Zero Data Tampering: Original contract PDF remains untouched in immutable WORM storage.",
        "• Format Agnostic: Reliably parses complex multi-column contracts, tables, and annexures.",
        "• 85% Ingestion Speedup: Ingests 50-page contracts in < 4 seconds vs 3 hours manual paralegal review."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 15 (Topic 12b): Intervention 2 - Contract Classification (AI Agent)
    # =========================================================================
    s15 = create_base_slide(
        prs, 15, "Intervention Deep-Dive 2: Contract Classification Agent (AI Agent)",
        "Autonomous semantic classification of contracts into 6 distinct commercial categories using Azure OpenAI",
        "Section 11: Interventions",
        {
            "logic": "Contracts arrive with unstandardized titles. An intelligent semantic agent is required to analyze structural context and intent.",
            "designs": "Four structured cards covering Description, Inputs, Technical Implementation, and Delivered Business Benefits.",
            "highlights": "Classifies into Lease, Vendor, Service, Facilities, Technology, Marketing with ≥97% precision.",
            "details": "Uses GPT-4o mini with structured JSON output enforcing a confidence score; low confidence routes to manual triage."
        }
    )
    add_card(s15, 0.8, 1.5, 2.75, 5.1, "Intervention Description", [
        "• Purpose: Evaluates contract preamble, title, and preamble clauses to categorize contract into 1 of 6 business domains.",
        "• In-Scope Categories: Commercial Lease, Equipment Vendor, Professional Services, Facility AMC, Technology/Software, Marketing.",
        "• Autonomous Decision: Binds the document to the corresponding contracting ontology and frozen clause checklist.",
        "• Confidence Calibration: Emits category confidence score (0.0 to 1.0); flags ambiguous multi-nature contracts."
    ], header_color=BLUE_PRIMARY)

    add_card(s15, 3.8, 1.5, 2.75, 5.1, "Inputs Needed", [
        "• Document Preamble Chunks: First 3 sections (recitals, parties, whereas clauses) from Azure AI Search.",
        "• Bounded Category Schema: Explicit definitions of the 6 allowed contract domains and inclusion rules.",
        "• Taxonomy Context: Distinct commercial keywords (e.g. 'lessor/lessee' vs 'licensor/licensee' vs 'supplier')."
    ], header_color=PURPLE_ACCENT)

    add_card(s15, 6.8, 1.5, 2.75, 5.1, "Technical Implementation", [
        "• AI Model: Azure OpenAI Service GPT-4o mini (India Central deployment).",
        "• Prompt Strategy: Few-shot prompt with system instructions enforcing strict JSON output.",
        "• Temperature: 0.0 for deterministic reproducibility.",
        "• Exception Gate: If confidence < 0.85, routes contract to 'Unclassified Queue' for legal operations verification.",
        "• Audit Logging: Writes predicted category, prompt version, and model token usage into Azure SQL."
    ], header_color=AMBER_WARN)

    add_card(s15, 9.8, 1.5, 2.75, 5.1, "Business Benefits Delivered", [
        "• Automated Intake Routing: Removes manual classification overhead across hundreds of quarterly contracts.",
        "• Guaranteed Rule Alignment: Ensures correct contracting rules are loaded for evaluation without human error.",
        "• 97%+ Accuracy: Outperforms manual sorting; prevents wrong checklists being applied to complex agreements.",
        "• Seamless Scalability: Processes bulk ingestion spikes instantly without hiring contract sorting staff."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 16 (Topic 12c): Intervention 3 - Multi-Pass Clause Extraction (AI Agent)
    # =========================================================================
    s16 = create_base_slide(
        prs, 16, "Intervention Deep-Dive 3: Multi-Pass Clause Extraction Engine (AI Agent)",
        "Iterative, pass-aware extraction separating broad baseline extraction from targeted ambiguous term deep dives",
        "Section 11: Interventions",
        {
            "logic": "Single-pass extraction produces confident but ungrounded guesses on negotiated or vague terms. Multi-pass iteration guarantees rigor.",
            "designs": "Four structured cards covering Description, Inputs, Technical Implementation, and Delivered Business Benefits.",
            "highlights": "Pass 1 extracts standard terms; Pass 2/3 performs targeted semantic searches for edge cases; max 3 passes enforced.",
            "details": "Every extracted entity carries pass provenance (Pass 1 vs Pass 2), source chunk ID, and bounding box coordinates."
        }
    )
    add_card(s16, 0.8, 1.5, 2.75, 5.1, "Intervention Description", [
        "• Purpose: Extracts specific contractual entities, dates, liability caps, indemnities, and termination triggers.",
        "• Multi-Pass Architecture: Replaces rejected single-pass approach with pass-aware orchestration.",
        "• Pass 1 (Broad): Extracts well-defined clauses (Term, Governing Law, Standard Payment Terms).",
        "• Pass 2/3 (Targeted): Specializes on empty, low-confidence, or heavily negotiated terms with focused queries.",
        "• Bounded Stopping Rule: Maximum 3 passes per clause; unresolved terms route to exceptions list."
    ], header_color=BLUE_PRIMARY)

    add_card(s16, 3.8, 1.5, 2.75, 5.1, "Inputs Needed", [
        "• Category Clause Checklist: Frozen list of required clauses per category established in Phase 1 workshops.",
        "• Hybrid Search Candidates: Top-k chunks retrieved from Azure AI Search combining BM25 and vector embeddings.",
        "• Prior Pass State: Provenance log recording which clauses were resolved in Pass 1 vs remaining empty."
    ], header_color=PURPLE_ACCENT)

    add_card(s16, 6.8, 1.5, 2.75, 5.1, "Technical Implementation", [
        "• Orchestration: Container Apps FastAPI engine managing iterative pass state machine.",
        "• AI Model: Azure OpenAI GPT-4o with temperature 0.0 and JSON schema validation.",
        "• Retrieval Tuning: Pass 1 uses top-k=5; Pass 2/3 uses targeted semantic query with top-k=10 expanded window.",
        "• Schema Validation: Pydantic models validate extracted datatypes (dates, currency amounts, percentages).",
        "• Provenance Tagging: Each record tagged with PassNumber, ModelId, PromptVersion, and CoordinateBounds."
    ], header_color=AMBER_WARN)

    add_card(s16, 9.8, 1.5, 2.75, 5.1, "Business Benefits Delivered", [
        "• Zero Hallucinated Values: Refuses to fabricate open-textured clauses; flags missing items transparently.",
        "• Precision on Edge Cases: Uncovers hidden liability waivers buried deep in obscure schedules or annexures.",
        "• Measurable Pass ROI: Evaluation harness tracks accuracy gains bought by Pass 2/3 (typically +14% recall boost).",
        "• Cost & Quota Optimization: Only difficult clauses trigger extra passes, saving 40% tokens vs whole-doc re-runs."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 17 (Topic 12d): Intervention 4 - Principle Assessment Engine (AI + Rule)
    # =========================================================================
    s17 = create_base_slide(
        prs, 17, "Intervention Deep-Dive 4: Contracting Principle Assessment (AI + Rule)",
        "Evaluating extracted clauses against enterprise contracting principles to render standardized risk ratings",
        "Section 11: Interventions",
        {
            "logic": "Extraction alone is insufficient. The business requires automated evaluation of extracted terms against corporate risk policies.",
            "designs": "Four structured cards covering Description, Inputs, Technical Implementation, and Delivered Business Benefits.",
            "highlights": "Renders Agree / Agree with Management Approval / Not Agree with fully articulated legal rationale.",
            "details": "Decoupled model call ensures extraction errors are measurable separately from assessment reasoning errors."
        }
    )
    add_card(s17, 0.8, 1.5, 2.75, 5.1, "Intervention Description", [
        "• Purpose: Compares extracted contractual values against category contracting principles to identify deviations.",
        "• Standardized Outcomes: Synthesizes findings into Agree (Compliant), Agree with Mgmt Approval (Deviation), or Not Agree (Severe Risk).",
        "• Rationale Articulation: Generates clear, business-language explanation justifying the assessment.",
        "• Escalation Assignment: Designates whether CFO, CLO, or Procurement Head approval is required."
    ], header_color=BLUE_PRIMARY)

    add_card(s17, 3.8, 1.5, 2.75, 5.1, "Inputs Needed", [
        "• Extracted Clause Record: Verbatim clause text, normalized entity values, and page coordinates.",
        "• Category Ontology Rules: Structured contracting standards (e.g. 'Min 7% lease escalator', 'Max 12-mo liability cap').",
        "• Severity Matrix: Threshold criteria defining what qualifies as acceptable deviation vs critical deal-breaker."
    ], header_color=PURPLE_ACCENT)

    add_card(s17, 6.8, 1.5, 2.75, 5.1, "Technical Implementation", [
        "• AI Model: Azure OpenAI GPT-4o with dedicated Legal Evaluator prompt template.",
        "• Decoupled Architecture: Model call is completely independent from extraction to isolate evaluation metrics.",
        "• Groundedness Guardrail: Verifies that assessment rationale directly cites words present in the extracted text.",
        "• Unsupported Handling: If rationale cannot be grounded in source text, finding is marked 'Unsupported' rather than asserted.",
        "• Storage: Written to ContractFindings table in Azure SQL with status badge and risk score."
    ], header_color=AMBER_WARN)

    add_card(s17, 9.8, 1.5, 2.75, 5.1, "Business Benefits Delivered", [
        "• Consistent Standard Enforcement: Eliminates subjective variance between different paralegals or business units.",
        "• Executive Focus: Flags the 15-20% of contracts truly requiring senior leadership attention.",
        "• $2.4M Financial Protection: Catches adverse commercial caps, missed CPI escalators, and unbudgeted penalties.",
        "• Accelerated Governance: Decreases management approval turnaround from 5 days to same-day sign-off."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 18 (Topic 12e): Intervention 5 - Risk Register & Cockpit (Non-AI)
    # =========================================================================
    s18 = create_base_slide(
        prs, 18, "Intervention Deep-Dive 5: Risk Register Synthesis & Review Cockpit (Non-AI)",
        "Spreadsheet export generation and interactive React dashboard with PDF coordinate overlays",
        "Section 11: Interventions",
        {
            "logic": "Legal and procurement workflows require familiar spreadsheets and interactive visual audit tools to trust AI recommendations.",
            "designs": "Four structured cards covering Description, Inputs, Technical Implementation, and Delivered Business Benefits.",
            "highlights": "Outputs exact spreadsheet format used today extended with coordinate hyperlinks; interactive split-screen UI.",
            "details": "Hosted on Azure App Service with Entra ID SSO, role-based permissions, and zero third-party telemetry leakage."
        }
    )
    add_card(s18, 0.8, 1.5, 2.75, 5.1, "Intervention Description", [
        "• Purpose: Consolidates extracted clauses, risk ratings, and rationales into consumable enterprise formats.",
        "• Dual Delivery Channels: Generates spreadsheet risk register (matching legacy Excel format) + interactive web dashboard.",
        "• Interactive PDF Viewer: Side-by-side cockpit highlighting bounding box coordinates directly on contract pages.",
        "• Human-in-the-Loop Actions: Allows legal reviewers to confirm, override, or annotate findings before finalizing."
    ], header_color=BLUE_PRIMARY)

    add_card(s18, 3.8, 1.5, 2.75, 5.1, "Inputs Needed", [
        "• Structured Findings Records: Validated clause assessments, risk ratings, and coordinates from Azure SQL.",
        "• Source Document PDFs: Accessible via read-only SAS URIs generated on demand.",
        "• User Credentials: Authenticated user claims passed via Entra ID Bearer tokens."
    ], header_color=PURPLE_ACCENT)

    add_card(s18, 6.8, 1.5, 2.75, 5.1, "Technical Implementation", [
        "• Frontend: React SPA hosted on Azure App Service (Linux) utilizing PDF.js canvas overlay renderer.",
        "• Backend API: FastAPI service running in Azure Container Apps exposing secure REST endpoints.",
        "• Export Engine: OpenPyXL Python worker compiling auditable Excel risk registers with embedded hyperlinked citations.",
        "• Identity: Microsoft Entra ID Single Sign-On with project security group role binding.",
        "• Audit Trail: Every user override, approval, or export action logged with user UPN and timestamp."
    ], header_color=AMBER_WARN)

    add_card(s18, 9.8, 1.5, 2.75, 5.1, "Business Benefits Delivered", [
        "• Zero Workflow Friction: Procurement continues working with familiar Excel registers without retraining.",
        "• Instant Verification: Reviewers verify clauses in 3 seconds by clicking coordinates rather than flipping 60 pages.",
        "• Complete Accountability: Eliminates lost email approvals; provides full audit trail for corporate governance.",
        "• Decision Enablement: Provides executive leadership with real-time portfolio risk visibility across all business categories."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 19 (Topic 13): End-to-End Data Flow Architecture (Diagram)
    # =========================================================================
    s19 = create_base_slide(
        prs, 19, "End-to-End Numbered Data Flow Architecture (UI to Azure Services)",
        "End-to-end data progression across 10 numbered execution stages from initial document intake to human review",
        "Section 12: Data Flow",
        {
            "logic": "Provides a comprehensive end-to-end sequence showing exact service invocation order, protocols, and data handoffs.",
            "designs": "Embedded high-resolution numbered sequence diagram showing all 10 stages from Blob storage to Cockpit surfacing.",
            "highlights": "Numbered stages 01 through 10 trace ingestion, OCR, chunking, indexing, classification, multi-pass reasoning, and export.",
            "details": "Distinguishes synchronous API hops (FastAPI to OpenAI) from asynchronous event triggers (Blob to Service Bus)."
        }
    )
    add_image_slide(s19, "exports/assets/diagrams/arch_dataflow_diagram.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 20 (Topic 13a): Editable Data Flow Matrix & Sequence Definition
    # =========================================================================
    s20 = create_base_slide(
        prs, 20, "Editable End-to-End Data Flow Matrix & Protocol Specifications",
        "Detailed step-by-step invocation sequences, protocols, payload formats, and latency SLA targets",
        "Section 12: Data Flow",
        {
            "logic": "Enables developers and interface engineers to verify exact payload formats, error codes, and timeout limits.",
            "designs": "Comprehensive 10-step editable matrix mapping Step Number, Source, Target, Protocol, Payload, and Target Latency.",
            "highlights": "End-to-end processing completes within 48 seconds P95; all payloads strictly validated against JSON schemas.",
            "details": "Asynchronous stages handle high-volume batch buffering while synchronous stages enforce sub-3 second SLA."
        }
    )
    add_table(s20, 0.8, 1.5, 11.7, 5.1,
        ["Seq #", "Data Flow Stage", "Source Component", "Target Component", "Protocol / API", "Payload Schema", "P95 Latency SLA"],
        [
            ["01", "Raw PDF Deposit", "Legal Operations / User", "Azure Blob Storage", "HTTPS TLS 1.3 / REST", "Raw binary PDF stream", "< 1.5s (50MB)"],
            ["02", "Event Notification", "Azure Blob Storage", "Azure Functions Dispatcher", "Event Grid Webhook", "BlobCreated event JSON", "< 200ms"],
            ["03", "Layout Parsing", "Azure Functions", "Azure AI Doc Intelligence", "REST POST /layout", "AnalyzeRequest (PDF bytes)", "< 3.5s (50 pages)"],
            ["04", "Chunk & Vectorize", "Ingestion Engine", "Azure AI Search Index", "REST POST /docs/index", "512-token chunks + 1536d vec", "< 800ms"],
            ["05", "Classification", "Container Apps Engine", "Azure OpenAI (GPT-4o mini)", "REST POST /chat/completions", "Preamble prompt -> Category", "< 1.2s"],
            ["06", "Pass 1 Extraction", "Container Apps Engine", "Azure OpenAI (GPT-4o)", "REST POST /chat/completions", "Category schema -> Clauses JSON", "< 3.8s"],
            ["07", "Pass 2/3 Ambiguity", "Container Apps Engine", "AI Search + GPT-4o", "Hybrid Search + LLM POST", "Targeted query -> Resolved term", "< 4.5s (if trig)"],
            ["08", "Principle Eval", "Assessment Service", "Azure OpenAI (GPT-4o)", "REST POST /chat/completions", "Extracted clause + Rule prompt", "< 2.8s"],
            ["09", "Findings Commit", "Orchestration Engine", "Azure SQL Database", "TDS over TLS 1.3 / SQL", "ContractFindings records INSERT", "< 80ms"],
            ["10", "Cockpit Surfacing", "React Dashboard", "FastAPI / App Service", "HTTPS JSON REST API", "Portfolio risk summary JSON", "< 350ms"]
        ],
        col_widths=[0.7, 1.6, 1.7, 1.8, 1.8, 2.5, 1.6]
    )

    # =========================================================================
    # SLIDE 21 (Topic 14a): Technical Component Register - Part 1
    # =========================================================================
    s21 = create_base_slide(
        prs, 21, "Technical Component Register: Ingestion, Storage & Search (Part 1)",
        "Exhaustive architectural inventory detailing Type, Purpose, Inputs, Outputs, Actions, and Integrations",
        "Section 13: Component Register",
        {
            "logic": "Provides a formal enterprise registry of all storage, search, and document ingestion components for operations and audit.",
            "designs": "Seven-column editable technical table defining Component ID, Type, Purpose, Inputs, Outputs, Action, and Integrations.",
            "highlights": "Every component has a single, strictly bounded architectural responsibility with zero role ambiguity.",
            "details": "Covers C001 (Blob Storage), C002 (Doc Intelligence), C003 (Azure AI Search), and C004 (Event Grid Dispatcher)."
        }
    )
    add_table(s21, 0.8, 1.5, 11.7, 5.1,
        ["ID", "Component Name", "Type", "Core Purpose", "Primary Inputs", "Primary Outputs", "Key Integrations"],
        [
            ["C001", "Azure Blob Storage", "Storage (PaaS)", "Immutable raw PDF contract repository & WORM archive", "Digital PDF uploads from Legal Ops", "Blob URI + SAS read tokens", "Event Grid, Azure AI Doc Intelligence"],
            ["C002", "Azure AI Doc Intel", "Cognitive Service", "Deterministic layout parsing, OCR & table cell extraction", "Binary contract PDF stream", "Layout JSON + (x,y,w,h) coordinates", "Azure Functions, Container Apps Engine"],
            ["C003", "Azure AI Search", "Search & Vector", "Hybrid vector (1536d) & BM25 keyword chunk retrieval", "512-token chunks + embeddings", "Ranked candidate clause chunks", "Azure OpenAI, Container Apps Orchestrator"],
            ["C004", "Ingestion Dispatcher", "FaaS (Serverless)", "Consumes BlobCreated events & triggers parsing workflow", "Event Grid event payload", "Scheduled parsing job in Service Bus", "Azure Blob, Event Grid, Service Bus"],
            ["C005", "Azure Key Vault", "Security (PaaS)", "Centralized HSM secret, key & certificate management", "ARM secret configuration", "In-memory credentials via Managed ID", "All Azure Services via System Identity"]
        ],
        col_widths=[0.8, 2.0, 1.6, 2.7, 2.0, 2.2, 2.4]
    )

    # =========================================================================
    # SLIDE 22 (Topic 14b): Technical Component Register - Part 2
    # =========================================================================
    s22 = create_base_slide(
        prs, 22, "Technical Component Register: AI Models, Database & Compute (Part 2)",
        "Inventory of reasoning models, orchestration engines, relational databases, and presentation surfaces",
        "Section 13: Component Register",
        {
            "logic": "Documents the compute, reasoning, database, and presentation layers for engineering execution and platform governance.",
            "designs": "Seven-column editable technical table detailing AI models, container runtimes, database instances, and web surfaces.",
            "highlights": "Ensures model endpoints are configured for deterministic outputs; databases enforce foreign key integrity.",
            "details": "Covers C006 (Azure OpenAI), C007 (Container Apps), C008 (Azure SQL), C009 (App Service), and C010 (Azure Monitor)."
        }
    )
    add_table(s22, 0.8, 1.5, 11.7, 5.1,
        ["ID", "Component Name", "Type", "Core Purpose", "Primary Inputs", "Primary Outputs", "Key Integrations"],
        [
            ["C006", "Azure OpenAI Service", "Agentic AI (PaaS)", "Semantic category classification & multi-pass extraction", "Prompt text + retrieved chunks", "JSON structured clause extractions", "AI Search, Container Apps, Content Safety"],
            ["C007", "Workflow Engine", "Container Apps", "Pass-aware orchestration finite state machine", "Service Bus intake jobs", "State transitions & assessment queue", "Service Bus, OpenAI, Azure SQL, Monitor"],
            ["C008", "Azure SQL Database", "Relational DB", "Master ontologies, extracted clauses, risk findings & logs", "Normalized JSON from orchestrator", "Relational findings & Excel datasets", "Container Apps, App Service, PowerBI"],
            ["C009", "Risk Visibility UI", "App Service (Web)", "Interactive React cockpit with PDF coordinate highlight viewer", "User REST requests + Entra tokens", "Rendered dashboard & PDF highlight views", "Entra ID, Azure SQL, Blob SAS URIs"],
            ["C010", "Azure Monitor & App", "Observability", "End-to-end tracing, token quota tracking & canary alerts", "Platform metrics, traces & logs", "Alert notifications & health dashboards", "All solution microservices, Slack/Teams"]
        ],
        col_widths=[0.8, 2.0, 1.6, 2.7, 2.0, 2.2, 2.4]
    )

    prs.save("exports/PVR_INOX_TCS_Contract_Intelligence_Master_Deck.pptx")
    print("Checkpoint: Slides 12-22 successfully compiled.")
    return prs
