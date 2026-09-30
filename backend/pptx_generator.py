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

# Color Palette: Premium Navy, Slate, Electric Cyan, Pure White
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
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_MAIN
    
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_ACCENT if is_dark else COLOR_PRIMARY

def add_card(slide, left: float, top: float, width: float, height: float, title: str, bullets: list, is_dark: bool = False):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_DARK if is_dark else COLOR_CARD_BG
    card.line.color.rgb = RGBColor(51, 65, 85) if is_dark else RGBColor(226, 232, 240)
    card.line.width = Pt(1)

    tb = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.2), Inches(width - 0.4), Inches(height - 0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(15)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_ACCENT if is_dark else COLOR_PRIMARY
    
    for bullet in bullets:
        p = tf.add_paragraph()
        p.text = f"• {bullet}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_LIGHT if is_dark else COLOR_TEXT_MAIN
        p.space_after = Pt(4)

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
    TOTAL_SLIDES = 10

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide (Dark Theme)
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_DARK_BG)
    add_header_footer(s1, brd, 1, TOTAL_SLIDES, is_dark=True)
    
    title_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(3.0))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    
    p_tag = tf1.paragraphs[0]
    p_tag.text = f"PRODUCTION-GRADE ARCHITECTURE & DELIVERY SPECIFICATION  |  {brd.delivery_tier.upper()}"
    p_tag.font.size = Pt(14)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_ACCENT
    
    p_title = tf1.add_paragraph()
    p_title.text = brd.project_title
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.space_after = Pt(14)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = f"Prepared for: {brd.client_name}  •  Duration: {brd.total_duration_weeks:.0f} Weeks  •  Total Effort: {brd.total_person_days:.1f} Person-Days (${brd.total_labour_cost_usd:,.2f} @ $30/hr)"
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)
    
    set_presenter_notes(
        s1,
        logic="Sets commercial and technical baseline for client leadership.",
        design="Dark-mode executive title slide adhering to TCS enterprise branding standards.",
        highlights=f"Initiative: {brd.project_title}, Tier: {brd.delivery_tier}, Budget: ${brd.total_labour_cost_usd:,.2f}.",
        details="Covers foundational scope, cloud boundaries, and role loading at $30/hr blended rate."
    )

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement & Business Impacts
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_header_footer(s2, brd, 2, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s2, "Problem Statement & Measurable Business Impacts", "Bridging operational bottlenecks with governed enterprise automation")
    
    add_card(s2, 0.8, 1.8, 5.6, 4.8, "Current Operational Pain Points", [
        f"Core Issue: {brd.problem_statement}",
        "Manual Review Dependency: Highly reliant on scarce domain expertise, creating multi-day review backlogs.",
        "Fragmented Auditability: Review findings reside in disconnected spreadsheets without unified visibility.",
        "Inconsistent Enforcement: Category-specific contracting principles are not uniformly caught during negotiations."
    ])
    
    add_card(s2, 6.8, 1.8, 5.7, 4.8, "Target Business Impacts & Value Drivers", brd.business_impacts)
    
    set_presenter_notes(
        s2,
        logic="Defines the operational justification for budget and executive sponsorship.",
        design="Side-by-side comparative card layout contrasting current friction against target ROI.",
        highlights="Transforms review cycle from days to <90s per document with 100% auditable traceability.",
        details="Addresses specific challenges identified in manual review processes."
    )

    # -------------------------------------------------------------
    # SLIDE 3: In-Scope vs. Explicitly Out-of-Scope Boundaries
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_header_footer(s3, brd, 3, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s3, "Scope Boundaries: In-Scope Capabilities vs. Out-of-Scope", f"Firm boundary definitions for {brd.delivery_tier} tier execution")
    
    add_card(s3, 0.8, 1.8, 5.6, 4.8, f"In-Scope for {brd.delivery_tier}", brd.in_scope)
    add_card(s3, 6.8, 1.8, 5.7, 4.8, "Explicitly Out-of-Scope (Deferred to Phase 2)", brd.out_of_scope)
    
    set_presenter_notes(
        s3,
        logic="Prevents scope creep and aligns expectations on what is delivered in this phase.",
        design="High-contrast dual boundary cards clearly delineating commitments.",
        highlights="Digital contracts in scope; live ERP writeback and scanned OCR tuning safely deferred.",
        details="Aligns with the enterprise governance tier."
    )

    # -------------------------------------------------------------
    # SLIDE 4: AI vs. Non-AI Demarcation (Critical Rule)
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_header_footer(s4, brd, 4, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s4, "Architectural Demarcation: AI vs. Non-AI Interventions", "Ensuring deterministic tasks are strictly handled by native cloud services, NOT LLMs")
    
    ai_bullets = [f"{ai['capability']} ({ai['type']}): {ai['purpose']}" for ai in brd.ai_interventions]
    add_card(s4, 0.8, 1.8, 5.6, 4.8, "Agentic AI Interventions (Reasoning / LLM)", ai_bullets)
    
    non_ai_bullets = [f"{nai['capability']}: {nai['purpose']} [{nai['azure_service']}]" for nai in brd.non_ai_interventions]
    add_card(s4, 6.8, 1.8, 5.7, 4.8, "Deterministic Non-AI Services (Zero Hallucination)", non_ai_bullets)
    
    set_presenter_notes(
        s4,
        logic="Enforces architectural rigor by preventing LLM misuse for deterministic cloud tasks.",
        design="Demarcation matrix distinguishing probabilistic reasoning from deterministic storage & compute.",
        highlights="Storage, parsing coordinates, relational schemas, and SSO are 100% deterministic.",
        details="Agentic LLM calls are isolated strictly to semantic classification and multi-pass clause reasoning."
    )

    # -------------------------------------------------------------
    # SLIDE 5: Production-Grade Cloud Architecture Narrative
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_DARK_BG)
    add_header_footer(s5, brd, 5, TOTAL_SLIDES, is_dark=True)
    add_slide_title(s5, "Target Cloud Component Architecture (Azure Native)", "Single-region, batch-resilient, containerized pipeline in India region", is_dark=True)
    
    # Left narrative card
    add_card(s5, 0.8, 1.8, 5.6, 4.8, "Architectural Topology & Boundary Narrative", [
        brd.target_architecture_narrative[:400] + "...",
        "Virtual Serverless: Azure Container Apps & Azure Functions provide stateless, auto-scaling compute.",
        "Agentic Framework: Azure OpenAI Service (GPT-4o) with structured JSON schemas and prompt versioning.",
        "Vector & Search Layer: Azure AI Search holds clause-level chunks, metadata coordinates, and embeddings.",
        "Zero-Trust IAM: Managed Identities eliminate shared credentials across all service-to-service links."
    ], is_dark=True)
    
    # Right services inventory
    srv_bullets = [f"{s['service']}: {s['purpose']}" for s in brd.azure_services_used]
    add_card(s5, 6.8, 1.8, 5.7, 4.8, "Cloud Service Component Register", srv_bullets, is_dark=True)
    
    set_presenter_notes(
        s5,
        logic="Demonstrates enterprise-grade Azure landing zone design meeting data residency criteria.",
        design="Dark-mode technical architecture slide detailing boundaries and container runtimes.",
        highlights="Azure Container Apps + Azure OpenAI + Document Intelligence in India cloud boundary.",
        details="Follows Well-Architected Framework guidelines."
    )

    # -------------------------------------------------------------
    # SLIDE 6: End-to-End Functional Data Flow
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_header_footer(s6, brd, 6, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s6, "End-to-End Functional Data Flow & Trigger Points", "Numbered lifecycle from ingestion to validated risk register presentation")
    
    flow_steps = brd.data_flow_narrative.split("\n")
    half = len(flow_steps) // 2
    
    add_card(s6, 0.8, 1.8, 5.6, 4.8, "Stages 1 to 5: Ingestion & Multi-Pass Extraction", flow_steps[:half])
    add_card(s6, 6.8, 1.8, 5.7, 4.8, "Stages 6 to 9: Assessment & Cockpit Surfacing", flow_steps[half:])
    
    set_presenter_notes(
        s6,
        logic="Provides unambiguous implementation roadmap for backend developers and integration engineers.",
        design="Chronological two-column data flow card layout.",
        highlights="Multi-pass extraction ensures open-textured terms are resolved without infinite retry loops.",
        details="Every output is coordinate-grounded."
    )

    # -------------------------------------------------------------
    # SLIDE 7: Resource Loading & Effort Breakdown ($30/hr Blended)
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_LIGHT_BG)
    add_header_footer(s7, brd, 7, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s7, f"Resource Loading & Commercial Estimate (${brd.total_labour_cost_usd:,.2f})", f"Blended $30.00/Hour Rate across 7 Specialized Engineering Disciplines")
    
    # Add a real PowerPoint table for roles!
    rows = len(brd.role_efforts) + 2
    cols = 5
    table_shape = s7.shapes.add_table(rows, cols, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.7))
    tbl = table_shape.table
    
    # Set headers
    headers = ["Role Title", "Functional Focus", "Days", "Hours", "Total Cost ($30/hr)"]
    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h_text
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_WHITE
        
    for r_idx, r_item in enumerate(brd.role_efforts):
        c0 = tbl.cell(r_idx + 1, 0)
        c0.text = r_item.role
        c0.text_frame.paragraphs[0].font.bold = True
        
        c1 = tbl.cell(r_idx + 1, 1)
        c1.text = r_item.description[:48] + "..."
        
        c2 = tbl.cell(r_idx + 1, 2)
        c2.text = f"{r_item.days:.1f}"
        
        c3 = tbl.cell(r_idx + 1, 3)
        c3.text = f"{r_item.hours:.0f}"
        
        c4 = tbl.cell(r_idx + 1, 4)
        c4.text = f"${r_item.cost:,.2f}"
        
    # Total row
    tot_row = rows - 1
    tbl.cell(tot_row, 0).text = "TOTAL DELIVERY EFFORT"
    tbl.cell(tot_row, 0).fill.solid()
    tbl.cell(tot_row, 0).fill.fore_color.rgb = RGBColor(241, 245, 249)
    tbl.cell(tot_row, 0).text_frame.paragraphs[0].font.bold = True
    
    tbl.cell(tot_row, 1).text = f"{brd.total_duration_weeks:.0f} Calendar Weeks Reference Duration"
    tbl.cell(tot_row, 2).text = f"{brd.total_person_days:.1f} Days"
    tbl.cell(tot_row, 2).text_frame.paragraphs[0].font.bold = True
    
    tbl.cell(tot_row, 3).text = f"{brd.total_person_hours:.0f} Hours"
    tbl.cell(tot_row, 3).text_frame.paragraphs[0].font.bold = True
    
    tbl.cell(tot_row, 4).text = f"${brd.total_labour_cost_usd:,.2f}"
    tbl.cell(tot_row, 4).fill.solid()
    tbl.cell(tot_row, 4).fill.fore_color.rgb = RGBColor(220, 252, 231)
    tbl.cell(tot_row, 4).text_frame.paragraphs[0].font.bold = True
    tbl.cell(tot_row, 4).text_frame.paragraphs[0].font.color.rgb = RGBColor(22, 101, 52)
    
    set_presenter_notes(
        s7,
        logic="Defensible commercial staffing model calculated at $30/hr blended labour rate.",
        design="Detailed tabular resource loading matrix detailing days, hours, and discipline responsibilities.",
        highlights=f"Total: {brd.total_person_days:.1f} Person-Days, {brd.total_person_hours:.0f} Person-Hours, ${brd.total_labour_cost_usd:,.2f}.",
        details="AI Engineer and Fullstack Developer lead the implementation effort."
    )

    # -------------------------------------------------------------
    # SLIDE 8: Phased Project Delivery & Milestones
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_LIGHT_BG)
    add_header_footer(s8, brd, 8, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s8, "Delivery Timeline & Milestone Schedule", f"{brd.total_duration_weeks:.0f}-Week Phased Execution Plan")
    
    col_w = 2.8
    gap = 0.2
    for p_idx, phase in enumerate(brd.project_phases):
        left_pos = 0.8 + (p_idx * (col_w + gap))
        add_card(s8, left_pos, 1.8, col_w, 4.8, f"{phase.phase_name}\n({phase.weeks:.1f} Wks)", [
            f"Key Focus: {phase.key_deliverables[0]}",
            f"Deliverable: {phase.key_deliverables[1]}",
            f"Validation: {phase.key_deliverables[2]}",
            f"Staffing: {', '.join(phase.roles_involved[:2])}"
        ])
        
    set_presenter_notes(
        s8,
        logic="Structures the project into clear sequential gates with accountable deliverables.",
        design="Four-column sprint progression roadmap.",
        highlights="Inception -> Core Build -> Evaluation Harness -> Executive Gate.",
        details="Enables tight milestone tracking and stakeholder visibility."
    )

    # -------------------------------------------------------------
    # SLIDE 9: Assumptions Ledger & Client Prerequisites
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_LIGHT_BG)
    add_header_footer(s9, brd, 9, TOTAL_SLIDES, is_dark=False)
    add_slide_title(s9, "Assumptions Ledger & Key External Dependencies", "Transparent documentation of standard baselines and ambiguity fallback defaults")
    
    asm_bullets = [f"[{a.category}] {a.statement} (Impact: {a.impact})" for a in brd.assumptions[:5]]
    add_card(s9, 0.8, 1.8, 5.6, 4.8, "Key Project Assumptions & Defaults", asm_bullets)
    
    prereq_bullets = [
        "Sample Contract Handover: Client provides representative sample contracts into Azure Blob Storage.",
        "Contracting Principles Freeze: Legal stakeholders approve category ontologies during Workshop 1.",
        "Benchmark Dataset Access: Legal-confirmed ground truth reviews provided for evaluation scoring.",
        "SME Availability Commitment: Named SPOC available for weekly validation sessions.",
        "Azure Subscription Provisioning: Non-production subscription enabled with required token quotas."
    ]
    add_card(s9, 6.8, 1.8, 5.7, 4.8, "Hard Client Prerequisites & Dependencies", prereq_bullets)
    
    set_presenter_notes(
        s9,
        logic="Protects timeline feasibility by making client dependencies and default assumptions explicit.",
        design="Dual-card ledger listing tracked assumptions and operational prerequisites.",
        highlights="Ambiguity defaults are documented and adjustable in the project workbench.",
        details="Clear separation of client obligations from delivery scope."
    )

    # -------------------------------------------------------------
    # SLIDE 10: Executive Summary & Next Steps (CXO Pitch)
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_DARK_BG)
    add_header_footer(s10, brd, 10, TOTAL_SLIDES, is_dark=True)
    add_slide_title(s10, "Executive Summary & Recommended Next Steps", "Decision Gate sign-off and initiation roadmap", is_dark=True)
    
    add_card(s10, 0.8, 1.8, 5.6, 4.8, "Why This Solution (Key Differentiators)", [
        "Multi-Pass Precision: Avoids single-pass hallucination by running focused passes for ambiguous terms.",
        "Deterministic Cost & Safety: High-risk actions handled by native Azure cloud services, not unconstrained agents.",
        "Defensible Economics: Total labour cost ${:,.2f} at $30/hr rate with full role accountability.".format(brd.total_labour_cost_usd),
        "Decision Gate Confidence: Quantitative accuracy benchmarks (≥95%) before committing to Phase 2 production."
    ], is_dark=True)
    
    add_card(s10, 6.8, 1.8, 5.7, 4.8, "Immediate Next Steps & Kick-off Actions", [
        "1. Executive Sponsor sign-off on Delivery Specification and ${:,.2f} baseline.".format(brd.total_labour_cost_usd),
        "2. Provision Azure landing zone in India region (Blob Storage, Key Vault, Container Apps).",
        "3. Conduct Workshop 1 to freeze the category clause list and contracting principles.",
        "4. Ingest first batch of historical contracts and configure benchmark evaluation harness.",
        "5. Deploy Demonstration Cockpit for weekly stakeholder validation sprints."
    ], is_dark=True)
    
    set_presenter_notes(
        s10,
        logic="Provides the closing pitch and actionable mobilization plan for senior decision-makers.",
        design="Dark-mode executive wrap-up highlighting strategic value and kick-off steps.",
        highlights=f"Total Investment: ${brd.total_labour_cost_usd:,.2f}, Timeline: {brd.total_duration_weeks:.0f} Weeks.",
        details="Phase 1 successfully validates commercial and operational feasibility."
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    return output_path
