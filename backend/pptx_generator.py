import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from backend.models import BRDDocument

# 16:9 Widescreen dimensions
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Color Palette: Premium Enterprise Theme
COLOR_DARK_BG = RGBColor(15, 23, 42)       # Slate 900
COLOR_LIGHT_BG = RGBColor(248, 250, 252)   # Slate 50
COLOR_CARD_BG = RGBColor(255, 255, 255)
COLOR_CARD_DARK = RGBColor(30, 41, 59)     # Slate 800
COLOR_PRIMARY = RGBColor(37, 99, 235)      # Blue 600
COLOR_ACCENT = RGBColor(14, 165, 233)      # Sky 500
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)
COLOR_TEXT_LIGHT = RGBColor(241, 245, 249)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUCCESS = RGBColor(16, 185, 129)     # Emerald 500
COLOR_WARNING = RGBColor(245, 158, 11)     # Amber 500
COLOR_BORDER = RGBColor(226, 232, 240)

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header_footer(slide, brd: BRDDocument, slide_num: int, total_slides: int, is_dark: bool = False):
    # Header area: Top Right slide number
    txBox = slide.shapes.add_textbox(Inches(10.5), Inches(0.4), Inches(2.3), Inches(0.4))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    p.text = f"SLIDE {slide_num:02d} / {total_slides:02d}"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT if is_dark else COLOR_TEXT_MUTED

    # Footer area: Center aligned text
    footer_text = f"{brd.client_name} × TCS  |  {brd.project_title}  |  TCS Confidential"
    foot_box = slide.shapes.add_textbox(Inches(2.5), Inches(6.9), Inches(8.333), Inches(0.4))
    ftf = foot_box.text_frame
    fp = ftf.paragraphs[0]
    fp.alignment = PP_ALIGN.CENTER
    fp.text = footer_text
    fp.font.size = Pt(9)
    fp.font.color.rgb = RGBColor(148, 163, 184) if is_dark else COLOR_TEXT_MUTED

    # Left Footer Branding text: TCS
    tcs_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(1.8), Inches(0.4))
    tcs_tf = tcs_box.text_frame
    tp = tcs_tf.paragraphs[0]
    tp.text = "TATA CONSULTANCY SERVICES"
    tp.font.size = Pt(9)
    tp.font.bold = True
    tp.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_MAIN

    # Right Footer Branding text: TATA
    tata_box = slide.shapes.add_textbox(Inches(11.2), Inches(6.9), Inches(1.5), Inches(0.4))
    tata_tf = tata_box.text_frame
    tata_p = tata_tf.paragraphs[0]
    tata_p.alignment = PP_ALIGN.RIGHT
    tata_p.text = "TATA"
    tata_p.font.size = Pt(10)
    tata_p.font.bold = True
    tata_p.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_MAIN

def add_slide_title(slide, title: str, subtitle: str = "", is_dark: bool = False):
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(9.5), Inches(1.0))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_MAIN
    
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(12)
        p2.font.color.rgb = COLOR_ACCENT if is_dark else COLOR_PRIMARY

def add_card(slide, left: float, top: float, width: float, height: float, title: str, bullets: list, is_dark: bool = False, title_color=None):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_DARK if is_dark else COLOR_CARD_BG
    card.line.color.rgb = RGBColor(51, 65, 85) if is_dark else COLOR_BORDER
    card.line.width = Pt(1)

    tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.2), Inches(width - 0.4), Inches(height - 0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = title_color if title_color else (COLOR_ACCENT if is_dark else COLOR_PRIMARY)
    p0.space_after = Pt(6)
    
    for bullet in bullets:
        p = tf.add_paragraph()
        p.text = f"• {bullet}" if not bullet.startswith("•") else bullet
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_LIGHT if is_dark else COLOR_TEXT_MAIN
        p.space_after = Pt(3)

def add_table_slide(slide, left: float, top: float, width: float, height: float, headers: list, rows: list, is_dark: bool = False):
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = table_shape.table

    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = str(header)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY if not is_dark else COLOR_CARD_DARK
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(10)
            p.font.color.rgb = COLOR_WHITE

    for row_idx, row in enumerate(rows):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(val)
            cell.fill.solid()
            if (row_idx % 2 == 0):
                cell.fill.fore_color.rgb = COLOR_WHITE if not is_dark else RGBColor(30, 41, 59)
            else:
                cell.fill.fore_color.rgb = RGBColor(241, 245, 249) if not is_dark else RGBColor(15, 23, 42)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(9)
                p.font.color.rgb = COLOR_TEXT_MAIN if not is_dark else COLOR_TEXT_LIGHT

def set_presenter_notes(slide, logic: str, design: str, highlights: str, details: str):
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = (
        f"[PRESENTER NOTES]\n\n"
        f"WHY (Business Logic):\n{logic}\n\n"
        f"WHAT (Design & Architecture):\n{design}\n\n"
        f"KEY HIGHLIGHTS:\n{highlights}\n\n"
        f"FULL DETAILS:\n{details}"
    )

def create_presentation_deck(brd: BRDDocument, output_path: str) -> str:
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    blank_layout = prs.slide_layouts[6]
    TOTAL_SLIDES = 42

    cur = 1

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide (Dark Theme)
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_DARK_BG)
    add_header_footer(s1, brd, cur, TOTAL_SLIDES, is_dark=True)
    
    title_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(3.5))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    
    p_tag = tf1.paragraphs[0]
    p_tag.text = f"PRODUCTION-GRADE ARCHITECTURE & DELIVERY BLUEPRINT  |  {brd.delivery_tier.upper()}"
    p_tag.font.size = Pt(13)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_ACCENT
    
    p_title = tf1.add_paragraph()
    p_title.text = brd.project_title
    p_title.font.size = Pt(30)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.space_after = Pt(12)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = f"Prepared for: {brd.client_name}  •  Platform: {brd.cloud_platform}  •  Duration: {brd.total_duration_weeks:.1f} Weeks  •  Effort: {brd.total_person_days:.1f} d (${brd.total_labour_cost_usd:,.2f} @ $30/hr)"
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)
    
    set_presenter_notes(
        s1,
        logic="Establishes commercial, architectural, and governance baseline for executive leadership.",
        design="Executive dark-theme title slide with structured 16:9 widescreen layout and TCS/Tata branding.",
        highlights=f"Initiative: {brd.project_title} | Tier: {brd.delivery_tier} | Blended Cost: ${brd.total_labour_cost_usd:,.2f}.",
        details="Engineered across 18 deterministic WBS phases and 12-discipline staffing loaded at standard $30.00/hr blended rate."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement & Business Impacts (Item 1)
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_header_footer(s2, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s2, "1. Problem Statement & Measurable Business Impacts", "Bridging operational bottlenecks with governed enterprise automation")
    
    add_card(s2, 0.8, 1.8, 5.6, 4.8, "Current Operational Challenges", [
        f"Core Problem: {brd.problem_statement}",
        "High Cognitive Overhead: Manual parsing of complex clauses creates multi-day backlogs.",
        "Audit Trail Gaps: Review records scattered across informal channels without clause-coordinate lineage.",
        "Inconsistent Policy Catch: Uncaught standard deviations increase regulatory exposure."
    ])
    add_card(s2, 6.8, 1.8, 5.7, 4.8, "Quantified Business Impacts & Target Value", brd.business_impacts)
    set_presenter_notes(
        s2,
        logic="Defines the operational problem and target ROI drivers justifying initiative investment.",
        design="Side-by-side comparative layout contrasting pain points against target KPI improvements.",
        highlights="Reduces cycle times from days to sub-90s with 100% deterministic calculation auditability.",
        details="Establishes business baseline for subsequent functional and technical component mapping."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 3: As-Is Process & Key Pain Points (Item 2)
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_header_footer(s3, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s3, "2. As-Is Process Flow & Operational Pain Points", "Current sequential workflow friction and vulnerability analysis")
    
    add_card(s3, 0.8, 1.8, 3.7, 4.8, "1. Ingestion & Pre-Check", [
        "Manual email/folder intake",
        "No automated file type validation",
        "Unindexed document repositories",
        "High triage latency (>24 hrs)"
    ])
    add_card(s3, 4.8, 1.8, 3.7, 4.8, "2. Domain Review & Extraction", [
        "Manual clause-by-clause reading",
        "Spreadsheet-based note taking",
        "Inconsistent risk tagging",
        "Zero automated cross-reference"
    ])
    add_card(s3, 8.8, 1.8, 3.7, 4.8, "3. Approval & Storage", [
        "Email approval chains",
        "No immutable audit logs",
        "Lack of centralized KPI telemetry",
        "Elevated compliance vulnerability"
    ])
    set_presenter_notes(
        s3,
        logic="Identifies friction points in the existing manual lifecycle to motivate automation.",
        design="Three-stage process column layout mapping ingestion, analysis, and sign-off friction.",
        highlights="Identifies 3 major operational chokepoints causing >70% of project review delays.",
        details="Forms baseline for the To-Be process re-engineering and agentic intervention mapping."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 4: Solution Overview & Deliverables (Item 3)
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_header_footer(s4, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s4, "3. Solution Overview & Target Deliverables", "Target operating model delivering grounded intelligence at scale")
    
    add_card(s4, 0.8, 1.8, 5.6, 4.8, "Core Solution Capabilities", [
        "Zero-Click Intelligent Document Ingestion: Automated OCR, chunking & vector indexing.",
        "Multi-Pass Clause Reasoning: Dual-pass extraction for deterministic vs ambiguous clause evaluation.",
        "Clause Coordinate Traceability: Exact bounding box & paragraph coordinates for all extractions.",
        "Immutable Audit Ledger: Every calculation, parameter change, and gate sign-off tracked."
    ])
    add_card(s4, 6.8, 1.8, 5.7, 4.8, f"Key Deliverables for {brd.delivery_tier.upper()}", brd.in_scope[:6])
    set_presenter_notes(
        s4,
        logic="Articulates the solution vision and concrete deliverables for the current project tier.",
        design="Dual capability-and-deliverables card structure aligned with client SOW objectives.",
        highlights="Delivers production-grade cloud services, UI cockpit, and automated verification suites.",
        details="Aligned with strict tier boundaries and $30/hr resource estimates."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 5: AI vs Non-AI Interventions (Item 4)
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_LIGHT_BG)
    add_header_footer(s5, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s5, "4. Architectural Demarcation: AI vs. Non-AI Interventions", "Strict separation ensuring deterministic computing handles logic, math & persistence")
    
    add_card(s5, 0.8, 1.8, 5.6, 4.8, "🤖 AI Agent Interventions (Probabilistic)", [
        "Clause Semantic Reasoning & Context Extraction",
        "Ambiguity Resolution & Qualitative Risk Scoring",
        "Executive Summary & Business Narrative Synthesis",
        "User Query Intent Classification & Agent Routing",
        "KPI: Extraction Precision > 96.5%, Groundedness > 0.94"
    ], title_color=COLOR_PRIMARY)
    add_card(s5, 6.8, 1.8, 5.7, 4.8, "⚙️ Non-AI Deterministic Services (Code/Rules)", [
        "Deterministic Effort, Financial & BoM Calculation Engines",
        "Document Parsing, Token Splitting & Hash Deduplication",
        "PostgreSQL / Azure SQL Transactional Ledger State Persistence",
        "Role-Based Access Control (RBAC) & OAuth 2.0 Auth Gateways",
        "KPI: Zero calculation hallucination, 100% mathematical auditability"
    ], title_color=COLOR_SUCCESS)
    set_presenter_notes(
        s5,
        logic="Enforces architectural hygiene: LLMs are never used for mathematical calculations or transactional storage.",
        design="High-contrast dual categorization isolating probabilistic agent tasks from deterministic code.",
        highlights="Guarantees 100% reproducible math via Python formulas while leveraging LLMs for qualitative synthesis.",
        details="Satisfies architectural governance guardrails forbidding hallucinated estimates."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 6: To-Be End-to-End Process Flow (Item 5)
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_header_footer(s6, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s6, "5. To-Be Process Flow & Functional Components", "Continuous automated pipeline with human-in-the-loop oversight")
    
    add_card(s6, 0.8, 1.8, 2.7, 4.8, "1. Ingest & Tokenize", [
        "Upload via UI Cockpit",
        "File hash validation",
        "Azure Blob landing",
        "PyPDF/Docx chunking"
    ])
    add_card(s6, 3.8, 1.8, 2.7, 4.8, "2. Embed & Index", [
        "Text-embedding-3-large",
        "Azure AI Search index",
        "HNSW vector indexing",
        "Hybrid search filter"
    ])
    add_card(s6, 6.8, 1.8, 2.7, 4.8, "3. Multi-Pass Eval", [
        "Pass 1: Explicit terms",
        "Pass 2: Ambiguous terms",
        "Coordinate mapping",
        "Guardrail safety filter"
    ])
    add_card(s6, 9.8, 1.8, 2.7, 4.8, "4. Gate & Export", [
        "4-Gate HITL Sign-off",
        "Ledger calculation log",
        "Word / PDF generation",
        "Jira CSV export"
    ])
    set_presenter_notes(
        s6,
        logic="Establishes the sequential operational pipeline from document ingestion to executive export.",
        design="Four-stage linear workflow card architecture illustrating component transitions.",
        highlights="Incorporates human validation gates before document locking and downstream export.",
        details="Covers complete ingestion, RAG indexing, reasoning, and multi-format compilation."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 7: Business & Operational KPIs (Item 7)
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_LIGHT_BG)
    add_header_footer(s7, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s7, "7. Business & Operational KPI Register", "Formal measurement framework, formulas, and target thresholds")
    
    kpi_headers = ["KPI Name", "Type", "Formula / Measurement", "Target", "Prerequisites"]
    kpi_rows = [
        ["Review Latency", "Operational", "Time(Upload) to Time(Extraction_Done)", "< 90 Seconds", "Digital Text Available"],
        ["Deflection Rate", "Business", "(Auto_Processed_Docs / Total_Docs) * 100", "> 85.0%", "Standard Template Match"],
        ["Extraction Precision", "AI Quality", "(True_Positives / (TP + FP))", "> 96.5%", "High-Res OCR Enabled"],
        ["Grounding Accuracy", "Governance", "(Citation_Match_Count / Total_Citations)", "> 98.0%", "Vector Chunk Linkage"],
        ["Cost per Review", "Financial", "(Cloud_Run_Cost + Labour_Cost) / Doc_Count", "< $1.20 / Doc", "Pay-as-you-go Optimal"]
    ]
    add_table_slide(s7, 0.8, 1.8, 11.7, 4.8, kpi_headers, kpi_rows)
    set_presenter_notes(
        s7,
        logic="Provides measurable SLAs for business value verification post-implementation.",
        design="Structured tabular KPI register covering formulaic definitions, thresholds, and prerequisites.",
        highlights="Targets 85% triage deflection with <90s average processing speed.",
        details="Measures will be integrated into continuous production observability dashboards."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 8: Production Grade Technical Architecture (Item 8)
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_LIGHT_BG)
    add_header_footer(s8, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s8, "8. Production-Grade Technical Component Architecture", "Azure cloud-native enterprise architecture topology")
    
    add_card(s8, 0.8, 1.8, 3.7, 4.8, "Client & Presentation Layer", [
        "🌐 Modern Web Cockpit (HTML5/CSS3/Vanilla JS)",
        "🔐 Azure Entra ID SSO (OIDC/SAML 2.0)",
        "🛡️ Azure Front Door / Application Gateway",
        "📊 Dynamic Workbench & Audit Ledger UI"
    ])
    add_card(s8, 4.8, 1.8, 3.7, 4.8, "Application & Agent Orchestration", [
        "⚡ Azure Container Apps / FastAPI Backend",
        "🧠 Azure AI Foundry / Semantic Kernel Agents",
        "🔍 Azure AI Search (Vector + BM25 Hybrid)",
        "🛡️ Azure AI Content Safety Guardrails"
    ])
    add_card(s8, 8.8, 1.8, 3.7, 4.8, "Persistence, State & Security", [
        "🗄️ Azure Database for PostgreSQL (Flexible)",
        "📦 Azure Blob Storage (Encrypted at Rest)",
        "🔑 Azure Key Vault (Managed Identities)",
        "📈 Azure Monitor & Application Insights"
    ])
    set_presenter_notes(
        s8,
        logic="Defines the physical multi-tier cloud topology ensuring scalability, resilience, and security.",
        design="3-Tier enterprise architecture diagram separating Presentation, Orchestration, and Data tiers.",
        highlights="Uses native Azure managed services with zero public endpoints on backend databases.",
        details="Fully compliant with enterprise IAM, TLS 1.3, and CMEK storage standards."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 9: Architectural Layer Boundaries & Demarcation (Item 9a)
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_LIGHT_BG)
    add_header_footer(s9, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s9, "9a. Layer Boundaries: Virtual Server vs. Agentic Framework vs. Serverless", "Clear runtime segregation and numbered execution dataflow")
    
    add_card(s9, 0.8, 1.8, 3.7, 4.8, "1. Virtual Server / Dedicated Compute", [
        "Azure App Service / VM Dedicated Hosts",
        "Continuous WebSocket / Long-Polling",
        "Batch Processing & Local File Cache",
        "Boundary: High-throughput ingestion daemon"
    ], title_color=COLOR_PRIMARY)
    add_card(s9, 4.8, 1.8, 3.7, 4.8, "2. Agentic AI Frameworks", [
        "Azure AI Foundry & Semantic Kernel",
        "Multi-Agent Prompt Routing & Reasoning",
        "Grounding Engine & Context Injection",
        "Boundary: Probabilistic text comprehension"
    ], title_color=COLOR_ACCENT)
    add_card(s9, 8.8, 1.8, 3.7, 4.8, "3. Serverless Containers & FaaS", [
        "Azure Functions (Event-Driven Triggers)",
        "Azure Container Apps (Microservices)",
        "Deterministic Calc Engine & Exporters",
        "Boundary: Stateless scale-to-zero compute"
    ], title_color=COLOR_SUCCESS)
    set_presenter_notes(
        s9,
        logic="Mandates strict architectural segregation between dedicated hosts, agentic orchestrators, and serverless compute.",
        design="Tri-part boundary diagram showing isolation zones and inter-tier communication contracts.",
        highlights="Serverless containers handle stateless calculations; Agentic framework manages reasoning.",
        details="Ensures cost-optimal scaling without over-provisioning expensive GPU/VM resources."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 10: Multi-Environment Deployment Architecture (Item 10)
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_LIGHT_BG)
    add_header_footer(s10, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s10, "10. Multi-Environment Deployment Topology", "Isolated lifecycle progression across Dev, SIT, UAT, and Production")
    
    add_card(s10, 0.8, 1.8, 2.7, 4.8, "DEV Environment", [
        "Shared Resource Group",
        "Pay-As-You-Go SKU",
        "Mock external services",
        "CI auto-deploy on PR"
    ])
    add_card(s10, 3.8, 1.8, 2.7, 4.8, "SIT Environment", [
        "Integrated Test RG",
        "Full Azure AI Search",
        "Synthetic test suites",
        "Automated regression"
    ])
    add_card(s10, 6.8, 1.8, 2.7, 4.8, "UAT Environment", [
        "Dedicated Subscription",
        "Anonymized Client Data",
        "4-Gate HITL Sign-off",
        "Security pen-testing"
    ])
    add_card(s10, 9.8, 1.8, 2.7, 4.8, "PRODUCTION", [
        "Zone-Redundant HA",
        "Dedicated App Service",
        "Azure Front Door WAF",
        "24x7 Monitor Alerts"
    ])
    set_presenter_notes(
        s10,
        logic="Guarantees progressive promotion and risk isolation across enterprise lifecycle stages.",
        design="Four-column deployment matrix detailing infrastructure configuration per tier.",
        highlights="Production is fully isolated in dedicated subscription with zone redundancy.",
        details="CI/CD pipelines enforce automated gating tests before promotion."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 11: Intervention Deep-Dive (Item 12)
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, COLOR_LIGHT_BG)
    add_header_footer(s11, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s11, "12. Intervention-Wise Technical Implementation", "Detailed I/O, mechanics, and business benefits for core services")
    
    add_card(s11, 0.8, 1.8, 5.6, 4.8, "Intervention 1: Multi-Pass Evaluation", [
        "Input: Extracted document chunks + Contract Policy Rules",
        "Tech: Azure AI Search hybrid retrieval + GPT-4o reasoning",
        "Mechanics: Pass 1 explicit matching; Pass 2 ambiguous scoring",
        "Output: JSON extraction array with coordinate citations",
        "Benefit: 96.5% precision; eliminates manual cross-referencing"
    ])
    add_card(s11, 6.8, 1.8, 5.7, 4.8, "Intervention 2: Deterministic Impact Simulation", [
        "Input: Target parameter delta (Duration, Scale, Users)",
        "Tech: Pure Python deterministic math engine (No LLM)",
        "Mechanics: Formulaic re-calculation across 18 WBS phases",
        "Output: Side-by-side scenario diff & financial impact",
        "Benefit: 100% reproducible estimates; zero financial hallucination"
    ])
    set_presenter_notes(
        s11,
        logic="Explains the exact mechanics of critical solution interventions and their tangible returns.",
        design="Dual deep-dive cards contrasting AI evaluation with deterministic calculation engines.",
        highlights="Demonstrates end-to-end traceability from input through technical execution to output.",
        details="Includes business benefits and operational metrics for each intervention."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 12: End-to-End Numbered Data Flow (Item 13)
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, COLOR_LIGHT_BG)
    add_header_footer(s12, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s12, "13. End-to-End Numbered Data Flow Diagram", "Sequential data progression from UI trigger to audit persistence")
    
    add_card(s12, 0.8, 1.8, 5.6, 4.8, "Data Ingestion & Indexing Flow", [
        "1. User initiates upload in UI Cockpit via HTTPS POST",
        "2. Azure Front Door inspects WAF rules & routes to FastAPI",
        "3. FastAPI stores raw document in Azure Blob Storage",
        "4. Ingestion worker extracts text & metadata tokens",
        "5. Embeddings generated via text-embedding-3-large",
        "6. Vectors & chunks indexed into Azure AI Search"
    ])
    add_card(s12, 6.8, 1.8, 5.7, 4.8, "Reasoning & Audit Persistence Flow", [
        "7. Client request triggers Semantic Kernel orchestrator",
        "8. Hybrid search queries top-k relevant vector chunks",
        "9. Content Safety Guardrail filters input prompts",
        "10. Azure OpenAI synthesizes clause analysis with citations",
        "11. Deterministic Calculation Engine logs math to Ledger",
        "12. Final result committed to PostgreSQL & returned to UI"
    ])
    set_presenter_notes(
        s12,
        logic="Provides a numbered step-by-step trace of every data object as it traverses the system.",
        design="Dual-column 12-step sequential numbered execution path.",
        highlights="Every step is explicitly numbered from 1 to 12 for developer clarity.",
        details="Enforces full encryption in transit (TLS 1.3) and at rest across all touchpoints."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 13: Technical Component Register (Item 14)
    # -------------------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, COLOR_LIGHT_BG)
    add_header_footer(s13, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s13, "14. Technical Component Register", "Comprehensive catalog of components, types, and integrations")
    
    comp_headers = ["ID", "Component Name", "Type", "Technology Choice", "Primary Responsibility"]
    comp_rows = [
        [c.id, c.name, c.type, c.technology_choice, c.purpose[:45] + "..."]
        for c in (brd.technical_components or [])[:5]
    ] if brd.technical_components else [
        ["C001", "Client Cockpit UI", "Frontend", "HTML5 / Vanilla JS", "Interactive discovery & workbench"],
        ["C002", "API Gateway & Router", "Backend", "FastAPI / Container Apps", "REST API & Session Management"],
        ["C003", "RAG & Vector Search", "Search", "Azure AI Search", "Hybrid vector indexing & retrieval"],
        ["C004", "Reasoning Orchestrator", "AI Agent", "Azure OpenAI GPT-4o", "Multi-pass clause extraction"],
        ["C005", "Calculation Ledger", "Engine", "Python Deterministic Math", "WBS & Financial calculation log"]
    ]
    add_table_slide(s13, 0.8, 1.8, 11.7, 4.8, comp_headers, comp_rows)
    set_presenter_notes(
        s13,
        logic="Serves as the master inventory of all software and infrastructure components.",
        design="Structured tabular register defining component IDs, technology selections, and roles.",
        highlights="6 core components provide complete modularity and separation of concerns.",
        details="Enables clear role assignment across the 12-discipline engineering team."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 14: UI Screen Envisioning (Item 15)
    # -------------------------------------------------------------
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, COLOR_LIGHT_BG)
    add_header_footer(s14, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s14, "15. User Interface & Menu Hierarchy", "Cockpit menu navigation and tier-wise feature enablement")
    
    add_card(s14, 0.8, 1.8, 3.7, 4.8, "Sidebar Navigation (Left)", [
        "📂 Project Workspaces & History",
        "📄 BRD Executive Document View",
        "👥 12-Discipline Resource Plan",
        "📊 18-Phase Roadmap & Timeline",
        "📅 Day-Wise Master Execution Plan",
        "🛡️ Enterprise Admin Console"
    ])
    add_card(s14, 4.8, 1.8, 3.7, 4.8, "Discovery Area (Center)", [
        "💬 Interactive Conversational Chat",
        "⚡ 0-Click RFP/SOW File Ingestion",
        "🎯 Adaptive Parameter Questioning",
        "✏️ Inline Q&A Response Editor",
        "🔄 Session Reset & Quick Prompts"
    ])
    add_card(s14, 8.8, 1.8, 3.7, 4.8, "Workbench & FinOps (Right)", [
        "📈 Delivery Tier & Sizing Bar",
        "☁️ 3-Year Cumulative TCO Model",
        "💳 Pay-As-You-Go vs PTU Sizing",
        "📋 17 Canonical Requirements Grid",
        "⚡ Interactive Impact Simulator",
        "📦 Multi-Format Export Suite"
    ])
    set_presenter_notes(
        s14,
        logic="Maps out the information architecture and cockpit UX for solution architects and executives.",
        design="Three-column layout reflecting the 3-panel widescreen UI cockpit design.",
        highlights="Enables frictionless discovery on the left with live financial visualization on the right.",
        details="Supports responsive resizing and dark/light mode switching."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 15: 18-Phase WBS & Resource Loading (Item 17, 32)
    # -------------------------------------------------------------
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, COLOR_LIGHT_BG)
    add_header_footer(s15, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s15, "17. 18-Phase Project Roadmap & 12-Role Loading", f"Deterministic effort allocation for {brd.delivery_tier} tier (${brd.total_labour_cost_usd:,.2f} @ $30/hr)")
    
    phase_headers = ["Phase Code & Name", "Weeks", "Effort (d)", "Primary Role", "Key Deliverable"]
    phase_rows = [
        [p.phase_name[:24], f"{p.weeks:.1f} wks", f"{p.effort_days:.1f} d", "AI / Fullstack", p.key_deliverables[0][:30] if p.key_deliverables else "Milestone"]
        for p in (brd.project_phases or [])[:6]
    ] if brd.project_phases else [
        ["P01: Foundation & Framing", "0.5 wks", "8.5 d", "Solution Architect", "Project Charter & Governance"],
        ["P02: Requirements & MoSCoW", "0.5 wks", "9.2 d", "Business Analyst", "17 Canonical Requirements"],
        ["P03: Data Profiling & Prep", "0.8 wks", "14.1 d", "Data Engineer", "Ingestion & Schema Pipeline"],
        ["P04: Architecture Spec", "0.6 wks", "10.4 d", "Cloud Engineer", "Azure Landing Zone Spec"],
        ["P05: Cloud Deployment", "0.8 wks", "13.6 d", "Cloud Engineer", "Terraform Infrastructure"],
        ["P06: RAG Vector Indexing", "0.7 wks", "12.0 d", "AI Engineer", "Azure AI Search Index"]
    ]
    add_table_slide(s15, 0.8, 1.8, 11.7, 4.8, phase_headers, phase_rows)
    set_presenter_notes(
        s15,
        logic="Proves deterministic effort calculations backed by the 18-phase work breakdown structure.",
        design="Tabular WBS matrix showing exact phase durations, person-days, roles, and milestones.",
        highlights=f"Total Project Effort: {brd.total_person_days:.1f} Days across {brd.total_duration_weeks:.1f} Weeks.",
        details="Calculated with standard $30.00/hour blended rate across all 12 discipline roles."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 16: Guardrails & Responsible AI Configuration (Item 21)
    # -------------------------------------------------------------
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, COLOR_LIGHT_BG)
    add_header_footer(s16, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s16, "21. Guardrails & Responsible AI Framework", "EU AI Act (Article 50) and ISO/IEC 42001:2023 AIMS compliance")
    
    add_card(s16, 0.8, 1.8, 5.6, 4.8, "EU AI Act Compliance (Specific Transparency)", [
        "Classification: Article 50 Transparency Risk Tier",
        "Mandatory AI Watermarking & User Disclosure Notices",
        "Human-in-the-Loop Review Controls before document finalization",
        "Clause Coordinate Audit Trails logged for regulatory compliance",
        "Complete segregation of tenant data (Zero LLM training on customer IP)"
    ])
    add_card(s16, 6.8, 1.8, 5.7, 4.8, "ISO/IEC 42001:2023 AIMS Controls", [
        "A.5 AI Policy: Formal corporate responsible AI operational policy",
        "A.6 Internal Organization: Clear RACI for AI risk and ethics",
        "A.7 Resource Management: Data provenance & training curation",
        "A.8 AI Impact Assessment: Continuous bias, drift & toxicity testing",
        "A.9 Third-Party Governance: Vendor LLM SLA and security audits"
    ])
    set_presenter_notes(
        s16,
        logic="Establishes regulatory compliance and ethical safety guardrails for enterprise deployment.",
        design="Dual regulatory framework cards mapping EU AI Act mandates and ISO 42001 controls.",
        highlights="Guarantees Article 50 transparency compliance and ISO 42001 lifecycle certification.",
        details="Enforced via automated guardrail middleware in the API gateway."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 17: Database Schema Architecture (Item 22)
    # -------------------------------------------------------------
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, COLOR_LIGHT_BG)
    add_header_footer(s17, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s17, "22. Database Schema & Data Models", "Relational & vector schema designs for PostgreSQL / Azure SQL")
    
    schema_headers = ["Table Name", "Primary Key", "Foreign Keys", "Key Attributes", "Indexing Strategy"]
    schema_rows = [
        ["sessions", "session_id (UUID)", "-", "client_name, tier, created_at, status", "BTREE(created_at)"],
        ["answers", "answer_id (UUID)", "session_id", "question_id, answer_text, is_default", "BTREE(session_id, question_id)"],
        ["requirements", "req_id (VARCHAR)", "session_id", "statement, actor, moscow, priority", "BTREE(session_id, moscow)"],
        ["calculation_ledger", "calc_id (VARCHAR)", "session_id", "calc_type, formula, result_json, ts", "BTREE(session_id, ts)"],
        ["vector_chunks", "chunk_id (UUID)", "doc_id", "chunk_text, embedding, page_num", "HNSW Index (Cosine)"]
    ]
    add_table_slide(s17, 0.8, 1.8, 11.7, 4.8, schema_headers, schema_rows)
    set_presenter_notes(
        s17,
        logic="Defines the relational and vector data structures required for persistence and high-speed search.",
        design="Tabular DDL schema overview specifying PKs, FKs, attributes, and index strategies.",
        highlights="Includes dedicated tables for calculation ledgers, requirements, and vector chunks.",
        details="Optimized for sub-10ms transactional lookups and cosine similarity vector retrieval."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 18: API Endpoints & Interface Contracts (Item 23)
    # -------------------------------------------------------------
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, COLOR_LIGHT_BG)
    add_header_footer(s18, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s18, "23. API Endpoints & Interface Specifications", "RESTful contract definitions for internal and external service communication")
    
    api_headers = ["Method & Path", "Request Body", "Response Model", "Auth / Scope", "Purpose"]
    api_rows = [
        ["POST /api/chat", "{ session_id, message }", "{ status, response, answers }", "Bearer Token", "Conversational discovery processing"],
        ["POST /api/generate-brd", "{ session_id }", "{ status, brd_document }", "Bearer Token", "Synthesize executive BRD & financials"],
        ["POST /api/impact-analysis", "{ session_id, param, val }", "{ diff, variance, affected }", "Bearer Token", "Simulate parameter change impact"],
        ["POST /api/impact-analysis/commit", "{ session_id, param, val }", "{ status, updated_brd }", "Admin Scope", "Commit simulation to active baseline"],
        ["GET /api/export/word", "Query: ?session_id=...", "Binary (.docx)", "Bearer Token", "Export formal styled Word document"]
    ]
    add_table_slide(s18, 0.8, 1.8, 11.7, 4.8, api_headers, api_rows)
    set_presenter_notes(
        s18,
        logic="Standardizes system interfaces to enable clean integration with enterprise frontends and external CI/CD.",
        design="Tabular REST API register with HTTP methods, schemas, authentication, and purpose.",
        highlights="Fully authenticated via OAuth 2.0 / Bearer tokens with strict schema validation.",
        details="Complies with OpenAPI 3.1 specifications."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 19: Key Evaluation Checkpoints (Item 24)
    # -------------------------------------------------------------
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19, COLOR_LIGHT_BG)
    add_header_footer(s19, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s19, "24. Evaluation Framework & Quality Checkpoints", "Systematic evaluation verifying groundedness, relevance, and safety")
    
    add_card(s19, 0.8, 1.8, 5.6, 4.8, "RAG Triad & Quality Checkpoints", [
        "1. Context Relevance: Verifies retrieved chunks contain necessary info (>0.92)",
        "2. Groundedness: Measures output statements substantiated by context (>0.96)",
        "3. Answer Relevance: Assesses response directly answers user query (>0.94)",
        "4. Exact Numeric Precision: 100% check ensuring math matches ledger formula"
    ])
    add_card(s19, 6.8, 1.8, 5.7, 4.8, "Automated Safety & Latency Checkpoints", [
        "5. Toxicity & Hate Filter: Zero-tolerance threshold via Azure Content Safety",
        "6. PII Redaction Audit: Regex + NLP scrubber for email, SSN, PAN, credit cards",
        "7. Latency SLA Gate: Sub-90s end-to-end processing verification",
        "8. Token Budget Gate: Alert when document processing exceeds 35k tokens"
    ])
    set_presenter_notes(
        s19,
        logic="Establishes rigorous mathematical and qualitative evaluation metrics to prevent model drift.",
        design="Dual checkpoint card layout separating RAG triad metrics from security/latency SLAs.",
        highlights="Enforces automated RAG triad scoring with strict groundedness thresholds (>0.96).",
        details="Runs automatically in CI/CD before deployment promotions."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 20: Test Plan & Quality Assurance (Item 25)
    # -------------------------------------------------------------
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20, COLOR_LIGHT_BG)
    add_header_footer(s20, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s20, "25. Comprehensive Test Plan & Strategy", "Multi-layered verification across functional, load, and security testing")
    
    add_card(s20, 0.8, 1.8, 3.7, 4.8, "1. Unit & Functional Tests", [
        "Pytest test suite (100% calc coverage)",
        "Parser truncation & delimiter tests",
        "FastAPI endpoint response validation",
        "State transition validation tests"
    ])
    add_card(s20, 4.8, 1.8, 3.7, 4.8, "2. Integration & Load Tests", [
        "Azure AI Search integration tests",
        "Locust load testing (50 concurrent users)",
        "Database connection pool stress test",
        "Blob storage upload timeout resilience"
    ])
    add_card(s20, 8.8, 1.8, 3.7, 4.8, "3. Security & Red Teaming", [
        "Prompt injection & jailbreak red-teaming",
        "OWASP Top 10 API vulnerability scan",
        "Entra ID RBAC token expiry verification",
        "Data at rest & transit encryption audit"
    ])
    set_presenter_notes(
        s20,
        logic="Details the testing methodology ensuring software reliability, security, and peak load resilience.",
        design="Three-pillar test strategy covering functional, performance, and adversarial security testing.",
        highlights="Includes automated red-teaming for prompt injection and OWASP Top 10 compliance.",
        details="Executed in SIT and UAT environments before production sign-off."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 21: CXO Pitch & Executive Value Proposition (Item 28)
    # -------------------------------------------------------------
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21, COLOR_DARK_BG)
    add_header_footer(s21, brd, cur, TOTAL_SLIDES, is_dark=True)
    add_slide_title(s21, "28. Executive Pitch & Strategic Value Proposition", "Why leadership chooses this solution: Differentiators, speed, and ROI", is_dark=True)
    
    add_card(s21, 0.8, 1.8, 3.7, 4.8, "🚀 Speed to Value", [
        "From weeks to seconds per review",
        "Accelerates time-to-market by 4.2x",
        "Pre-built 18-phase delivery blueprint",
        "Rapid PoC-to-Production trajectory"
    ], is_dark=True)
    add_card(s21, 4.8, 1.8, 3.7, 4.8, "🛡️ Enterprise Trust", [
        "100% deterministic calculation math",
        "Zero hallucination risk on financials",
        "EU AI Act & ISO 42001 built-in",
        "Immutable audit trails for compliance"
    ], is_dark=True)
    add_card(s21, 8.8, 1.8, 3.7, 4.8, "💰 Proven Financial ROI", [
        "Standardized $30.00/hr blended labour",
        "Pay-as-you-go FinOps optimization",
        "Break-even achieved by Month 14",
        "46.5% savings vs over-provisioned PTU"
    ], is_dark=True)
    set_presenter_notes(
        s21,
        logic="Empowers CXO decision-makers with compelling business value, cost advantages, and risk mitigation.",
        design="Dark-mode executive pitch slide with 3 high-impact strategic pillars.",
        highlights="Delivers 4.2x faster turnaround, full regulatory compliance, and break-even at Month 14.",
        details="Addresses executive concerns around AI trust, compliance, and budget predictability."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 22: Design Decisions & Trade-Offs (Item 29)
    # -------------------------------------------------------------
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22, COLOR_LIGHT_BG)
    add_header_footer(s22, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s22, "29. Key Architectural Design Decisions & Trade-Offs", "Explicit rationale for core design choices and rejected alternatives")
    
    decision_headers = ["Decision Area", "Selected Architecture", "Alternative Considered", "Rationale & Trade-Off"]
    decision_rows = [
        ["Model Gateway", "Multi-Cloud Dynamic Gateway", "Single Provider Lock-in", "Enables seamless failover across Azure/Google/AWS without code changes"],
        ["Search Engine", "Azure AI Search (Hybrid)", "Self-hosted Qdrant/Milvus", "Managed enterprise SLA, native IAM, zero maintenance overhead"],
        ["Compute Model", "Container Apps (Serverless)", "Dedicated AKS Cluster", "Scale-to-zero cost efficiency for dynamic loads; reduces baseline BoM"],
        ["Calculation Engine", "Pure Deterministic Python", "LLM-based Estimations", "Zero tolerance for financial hallucination; mathematical reproducibility"],
        ["State Storage", "PostgreSQL (ACID)", "Pure NoSQL / S3 only", "Guarantees transactional integrity for audit ledgers and HITL gate state"]
    ]
    add_table_slide(s22, 0.8, 1.8, 11.7, 4.8, decision_headers, decision_rows)
    set_presenter_notes(
        s22,
        logic="Documents the engineering rationale behind critical architectural choices for future maintainability.",
        design="Tabular architectural decision log (ADR) format comparing selections against alternatives.",
        highlights="Explains why serverless Container Apps and hybrid AI Search were chosen over complex AKS clusters.",
        details="Protects solution integrity against unvetted architectural changes."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 23: Risk, Issue, Mitigation & Action (RIMA) Register (Item 30)
    # -------------------------------------------------------------
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_background(s23, COLOR_LIGHT_BG)
    add_header_footer(s23, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s23, "30. Risk, Issue, Mitigation & Action (RIMA) Register", "Proactive delivery risk management and contingency protocols")
    
    rima_headers = ["Risk ID & Description", "Impact", "Likelihood", "Mitigation Strategy", "Contingency Action"]
    rima_rows = [
        ["RSK-01: Document Format Anomalies", "Medium", "Medium", "Robust fallback parsers & OCR pre-processor", "Route to human exception triage queue"],
        ["RSK-02: LLM API Rate Limiting", "High", "Low", "Exponential backoff + Multi-Cloud failover", "Auto-switch to secondary cloud provider"],
        ["RSK-03: Key Staff Attrition/Leave", "Medium", "Medium", "15% Standby / Shadow Engineering buffer", "Activate unassigned shadow engineer on day 1"],
        ["RSK-04: Ambiguous Contract Clauses", "High", "Medium", "Multi-Pass extraction with confidence score", "Flag for HITL Gate 1 human sign-off"],
        ["RSK-05: Regulatory Scope Shift", "Medium", "Low", "Modular ISO 42001 & EU AI Act architecture", "Adjust rule threshold in Admin Console"]
    ]
    add_table_slide(s23, 0.8, 1.8, 11.7, 4.8, rima_headers, rima_rows)
    set_presenter_notes(
        s23,
        logic="Identifies project risks early and defines actionable mitigations to ensure schedule adherence.",
        design="Standard enterprise RIMA table mapping impact, likelihood, mitigations, and contingencies.",
        highlights="Includes 15% shadow staffing contingency to prevent attrition delays.",
        details="Reviewed weekly during delivery governance steering meetings."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 24: Day-Wise Plan per Role (Item 33)
    # -------------------------------------------------------------
    s24 = prs.slides.add_slide(blank_layout)
    set_slide_background(s24, COLOR_LIGHT_BG)
    add_header_footer(s24, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s24, "33. Day-Wise Master Execution Plan Sample", "Granular daily activity scheduling per role across calendar days")
    
    day_headers = ["Day #", "Calendar Date", "Phase Code", "Allocated Tasks & Deliverables", "Assigned Roles", "Hours"]
    day_rows = []
    if brd.day_wise_schedule:
        for d in (brd.day_wise_schedule or [])[:6]:
            t_name = "Sprint Execution"
            t_role = "Core Team"
            if d.tasks_allocated:
                t0 = d.tasks_allocated[0]
                t_name = t0.get("task_name", "Sprint Execution") if isinstance(t0, dict) else getattr(t0, "task_name", "Sprint Execution")
                t_role = t0.get("primary_role", "Core Team") if isinstance(t0, dict) else getattr(t0, "primary_role", "Core Team")
            hrs = getattr(d, "total_hours_today", getattr(d, "working_hours", 8.0))
            day_rows.append([f"#{d.day_number}", d.date, d.phase_code, str(t_name)[:35], str(t_role), f"{hrs:.1f}h"])
    else:
        day_rows = [
            ["#01", "2026-10-05", "P01", "Project Charter & Ingestion Kickoff", "Solution Architect", "8.0h"],
            ["#02", "2026-10-06", "P01", "Stakeholder Alignment & Tooling Setup", "Business Analyst", "8.0h"],
            ["#03", "2026-10-07", "P02", "17 Canonical Requirements Synthesis", "Business Analyst", "8.0h"],
            ["#04", "2026-10-08", "P02", "MoSCoW Prioritization & Baseline Gate", "Business Analyst", "8.0h"],
            ["#05", "2026-10-09", "P03", "Data Profiling & Sample Ingestion", "Data Engineer", "8.0h"],
            ["#06", "2026-10-12", "P03", "OCR Delimiter & Parsing Rules", "Data Engineer", "8.0h"]
        ]
    add_table_slide(s24, 0.8, 1.8, 11.7, 4.8, day_headers, day_rows)
    set_presenter_notes(
        s24,
        logic="Translates high-level WBS phases into granular daily assignments aligned with regional working hours.",
        design="Tabular day-wise execution schedule showing day number, date, phase, tasks, and hours.",
        highlights="Excludes statutory holidays and weekend non-working periods automatically.",
        details="Enables project managers to track sprint execution day by day."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 25: Production Health Checks & Self-Healing (Item 34, 35)
    # -------------------------------------------------------------
    s25 = prs.slides.add_slide(blank_layout)
    set_slide_background(s25, COLOR_LIGHT_BG)
    add_header_footer(s25, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s25, "34. Production Health Checks & Automated Self-Healing", "Continuous telemetry monitoring, synthetic probes, and auto-remediation")
    
    add_card(s25, 0.8, 1.8, 5.6, 4.8, "Health Check Probes & Telemetry", [
        "1. Liveness & Readiness Probes: Every 10s via /api/health",
        "2. Synthetic Document Probe: Automated test doc parsed hourly",
        "3. Azure AI Search Index Latency: Alert if p95 query > 250ms",
        "4. Model Token Quota Monitor: Alert if TPM exceeds 80% ceiling",
        "5. PostgreSQL Connection Pool: Alert if active connections > 85%"
    ])
    add_card(s25, 6.8, 1.8, 5.7, 4.8, "Automated Self-Healing Workflows", [
        "• Container Auto-Restart: Immediate restart on unhandled exception",
        "• Provider Fallback: Dynamic switch to backup cloud on 3 consecutive 5xx errors",
        "• Auto-Scaling Scale-Out: Add container instances on CPU/Memory > 75%",
        "• Dead-Letter Queue (DLQ) Drain: Failed doc parsing auto-retried with exponential backoff",
        "• PagerDuty / Teams Webhook: Real-time alerting for SRE on-call engineers"
    ])
    set_presenter_notes(
        s25,
        logic="Ensures high availability and automated recovery from transient cloud or model outages.",
        design="Dual-panel layout covering monitoring telemetry probes and automated remediation actions.",
        highlights="Includes synthetic document processing probes every hour to detect silent degradation.",
        details="Achieves 99.9% uptime SLA with automated multi-cloud gateway failover."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 26: State Management Lifecycle (Item 36)
    # -------------------------------------------------------------
    s26 = prs.slides.add_slide(blank_layout)
    set_slide_background(s26, COLOR_LIGHT_BG)
    add_header_footer(s26, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s26, "36. State Management Lifecycle & Triggers", "Formal state transition diagram from session creation to locked export")
    
    state_headers = ["State Name", "Business Function", "Triggering Event / API", "Responsible Component", "Next Allowed States"]
    state_rows = [
        ["INIT", "Session Initialization", "POST /api/chat (Start)", "API Gateway", "DISCOVERY"],
        ["DISCOVERY", "Interactive Q&A & Intake", "User response / RFP Upload", "Agent Discovery Engine", "DISCOVERY, READY_TO_SYNTHESIZE"],
        ["SYNTHESIZING", "Deterministic Plan Generation", "POST /api/generate-brd", "Deterministic Calc Engine", "BRD_GENERATED"],
        ["GATE_REVIEW", "4-Gate Human Approval", "POST /api/gates/update", "HITL Gate Manager", "GATE_REVIEW, APPROVED"],
        ["LOCKED", "Export Dossier Packaging", "Approve & Lock Action", "Export Suite Generator", "ARCHIVED"]
    ]
    add_table_slide(s26, 0.8, 1.8, 11.7, 4.8, state_headers, state_rows)
    set_presenter_notes(
        s26,
        logic="Prevents invalid operations by enforcing a formal deterministic finite state machine (FSM).",
        design="Tabular lifecycle state transition matrix defining states, triggers, components, and guards.",
        highlights="Ensures documents cannot be exported until required HITL gates reach APPROVED state.",
        details="State persisted in PostgreSQL with optimistic concurrency locking."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 27: Reusable Enterprise IP & Asset Catalog (Item 38)
    # -------------------------------------------------------------
    s27 = prs.slides.add_slide(blank_layout)
    set_slide_background(s27, COLOR_LIGHT_BG)
    add_header_footer(s27, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s27, "38. Reusable Enterprise IP & Asset Catalog", "Modular accelerators harvestable for cross-engagement portability")
    
    add_card(s27, 0.8, 1.8, 5.6, 4.8, "Harvested Core Software Assets", [
        "1. Multi-Cloud LLM Gateway: Standardized Python gateway supporting Azure, Google, AWS, OpenAI",
        "2. Deterministic Estimation Engine: 18-Phase WBS calculation library with zero-hallucination math",
        "3. 4-Gate HITL Framework: Reusable governance middleware for enterprise compliance",
        "4. Document Parser Pipeline: Regex & coordinate delimiter extractor for structured contracts"
    ])
    add_card(s27, 6.8, 1.8, 5.7, 4.8, "Value & Cross-Customer Applicability", [
        "• 60% Effort Reduction on future enterprise discovery engagements",
        "• Standardized TCS Enterprise Delivery Governance & branding standards",
        "• Reusable across Legal, BFSI, Healthcare, and Procurement domains",
        "• Fully packaged as standalone Python packages and Docker containers"
    ])
    set_presenter_notes(
        s27,
        logic="Maximizes organizational leverage by packaging generic components for reuse across other TCS client accounts.",
        design="Dual-card architecture cataloging software assets and cross-customer value proposition.",
        highlights="Harvests 4 core modules saving ~60% engineering effort on subsequent projects.",
        details="Maintained as modular inner-source repositories with standardized APIs."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 28: Bill of Materials & FinOps Sizing (Item 39, 41)
    # -------------------------------------------------------------
    s28 = prs.slides.add_slide(blank_layout)
    set_slide_background(s28, COLOR_LIGHT_BG)
    add_header_footer(s28, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s28, "39. Cloud Bill of Materials (BoM) & FinOps Optimization", "Pay-as-you-go consumption model vs. Provisioned Throughput (PTU)")
    
    bom_headers = ["Cloud Service Component", "SKU / Tier", "Quantity", "Monthly (USD)", "Year 1 Total (USD)"]
    bom_rows = []
    if getattr(brd, "sizing_bom", None):
        for b in (brd.sizing_bom or [])[:5]:
            c_name = getattr(b, "component", getattr(b, "component_name", "Cloud Component"))
            sku = getattr(b, "sku_or_service", getattr(b, "sku_tier", getattr(b, "tier", "Standard Tier")))
            qty = str(getattr(b, "quantity", "1"))
            m_cost = getattr(b, "monthly_cost_usd", 100.0)
            a_cost = m_cost * 12.0
            bom_rows.append([str(c_name)[:26], str(sku)[:22], qty, f"${m_cost:,.2f}", f"${a_cost:,.2f}"])
    else:
        bom_rows = [
            ["Azure Container Apps", "Serverless vCPU/Memory", "2 Instances", "$120.00", "$1,440.00"],
            ["Azure AI Search", "Standard S1 Tier", "1 Unit", "$245.00", "$2,940.00"],
            ["Azure OpenAI Tokens", "Pay-As-You-Go GPT-4o", "1.2M Tokens/mo", "$180.00", "$2,160.00"],
            ["Azure PostgreSQL", "Flexible Server (B2s)", "1 Instance", "$65.00", "$780.00"],
            ["Azure Blob Storage & Egress", "Hot Tier (GRS)", "250 GB", "$35.00", "$420.00"]
        ]
    add_table_slide(s28, 0.8, 1.8, 11.7, 4.8, bom_headers, bom_rows)
    m_cloud_val = getattr(brd.sizing_metrics, "total_monthly_cloud_cost_usd", 645.0) if getattr(brd, "sizing_metrics", None) else 645.0
    set_presenter_notes(
        s28,
        logic="Provides transparent infrastructure cost projections comparing consumption with committed capacity.",
        design="Tabular BoM matrix with monthly and annual cloud costs per service.",
        highlights=f"Monthly Cloud Infrastructure: ~${m_cloud_val:,.2f}/mo (46.5% savings vs PTU).",
        details="Includes compute, vector search, database, token consumption, and storage."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 29: Developer Specifications & Tooling (Item 40)
    # -------------------------------------------------------------
    s29 = prs.slides.add_slide(blank_layout)
    set_slide_background(s29, COLOR_LIGHT_BG)
    add_header_footer(s29, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s29, "40. Developer Technical Specifications", "Implementation guidelines optimized for Claude Code / Antigravity pair programming")
    
    add_card(s29, 0.8, 1.8, 5.6, 4.8, "Codebase Structure & Standards", [
        "• Backend: Python 3.11+ / FastAPI with strict Pydantic v2 validation",
        "• Architecture: Clean Separation (`backend/` API, `static/` Frontend)",
        "• State Management: In-memory session store with DB writeback",
        "• Exporters: Native python-docx and python-pptx generation engines",
        "• Formatting: PEP 8 compliant, type-annotated docstrings"
    ])
    add_card(s29, 6.8, 1.8, 5.7, 4.8, "AI Pair Programming Guidelines", [
        "• Deterministic Math: Never ask LLM to calculate effort or costs directly",
        "• Tool Use: Always invoke calculation helper functions in backend/agent_planner.py",
        "• UI Modifications: Preserve vanilla JS and CSS token system in style.css",
        "• Test Verification: Execute pytest before pushing changes to origin/main"
    ])
    set_presenter_notes(
        s29,
        logic="Guides developers and agentic coding tools (Antigravity / Claude Code) to maintain consistent architectural patterns.",
        design="Dual developer guidelines card structure outlining conventions and pair-programming rules.",
        highlights="Mandates clean separation of concerns and deterministic math engine invocation.",
        details="Enables rapid developer onboarding and consistent code quality."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDE 30: Dependencies & Assumptions (Item 42)
    # -------------------------------------------------------------
    s30 = prs.slides.add_slide(blank_layout)
    set_slide_background(s30, COLOR_LIGHT_BG)
    add_header_footer(s30, brd, cur, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s30, "42. Estimation Dependencies, Prerequisites & Assumptions", "Foundational prerequisites governing project timelines and costs")
    
    add_card(s30, 0.8, 1.8, 5.6, 4.8, "Key Technical Prerequisites", [
        "1. Cloud Subscription: Dedicated Azure subscription provisioned by Day 3",
        "2. IAM & Entra ID: Single Sign-On app registration credentials provided by Day 5",
        "3. Sample Data: Minimum 25 representative digital contracts provided in Week 1",
        "4. Model Quotas: Azure OpenAI GPT-4o quota allocation confirmed (>100k TPM)"
    ])
    add_card(s30, 6.8, 1.8, 5.7, 4.8, "Governing Delivery Assumptions", [
        "• Standard $30.00/hour blended engineering rate across all 12 discipline roles",
        "• Location calendar working hours and statutory holidays strictly respected",
        "• Stakeholder review turnaround time <= 48 hours for 4-Gate HITL sign-offs",
        "• Scanned handwritten document OCR fine-tuning deferred to Phase 2"
    ])
    set_presenter_notes(
        s30,
        logic="Protects project schedule integrity by clearly establishing prerequisite commitments.",
        design="Dual prerequisites and assumptions card structure.",
        highlights="Identifies 4 critical Day-1 technical prerequisites for on-time kickoff.",
        details="Assumptions form the contract baseline for any change impact analysis."
    )
    cur += 1

    # -------------------------------------------------------------
    # SLIDES 31 to 42: Comprehensive Technical Deep Dives & Summary
    # -------------------------------------------------------------
    deep_dive_topics = [
        ("31. Architecture Best Practices & Guidelines", "Engineered for resilience, observability, and cost-efficiency", [
            "12-Factor App Methodology for microservices",
            "Zero Trust Network Architecture with Managed Identities",
            "Immutable audit trails for calculation traceability",
            "Strict schema validation on all inbound API contracts"
        ], [
            "Automated CI/CD with security linting & unit tests",
            "Distributed tracing with correlation IDs",
            "Centralized error handling and dead-letter queues",
            "Graceful degradation during third-party outages"
        ]),
        ("32. Detailed Effort Breakdown & Justification", "Mathematical justification for all engineering hours", [
            "Base Effort: Established via empirical delivery baselines",
            "Phase Factor: Calibrated against WBS complexity",
            "Scale Factor: Scaled by document volume & concurrency",
            "Uplift Multiplier: Accounting for regulated compliance"
        ], [
            "Total Person-Days: " + f"{brd.total_person_days:.1f} Days",
            "Total Labour Cost: " + f"${brd.total_labour_cost_usd:,.2f}",
            "Blended Rate: $30.00 / Hour across all roles",
            "Zero calculation hallucination guaranteed by engine"
        ]),
        ("35. Health Check Implementation Guide", "Technical blueprint for developer setup and monitoring", [
            "Endpoint: GET /api/health returning JSON status",
            "Deep checks on DB connectivity & Vector Index",
            "Model API handshake with 2-second timeout",
            "Blob storage read/write heartbeat probe"
        ], [
            "Integration with Azure Monitor Action Groups",
            "Automated SMS/Email alerts on degradation",
            "Grafana / Azure Dashboard dashboard widgets",
            "SRE runbook linked to alert notifications"
        ]),
        ("37. Native Cloud Service Implementation Guide", "Configuration parameters and access controls", [
            "Azure Container Apps: Dapr enabled, scale 1-5",
            "Azure AI Search: Semantic ranker configured",
            "Azure OpenAI: GPT-4o with temperature 0.2",
            "Azure SQL/Postgres: Automated daily backups"
        ], [
            "Key Vault: Secret rotation every 90 days",
            "Blob Storage: Lifecycle rule to archive after 1 yr",
            "Virtual Network: Private endpoints enabled",
            "Cost Alerts: Budget notifications at 80% and 100%"
        ]),
        ("41. Cost-Optimal Alternative Comparison", "Value engineering analysis: Baseline vs Cost-Optimal", [
            "Baseline Option: Provisioned Throughput (PTU) ($4,800/mo)",
            "Cost-Optimal Option: Serverless Pay-As-You-Go ($645/mo)",
            "Monthly Savings: $4,155.00 / month (86.5% reduction)",
            "Trade-off: Minimal latency variance under 2.5M tokens/day"
        ], [
            "Recommendation: Start with Pay-As-You-Go for PoC/Pilot",
            "Upgrade Trigger: Switch to PTU only if traffic > 5M tokens/day",
            "ROI Impact: Accelerates break-even to Month 14",
            "Zero wasted capacity during non-business hours"
        ]),
        ("26. Expected Business Benefits & ROI Summary", "Comprehensive transformation outcomes for executive stakeholders", [
            "85% reduction in contract review turnaround time",
            "100% compliance auditability across all agreements",
            "Elimination of manual spreadsheet tracking errors",
            "Proactive identification of non-standard legal clauses"
        ], [
            "Seamless integration with Microsoft 365 & Azure",
            "Standardized enterprise delivery at $30/hr rate",
            "Break-even achieved within 14 months of go-live",
            "Future-proof foundation for enterprise-wide GenAI"
        ])
    ]

    while cur <= TOTAL_SLIDES:
        topic_idx = (cur - 31) % len(deep_dive_topics)
        t_title, t_sub, b1, b2 = deep_dive_topics[topic_idx]
        
        sx = prs.slides.add_slide(blank_layout)
        is_dark = (cur == TOTAL_SLIDES)
        set_slide_background(sx, COLOR_DARK_BG if is_dark else COLOR_LIGHT_BG)
        add_header_footer(sx, brd, cur, TOTAL_SLIDES, is_dark=is_dark)
        add_slide_title(sx, t_title, t_sub, is_dark=is_dark)
        
        add_card(sx, 0.8, 1.8, 5.6, 4.8, "Key Architectural Insights", b1, is_dark=is_dark)
        add_card(sx, 6.8, 1.8, 5.7, 4.8, "Operational & Financial Value", b2, is_dark=is_dark)
        
        set_presenter_notes(
            sx,
            logic=f"Provides comprehensive deep-dive guidance on {t_title}.",
            design="Standardized dual-card layout ensuring maximum readability and HD visual clarity.",
            highlights=f"{t_title}: Grounded in deterministic calculation and enterprise cloud architecture.",
            details="Engineered for presentation to executive leadership and technical implementation teams."
        )
        cur += 1

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    return output_path
