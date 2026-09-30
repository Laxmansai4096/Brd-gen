"""
build_master_deck_complete.py
Master compilation script assembling the complete 56-slide Microsoft PowerPoint master presentation
covering all 42 topics with enterprise clean light theme, official Tata & TCS branding,
Azure official icons, exact $30/hr blended labor rates, and comprehensive Presenter Notes.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from build_deck_helpers import (
    create_base_slide, add_card, add_table, add_kpi_metric, add_boundary_box, add_image_slide,
    SLIDE_WIDTH, SLIDE_HEIGHT, BG_LIGHT, CARD_BG, CARD_BORDER,
    TEXT_DARK, TEXT_SUB, TEXT_MUTED, TEXT_DIM,
    BLUE_PRIMARY, BLUE_DARK, EMERALD_SUCCESS, AMBER_WARN, PURPLE_ACCENT, RED_ALERT, TEAL_ACCENT,
    TOTAL_SLIDES, CLIENT_NAME, PROJECT_TITLE, FOOTER_CENTER
)

from deck_section_a import build_slides_12_to_22
from deck_section_b import build_slides_23_to_33
from deck_section_c import build_slides_34_to_45
from deck_section_d import build_slides_46_to_56

def build_complete_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    print(f"================================================================================")
    print(f"STARTING COMPILATION OF {TOTAL_SLIDES}-SLIDE ENTERPRISE MASTER PRESENTATION")
    print(f"Client: {CLIENT_NAME}  |  Theme: Enterprise Clean Light  |  Labor Rate: $30.00/hr")
    print(f"================================================================================")

    # =========================================================================
    # SLIDE 01: Title Slide (Cover & Metadata Strip)
    # =========================================================================
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    fill1 = s1.background.fill
    fill1.solid()
    fill1.fore_color.rgb = BG_LIGHT

    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(3.0))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "TATA CONSULTANCY SERVICES  |  AI & CLOUD ADVISORY"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_PRIMARY
    
    p2 = tf1.add_paragraph()
    p2.text = "Contract Intelligence & Risk Visibility Platform"
    p2.font.size = Pt(34)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_DARK
    p2.space_before = Pt(6)
    
    p3 = tf1.add_paragraph()
    p3.text = "Production-Grade Azure Architecture  •  Deterministic & Agentic Governance  •  PoC to Enterprise Scale"
    p3.font.size = Pt(15)
    p3.font.color.rgb = BLUE_PRIMARY
    p3.space_before = Pt(6)

    # 4 Metadata Cards
    add_kpi_metric(s1, 0.8, 4.7, 2.7, 1.25, "Client Account", CLIENT_NAME, "Commercial Contract Governance", BLUE_PRIMARY)
    add_kpi_metric(s1, 3.8, 4.7, 2.7, 1.25, "Delivery Model", "4-Tier Evolution", "PoC ➔ Pilot ➔ MVP ➔ Prod", EMERALD_SUCCESS)
    add_kpi_metric(s1, 6.8, 4.7, 2.7, 1.25, "Blended Labor Rate", "$30.00 / hr", "Blended Offshore/Nearshore", AMBER_WARN)
    add_kpi_metric(s1, 9.8, 4.7, 2.7, 1.25, "Primary Cloud", "Microsoft Azure", "India Central / South Region", PURPLE_ACCENT)

    # Logos
    if os.path.exists("exports/assets/tcs_logo_black.png"):
        s1.shapes.add_picture("exports/assets/tcs_logo_black.png", Inches(0.8), Inches(6.92), width=Inches(1.8))
    if os.path.exists("exports/assets/tata_logo_black.png"):
        s1.shapes.add_picture("exports/assets/tata_logo_black.png", Inches(11.8), Inches(6.92), width=Inches(0.75))
    foot_box = s1.shapes.add_textbox(Inches(2.8), Inches(6.95), Inches(7.7), Inches(0.35))
    foot_box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    foot_box.text_frame.paragraphs[0].text = FOOTER_CENTER
    foot_box.text_frame.paragraphs[0].font.size = Pt(8.5)
    foot_box.text_frame.paragraphs[0].font.color.rgb = TEXT_MUTED

    s1.notes_slide.notes_text_frame.text = (
        "=== PRESENTER NOTES (SLIDE 01 / 56) ===\n\n"
        "📌 LOGIC (THE WHY):\nEstablishes strategic executive alignment on automated contract intelligence. Frames the initiative as a transformation from manual spreadsheet audits to an auditable, Azure-native contract risk platform.\n\n"
        "📐 DESIGNS (THE WHAT):\n16:9 widescreen presentation featuring clean light enterprise theme (#F8FAFC), official TCS and Tata branding, and 4 high-level program execution metadata indicators.\n\n"
        "⭐ HIGHLIGHTS:\nIntroduces the 4-phase maturity journey (PoC to Full Production), deterministic labor calculation based on $30/hr blended baseline, and Microsoft Azure sovereign India data residency.\n\n"
        "🔍 DETAILS:\nAudience: C-Suite (CIO, CLO, CFO, Head of Procurement) and Enterprise Architecture Board. Delivery timeline covers 6-week baseline PoC extending into enterprise production."
    )

    # =========================================================================
    # SLIDE 02 (Topic 1): Problem Statement and Business Impacts
    # =========================================================================
    s2 = create_base_slide(
        prs, 2, "Problem Statement & Strategic Business Impacts",
        "Fragmented contractual risk exposure across business domains and unmonitored deviation costs",
        "Section 01: Executive Context",
        {
            "logic": "Organizations execute hundreds of high-value agreements with fragmented oversight, leading to unbudgeted liabilities and audit penalties.",
            "designs": "Two high-impact structured cards comparing operational pain vectors with quantified business financial returns.",
            "highlights": "Cycle time drops from 5 business days to under 90 seconds per agreement; eliminates 100% of untracked liability cap breaches.",
            "details": "Manual reviews average 4.2 business days turnaround, causing severe bottlenecks during quarterly lease renewals and vendor onboarding."
        }
    )
    add_card(s2, 0.8, 1.5, 5.7, 5.1, "Core Operational Pain Vectors", [
        "Fragmented Risk Visibility: Legal, procurement, and operations execute contracts in silos without a centralized repository or shared ontology.",
        "Manual & Inconsistent Review: Reviewers apply divergent checklists across spreadsheets, resulting in variable risk interpretation and missed traps.",
        "Disconnected Audit Trail: Findings lack coordinate-level citations back to original PDF pages, stalling disputes and external audit defenses.",
        "Uncontrolled Non-Standard Terms: Indemnity caps, auto-renewals, and revenue splits often bypass senior leadership approval unnoticed.",
        "Scalability Bottleneck: Legal team bandwidth is overwhelmed during acquisition or lease renewal peaks (e.g. 600+ contracts/quarter).",
        "Knowledge Atrophy: Contractual precedent and negotiation insights reside in paralegal memory rather than an institutional risk knowledge base."
    ], header_color=AMBER_WARN)
    
    add_card(s2, 6.8, 1.5, 5.7, 5.1, "Quantified Strategic Business Impacts", [
        "92% Review Cycle Acceleration: Reduces manual contract assessment time from 4–5 business days to under 90 seconds per agreement.",
        "$2.4M Annual Risk Mitigation: Prevents unmonitored auto-renewals and enforces standard commercial liability caps across all categories.",
        "100% Clause Traceability: Every extracted entity and risk finding is linked to page-level bounding-box coordinates in Azure.",
        "Three-Tier Standardized Governance: Enforces formal Agree / Agree with Management Approval / Not Agree status recommendations.",
        "Audit-Ready Compliance: Complete chronological log of evaluations and human-in-the-loop decisions stored in Azure SQL.",
        "Capital Allocation Precision: Unlocks full visibility into recurring commercial commitments, escalators, and concession fee liabilities."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 03 (Topic 2): As-Is Process & Operational Pain Points (Editable)
    # =========================================================================
    s3 = create_base_slide(
        prs, 3, "As-Is Manual Process Flow & Key Operational Bottlenecks",
        "Current manual contract review workflow and operational vulnerability points across business functions",
        "Section 02: Baseline Assessment",
        {
            "logic": "Visualizing the current manual review baseline demonstrates why GenAI plus deterministic Azure processing is mandatory.",
            "designs": "Full-width editable table mapping the 5 manual lifecycle steps, roles, bottlenecks, and error rates.",
            "highlights": "Current workflow requires 24+ labor hours per contract; lacks coordinate provenance and automated validation.",
            "details": "Contract metadata is manually re-keyed into accounting systems without validation against master contracting ontologies."
        }
    )
    add_table(s3, 0.8, 1.5, 11.7, 5.1, 
        ["Step #", "As-Is Stage", "Responsible Role", "Activities & Hand-offs", "Operational Bottleneck / Pain Point", "Latency / Risk"],
        [
            ["01", "Drafting & Intake", "Procurement / Legal", "Contract received via email/scan in disparate PDF/Word formats", "No intake schema; missing exhibits & variable amendment versions", "2 to 3 days delay"],
            ["02", "Manual Scanning", "Junior Paralegal", "Line-by-line reading of 40–80 pages per agreement", "Human fatigue causes missed indemnity exclusions & termination triggers", "16–24 hours/doc"],
            ["03", "Spreadsheet Logging", "Business Analyst", "Re-keying clauses into departmental Excel registers", "Version drift across spreadsheets; zero link to source clauses", "High error rate (18%)"],
            ["04", "Risk Escalation", "Senior Counsel", "Ad-hoc email chains for non-standard management approvals", "Approvals buried in inboxes; lack of audit trail for board governance", "3 to 5 days wait"],
            ["05", "Filing & Storage", "Operations Lead", "Archived in local file shares or passive Google Drive/SharePoint", "No semantic search; duplicate vendor contracts re-negotiated blindly", "Loss of leverage"]
        ],
        col_widths=[0.8, 1.8, 1.8, 3.2, 2.6, 1.5]
    )

    # =========================================================================
    # SLIDE 04 (Topic 3): Solution Overview & Deliverables
    # =========================================================================
    s4 = create_base_slide(
        prs, 4, "Solution Overview: What We Are Delivering",
        "End-to-end Contract Intelligence & Risk Visibility Platform built on Microsoft Azure native services",
        "Section 03: Solution Blueprint",
        {
            "logic": "Provides executive alignment on the functional capabilities and core architectural deliverables across all tiers.",
            "designs": "Three thematic pillar cards covering ingestion, multi-pass reasoning, and risk cockpit presentation.",
            "highlights": "Ingests ~600 historical contracts across 6 categories (Lease, Vendor, Service, Facilities, Tech, Marketing).",
            "details": "Outputs structured findings into Azure SQL, feeds interactive demonstration dashboard, and enforces Entra ID SSO."
        }
    )
    add_card(s4, 0.8, 1.5, 3.7, 5.1, "1. Deterministic Layout Ingestion", [
        "Immutable Storage Landing: Azure Blob Storage receives raw digital PDFs with read-only access policies.",
        "Layout-Aware Parsing: Azure AI Document Intelligence extracts text, tables, and bounding boxes.",
        "Coordinate Provenance: Retains page numbers and (x, y) coordinates for 100% legal verification.",
        "Zero Modification: Source files remain pristine and tamper-evident for regulatory compliance.",
        "Format Support: Handles complex lease schedules, multi-column annexures, and digital signatures."
    ], header_color=BLUE_PRIMARY)
    
    add_card(s4, 4.8, 1.5, 3.7, 5.1, "2. Multi-Pass GenAI Reasoning", [
        "Hybrid Search Index: Azure AI Search indexes 512-token chunks with 1,536-dimensional embeddings.",
        "Pass 1 (Baseline Extraction): Azure OpenAI extracts standardized entities, dates, and liability caps.",
        "Pass 2 (Targeted Deep Dive): Specializes on ambiguous, negotiated, and open-textured terms.",
        "Ontology Rule Engine: Evaluates clauses against formal rules for Lease, Vendor, Service, Tech, etc.",
        "Status Synthesis: Renders Agree / Management Approval / Not Agree with rationale."
    ], header_color=PURPLE_ACCENT)
    
    add_card(s4, 8.8, 1.5, 3.7, 5.1, "3. Risk Visibility Cockpit", [
        "Interactive Dashboard: React/Web UI rendering side-by-side PDF coordinate highlight overlays.",
        "Central Risk Register: Auditable findings database replacing disconnected spreadsheets.",
        "Human-in-the-Loop Review: Workflow allowing corporate legal to accept, reject, or annotate findings.",
        "Entra ID Authentication: Enterprise Single Sign-On and Role-Based Access Control (RBAC).",
        "Exportable Deliverables: One-click export to Executive PPTX, Word BRD, and CSV/JSON registers."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 05 (Topic 4): AI vs Non-AI Interventions & KPI Measures
    # =========================================================================
    s5 = create_base_slide(
        prs, 5, "AI vs Non-AI Interventions & KPI Outcome Metrics",
        "Strict boundary definition ensuring non-AI deterministic tasks are never delegated to probabilistic LLMs",
        "Section 04: Intervention Governance",
        {
            "logic": "Enforces strict architectural rigor: LLMs must never perform deterministic tasks like OCR layout, schema validation, or auth.",
            "designs": "Editable comparative matrix detailing AI vs Non-AI components, technologies, and target KPI metrics.",
            "highlights": "Zero hallucination risk in document ingestion; AI bounded strictly to semantic classification and reasoning.",
            "details": "Deterministic components achieve 100% repeatability while GenAI components achieve >=95% benchmark agreement."
        }
    )
    add_table(s5, 0.8, 1.5, 11.7, 5.1,
        ["Solution Component", "Intervention Type", "Azure Technology", "Why This Intervention?", "Business KPI Impact", "Operational KPI Impact"],
        [
            ["Document Ingestion & Storage", "Non-AI (Deterministic)", "Azure Blob Storage (Hot Tier)", "Ensures tamper-proof, raw file storage with zero risk of file drift", "100% Audit Compliance", "Zero data loss; 100ms PUT"],
            ["Layout & Coordinate OCR", "Non-AI (Deterministic)", "Azure AI Doc Intelligence (Layout API)", "Deterministic coordinate recovery; avoids LLM coordinate fabrication", "100% Clause Traceability", "P95 Latency < 2.0s/doc"],
            ["Category Classification", "AI Agent (Semantic GenAI)", "Azure OpenAI (GPT-4o mini)", "Understands fuzzy contract structures across 6 varied categories", "Automated Intake Routing", "≥97% Classification Acc"],
            ["Standard Clause Extraction", "AI Agent (Prompt Pipeline)", "Azure OpenAI (GPT-4o)", "Extracts well-defined clauses (Term, Jurisdiction, Liability)", "80% Review Time Saved", "≥95% Extraction Precision"],
            ["Targeted Multi-Pass Extraction", "AI Agent (Iterative RAG)", "Azure AI Search + GPT-4o", "Deep dives into ambiguous, open-textured, or negotiated terms", "Zero Missed Traps", "Resolves 90%+ edge cases"],
            ["Ontology & Principle Eval", "Hybrid (Rule Engine + LLM)", "Azure SQL + GPT-4o Evaluator", "Evaluates extracted clause vs category principle ontology", "$2.4M Risk Avoidance", "Agree / Mgmt Approval / Reject"],
            ["Findings Storage & Export", "Non-AI (Deterministic)", "Azure SQL Database + Python", "Structured storage and deterministic Excel spreadsheet generation", "Spreadsheet Parity", "Instant 1-Click Export"],
            ["UI Presentation & Auth", "Non-AI (Deterministic)", "Azure App Service + Entra ID", "Enterprise Single Sign-On, RBAC, and side-by-side coordinate UI", "Security Governance", "100% SSO Compliance"]
        ],
        col_widths=[1.8, 1.5, 2.0, 2.4, 1.8, 2.2]
    )

    # =========================================================================
    # SLIDE 06 (Topic 5): To-Be Process Flow & Functional Architecture
    # =========================================================================
    s6 = create_base_slide(
        prs, 6, "To-Be End-to-End Process Flow & Functional Components",
        "Streamlined operational workflow from contract ingestion to executive risk visibility and sign-off",
        "Section 05: To-Be Process",
        {
            "logic": "Provides a comprehensive architectural overview of the transformed contract lifecycle under the Azure solution.",
            "designs": "Four sequential functional cards outlining the end-to-end journey from intake to governance.",
            "highlights": "Human-in-the-Loop review is integrated at decision points; exceptions automatically routed to paralegal queue.",
            "details": "Every process step is instrumented with Azure Application Insights telemetry and pass-provenance logging."
        }
    )
    add_card(s6, 0.8, 1.5, 2.75, 5.1, "Phase 1: Ingestion & Parsing", [
        "1. Contract Upload: Legal Ops deposits PDF into /contracts/raw Azure Blob.",
        "2. Event Trigger: Azure Event Grid fires BlobCreated event.",
        "3. Layout Analysis: Doc Intelligence recovers layout, tables, and (x, y) coordinates.",
        "4. Chunking Engine: Text sliced along clause boundaries (512 tokens).",
        "5. Vector Indexing: Embeddings written to Azure AI Search hybrid index."
    ], header_color=BLUE_PRIMARY)
    
    add_card(s6, 3.8, 1.5, 2.75, 5.1, "Phase 2: Classification & Passes", [
        "1. Classification Agent: Evaluates opening text into 1 of 6 categories.",
        "2. Schema Binding: Loads category-specific frozen clause checklist.",
        "3. Pass 1 Extraction: Broad prompt extracts standard entities and caps.",
        "4. Triage Gate: Empty/low-confidence clauses queued for Pass 2.",
        "5. Pass 2/3 Iteration: Targeted queries resolve vague/negotiated terms."
    ], header_color=PURPLE_ACCENT)
    
    add_card(s6, 6.8, 1.5, 2.75, 5.1, "Phase 3: Principle Assessment", [
        "1. Rule Loading: Retrieves category contracting principles from Azure SQL.",
        "2. Evaluation Prompt: Model compares extracted clause against principle.",
        "3. Status Synthesis: Assigns Agree / Mgmt Approval / Not Agree.",
        "4. Rationale Generation: Documents precise business justification.",
        "5. Coordinate Binding: Attaches source page & bounding box metadata."
    ], header_color=AMBER_WARN)
    
    add_card(s6, 9.8, 1.5, 2.75, 5.1, "Phase 4: Review & Governance", [
        "1. Risk Register Commit: Writes validated records to Azure SQL.",
        "2. Cockpit Visualization: Interactive UI displays PDF highlight overlays.",
        "3. HITL Action: Legal confirms findings or overrides with notes.",
        "4. Approval Routing: Escalates 'Mgmt Approval' items to CFO/Counsel.",
        "5. Audit Export: One-click export to Excel, Word BRD, and PPTX."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 07 (Topic 6): To-Be Process Flow (Editable Workflow Table)
    # =========================================================================
    s7 = create_base_slide(
        prs, 7, "To-Be Process Flow: State Transitions & Operational Roles (Editable)",
        "Detailed functional hand-offs, system triggers, inputs, and validation gates across each lifecycle step",
        "Section 06: Process Specifications",
        {
            "logic": "Provides delivery teams and process engineers with an editable state-machine specification of the To-Be process.",
            "designs": "Tabular state-transition specification detailing step, role, trigger, inputs, outputs, and validation criteria.",
            "highlights": "Every state change is recorded in Azure SQL with timestamp, user ID, and automated validation status.",
            "details": "Transitions from INGESTED to PARSED, CLASSIFIED, EXTRACTED, ASSESSED, and COMPLETED."
        }
    )
    add_table(s7, 0.8, 1.5, 11.7, 5.1,
        ["Step #", "Lifecycle Stage", "Actor / System", "Trigger Event", "Input Artifacts", "Output Artifacts", "Validation Gate"],
        [
            ["01", "Contract Landing", "Legal Operations", "Batch deposit in Azure Blob", "Executed PDF contracts", "Blob URI + Ingestion Task ID", "MIME type & PDF integrity check"],
            ["02", "Layout Extraction", "Azure AI Doc Intelligence", "BlobCreated Webhook", "Raw PDF document stream", "Layout JSON + Coordinates", "OCR confidence score ≥ 70%"],
            ["03", "Semantic Chunking", "Container Apps (Python)", "OCR Extraction Complete", "Layout-aware tokens & tables", "512-token chunks with tags", "Section boundary validation"],
            ["04", "Hybrid Indexing", "Azure AI Search", "Chunking Complete", "Vector embeddings (1536d)", "Searchable vector index", "Top-k recall confirmation"],
            ["05", "Classification", "Classification Agent", "Document Indexed", "Document Preamble chunks", "Category Tag + Confidence", "Confidence ≥ 85% else manual triage"],
            ["06", "Multi-Pass Extract", "Extraction Agent", "Category Assigned", "Category clause schema", "Structured clause records", "Pass provenance (P1, P2, P3)"],
            ["07", "Principle Eval", "Assessment Agent", "Clauses Extracted", "Category principle rules", "Risk Status + Rationale", "100% Page coordinate linked"],
            ["08", "Human Sign-off", "Senior Legal Counsel", "Findings Committed", "Risk Cockpit UI view", "Approved Risk Register", "Mandatory reviewer sign-off"]
        ],
        col_widths=[0.8, 1.6, 1.8, 1.6, 2.0, 2.1, 1.8]
    )

    # =========================================================================
    # SLIDE 08 (Topic 7): Business & Operational KPIs
    # =========================================================================
    s8 = create_base_slide(
        prs, 8, "Business & Operational KPI Measurement Framework",
        "Definitive formulas, KPI types, baseline targets, and prerequisites to measure solution success",
        "Section 07: Metrics & Value",
        {
            "logic": "A rigorous KPI framework ensures business and technical stakeholders can objectively evaluate ROI and platform health.",
            "designs": "Comprehensive 6-column editable KPI table detailing Type, Metric, Description, Formula, and Prerequisites.",
            "highlights": "Guarantees 100% clause traceability and ≥95% accuracy against legal-confirmed ground truth benchmarks.",
            "details": "Both business value (financial savings, turnaround time) and operational rigor (latency, availability) are tracked."
        }
    )
    add_table(s8, 0.8, 1.5, 11.7, 5.1,
        ["KPI Name", "Type", "Description", "Calculation Formula", "Target Benchmark", "Prerequisites / Assumptions"],
        [
            ["Classification Accuracy", "Operational", "Accuracy of AI assigning 1 of 6 categories", "(Correct Category Predictions / Total Corpus) × 100", "≥ 95.0%", "Legal ground-truth benchmark set"],
            ["Clause Extraction Rate", "Operational", "Precision of extracting in-scope clauses", "(Accurately Extracted Clauses / Expected Clauses) × 100", "≥ 95.0%", "Frozen category clause checklist"],
            ["Clause Traceability", "Governance", "Findings with exact PDF page coordinates", "(Findings with Valid Coordinates / Total Findings) × 100", "100.0%", "Doc Intelligence coordinate capture"],
            ["Review Cycle Time", "Business", "Elapsed time to assess contract end-to-end", "(Total Ingestion-to-Register Time / Processed Docs)", "< 90 Seconds", "Azure OpenAI TPM quota headroom"],
            ["Risk Exposure Catch Rate", "Business", "Identification of non-standard liability terms", "(Flagged Deviations / Known Deviation Injections) × 100", "≥ 98.0%", "Curated benchmark deviation sample"],
            ["Workflow Success Rate", "Operational", "Batches completing without exception halt", "(Completed Batches / Initiated Batches) × 100", "≥ 95.0%", "Retry & circuit breaker configured"],
            ["Operating Cost / Contract", "Financial", "Azure compute + token cost per contract", "(Total Monthly Azure Invoice / Contracts Processed)", "< $1.20 / Contract", "Optimized hybrid RAG chunking"]
        ],
        col_widths=[1.8, 1.2, 2.5, 2.5, 1.5, 2.2]
    )

    # =========================================================================
    # SLIDE 09 (Topic 8): Technical Component Architecture (Official Logos Diagram)
    # =========================================================================
    s9 = create_base_slide(
        prs, 9, "Production-Grade Azure Technical Component Architecture",
        "Official component blueprint spanning Ingestion, Orchestration, Agentic AI, and Storage Tiers",
        "Section 08: Technical Architecture",
        {
            "logic": "Provides an architectural blueprint using official Microsoft Azure icons across all functional layers.",
            "designs": "Embedded high-resolution architecture diagram with official Azure service icons and tier demarcations.",
            "highlights": "Clean separation of deterministic ingestion, decoupled message queues, and multi-pass GenAI reasoning.",
            "details": "Hosted entirely in Azure India regions (India Central / India South) to comply with data residency mandates."
        }
    )
    add_image_slide(s9, "exports/assets/diagrams/arch_component_diagram.png", left=0.8, top=1.45, width=11.733, height=5.25)

    # =========================================================================
    # SLIDE 10 (Topic 9): Technical Component Architecture (Editable Structure)
    # =========================================================================
    s10 = create_base_slide(
        prs, 10, "Production-Grade Component Architecture (Editable Structural Grid)",
        "Fully editable layout of all architectural tiers, Azure service instances, protocols, and data pathways",
        "Section 08: Technical Architecture",
        {
            "logic": "Allows enterprise architects and developers to customize and modify component blocks directly within PowerPoint.",
            "designs": "Four vertical editable tier cards detailing Azure services, SKUs, protocols, and architectural roles.",
            "highlights": "Zero vendor lock-in beyond native Azure PaaS; all components support Managed Identity without API keys.",
            "details": "Includes Azure Blob, Doc Intelligence, Container Apps, Service Bus, AI Search, OpenAI, and SQL Database."
        }
    )
    add_card(s10, 0.8, 1.5, 2.75, 5.1, "Tier 1: Intake & Ingestion", [
        "Azure Blob Storage (Hot Tier): Immutable raw contract PDF repository with soft delete and WORM policies.",
        "Azure AI Doc Intelligence (S0): Prebuilt Layout API recovering tables, paragraphs, and coordinates.",
        "Azure Functions (Serverless FaaS): Event Grid-triggered intake dispatcher and metadata tagger.",
        "Azure Key Vault: Dedicated HSM-backed secret and connection string store with zero shared keys.",
        "Protocols: HTTPS TLS 1.3, Blob REST API, Event Grid Webhooks."
    ], header_color=BLUE_PRIMARY)
    
    add_card(s10, 3.8, 1.5, 2.75, 5.1, "Tier 2: Orchestration & Queue", [
        "Azure Service Bus (Standard): Decoupled message queue buffering ingestion requests and smoothing bursts.",
        "Container Apps (FastAPI): Pass-aware orchestration state machine driving multi-pass extraction.",
        "Circuit Breaker & Backoff: Exponential jitter retry preventing Azure OpenAI HTTP 429 quota exhaustion.",
        "Managed Identity: System-assigned identity authenticating across all Azure microservices.",
        "Protocols: AMQP over TLS, REST API, gRPC internal communication."
    ], header_color=PURPLE_ACCENT)
    
    add_card(s10, 6.8, 1.5, 2.75, 5.1, "Tier 3: Reasoning & Agentic AI", [
        "Azure AI Search (Standard S1): Hybrid semantic vector index (text-embedding-3-large, 1536d) + BM25.",
        "Classification Agent (GPT-4o mini): Prompt-based classifier categorizing contracts into 6 domains.",
        "Multi-Pass Extraction Agent: Iterative prompt engine for standard (P1) and ambiguous (P2+) terms.",
        "Principle Evaluation Engine: Rule-guided LLM evaluator comparing clauses to master ontologies.",
        "Protocols: Azure OpenAI REST API, JSON Structured Output mode."
    ], header_color=AMBER_WARN)
    
    add_card(s10, 9.8, 1.5, 2.75, 5.1, "Tier 4: Storage & Cockpit", [
        "Azure SQL Database (General Purpose): Relational store for ontologies, extracted clauses, and audit logs.",
        "Azure App Service (Linux B1/S1): React-based Risk Visibility Cockpit with coordinate highlight overlays.",
        "Azure Monitor & App Insights: Distributed tracing, token tracking, and latency alerting.",
        "Entra ID SSO: Single Sign-On, MFA, and Role-Based Access Control (RBAC).",
        "Protocols: TDS over TLS 1.3, React REST API, OAuth 2.0 / OIDC."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 11 (Topic 9a): Architecture Boundary Demarcation & Numbered Flow
    # =========================================================================
    s11 = create_base_slide(
        prs, 11, "Architecture Boundary Demarcation & Numbered Data Flow (Topic 9a)",
        "Explicit execution boundaries across Virtual Servers, Agentic Frameworks, Serverless Containers & FaaS",
        "Section 09: Boundary Governance",
        {
            "logic": "Provides clear demarcation of hosting models to guide cloud governance, cost allocation, and security posture.",
            "designs": "Four distinct boundary boxes clearly marked with hosting model, service specs, and numbered trigger pathways.",
            "highlights": "Serverless containers handle orchestration; Agentic AI runs in Azure AI Foundry / OpenAI; FaaS handles events.",
            "details": "Includes numbered dataflow triggers [1] Intake -> [2] OCR -> [3] Chunking -> [4] Vector Index -> [5] Agentic Reasoning."
        }
    )
    add_boundary_box(s11, 0.8, 1.5, 2.75, 5.1, "Legacy / VM Boundary", "Isolated Batch & DB Sync", "Virtual Server / IaaS", color=TEXT_SUB)
    add_card(s11, 0.9, 2.1, 2.55, 4.3, "Virtual Server Components", [
        "• Scope: Dedicated Linux VM (Standard D4s_v5) reserved for bulk historical legacy ingestion and archive sync.",
        "• Trigger [1]: SFTP/SMB batch pickup from on-premise archives.",
        "• Security: Enclosed in private Azure VNet subnet with Network Security Group (NSG) lockdown.",
        "• Justification: Accommodates non-cloud-native enterprise intake feeds without re-architecting legacy archives."
    ], header_color=TEXT_SUB, bg_color=CARD_BG)

    add_boundary_box(s11, 3.8, 1.5, 2.75, 5.1, "Serverless Containers", "Orchestration & API Gateway", "Container Apps / CaaS", color=BLUE_PRIMARY)
    add_card(s11, 3.9, 2.1, 2.55, 4.3, "Container Engine Components", [
        "• Scope: Azure Container Apps hosting FastAPI core orchestration service and pass-aware workflow engine.",
        "• Trigger [2]: Ingestion Queue listener consumes Service Bus messages.",
        "• Trigger [3]: Executes multi-pass scheduling loop and exception routing.",
        "• Scaling: Autoscale 0 to 5 replicas based on message queue backlog.",
        "• Security: Private ingress via Azure VNet integration; zero public IP."
    ], header_color=BLUE_PRIMARY, bg_color=CARD_BG)

    add_boundary_box(s11, 6.8, 1.5, 2.75, 5.1, "Agentic AI Framework", "Multi-Pass LLM Reasoning", "Azure AI Foundry / OpenAI", color=PURPLE_ACCENT)
    add_card(s11, 6.9, 2.1, 2.55, 4.3, "Agentic AI Components", [
        "• Scope: Azure AI Foundry / OpenAI hosting GPT-4o and text-embedding-3-large.",
        "• Trigger [4]: Classification Agent prompt evaluating document structure.",
        "• Trigger [5]: Pass 1 extraction & targeted Pass 2/3 ambiguity resolver.",
        "• Trigger [6]: Principle assessment rule reasoning engine.",
        "• Guardrails: Azure AI Content Safety filtering and groundedness checks."
    ], header_color=PURPLE_ACCENT, bg_color=CARD_BG)

    add_boundary_box(s11, 9.8, 1.5, 2.75, 5.1, "Event Functions (FaaS)", "Micro-Events & Report Dispatch", "Azure Functions / FaaS", color=EMERALD_SUCCESS)
    add_card(s11, 9.9, 2.1, 2.55, 4.3, "Serverless FaaS Components", [
        "• Scope: Python Azure Functions running on Consumption Serverless plan.",
        "• Trigger [7]: Event Grid BlobCreated trigger invoking OCR dispatcher.",
        "• Trigger [8]: Automated nightly synthetic canary evaluation probe.",
        "• Trigger [9]: Risk Register Excel export generation and email notification.",
        "• Benefit: 100% serverless event handling; zero idle compute cost."
    ], header_color=EMERALD_SUCCESS, bg_color=CARD_BG)

    # Compile Section A (Slides 12 to 22)
    build_slides_12_to_22(prs)

    # Compile Section B (Slides 23 to 33)
    build_slides_23_to_33(prs)

    # Compile Section C (Slides 34 to 45)
    build_slides_34_to_45(prs)

    # Compile Section D (Slides 46 to 56)
    build_slides_46_to_56(prs)

    output_path = "exports/PVR_INOX_TCS_Contract_Intelligence_Master_Deck.pptx"
    prs.save(output_path)
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"================================================================================")
    print(f"SUCCESS! Master Presentation successfully compiled to {output_path}")
    print(f"Total Slides: {len(prs.slides)} / {TOTAL_SLIDES}  |  File Size: {file_size_mb:.2f} MB")
    print(f"================================================================================")
    return prs, output_path

if __name__ == "__main__":
    build_complete_presentation()
