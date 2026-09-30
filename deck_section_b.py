"""
deck_section_b.py
Contains builders for Slides 23 through 33:
- Slide 23: UI Mockup 1 - Master Risk Cockpit & Ingestion Portfolio (HD Image)
- Slide 24: UI Mockup 2 - Side-by-Side Clause Coordinate Inspector (HD Image)
- Slide 25: UI Mockup 3 - Exceptions Queue & Production System Health Monitor (HD Image)
- Slide 26: Process Step Deep-Dive - Steps 1 to 3 (Intake, Layout OCR, Indexing)
- Slide 27: Process Step Deep-Dive - Steps 4 to 6 (Classification, Extraction, Assessment)
- Slide 28: Process Step Deep-Dive - Steps 7 to 9 (Register Synthesis, Review, Export)
- Slide 29: Phased Estimates & Role vs Week Resource Loading Matrix (4-Tier Evolution)
- Slide 30: Contextual Solution Architecture Diagram (Official Logos)
- Slide 31: Contextual Solution Architecture (Editable Structural Grid)
- Slide 32: Developer Implementation Blueprint - Ingestion, Doc Intel & AI Search
- Slide 33: Developer Implementation Blueprint - Multi-Pass OpenAI Extraction Engine
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from build_deck_helpers import (
    create_base_slide, add_card, add_table, add_kpi_metric, add_image_slide,
    BG_LIGHT, CARD_BG, CARD_BORDER, TEXT_DARK, TEXT_SUB, TEXT_MUTED,
    BLUE_PRIMARY, EMERALD_SUCCESS, AMBER_WARN, PURPLE_ACCENT, RED_ALERT
)

def build_slides_23_to_33(prs):
    print("Building Slides 23 to 33 (Section B)...")

    # =========================================================================
    # SLIDE 23 (Topic 15a): UI Mockup 1 - Master Risk Cockpit (HD Image)
    # =========================================================================
    s23 = create_base_slide(
        prs, 23, "UI Envisioning: Executive Risk Visibility & Portfolio Cockpit (Topic 15)",
        "High-fidelity interface showcasing portfolio metrics, category distribution, and contract risk grid",
        "Section 14: User Experience",
        {
            "logic": "Executive and legal users require a centralized dashboard to track contract portfolio health and risk distribution.",
            "designs": "Embedded HD user interface mockup with 6 KPI indicator cards, category filters, and interactive data table.",
            "highlights": "Every navigation menu item is explicitly tagged with delivery tier badges [PoC], [Pilot], [MVP], and [Prod].",
            "details": "Surfaces total processed contracts (600), classification accuracy (97.2%), and Agree/Management Approval distributions."
        }
    )
    add_image_slide(s23, "exports/assets/ui/ui_dashboard_cockpit.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 24 (Topic 15b): UI Mockup 2 - Split-Screen Clause Inspector (HD Image)
    # =========================================================================
    s24 = create_base_slide(
        prs, 24, "UI Envisioning: Side-by-Side Clause Inspector & HITL Review (Topic 15)",
        "Split-screen interface displaying original contract PDF coordinates alongside AI-extracted principles",
        "Section 14: User Experience",
        {
            "logic": "Legal counsel will not accept automated findings without verifying the verbatim clause on the source document page.",
            "designs": "Split-screen mockup featuring PDF viewer with coordinate bounding-box highlight (left) and assessment inspector (right).",
            "highlights": "Displays exact bounding box [x:48, y:312, w:867, h:56], pass provenance (Pass 2), and groundedness score (98.4%).",
            "details": "Includes Human-in-the-Loop action buttons: Confirm Finding, Override Assessment, Reject Term, and Re-run Pass 3."
        }
    )
    add_image_slide(s24, "exports/assets/ui/ui_clause_inspector.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 25 (Topic 15c): UI Mockup 3 - Exceptions & Health Cockpit (HD Image)
    # =========================================================================
    s25 = create_base_slide(
        prs, 25, "UI Envisioning: Exceptions Management & System Telemetry (Topic 15)",
        "Operational cockpit managing unresolvable edge cases, paralegal triage, and real-time cloud health",
        "Section 14: User Experience",
        {
            "logic": "Production systems require transparent handling of failed extractions and continuous service health monitoring.",
            "designs": "Two-column operational cockpit: Left column displays Exceptions Queue; Right column displays Real-Time Azure Telemetry.",
            "highlights": "Exceptions triage cards detail reason, document ID, and resolution action; telemetry monitors latency, token TPM, and canaries.",
            "details": "Enforces operational runbooks for automated exponential backoff, circuit breaking, and canary alert thresholds."
        }
    )
    add_image_slide(s25, "exports/assets/ui/ui_exceptions_health.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 26 (Topic 16a): Process Step Deep-Dive - Steps 1 to 3
    # =========================================================================
    s26 = create_base_slide(
        prs, 26, "Process Step Deep-Dive: Intake, OCR & Indexing (Steps 1 to 3)",
        "Technical execution, service invocations, inputs, outputs, and governance guardrails for intake stages",
        "Section 15: Process Specifications",
        {
            "logic": "Provides developers and pipeline engineers with granular implementation specifications for initial ingestion stages.",
            "designs": "Three horizontal process step cards detailing Purpose, Technical Flow, Inputs, Outputs, and Governance Rules.",
            "highlights": "Non-AI deterministic OCR guarantees 100% layout fidelity; chunking strictly adheres to legal clause boundaries.",
            "details": "Covers Step 1 (Blob Intake), Step 2 (Doc Intelligence Layout Analysis), and Step 3 (Chunking & Hybrid AI Search Indexing)."
        }
    )
    add_card(s26, 0.8, 1.5, 3.7, 5.1, "Step 1: Raw Contract Intake", [
        "• Purpose: Authoritative executed contract deposit into cloud landing zone.",
        "• Services: Azure Blob Storage + Event Grid.",
        "• Technical Flow: Legal Ops deposits PDF -> BlobCreated event generated -> Ingestion Function triggered.",
        "• Inputs: Executed digital PDF contracts.",
        "• Outputs: Immutable Blob URI with cryptographic SHA-256 hash.",
        "• Governance / Best Practices: Enforce WORM storage policies; encrypt with SSE-KMS; restrict write access via Entra RBAC."
    ], header_color=BLUE_PRIMARY)

    add_card(s26, 4.8, 1.5, 3.7, 5.1, "Step 2: Layout Decomposition & OCR", [
        "• Purpose: Deterministic text, table, and coordinate extraction.",
        "• Services: Azure AI Document Intelligence (Prebuilt Layout API).",
        "• Technical Flow: Function submits PDF stream -> Doc Intelligence parses layout -> Returns JSON with (x,y,w,h) coordinates.",
        "• Inputs: Raw PDF document binary.",
        "• Outputs: Full-text layout JSON, table matrices, normalized bounding boxes.",
        "• Governance / Best Practices: Recheck OCR confidence threshold (≥ 70%); reject illegible scans to exceptions queue immediately."
    ], header_color=PURPLE_ACCENT)

    add_card(s26, 8.8, 1.5, 3.7, 5.1, "Step 3: Chunking & Hybrid Indexing", [
        "• Purpose: Semantic chunking and vector index population.",
        "• Services: Azure Container Apps + Azure AI Search.",
        "• Technical Flow: Slices text at clause boundaries (512 tokens) -> Generates 1536d embeddings via text-embedding-3-large -> Indexes chunks.",
        "• Inputs: Layout JSON with paragraph boundaries.",
        "• Outputs: Searchable hybrid index with BM25 + Vector vectors.",
        "• Governance / Best Practices: Never split a legal clause across chunk boundaries; preserve chunk-to-page coordinate mapping."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 27 (Topic 16b): Process Step Deep-Dive - Steps 4 to 6
    # =========================================================================
    s27 = create_base_slide(
        prs, 27, "Process Step Deep-Dive: Reasoning & Assessment (Steps 4 to 6)",
        "Technical execution, service invocations, inputs, outputs, and governance guardrails for AI reasoning stages",
        "Section 15: Process Specifications",
        {
            "logic": "Documents the agentic core of the platform where prompt-based classification, multi-pass extraction, and assessment occur.",
            "designs": "Three horizontal process step cards detailing Purpose, Technical Flow, Inputs, Outputs, and Governance Rules.",
            "highlights": "Multi-pass iteration bounds difficult clauses to max 3 passes; assessment model call is strictly decoupled from extraction.",
            "details": "Covers Step 4 (Category Classification), Step 5 (Multi-Pass Clause Extraction), and Step 6 (Principle Assessment Reasoning)."
        }
    )
    add_card(s27, 0.8, 1.5, 3.7, 5.1, "Step 4: Category Classification", [
        "• Purpose: Assigns contract to 1 of 6 business categories.",
        "• Services: Azure OpenAI Service (GPT-4o mini).",
        "• Technical Flow: Loads preamble chunks -> Evaluates structure and parties -> Emits category tag and confidence score.",
        "• Inputs: First 3 document chunks (preamble, recitals).",
        "• Outputs: Category code (e.g. LEASE, VENDOR) + Confidence score.",
        "• Governance / Best Practices: Temperature 0.0; confidence < 0.85 halts pipeline and routes to manual paralegal confirmation."
    ], header_color=BLUE_PRIMARY)

    add_card(s27, 4.8, 1.5, 3.7, 5.1, "Step 5: Multi-Pass Clause Extract", [
        "• Purpose: Extracts standardized entities and ambiguous edge terms.",
        "• Services: Azure OpenAI GPT-4o + Azure AI Search.",
        "• Technical Flow: Pass 1 retrieves broad category checklist -> Empty/vague terms queued -> Pass 2/3 runs targeted semantic query.",
        "• Inputs: Category clause schema + Top-k hybrid chunks.",
        "• Outputs: Structured clause JSON with pass provenance tag.",
        "• Governance / Best Practices: Enforce max 3 passes; never invent default values; flag unresolved items explicitly."
    ], header_color=PURPLE_ACCENT)

    add_card(s27, 8.8, 1.5, 3.7, 5.1, "Step 6: Principle Assessment", [
        "• Purpose: Evaluates extracted clauses against risk ontologies.",
        "• Services: Azure OpenAI GPT-4o (Legal Evaluator).",
        "• Technical Flow: Compares clause value to contracting rule -> Emits Agree / Agree w/ Mgmt Approval / Not Agree with rationale.",
        "• Inputs: Extracted clause record + Master category rule.",
        "• Outputs: Status rating, business rationale, risk severity.",
        "• Governance / Best Practices: Groundedness check mandatory; rationale must cite extracted words; flag unsupported findings."
    ], header_color=AMBER_WARN)

    # =========================================================================
    # SLIDE 28 (Topic 16c): Process Step Deep-Dive - Steps 7 to 9
    # =========================================================================
    s28 = create_base_slide(
        prs, 28, "Process Step Deep-Dive: Review, Export & Audit (Steps 7 to 9)",
        "Technical execution, service invocations, inputs, outputs, and governance guardrails for governance stages",
        "Section 15: Process Specifications",
        {
            "logic": "Completes the process lifecycle by detailing how findings are committed, surfaced to human reviewers, and exported.",
            "designs": "Three horizontal process step cards detailing Purpose, Technical Flow, Inputs, Outputs, and Governance Rules.",
            "highlights": "Guarantees 100% traceability; human reviewer sign-off is mandatory before findings are published as approved.",
            "details": "Covers Step 7 (Risk Register Commit), Step 8 (Human-in-the-Loop Cockpit Review), and Step 9 (Audit Export & Archival)."
        }
    )
    add_card(s28, 0.8, 1.5, 3.7, 5.1, "Step 7: Risk Register Commit", [
        "• Purpose: Persists validated findings and provenance metadata.",
        "• Services: Azure SQL Database (Relational Store).",
        "• Technical Flow: Orchestrator commits transaction -> Inserts clause rows, coordinate bounds, pass history, and assessment status.",
        "• Inputs: Validated findings payload from Assessment Engine.",
        "• Outputs: Relational ContractFindings record with primary key.",
        "• Governance / Best Practices: Foreign key integrity to master contract; maintain immutable audit log table for all writes."
    ], header_color=BLUE_PRIMARY)

    add_card(s28, 4.8, 1.5, 3.7, 5.1, "Step 8: Human Review Cockpit", [
        "• Purpose: Legal counsel validation and deviation approval.",
        "• Services: Azure App Service (React) + Entra ID SSO.",
        "• Technical Flow: Counsel opens dashboard -> Reviews PDF highlights -> Approves standard terms or overrides deviation rating.",
        "• Inputs: Authenticated user session + Contract ID.",
        "• Outputs: Human review sign-off record + Override rationale.",
        "• Governance / Best Practices: Mandatory user justification required for any model override; log reviewer UPN and timestamp."
    ], header_color=EMERALD_SUCCESS)

    add_card(s28, 8.8, 1.5, 3.7, 5.1, "Step 9: Excel Export & Archival", [
        "• Purpose: Enterprise spreadsheet compilation and governance.",
        "• Services: Container Apps Python Worker + OpenPyXL.",
        "• Technical Flow: User clicks Export -> Worker queries Azure SQL -> Generates formatted Excel workbook with coordinate URLs.",
        "• Inputs: Filtered contract portfolio query.",
        "• Outputs: Audit-ready XLSX register + Word BRD summary.",
        "• Governance / Best Practices: Maintain strict column mapping with legacy Excel registers; enforce 12-month data retention rule."
    ], header_color=PURPLE_ACCENT)

    # =========================================================================
    # SLIDE 29 (Topic 17): Phased Estimates & Role Loading (4-Tier Evolution)
    # =========================================================================
    s29 = create_base_slide(
        prs, 29, "Phased Estimates & Role Loading Matrix Across 4 Delivery Tiers (Topic 17)",
        "Deterministic effort estimates, role-wise loading, duration, and labor costs calculated at $30/hr blended baseline",
        "Section 16: Effort & Schedule",
        {
            "logic": "Provides executive leadership with a defensible, formula-driven estimate across PoC, Pilot, MVP, and Full Production.",
            "designs": "Comprehensive editable table comparing Phases, Durations, Role Person-Days, Total Days, and Financial Labor Cost ($30/hr).",
            "highlights": "PoC baseline requires 30 working days (6 weeks) and $38,880 labor cost; Full Production requires $134,640 total.",
            "details": "Labor rate strictly calibrated to blended hourly cost of $30.00 (8 hours/day = $240/person-day) across all engineering roles."
        }
    )
    add_table(s29, 0.8, 1.5, 11.7, 5.1,
        ["Delivery Tier / Scope", "Duration", "AI Engineer", "ML Engineer", "Fullstack Dev", "UI Developer", "Data Engineer", "Cloud Eng", "RAI Specialist", "Total Days", "Total Cost ($30/hr)"],
        [
            ["Phase 1: Proof of Concept (PoC)", "6 Wks (30d)", "32 d", "14 d", "28 d", "22 d", "26 d", "24 d", "16 d", "162 d", "$38,880"],
            ["Phase 2: Pilot Trial (Cohort)", "8 Wks (40d)", "42 d", "18 d", "36 d", "28 d", "32 d", "30 d", "22 d", "208 d", "$49,920"],
            ["Phase 3: Min Viable Product (MVP)", "12 Wks (60d)", "68 d", "28 d", "58 d", "46 d", "52 d", "48 d", "34 d", "334 d", "$80,160"],
            ["Phase 4: Full Production Grade", "16 Wks (80d)", "112 d", "46 d", "96 d", "78 d", "86 d", "82 d", "61 d", "561 d", "$134,640"],
            ["PoC Uplift to Pilot (Delta)", "+4 Wks (20d)", "16 d", "6 d", "14 d", "10 d", "12 d", "10 d", "8 d", "76 d", "$18,240"],
            ["Pilot Uplift to Prod (Delta)", "+8 Wks (40d)", "70 d", "28 d", "60 d", "50 d", "54 d", "52 d", "39 d", "353 d", "$84,720"]
        ],
        col_widths=[2.3, 1.1, 0.9, 0.9, 1.0, 0.9, 1.0, 0.9, 1.0, 0.9, 1.4]
    )

    # =========================================================================
    # SLIDE 30 (Topic 18): Contextual Solution Architecture (Official Logos Diagram)
    # =========================================================================
    s30 = create_base_slide(
        prs, 30, "Contextual Solution Architecture & Enterprise Boundary (Topic 18)",
        "Contextual architecture depicting enterprise actors, source repositories, Azure solution core, and deliverables",
        "Section 17: Contextual Architecture",
        {
            "logic": "Establishes system context and external integration boundaries across Legal Ops, Procurement, CFO, and Phase 2 CLM/ERP systems.",
            "designs": "Embedded high-resolution contextual architecture diagram with official Azure icons and clear enterprise boundaries.",
            "highlights": "Clean separation between external ingestion sources, secure Azure platform boundary, and outbound audit deliverables.",
            "details": "Hosted in Azure India Central; complies with strict enterprise information barriers and data classification guidelines."
        }
    )
    add_image_slide(s30, "exports/assets/diagrams/arch_contextual_diagram.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 31 (Topic 19): Contextual Solution Architecture (Editable Structural Grid)
    # =========================================================================
    s31 = create_base_slide(
        prs, 31, "Contextual Solution Architecture (Editable Structural Grid)",
        "Configurable enterprise boundary layout detailing external actors, internal subsystems, and outbound artifacts",
        "Section 17: Contextual Architecture",
        {
            "logic": "Provides enterprise architects with an editable view to adjust external integrations as Phase 2 ERP/CLM systems are scoped.",
            "designs": "Three horizontal editable enterprise context cards: External Actors, Azure Platform Core, and Outbound Deliverables.",
            "highlights": "Shows zero-integration PoC intake evolving into automated system-to-system API connectors in Phase 2.",
            "details": "Includes Legal Operations, Procurement Leads, Executive Sponsors, SAP/Oracle ERP, and Microsoft Entra ID."
        }
    )
    add_card(s31, 0.8, 1.5, 3.7, 5.1, "1. External Actors & Systems", [
        "• Corporate Legal Operations: Uploads executed contracts and validates extracted findings in the review cockpit.",
        "• Procurement & Category Leads: Enforces category-specific commercial rules, pricing caps, and escalator limits.",
        "• Executive Leadership (CFO / CLO): Reviews consolidated risk exposure dashboards and approves escalated deviations.",
        "• IT Security & Governance: Manages Entra ID role assignments, key rotation, and compliance auditing.",
        "• Phase 2 Upstream Systems: SAP S/4HANA, Oracle ERP, Icertis CLM, SharePoint, and corporate email intake."
    ], header_color=BLUE_PRIMARY)

    add_card(s31, 4.8, 1.5, 3.7, 5.1, "2. Azure Platform Core Boundary", [
        "• Storage & Ingestion: Azure Blob Storage + Azure AI Doc Intelligence for layout-aware PDF decomposition.",
        "• Orchestration State Machine: Container Apps hosting FastAPI pass-aware workflow engine and queue listeners.",
        "• Agentic Reasoning Framework: Azure AI Search hybrid RAG + Azure OpenAI GPT-4o multi-pass reasoning engine.",
        "• Relational Data Store: Azure SQL Database holding frozen ontologies, clause records, and audit logs.",
        "• Identity & Secrets: Entra ID Single Sign-On + Azure Key Vault with platform managed identities."
    ], header_color=PURPLE_ACCENT)

    add_card(s31, 8.8, 1.5, 3.7, 5.1, "3. Outbound Governance Deliverables", [
        "• Consolidated Risk Register: Excel/CSV export matching legacy procurement columns with coordinate hyperlinks.",
        "• Interactive Risk Cockpit: Web interface displaying side-by-side PDF coordinate highlight overlays.",
        "• Executive Deviation Briefs: PPTX presentation decks summarizing portfolio risk distribution and outliers.",
        "• Exceptions & Triage Log: Actionable report of low-confidence documents or ambiguous terms for paralegals.",
        "• Benchmark Evaluation Report: Accuracy metrics scored against legal-confirmed ground truth datasets."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 32 (Topic 20a): Developer Implementation Blueprint - Ingestion & Search
    # =========================================================================
    s32 = create_base_slide(
        prs, 32, "Developer Blueprint: Ingestion, Doc Intelligence & AI Search (Topic 20)",
        "Granular technical instructions, API calls, SDK methods, and configuration parameters for pipeline developers",
        "Section 18: Developer Specifications",
        {
            "logic": "Gives developers concrete code patterns, SDK calls, and configuration parameters to build the ingestion pipeline.",
            "designs": "Three structured developer blueprint cards covering Blob Intake, Doc Intelligence Layout API, and Azure AI Search.",
            "highlights": "Includes concrete SDK methods (begin_analyze_document), chunking parameters (512 tokens), and index schemas.",
            "details": "Enforces asynchronous polling with exponential backoff and normalized 72-DPI coordinate mapping."
        }
    )
    add_card(s32, 0.8, 1.5, 3.7, 5.1, "1. Azure Blob Storage Handler", [
        "• SDK: azure-storage-blob Python v12.19.0.",
        "• Client: BlobServiceClient with DefaultAzureCredential (no keys).",
        "• Container: contracts-raw with hierarchical namespace enabled.",
        "• Event Trigger: Azure Event Grid fires BlobCreated webhook to Azure Functions.",
        "• Metadata Header: Attaches upload_time, doc_id, category_hint, sha256_hash.",
        "• Code Pattern: blob_client.download_blob().readinto(stream)."
    ], header_color=BLUE_PRIMARY)

    add_card(s32, 4.8, 1.5, 3.7, 5.1, "2. Doc Intelligence Layout Client", [
        "• SDK: azure-ai-documentintelligence Python v1.0.0b1.",
        "• Model: prebuilt-layout with output_content_format='markdown'.",
        "• Polling Pattern: poller = client.begin_analyze_document('prebuilt-layout', body=stream).",
        "• Coordinate Recovery: Extract polygon points [p1, p2, p3, p4] per paragraph and cell; normalize to 72 DPI (x, y, w, h).",
        "• Error Handling: Retry on HTTP 429 with jitter (2s, 4s, 8s); flag OCR confidence < 0.70 to exceptions table."
    ], header_color=PURPLE_ACCENT)

    add_card(s32, 8.8, 1.5, 3.7, 5.1, "3. Azure AI Search Vector Store", [
        "• SDK: azure-search-documents Python v11.4.0.",
        "• Index: contract-chunks-idx with HNSW vector config (M=4, efConstruction=400).",
        "• Fields: chunk_id (Key), doc_id, category, page_num, text_content, vector (1536d), bbox_json.",
        "• Chunking Rule: Section-aware chunking (max 512 tokens, 64 token overlap); never split a legal clause sentence.",
        "• Query Strategy: VectorizedQuery(k=5) + search_text (BM25) with semantic reranker enabled."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 33 (Topic 20b): Developer Blueprint - Multi-Pass OpenAI Engine
    # =========================================================================
    s33 = create_base_slide(
        prs, 33, "Developer Blueprint: Multi-Pass OpenAI Extraction Engine (Topic 20)",
        "Granular technical instructions, prompt templates, structured output schemas, and pass stopping logic",
        "Section 18: Developer Specifications",
        {
            "logic": "Provides developers with prompt templates, JSON schema models, and pass-aware control flow to build the extraction engine.",
            "designs": "Three structured developer blueprint cards covering Classification, Multi-Pass Extraction, and Assessment.",
            "highlights": "Enforces JSON schema validation via Pydantic; guarantees zero hallucinated values through groundedness checks.",
            "details": "Includes stopping condition: max 3 passes per clause item before routing unresolved terms to exceptions table."
        }
    )
    add_card(s33, 0.8, 1.5, 3.7, 5.1, "1. Classification Agent Prompts", [
        "• Model: gpt-4o-mini (deployment: gpt-4o-mini-india).",
        "• API Call: client.beta.chat.completions.parse().",
        "• Response Model: Pydantic ContractClassification(category: Enum, confidence: float, rationale: str).",
        "• System Prompt: 'You are an enterprise contract classifier. Analyze preamble text and classify into 1 of 6 frozen categories.'",
        "• Temperature: 0.0 (Strict determinism); Top-p: 1.0; Max tokens: 500."
    ], header_color=BLUE_PRIMARY)

    add_card(s33, 4.8, 1.5, 3.7, 5.1, "2. Multi-Pass Extraction Loop", [
        "• Pass 1 Call: Broad extraction of standardized clauses against category checklist using retrieved chunks (k=5).",
        "• Validation Filter: If clause value is empty or confidence < 0.80, append to unresolved_queue.",
        "• Pass 2/3 Iteration: For item in unresolved_queue: execute focused semantic query (k=10) with targeted single-clause prompt.",
        "• Stopping Rule: if pass_count >= 3: mark clause as 'Unresolved - Escalated' and route to Exceptions Queue.",
        "• Provenance Logging: Record chunk_id, page_num, bbox, pass_number for every valid extraction."
    ], header_color=PURPLE_ACCENT)

    add_card(s33, 8.8, 1.5, 3.7, 5.1, "3. Principle Assessment Engine", [
        "• Model: gpt-4o (deployment: gpt-4o-india).",
        "• System Prompt: 'Compare extracted clause value against corporate contracting rule PR-XXX. Synthesize status: Agree, Agree with Mgmt Approval, or Not Agree.'",
        "• Groundedness Check: Execute cosine similarity between rationale and extracted clause text; flag if similarity < 0.85.",
        "• Unsupported Handling: If clause is missing, emit status='Not Agree (Missing Mandatory Term)' with zero invented text.",
        "• Output: Writes ContractFindings record to Azure SQL via SQLAlchemy."
    ], header_color=AMBER_WARN)

    prs.save("exports/PVR_INOX_TCS_Contract_Intelligence_Master_Deck.pptx")
    print("Checkpoint: Slides 23-33 successfully compiled.")
    return prs
