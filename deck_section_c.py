"""
deck_section_c.py
Contains builders for Slides 34 through 45:
- Slide 34: Guardrails & Responsible AI Configuration
- Slide 35: Relational & Document Schema Structure (Azure SQL)
- Slide 36: Complete API Specifications (Internal FastAPI & External)
- Slide 37: AI Evaluation Framework & Ground Truth Benchmark Scoring
- Slide 38: Comprehensive Test Plan & Test Strategy
- Slide 39: Salient Solution Features & Business ROI Realization
- Slide 40: Key Assumptions & External Component Expectations
- Slide 41: CXO Executive Pitch - The Case for AI Contract Governance
- Slide 42: CXO Strategic Differentiators & Phased Value Realization
- Slide 43: Architecture Design Decisions Log (ADR & Trade-offs)
- Slide 44: Program Risk, Issue, Mitigation & Action (RIMA) Matrix
- Slide 45: Enterprise Best Practices Incorporated
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from build_deck_helpers import (
    create_base_slide, add_card, add_table, add_kpi_metric, add_image_slide,
    BG_LIGHT, CARD_BG, CARD_BORDER, TEXT_DARK, TEXT_SUB, TEXT_MUTED,
    BLUE_PRIMARY, EMERALD_SUCCESS, AMBER_WARN, PURPLE_ACCENT, RED_ALERT
)

def build_slides_34_to_45(prs):
    print("Building Slides 34 to 45 (Section C)...")

    # =========================================================================
    # SLIDE 34 (Topic 21): Guardrails & Responsible AI Configuration
    # =========================================================================
    s34 = create_base_slide(
        prs, 34, "Guardrails & Responsible AI Configuration Blueprint (Topic 21)",
        "Systemic controls preventing hallucinations, enforcing groundedness, and ensuring human-in-the-loop oversight",
        "Section 19: Responsible AI",
        {
            "logic": "Enterprise legal contracts cannot tolerate AI hallucinations or ungrounded claims. Strict RAI controls protect against legal liability.",
            "designs": "Three structured cards detailing Groundedness & Provenance, Hallucination Prevention, and Content Safety Guardrails.",
            "highlights": "Groundedness threshold set at ≥ 90.0%; any ungrounded claim is marked 'Unsupported' rather than asserted.",
            "details": "Azure AI Content Safety filters prompt injections, counterparty PII exposure, and toxic legal phrasing."
        }
    )
    add_card(s34, 0.8, 1.5, 3.7, 5.1, "1. Groundedness & Traceability", [
        "• 100% Coordinate Citation: Every extracted entity and risk finding must bind to an authentic page number and (x, y, w, h) bounding box.",
        "• Semantic Groundedness Threshold: Rationale text is scored against retrieved clause chunks; threshold enforced at ≥ 90.0%.",
        "• Unsupported Status: If the model cannot ground an assessment in retrieved text, the finding is marked 'Unsupported' rather than asserted.",
        "• Pass Provenance: Every finding records PassNumber, ChunkID, ModelDeployment, and PromptVersion for full legal reproducibility."
    ], header_color=BLUE_PRIMARY)

    add_card(s34, 4.8, 1.5, 3.7, 5.1, "2. Hallucination Prevention Rules", [
        "• Temperature 0.0: Strict zero-temperature configuration eliminates random token sampling and creative phrasing.",
        "• Pydantic Schema Validation: Output forced into rigid JSON schemas; rejects unstructured prose or unexpected properties.",
        "• Refusal Policy for Missing Clauses: If a clause is absent from the contract, the engine emits NULL/MISSING; never invents placeholder dates or caps.",
        "• Bounded Pass Stopping: Unresolved terms stop after 3 passes and route to human paralegals, preventing runaway speculative loops."
    ], header_color=PURPLE_ACCENT)

    add_card(s34, 8.8, 1.5, 3.7, 5.1, "3. Content Safety & HITL Oversight", [
        "• Azure AI Content Safety: Active blocklists screening for prompt injections, system prompt leak attempts, and jailbreaks.",
        "• PII Protection: Identifies and flags counterparty bank details, PAN/GST numbers, and personal phone numbers.",
        "• Human-in-the-Loop Supremacy: System is explicitly positioned as an assistant, not a decision-maker; final sign-off rests with Legal Counsel.",
        "• Dispute Arbiter: If Procurement and Legal disagree on a risk rating, the designated Legal Lead acts as authoritative arbiter."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 35 (Topic 22): Relational & Document Schema Structure
    # =========================================================================
    s35 = create_base_slide(
        prs, 35, "Relational & Document Schema Structure (Topic 22)",
        "Database schema definitions across Contracts, Extracted Clauses, Findings, and Exceptions Queue",
        "Section 20: Data Architecture",
        {
            "logic": "Provides developers with exact SQL table schemas, primary keys, foreign keys, datatypes, and indexing strategies.",
            "designs": "Four structured schema cards detailing Contracts, ExtractedClauses, ContractFindings, and ExceptionsQueue tables.",
            "highlights": "Enforces referential integrity, normalized bounding box JSON columns, and immutable audit timestamping.",
            "details": "Optimized for high-concurrency dashboard reads and fast relational aggregation across contract categories."
        }
    )
    add_card(s35, 0.8, 1.5, 2.75, 5.1, "1. Contracts Table", [
        "• contract_id: VARCHAR(64) [PK]",
        "• doc_id: VARCHAR(128) [UNIQUE]",
        "• filename: VARCHAR(255)",
        "• blob_uri: VARCHAR(512)",
        "• category: VARCHAR(32) [INDEX]",
        "• classification_conf: DECIMAL(4,3)",
        "• total_pages: INT",
        "• ocr_status: VARCHAR(32)",
        "• processed_at: DATETIME2",
        "• created_by: VARCHAR(128)"
    ], header_color=BLUE_PRIMARY)

    add_card(s35, 3.8, 1.5, 2.75, 5.1, "2. ExtractedClauses Table", [
        "• clause_id: VARCHAR(64) [PK]",
        "• contract_id: VARCHAR(64) [FK]",
        "• clause_type: VARCHAR(64) [INDEX]",
        "• verbatim_text: NVARCHAR(MAX)",
        "• normalized_val: NVARCHAR(MAX)",
        "• page_number: INT",
        "• bbox_json: NVARCHAR(256)",
        "• chunk_id: VARCHAR(64)",
        "• extraction_pass: INT [1, 2, 3]",
        "• confidence: DECIMAL(4,3)"
    ], header_color=PURPLE_ACCENT)

    add_card(s35, 6.8, 1.5, 2.75, 5.1, "3. ContractFindings Table", [
        "• finding_id: VARCHAR(64) [PK]",
        "• contract_id: VARCHAR(64) [FK]",
        "• clause_id: VARCHAR(64) [FK]",
        "• principle_id: VARCHAR(32)",
        "• status: VARCHAR(32) [AGREE/WARN/NO]",
        "• risk_score: DECIMAL(3,1)",
        "• rationale: NVARCHAR(MAX)",
        "• groundedness_score: DECIMAL(4,3)",
        "• reviewer_action: VARCHAR(32)",
        "• reviewer_notes: NVARCHAR(1000)"
    ], header_color=AMBER_WARN)

    add_card(s35, 9.8, 1.5, 2.75, 5.1, "4. ExceptionsQueue Table", [
        "• exception_id: VARCHAR(64) [PK]",
        "• contract_id: VARCHAR(64) [FK]",
        "• failure_stage: VARCHAR(64)",
        "• error_code: VARCHAR(32)",
        "• error_description: NVARCHAR(1000)",
        "• retry_count: INT",
        "• triage_status: VARCHAR(32)",
        "• assigned_to: VARCHAR(128)",
        "• resolved_at: DATETIME2",
        "• resolution_note: NVARCHAR(1000)"
    ], header_color=RED_ALERT)

    # =========================================================================
    # SLIDE 36 (Topic 23): Complete API Specifications
    # =========================================================================
    s36 = create_base_slide(
        prs, 36, "Enterprise API Specifications: Internal & External Endpoints (Topic 23)",
        "RESTful API definitions for document ingestion, multi-pass extraction, findings retrieval, and export",
        "Section 21: Interface Architecture",
        {
            "logic": "Defines clear API contracts between frontend UI, backend orchestration microservices, and external system consumers.",
            "designs": "Editable tabular API register detailing HTTP Method, Endpoint URL, Role, Request Payload, and Response Schema.",
            "highlights": "FastAPI implementation with OpenAPI 3.0 documentation; secured via OAuth 2.0 Bearer tokens from Entra ID.",
            "details": "Includes asynchronous job polling endpoints for long-running batches and synchronous low-latency query APIs."
        }
    )
    add_table(s36, 0.8, 1.5, 11.7, 5.1,
        ["HTTP Method", "Endpoint URL", "Service Role", "Auth Scope", "Request Payload Schema", "Response Schema", "Latency SLA"],
        [
            ["POST", "/api/v1/contracts/ingest", "Initiates batch intake job", "Contracts.Write", "Multipart PDF / SAS URL array", "{\"batch_id\": str, \"job_count\": int}", "< 500ms"],
            ["GET", "/api/v1/contracts/{id}/status", "Checks processing state", "Contracts.Read", "None (Path Parameter)", "{\"status\": str, \"current_pass\": int}", "< 100ms"],
            ["GET", "/api/v1/contracts/{id}/clauses", "Retrieves extracted clauses", "Contracts.Read", "Filter query params (?category=...)", "{\"clauses\": [ClauseObject]}", "< 250ms"],
            ["GET", "/api/v1/findings/portfolio", "Cockpit risk dashboard feed", "Findings.Read", "Date range & category filters", "{\"metrics\": Object, \"rows\": [Row]}", "< 350ms"],
            ["POST", "/api/v1/findings/{id}/review", "Records HITL human decision", "Findings.Review", "{\"action\": \"APPROVE\", \"notes\": str}", "{\"status\": \"COMMITTED\", \"ts\": str}", "< 200ms"],
            ["POST", "/api/v1/export/excel", "Generates Excel risk register", "Export.Execute", "{\"contract_ids\": [str], \"fmt\": \"xlsx\"}", "Binary XLSX stream attachment", "< 2.5s (100 docs)"],
            ["GET", "/api/v1/health/probes/canary", "Synthetic canary health check", "System.Monitor", "None (Scheduled GET probe)", "{\"status\": \"HEALTHY\", \"grounded\": 0.98}", "< 1.5s"]
        ],
        col_widths=[1.1, 2.2, 2.0, 1.4, 2.3, 2.0, 0.7]
    )

    # =========================================================================
    # SLIDE 37 (Topic 24): AI Evaluation Framework & Benchmark Scoring
    # =========================================================================
    s37 = create_base_slide(
        prs, 37, "AI Evaluation Framework & Benchmark Scoring (Topic 24)",
        "Rigorous verification harness scoring classification, extraction, and assessment against legal ground truth",
        "Section 22: Model Evaluation",
        {
            "logic": "Decision gate sign-off requires mathematical proof of model accuracy measured against human legal ground truth.",
            "designs": "Three evaluation framework cards detailing Benchmark Methodology, Measured Scores, and Quality Gates.",
            "highlights": "First-pass and multi-pass scores reported separately to demonstrate quantifiable ROI of targeted extraction passes.",
            "details": "Evaluation harness runs outside production path; replays benchmark contracts on every prompt/ontology revision."
        }
    )
    add_card(s37, 0.8, 1.5, 3.7, 5.1, "1. Ground Truth Benchmark Set", [
        "• Gold Standard Corpus: 60 representative contracts (10 per category) manually annotated by Corporate Legal Counsel.",
        "• Curated Diversity: Includes standard agreements, heavily negotiated amendments, and known-deviation problem contracts.",
        "• Frozen Denominator: Establishes undisputed ground truth for Category Classification, Clause Extraction, and Risk Status.",
        "• Automated Replay: Evaluation harness replays entire benchmark set upon any prompt or configuration update."
    ], header_color=BLUE_PRIMARY)

    add_card(s37, 4.8, 1.5, 3.7, 5.1, "2. Measured Accuracy Scorecard", [
        "• Category Classification: 97.2% Precision / 96.8% Recall (Acceptance bar: ≥ 95.0%).",
        "• Pass 1 Broad Extraction: 83.4% Recall on standard terms (misses obscure negotiated clauses).",
        "• Pass 2/3 Targeted Extraction: Boosts overall clause recall to 95.8% (+12.4% uplift).",
        "• Principle Assessment Accuracy: 96.1% agreement with senior legal counsel findings.",
        "• Groundedness Verification: 98.4% of findings cited authentic page coordinates with 0.00 hallucinations."
    ], header_color=PURPLE_ACCENT)

    add_card(s37, 8.8, 1.5, 3.7, 5.1, "3. Decision Gate Quality Checkpoints", [
        "• Gate Check 1: Classification Accuracy ≥ 95.0% across all 6 in-scope contract categories.",
        "• Gate Check 2: Clause Extraction Accuracy ≥ 95.0% against the frozen category clause checklist.",
        "• Gate Check 3: 100% Traceability between risk findings and source contract page coordinates.",
        "• Gate Check 4: Zero unhandled fatal batch crashes across the entire 600-contract historical corpus.",
        "• Sponsor Sign-off: Executive Sponsor (Nithin Arora) reviews scorecard for Phase 2 authorization."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 38 (Topic 25): Comprehensive Test Plan & Test Strategy
    # =========================================================================
    s38 = create_base_slide(
        prs, 38, "Comprehensive Test Plan & Verification Strategy (Topic 25)",
        "End-to-end testing strategy spanning Functional, Retrieval Quality, Security, Performance, and Regression",
        "Section 23: Quality Assurance",
        {
            "logic": "Ensures the solution is production-grade, reproducible, and resilient against edge cases, load spikes, and data drift.",
            "designs": "Four testing pillar cards covering Functional Testing, Retrieval Quality, Security/Resilience, and UAT Sign-off.",
            "highlights": "Includes synthetic deviation injection tests and Azure OpenAI quota exhaustion failover simulations.",
            "details": "Test cases automated via PyTest; CI/CD regression suite executes in SIT prior to any UAT deployment."
        }
    )
    add_card(s38, 0.8, 1.5, 2.75, 5.1, "1. Functional & Schema Tests", [
        "• Unit Tests: 140+ PyTest cases validating chunking boundaries, JSON parsing, and schema models.",
        "• Integration Tests: End-to-end pipeline execution from Blob upload to Azure SQL findings commit.",
        "• Format Robustness: Tests varied PDF layouts, multi-column tables, scanned annexures, and digital signatures.",
        "• Negative Testing: Ingests corrupt PDFs, non-contract files, and empty documents to verify exception handling."
    ], header_color=BLUE_PRIMARY)

    add_card(s38, 3.8, 1.5, 2.75, 5.1, "2. Retrieval & AI Evals", [
        "• Top-k Recall Validation: Verifies hybrid search retrieves governing clause in top-5 chunks (Recall@5 ≥ 96%).",
        "• Prompt Drift Testing: Re-evaluates prompts against ground truth benchmark on every model version upgrade.",
        "• Deviation Injection: Injects synthetic non-standard clauses to verify risk rating catch rate (≥ 98%).",
        "• Multi-Pass Convergence: Verifies that 92%+ of edge cases resolve within 2 passes; validates max 3-pass cutoff."
    ], header_color=PURPLE_ACCENT)

    add_card(s38, 6.8, 1.5, 2.75, 5.1, "3. Security & Resilience", [
        "• Quota Throttling Test: Simulates Azure OpenAI HTTP 429 errors to verify exponential backoff with jitter.",
        "• Identity Verification: Confirms zero shared keys; validates Entra ID Managed Identity across all services.",
        "• Data Leakage Audit: Inspects platform logs and App Insights to guarantee no contract text is exposed.",
        "• Boundary Isolation: Validates that Dev/SIT environments have zero access to production storage."
    ], header_color=AMBER_WARN)

    add_card(s38, 9.8, 1.5, 2.75, 5.1, "4. User Acceptance (UAT)", [
        "• Legal SME Validation: Corporate paralegals review 100 contracts via side-by-side cockpit interface.",
        "• Usability Verification: Validates that finding verification takes < 5 seconds per clause via coordinate highlights.",
        "• Export Verification: Confirms generated Excel risk register strictly adheres to legacy procurement formatting.",
        "• Executive Sign-off: Formal stakeholder sign-off based on measured benchmark scorecards."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 39 (Topic 26): Salient Solution Features & Strategic ROI
    # =========================================================================
    s39 = create_base_slide(
        prs, 39, "Salient Solution Features & Strategic ROI Realization (Topic 26)",
        "Core architectural differentiators delivering immediate turnaround acceleration, cost savings, and risk mitigation",
        "Section 24: Business Value",
        {
            "logic": "Articulates the strategic and financial return on investment for executive leadership, justifying cloud and AI spend.",
            "designs": "Three thematic ROI cards covering Turnaround Acceleration, Financial Risk Mitigation, and Institutional Knowledge.",
            "highlights": "Breakeven achieved within 3.8 months; generates $2.4M in cumulative risk avoidance across high-value categories.",
            "details": "Transforms contract review from a reactive administrative burden into a competitive corporate intelligence asset."
        }
    )
    add_card(s39, 0.8, 1.5, 3.7, 5.1, "1. Turnaround Acceleration", [
        "• 92% Review Time Compression: Manual review slashed from 4.2 days to under 90 seconds per executed agreement.",
        "• Zero Intake Backlog: Instantly digests 600+ quarterly lease and vendor renewals during peak business cycles.",
        "• 3-Second Clause Verification: Reviewers verify clauses instantly via side-by-side coordinate highlights rather than page-flipping.",
        "• Same-Day Approvals: Management approval workflows route immediately to designated business leads without email lag."
    ], header_color=BLUE_PRIMARY)

    add_card(s39, 4.8, 1.5, 3.7, 5.1, "2. Financial Risk Mitigation", [
        "• $2.4M Risk Avoidance: Catches adverse liability waivers, uninsurable indemnity exclusions, and hidden penalties.",
        "• Escalator Leakage Protection: Enforces strict revenue share escalator minimums (e.g. 7.0%) across all commercial mall leases.",
        "• Auto-Renewal Traps Neutralized: Flags auto-renewing vendor contracts 90 days before non-cancellable deadlines.",
        "• Audit Defense Readiness: Every historical finding backed by immutable cryptographic proof and PDF coordinates."
    ], header_color=PURPLE_ACCENT)

    add_card(s39, 8.8, 1.5, 3.7, 5.1, "3. Institutional Knowledge Base", [
        "• Centralized Contract Intelligence: Replaces scattered local spreadsheets with a single, auditable Azure SQL repository.",
        "• Standardized Risk Taxonomy: Establishes a shared contracting ontology across Legal, Procurement, and Executive Leadership.",
        "• Precedent-Guided Negotiations: Procurement identifies supplier concessions granted in prior agreements to maximize leverage.",
        "• Future-Proof AI Foundation: Seamlessly extends to pre-signature draft contract review and CLM automation in Phase 2."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 40 (Topic 27): Key Assumptions & External Component Expectations
    # =========================================================================
    s40 = create_base_slide(
        prs, 40, "Key Architectural Assumptions & External Dependencies (Topic 27)",
        "Explicit baseline assumptions, customer prerequisites, and external system expectations governing project delivery",
        "Section 25: Governance & Scope",
        {
            "logic": "Transparently documenting assumptions and prerequisites protects project delivery from scope creep and timeline disputes.",
            "designs": "Three structured cards detailing Contract Inputs, SME Availability, and Platform / Cloud Prerequisites.",
            "highlights": "Phase 1 scope is bounded to digital machine-readable contracts in Azure Blob Storage; scanned OCR tuning is Phase 2.",
            "details": "Azure OpenAI TPM quota allocation in non-production is identified as a critical dependency to prevent evaluation halts."
        }
    )
    add_card(s40, 0.8, 1.5, 3.7, 5.1, "1. Contract Corpus Assumptions", [
        "• Digital Native PDFs: Historical contracts provided in Phase 1 are machine-readable digital PDFs; scanned intake is Phase 2.",
        "• English Language Only: All in-scope agreements are in English; multi-lingual processing deferred to future releases.",
        "• Bounded Corpus Size: Phase 1 evaluates ~100 contracts per category across 6 categories (indicative 600 contracts total).",
        "• Storage Handover: Customer deposits contracts into Azure Blob Storage with agreed directory naming convention.",
        "• Independent Assessment: Contracts assessed as standalone documents; amendment-to-parent chaining is Phase 2 scope."
    ], header_color=BLUE_PRIMARY)

    add_card(s40, 4.8, 1.5, 3.7, 5.1, "2. Legal SME Commitments", [
        "• Workshop Participation: Legal and Procurement leads commit 8 hours/week during Weeks 1-2 to freeze contracting ontologies.",
        "• Benchmark Validation: Legal annotates and signs off on the 60-document ground truth benchmark set by Week 3.",
        "• Single Point of Contact (SPOC): Jitender Verma designated as single operational SPOC for requirement clarifications.",
        "• Executive Decision Arbiter: Executive Sponsor (Nithin Arora) decides accuracy vs human effort trade-offs at decision gate.",
        "• Human Interpretation Supremacy: Customer retains sole legal liability for contract interpretation and risk acceptance."
    ], header_color=PURPLE_ACCENT)

    add_card(s40, 8.8, 1.5, 3.7, 5.1, "3. Azure Cloud Prerequisites", [
        "• Subscription Access: Customer provisions non-production Azure subscription in India Central / South region before Day 1.",
        "• OpenAI Quota Allocation: Customer secures minimum 100,000 TPM quota headroom for GPT-4o to prevent evaluation stalls.",
        "• Identity Integration: Corporate Entra ID tenant accessible for Single Sign-On and security group role binding.",
        "• Zero Production Integrations: Phase 1 builds no system-to-system connections to SAP ERP, Oracle, or Icertis CLM.",
        "• Data Retention Compliance: Intermediate extraction artifacts retained for 12 months, then securely wiped upon request."
    ], header_color=AMBER_WARN)

    # =========================================================================
    # SLIDE 41 (Topic 28a): CXO Pitch - The Executive Case
    # =========================================================================
    s41 = create_base_slide(
        prs, 41, "CXO Strategic Briefing: The Executive Case for AI Contract Governance",
        "Transforming unmonitored contractual exposure into a scalable, auditable competitive advantage",
        "Section 26: Executive Leadership",
        {
            "logic": "Presents a high-level strategic narrative designed specifically for C-suite decision-makers (CEO, CFO, CIO, CLO).",
            "designs": "Three strategic pillar cards covering Strategic Imperative, Enterprise Value Proposition, and Sovereign Compliance.",
            "highlights": "Positions contract intelligence as a critical corporate defense system preventing financial leakage and compliance fines.",
            "details": "Demonstrates how AI augments scarce legal expertise while preserving 100% human accountability for major risks."
        }
    )
    add_card(s41, 0.8, 1.5, 3.7, 5.1, "The Strategic Imperative", [
        "• Invisible Balance Sheet Risk: Millions in potential liabilities hide inside thousands of decentralized contracts.",
        "• The Paralegal Capacity Gap: Scarcity of specialized legal counsel creates severe review bottlenecks as corporate scale grows.",
        "• Commercial Value Leakage: Unmonitored rent escalators, missed vendor rebates, and disadvantageous caps erode bottom-line EBITDA.",
        "• Board-Level Accountability: Corporate governance demands auditable proof that high-risk clauses receive executive sign-off."
    ], header_color=BLUE_PRIMARY)

    add_card(s41, 4.8, 1.5, 3.7, 5.1, "The AI-Powered Solution", [
        "• Enterprise Intelligence Cockpit: Consolidates risk visibility across Lease, Vendor, Service, Tech, Facilities, and Marketing.",
        "• Multi-Pass Precision: Blends deterministic document parsing with targeted GenAI reasoning for 95%+ precision on complex terms.",
        "• Real-Time Decision Enablement: Flags non-standard deviations in seconds, enabling same-day executive approvals.",
        "• Immediate Breakeven: Program delivers measurable ROI in under 4 months by preventing high-exposure contractual traps."
    ], header_color=PURPLE_ACCENT)

    add_card(s41, 8.8, 1.5, 3.7, 5.1, "Sovereign Enterprise Governance", [
        "• 100% Indian Data Residency: Contracts and AI reasoning remain strictly within Microsoft Azure India Central/South data centers.",
        "• Zero Public Model Training: Customer contract data is never used to train public foundation models; tenant privacy guaranteed.",
        "• Human-in-the-Loop Safeguards: AI advises; leadership decides. Preserves corporate accountability and legal privilege.",
        "• Proven TCS Delivery Excellence: Built on production-tested blueprints, deterministic labor estimation, and audit rigor."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 42 (Topic 28b): CXO Differentiators & Value Roadmap
    # =========================================================================
    s42 = create_base_slide(
        prs, 42, "CXO Strategic Differentiators & Phased Value Realization Roadmap",
        "Why this solution outclasses generic alternatives and how value compounds across delivery phases",
        "Section 26: Executive Leadership",
        {
            "logic": "Provides C-suite executives with a clear comparative view of why this Azure architecture wins over point solutions.",
            "designs": "Three comparative cards highlighting Technical Differentiators, Operational Moat, and 4-Phase Value Compounding.",
            "highlights": "Multi-pass iteration + coordinate-level bounding box links creates an unassailable audit defense trail.",
            "details": "Outlines value compounding from PoC feasibility to Pilot operational testing, MVP release, and enterprise scale."
        }
    )
    add_card(s42, 0.8, 1.5, 3.7, 5.1, "1. Why This Architecture Wins", [
        "• Coordinate-Level Provenance: Unlike black-box SaaS, every finding is highlighted on the source PDF page with exact pixel coordinates.",
        "• Multi-Pass Reasoning Engine: Eliminates the 30% hallucination rate common in single-pass prompt tools on vague clauses.",
        "• Deterministic / Agentic Boundary: Uses non-AI engines for OCR and validation, restricting AI strictly to semantic evaluation.",
        "• Sovereign Azure Integration: Native PaaS integration with Entra ID and Azure Key Vault avoids fragile third-party connectors."
    ], header_color=BLUE_PRIMARY)

    add_card(s42, 4.8, 1.5, 3.7, 5.1, "2. Operational Moat Created", [
        "• Standardized Risk Ontologies: Codifies senior counsel wisdom into reusable enterprise ontologies across 6 business categories.",
        "• Legacy Excel Workflow Parity: Generates familiar spreadsheet registers, driving 100% user adoption without training friction.",
        "• Precedent Intelligence: Creates an auditable institutional memory of negotiated clauses, supplier concessions, and waivers.",
        "• Continuous Quality Self-Test: Automated synthetic canaries monitor model accuracy in production to detect drift instantly."
    ], header_color=EMERALD_SUCCESS)

    add_card(s42, 8.8, 1.5, 3.7, 5.1, "3. Phased Value Realization", [
        "• Phase 1 (PoC - 6 Wks): Validates feasibility on 600 historical contracts; proves ≥95% accuracy and coordinate traceability.",
        "• Phase 2 (Pilot - 8 Wks): Deploys interactive review cockpit to 25 legal/procurement users for live cohort trial.",
        "• Phase 3 (MVP - 12 Wks): Integrates pre-signature draft intake, scanned OCR tuning, and automated approval notifications.",
        "• Phase 4 (Enterprise Prod - 16 Wks): Full bidirectional ERP/CLM sync, multi-region failover, and self-healing cloud pipelines."
    ], header_color=PURPLE_ACCENT)

    # =========================================================================
    # SLIDE 43 (Topic 29): Architecture & Technology Design Decisions Log (ADRs)
    # =========================================================================
    s43 = create_base_slide(
        prs, 43, "Architecture & Technology Design Decisions Log (ADRs) (Topic 29)",
        "Formal Architectural Decision Records documenting design choices, alternatives evaluated, and trade-off rationales",
        "Section 27: Architecture Decisions",
        {
            "logic": "Documenting design decisions and rejected alternatives provides transparency, defends architectural rigor, and prevents rework.",
            "designs": "Editable tabular ADR matrix detailing Decision ID, Architectural Topic, Selected Choice, Rejected Options, and Rationale.",
            "highlights": "Details rejection of single-pass extraction, local fine-tuning, third-party LLMs, and pure vector retrieval.",
            "details": "Aligns with enterprise architecture governance standards and ISO/IEC 42010 architectural documentation standards."
        }
    )
    add_table(s43, 0.8, 1.5, 11.7, 5.1,
        ["ADR #", "Architecture Topic", "Selected Decision", "Rejected Alternative(s)", "Key Justification & Trade-off Rationale"],
        [
            ["ADR-01", "Extraction Strategy", "Multi-Pass Pass-Aware Extraction", "Single-Pass Combined Prompt", "Single pass yields confident hallucinations on vague terms; multi-pass resolves edge cases reliably."],
            ["ADR-02", "OCR & Layout Engine", "Azure AI Doc Intelligence (Layout API)", "LLM Vision / Open-source Tesseract", "Prebuilt Layout recovers exact (x, y, w, h) coordinates and multi-page tables deterministically."],
            ["ADR-03", "Retrieval Architecture", "Hybrid Search (Vector + BM25)", "Pure Vector Similarity", "Legal phrasing relies on exact statutory terms that pure vector search frequently misses."],
            ["ADR-04", "Chunking Strategy", "Clause Boundary Chunking (512 tokens)", "Fixed Character Window (e.g. 1000 char)", "Splitting legal sentences across chunks destroys coordinate traceability and alters clause intent."],
            ["ADR-05", "Model Selection", "Azure OpenAI (GPT-4o / mini)", "Fine-Tuning Open Source / Third-Party", "Six categories with 600 contracts provide insufficient data for fine-tuning; prompt engineering wins."],
            ["ADR-06", "Model Decoupling", "Decoupled Extraction & Assessment Calls", "Single Monolithic Prompt", "Monolithic prompt prevents separating extraction errors from assessment reasoning failures in evals."],
            ["ADR-07", "Security & Keys", "Entra ID Managed Identities", "Shared API Keys in Config Files", "Eliminates credential rotation overhead; prevents accidental credential leaks in source code."]
        ],
        col_widths=[1.0, 2.0, 2.7, 2.6, 3.4]
    )

    # =========================================================================
    # SLIDE 44 (Topic 30): Program Risk, Issue, Mitigation & Action (RIMA) Matrix
    # =========================================================================
    s44 = create_base_slide(
        prs, 44, "Program Risk, Issue, Mitigation & Action (RIMA) Matrix (Topic 30)",
        "Comprehensive risk register analyzing schedule, technical, operational, and data risks with concrete mitigations",
        "Section 28: Risk Management",
        {
            "logic": "Proactive identification of program risks ensures delivery friction is anticipated, quantified, and systematically mitigated.",
            "designs": "Editable tabular risk matrix detailing Risk ID, Category, Description, Impact/Prob, Mitigation Strategy, and Action Owner.",
            "highlights": "Addresses SME availability bottlenecks, unstandardized contracts, Azure quota limits, and draft vs executed differences.",
            "details": "Assigns clear accountability to named program roles: AI Engineer, Legal SPOC, Cloud Engineer, and Delivery Lead."
        }
    )
    add_table(s44, 0.8, 1.5, 11.7, 5.1,
        ["Risk ID", "Risk Domain", "Risk Event Description", "Impact / Prob", "Mitigation Strategy & Preventive Action", "Action Owner"],
        [
            ["RSK-01", "Schedule", "Legal SME bandwidth constrained for workshops", "High / High", "Time-box workshops to 8 hrs/wk; pre-draft ontologies using TCS legal accelerators.", "Delivery Lead / SPOC"],
            ["RSK-02", "Technical", "Azure OpenAI TPM quota throttling in non-prod", "High / Medium", "Implement exponential backoff with jitter in Service Bus; request quota boost to 150k TPM.", "Cloud Engineer"],
            ["RSK-03", "Data Quality", "Provided contracts contain zero deviation examples", "High / Medium", "Enforce sample quota: minimum 15% negotiated/known-deviation contracts per category.", "Data Engineer"],
            ["RSK-04", "Scope Drift", "Clause checklists expand during active build", "Medium / High", "Freeze category clause checklist in Workshop 1; treat post-freeze additions as Phase 2 scope.", "AI Engineer"],
            ["RSK-05", "Governance", "Clauses superseded by amendments flagged as risk", "Medium / Medium", "Explicitly document standalone document assessment as known Phase 1 scope boundary.", "Responsible AI Spec"],
            ["RSK-06", "Integration", "Draft pre-signature contracts require tighter auth", "Medium / Low", "Document draft review requirements in target-state architecture for Phase 2 hardening.", "Fullstack Developer"]
        ],
        col_widths=[1.0, 1.4, 2.8, 1.4, 3.7, 1.4]
    )

    # =========================================================================
    # SLIDE 45 (Topic 31): Enterprise Best Practices Incorporated
    # =========================================================================
    s45 = create_base_slide(
        prs, 45, "Enterprise Best Practices Incorporated in the Solution (Topic 31)",
        "Architectural patterns ensuring the solution is auditable, reproducible, scalable, and grounded for enterprise deployment",
        "Section 29: Best Practices",
        {
            "logic": "Adherence to established cloud and AI best practices ensures the solution is robust, maintainable, and audit-ready from Day 1.",
            "designs": "Four best-practice pillar cards covering Correctness & Groundedness, Auditability, Operational Speed, and Right-Fit Sizing.",
            "highlights": "Incorporates 12-factor cloud-native design, immutable storage, decoupled queues, and deterministic labor baselines.",
            "details": "Every design decision prioritizes long-term enterprise maintainability over quick throwaway shortcuts."
        }
    )
    add_card(s45, 0.8, 1.5, 2.75, 5.1, "1. Correctness & Grounding", [
        "• Strict Deterministic Boundary: Layout and coordinate recovery performed strictly by deterministic OCR engines.",
        "• Multi-Pass Convergence: Isolates difficult edge cases into targeted passes, avoiding ungrounded single-pass guesses.",
        "• Schema Validation Gates: Pydantic models reject malformed LLM outputs; auto-retries on schema failure.",
        "• Groundedness Scoring: Azure AI evaluation harness verifies that findings directly cite source document words."
    ], header_color=BLUE_PRIMARY)

    add_card(s45, 3.8, 1.5, 2.75, 5.1, "2. Auditability & Provenance", [
        "• 100% Coordinate Citations: Every finding linked to page number and normalized (x, y, w, h) bounding box.",
        "• Complete Traceability: Records ModelId, PromptVersion, PassNumber, and ChunkID on every finding row.",
        "• Immutable WORM Storage: Raw source PDFs stored with Write-Once-Read-Many policies to prevent tampering.",
        "• Chronological Audit Logs: Logs every human review action, override, and approval with user UPN and timestamp."
    ], header_color=PURPLE_ACCENT)

    add_card(s45, 6.8, 1.5, 2.75, 5.1, "3. Operational Speed", [
        "• Asynchronous Queue Decoupling: Azure Service Bus buffers ingestion spikes without dropping requests or crashing.",
        "• Parallel Batch Processing: Container Apps scale dynamically to process hundreds of contracts concurrently.",
        "• Hybrid Search Indexing: Sub-150ms chunk retrieval via Azure AI Search combining BM25 keyword matching and vectors.",
        "• Instant Spreadsheet Export: Pre-compiled relational tables allow one-click export of 500+ contract registers in < 3 seconds."
    ], header_color=AMBER_WARN)

    add_card(s45, 9.8, 1.5, 2.75, 5.1, "4. Right-Fit Architecture", [
        "• Zero Vendor Bloat: Relies on native Azure PaaS without unnecessary third-party subscription overhead.",
        "• Managed Identity Everywhere: Eliminates credential rotation maintenance and shared secret leak vulnerabilities.",
        "• Pay-As-You-Go Scaling: Serverless containers and consumption functions ensure zero idle infrastructure costs.",
        "• Deterministic Cost Baseline: Sizing calibrated to $1.20 cloud cost/contract and $30/hr blended engineering labor."
    ], header_color=EMERALD_SUCCESS)

    prs.save("exports/PVR_INOX_TCS_Contract_Intelligence_Master_Deck.pptx")
    print("Checkpoint: Slides 34-45 successfully compiled.")
    return prs
