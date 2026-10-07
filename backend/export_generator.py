import os
import csv
import io
from datetime import datetime
from typing import Dict, Any, List
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.models import BRDDocument, ProjectSession

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    ns_w = nsdecls('w')
    shd = parse_xml(f'<w:shd {ns_w} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m_name, m_val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m_name}')
        node.set(qn('w:w'), str(m_val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def generate_word_brd(brd: BRDDocument, output_path: str) -> str:
    """Generates a comprehensive, enterprise-grade Word (.docx) BRD document."""
    doc = Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Document Header & Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(f"BUSINESS REQUIREMENTS DOCUMENT (BRD)\n{brd.project_title.upper()}")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(14, 116, 144)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run(f"Enterprise AI Engineering Specification & Resource Loading Plan | Delivery Tier: {brd.delivery_tier}")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Metadata Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Client / Account", brd.client_name),
        ("Target Delivery Tier", f"{brd.delivery_tier} ({brd.tier_kind})"),
        ("Target Kick-Off & Completion", f"{brd.start_date} to {brd.target_end_date} ({brd.total_duration_weeks:.1f} Weeks)"),
        ("Commercial Model", f"/hr Blended Rate | Total Labour: "),
        ("Primary Cloud & Residency", f"{brd.azure_services_used[0]['service'] if brd.azure_services_used else 'Cloud Native'} ({brd.delivery_model})"),
        ("Resilience & Buffer Staffing", f"{brd.buffer_capacity_pct:.0f}% Shadow Staffing ({len(brd.backup_resources)} Standby Engineers)")
    ]
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.6)
        c0.text = label
        c1.text = val
        c0.paragraphs[0].runs[0].font.bold = True
        set_cell_background(c0, "F1F5F9")
        set_cell_margins(c0, 80, 80, 100, 100)
        set_cell_margins(c1, 80, 80, 100, 100)

    # 1. Introduction
    doc.add_heading("1. Introduction", level=1)
    p_intro = doc.add_paragraph()
    p_intro.add_run(
        f"Version: 1.0.0\n\n"
        f"This Business Requirements Document (BRD) outlines the purpose, scope, and objectives of {brd.project_title}. "
        f"It provides a detailed description of business needs and the requirements that the solution must fulfill. "
        f"This document serves as a formal agreement between stakeholders and the project team on the expected deliverables."
    )
    if brd.executive_summary:
        doc.add_paragraph(brd.executive_summary)

    # 2. Project Overview
    doc.add_heading("2. Project Overview", level=1)
    doc.add_heading("2.1 Business Context & Justification", level=2)
    doc.add_paragraph(brd.problem_statement)

    doc.add_heading("2.2 High-Level Goals & Expected Benefits", level=2)
    for imp in brd.business_impacts:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(imp)

    # 3. Scope
    doc.add_heading("3. Scope", level=1)
    doc.add_paragraph(
        f"The scope defines what is included and excluded from the {brd.project_title} engagement. "
        f"Target delivery tier is established as {brd.delivery_tier} ({brd.tier_kind})."
    )
    doc.add_heading("3.1 In-Scope Capabilities & Deliverables", level=2)
    for item in brd.in_scope:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    doc.add_heading("3.2 Explicitly Out-of-Scope", level=2)
    for item in brd.out_of_scope:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    # 4. Business Requirements
    doc.add_heading("4. Business Requirements", level=1)
    doc.add_paragraph(
        "Business requirements specify what needs to be achieved to deliver measurable organizational value, prioritized by MoSCoW importance:"
    )
    br_items = [
        ("BR-1", "Authentication & Access Governance", "The system shall allow users to securely authenticate using unique corporate credentials and role-based permissions.", "MUST"),
        ("BR-2", "Real-Time Operational Reporting", "The system shall provide real-time reporting, metrics visibility, and KPI tracking dashboards.", "MUST"),
        ("BR-3", "Configurable Permission Matrix", "The system shall support multi-tiered user roles (e.g. Employee, Manager, Admin) with granular permission boundaries.", "MUST"),
        ("BR-4", "Standardized Data Import / Export", "The system shall enable data ingestion and export using standardized formats (JSON, CSV, REST APIs).", "SHOULD"),
        ("BR-5", "Regulatory & Statutory Compliance", "The system shall ensure compliance with applicable enterprise security, privacy, and regional statutory regulations.", "MUST")
    ]
    br_table = doc.add_table(rows=len(br_items) + 1, cols=4)
    br_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    br_headers = ["Req ID", "Requirement Title", "Statement & Business Objective", "MoSCoW Priority"]
    for c_idx, h in enumerate(br_headers):
        cell = br_table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "0E7490")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 80, 80, 80, 80)
    for r_idx, (req_id, title, stmt, prio) in enumerate(br_items):
        row = br_table.rows[r_idx + 1]
        row.cells[0].text = req_id
        row.cells[1].text = title
        row.cells[2].text = stmt
        row.cells[3].text = prio
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[3].paragraphs[0].runs[0].font.bold = True
        for c_idx in range(4):
            set_cell_margins(row.cells[c_idx], 60, 60, 60, 60)
            if r_idx % 2 == 1:
                set_cell_background(row.cells[c_idx], "F8FAFC")

    # 5. Functional Requirements
    doc.add_heading("5. Functional Requirements", level=1)
    doc.add_paragraph("Functional requirements define specific capabilities, user interactions, and system behaviors:")
    fr_items = [
        ("FR-1", "CRUD & Transaction Management", "The system shall allow authorized users to create, read, update, and manage core transaction records."),
        ("FR-2", "Customizable Management Dashboard", "The system shall provide an interactive dashboard with status widgets, charts, and activity summaries."),
        ("FR-3", "Automated Notifications & Alerts", "The system shall send automated notifications (email, in-app) triggered by status changes and approvals."),
        ("FR-4", "Detailed Immutable Audit Logging", "The system shall maintain comprehensive audit logs of all user actions, timestamped with user ID."),
        ("FR-5", "Third-Party & Enterprise Integrations", "The system shall interface securely with upstream enterprise systems via authenticated REST endpoints.")
    ]
    fr_table = doc.add_table(rows=len(fr_items) + 1, cols=3)
    fr_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    fr_headers = ["Req ID", "Function / Feature Name", "Functional Behavior Specification"]
    for c_idx, h in enumerate(fr_headers):
        cell = fr_table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "0E7490")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 80, 80, 80, 80)
    for r_idx, (req_id, fname, fspec) in enumerate(fr_items):
        row = fr_table.rows[r_idx + 1]
        row.cells[0].text = req_id
        row.cells[1].text = fname
        row.cells[2].text = fspec
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        for c_idx in range(3):
            set_cell_margins(row.cells[c_idx], 60, 60, 60, 60)
            if r_idx % 2 == 1:
                set_cell_background(row.cells[c_idx], "F8FAFC")

    # 6. Non-Functional Requirements
    doc.add_heading("6. Non-Functional Requirements", level=1)
    nfr_items = [
        ("NFR-1", "Performance & Latency SLA", "The system shall respond to 95% of standard user requests within two (2.0) seconds under peak load."),
        ("NFR-2", "High Availability & Uptime", f"The system shall guarantee {getattr(brd, 'ha_dr_tier', 'Standard High Availability (99.5%)')} uptime availability (99.5% - 99.9%), excluding scheduled maintenance."),
        ("NFR-3", "Regulatory & Security Standards", f"The system shall comply with {getattr(brd, 'compliance_framework', 'ISO 27001 / GDPR / SOC2')} standards and regional data protection regulations."),
        ("NFR-4", "Accessibility & Usability", "The user interface shall support Web Content Accessibility Guidelines (WCAG 2.1 Level AA)."),
        ("NFR-5", "Data Encryption & Protection", "All sensitive data shall be encrypted in-transit (TLS 1.3) and at-rest (AES-256) with secure key management.")
    ]
    for n_id, n_title, n_desc in nfr_items:
        p = doc.add_paragraph(style='List Bullet')
        r_b = p.add_run(f"{n_id} ({n_title}): ")
        r_b.bold = True
        p.add_run(n_desc)

    # 7. Assumptions and Constraints
    doc.add_heading("7. Assumptions and Constraints", level=1)
    assumptions = [
        "The project assumes active availability of key business stakeholders and SMEs for weekly validation workshops.",
        "The solution must operate within the designated cloud infrastructure without requiring unapproved firewall exemptions.",
        "Integration with existing upstream systems shall not degrade current enterprise production throughput.",
        f"Delivery timeline is planned for {brd.total_duration_weeks:.1f} weeks based on confirmed scope tier ({brd.delivery_tier}).",
        f"Resourcing allocates {brd.buffer_capacity_pct:.0f}% standby shadow capacity to absorb sprint leaves or critical technical blockers."
    ]
    for asm in assumptions:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(asm)

    # 8. Dependencies
    doc.add_heading("8. Dependencies", level=1)
    dependencies = [
        "Dependency on Enterprise Identity Provider (Azure AD / Okta / Corporate SSO) for unified authentication.",
        "Timely provisioning of target cloud subscriptions, storage buckets, and database instances.",
        "Availability of upstream API credentials, test datasets, and schema documentation during Sprint 1.",
        "Coordination with enterprise security team for automated VAPT and architecture review gates.",
        "Adherence to corporate data governance policies and retention schedules."
    ]
    for dep in dependencies:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(dep)

    # 9. Acceptance Criteria
    doc.add_heading("9. Acceptance Criteria", level=1)
    criteria = [
        "All business and functional requirements (BR-1..BR-5, FR-1..FR-5) are implemented and verified by test suites.",
        "The system passes security and compliance audits in accordance with organizational policies.",
        "Performance benchmarks meet or exceed the specified latency thresholds (<2.0s under peak load).",
        "User Acceptance Testing (UAT) is successfully completed with documented business sponsor approval.",
        "Delivery handover dossier, API documentation, and training materials are delivered and approved."
    ]
    for crit in criteria:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(crit)

    # 10. Glossary
    doc.add_heading("10. Glossary", level=1)
    glossary_items = [
        ("BRD", "Business Requirements Document — formal specification defining business needs and solution requirements."),
        ("WBS", "Work Breakdown Structure — hierarchical decomposition of the total scope of work into 18 standardized phases."),
        ("SLA", "Service Level Agreement — commitment between service provider and customer defining uptime and performance metrics."),
        ("RTO / RPO", "Recovery Time Objective / Recovery Point Objective — metrics defining disaster recovery speed and data loss tolerances."),
        ("RBAC", "Role-Based Access Control — security mechanism restricting system access based on authorized user roles."),
        ("SSO", "Single Sign-On — authentication process that allows a user to access multiple applications with one set of credentials."),
        ("WCAG", "Web Content Accessibility Guidelines — international standards for digital accessibility (Level AA)."),
        ("FinOps BoM", "Financial Operations Bill of Materials — structured itemization of monthly cloud infrastructure hosting expenses.")
    ]
    for term, definition in glossary_items:
        p = doc.add_paragraph(style='List Bullet')
        r_t = p.add_run(f"{term}: ")
        r_t.bold = True
        p.add_run(definition)

    # 11. Signatures
    doc.add_heading("11. Formal Stakeholder Signatures & Approvals", level=1)
    doc.add_paragraph(
        "By signing below, the project stakeholders acknowledge that this Business Requirements Document accurately represents the agreed scope, functional capabilities, and delivery baseline."
    )
    sign_table = doc.add_table(rows=4, cols=4)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_headers = ["Stakeholder Role", "Representative Name", "Signature", "Date Approved"]
    for c_idx, h in enumerate(sign_headers):
        cell = sign_table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "0E7490")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 100, 100, 80, 80)

    sign_roles = [
        ("Project Sponsor (Executive)", brd.client_name),
        ("Lead Business Analyst", "AI Practice Business Analysis Team"),
        ("Principal Solutions Architect", "Enterprise Solutions Architecture Lead")
    ]
    for s_idx, (s_role, s_name) in enumerate(sign_roles):
        row = sign_table.rows[s_idx + 1]
        row.cells[0].text = s_role
        row.cells[1].text = s_name
        row.cells[2].text = "___________________"
        row.cells[3].text = "____ / ____ / 2026"
        for cell in row.cells:
            set_cell_margins(cell, 120, 120, 80, 80)

    # 12. Resource Allocation & Engineering Budget
    doc.add_heading("12. Resource Allocation & Engineering Budget", level=1)
    role_table = doc.add_table(rows=len(brd.role_efforts) + 2, cols=6)
    role_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Code", "Discipline Role", "Days", "Hours", "Cost (/hr)", "Staffed FTE"]
    for c_idx, h in enumerate(headers):
        cell = role_table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "0E7490")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 100, 100, 80, 80)

    for r_idx, r in enumerate(brd.role_efforts):
        row = role_table.rows[r_idx + 1]
        vals = [r.role_code, r.role, f"{r.days:.1f} d", f"{r.hours:.0f} h", f"", f"{r.total_assigned_fte:.2f} FTE"]
        for c_idx, v in enumerate(vals):
            cell = row.cells[c_idx]
            cell.text = v
            set_cell_margins(cell, 80, 80, 80, 80)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")

    # Total Row
    tot_row = role_table.rows[-1]
    tot_vals = ["TOTAL", "12 Disciplines Standardized", f"{brd.total_person_days:.1f} d", f"{brd.total_person_hours:.0f} h", f"", "-"]
    for c_idx, v in enumerate(tot_vals):
        cell = tot_row.cells[c_idx]
        cell.text = v
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "E2E8F0")
        set_cell_margins(cell, 100, 100, 80, 80)

    # 13. Cloud Infrastructure Bill of Materials (BoM)
    doc.add_heading("13. Cloud Infrastructure Bill of Materials (BoM)", level=1)
    bom_table = doc.add_table(rows=len(brd.sizing_bom) + 2, cols=5)
    bom_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    bom_headers = ["Component", "Cloud SKU / Service", "Tier", "Qty", "Monthly Cost (USD)"]
    for c_idx, h in enumerate(bom_headers):
        cell = bom_table.rows[0].cells[c_idx]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "0E7490")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, 100, 100, 80, 80)

    for b_idx, b in enumerate(brd.sizing_bom):
        row = bom_table.rows[b_idx + 1]
        vals = [b.component, b.sku_or_service, b.tier, str(b.quantity), f""]
        for c_idx, v in enumerate(vals):
            cell = row.cells[c_idx]
            cell.text = v
            set_cell_margins(cell, 80, 80, 80, 80)
            if b_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")

    tot_bom_row = bom_table.rows[-1]
    tot_bom_vals = ["TOTAL CLOUD INFRASTRUCTURE", "-", "-", "-", f" / mo"]
    for c_idx, v in enumerate(tot_bom_vals):
        cell = tot_bom_row.cells[c_idx]
        cell.text = v
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_background(cell, "E2E8F0")
        set_cell_margins(cell, 100, 100, 80, 80)

    doc.save(output_path)
    return output_path

def generate_excel_financial_model(brd: BRDDocument, output_path: str) -> str:
    """Generates a multi-tab formula-driven Excel (.xlsx) financial workbook."""
    wb = openpyxl.Workbook()
    
    # Styles
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0E7490", end_color="0E7490", fill_type="solid")
    total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    total_font = Font(name="Calibri", size=11, bold=True, color="000000")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # 1. Sheet 1: Executive Summary
    ws_exec = wb.active
    ws_exec.title = "Executive Summary"
    ws_exec.views.sheetView[0].showGridLines = True
    
    ws_exec["A1"] = "AI BUSINESS REQUIREMENTS & FINANCIAL ESTIMATION MODEL"
    ws_exec["A1"].font = Font(name="Calibri", size=16, bold=True, color="0E7490")
    ws_exec["A2"] = f"Project: {brd.project_title} | Client: {brd.client_name}"
    ws_exec["A2"].font = Font(name="Calibri", size=11, italic=True, color="64748B")

    summary_kpis = [
        ("Delivery Tier", brd.delivery_tier),
        ("Reference Duration (Weeks)", brd.reference_duration_weeks),
        ("Resolved Duration (Weeks)", brd.total_duration_weeks),
        ("Total Person-Days", brd.total_person_days),
        ("Total Person-Hours", brd.total_person_hours),
        ("Blended Hourly Rate (USD)", brd.blended_hourly_rate),
        ("Total Labour Cost (USD)", brd.total_labour_cost_usd),
        ("Monthly Cloud Infrastructure (USD)", brd.sizing_metrics.total_monthly_cloud_cost_usd),
        ("Standby Buffer Staffing", f"{brd.buffer_capacity_pct}%"),
        ("Target Kick-Off Date", brd.start_date),
        ("Target Completion Date", brd.target_end_date)
    ]
    
    for row_idx, (k, v) in enumerate(summary_kpis, start=4):
        ws_exec.cell(row=row_idx, column=1, value=k).font = Font(name="Calibri", size=11, bold=True)
        c_val = ws_exec.cell(row=row_idx, column=2, value=v)
        c_val.font = Font(name="Calibri", size=11)
        if isinstance(v, float):
            c_val.number_format = "$#,##0.00" if "Cost" in k or "Rate" in k else "#,##0.0"

    # 2. Sheet 2: 12-Discipline Resource Loading
    ws_roles = wb.create_sheet(title="12 Disciplines Resource Loading")
    ws_roles.views.sheetView[0].showGridLines = True
    
    role_headers = ["Role Code", "Discipline Name", "Standing Scope", "Days (d)", "Hours (h)", "Blended Rate ($/h)", "Total Labour Cost ($)", "Active FTE", "Buffer FTE (+15%)", "Total Staffed FTE"]
    for col_idx, h in enumerate(role_headers, start=1):
        cell = ws_roles.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx, r in enumerate(brd.role_efforts, start=2):
        ws_roles.cell(row=r_idx, column=1, value=r.role_code).alignment = Alignment(horizontal="center")
        ws_roles.cell(row=r_idx, column=2, value=r.role).font = Font(bold=True)
        ws_roles.cell(row=r_idx, column=3, value=r.description)
        ws_roles.cell(row=r_idx, column=4, value=r.days).number_format = "#,##0.0"
        ws_roles.cell(row=r_idx, column=5, value=f"=D{r_idx}*{brd.daily_working_hours}").number_format = "#,##0"
        ws_roles.cell(row=r_idx, column=6, value=brd.blended_hourly_rate).number_format = "$#,##0.00"
        ws_roles.cell(row=r_idx, column=7, value=f"=E{r_idx}*F{r_idx}").number_format = "$#,##0.00"
        ws_roles.cell(row=r_idx, column=8, value=r.active_fte).number_format = "0.00"
        ws_roles.cell(row=r_idx, column=9, value=r.buffer_fte).number_format = "0.00"
        ws_roles.cell(row=r_idx, column=10, value=f"=H{r_idx}+I{r_idx}").number_format = "0.00"

    # Total row for roles
    last_r = len(brd.role_efforts) + 2
    ws_roles.cell(row=last_r, column=1, value="TOTAL")
    ws_roles.cell(row=last_r, column=2, value="12 Disciplines Standardized")
    ws_roles.cell(row=last_r, column=4, value=f"=SUM(D2:D{last_r-1})").number_format = "#,##0.0"
    ws_roles.cell(row=last_r, column=5, value=f"=SUM(E2:E{last_r-1})").number_format = "#,##0"
    ws_roles.cell(row=last_r, column=7, value=f"=SUM(G2:G{last_r-1})").number_format = "$#,##0.00"
    for col_idx in range(1, 11):
        c = ws_roles.cell(row=last_r, column=col_idx)
        c.font = total_font
        c.fill = total_fill

    # 3. Sheet 3: Cloud BoM & 3-Year TCO
    ws_bom = wb.create_sheet(title="Cloud BoM & 3-Yr TCO")
    ws_bom.views.sheetView[0].showGridLines = True
    
    bom_headers = ["Component", "Cloud SKU / Resource", "Tier / Dimension", "Quantity", "Monthly Cost (USD)", "Annual Cost (USD)", "Architecture Justification"]
    for col_idx, h in enumerate(bom_headers, start=1):
        cell = ws_bom.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill

    for b_idx, b in enumerate(brd.sizing_bom, start=2):
        ws_bom.cell(row=b_idx, column=1, value=b.component).font = Font(bold=True)
        ws_bom.cell(row=b_idx, column=2, value=b.sku_or_service)
        ws_bom.cell(row=b_idx, column=3, value=b.tier)
        ws_bom.cell(row=b_idx, column=4, value=b.quantity)
        ws_bom.cell(row=b_idx, column=5, value=b.monthly_cost_usd).number_format = "$#,##0.00"
        ws_bom.cell(row=b_idx, column=6, value=f"=E{b_idx}*12").number_format = "$#,##0.00"
        ws_bom.cell(row=b_idx, column=7, value=b.justification)

    # Auto-adjust column widths
    for ws in [ws_exec, ws_roles, ws_bom]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    wb.save(output_path)
    return output_path

def generate_jira_backlog_csv(brd: BRDDocument, output_path: str) -> str:
    """Generates a standard Jira / Azure DevOps importable CSV backlog with Epics, Stories, and Tasks."""
    fieldnames = [
        "Issue Type", "Key", "Summary", "Description", "Phase", 
        "Primary Role", "Original Estimate (Hours)", "Story Points", 
        "Priority", "Component", "Acceptance Criteria"
    ]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write 18 Phase Epics
        for p_idx, phase in enumerate(brd.project_phases, start=1):
            epic_key = f"EPIC-{phase.phase_code}"
            writer.writerow({
                "Issue Type": "Epic",
                "Key": epic_key,
                "Summary": f"[{phase.phase_code}] {phase.phase_name}",
                "Description": f"Phase Duration: {phase.weeks:.1f} Weeks | Effort: {phase.effort_days:.1f} Person-Days. Deliverables: {', '.join(phase.key_deliverables)}",
                "Phase": phase.phase_name,
                "Primary Role": "Lead Solution Architect / Project Manager",
                "Original Estimate (Hours)": round(phase.effort_days * brd.daily_working_hours, 1),
                "Story Points": int(phase.effort_days * 1.5),
                "Priority": "High",
                "Component": brd.project_title,
                "Acceptance Criteria": f"All deliverables verified and signed off for {phase.phase_name}."
            })
            
        # Write Granular Tasks
        for t_idx, task in enumerate(brd.task_estimates, start=1):
            writer.writerow({
                "Issue Type": "Task",
                "Key": f"TASK-{task.phase_code}-{t_idx:03d}",
                "Summary": task.task_name,
                "Description": f"Task in {task.phase_name}. Primary: {task.primary_role} | Support: {task.support_roles}. Uplift: {task.uplift_tag}",
                "Phase": task.phase_name,
                "Primary Role": task.primary_role,
                "Original Estimate (Hours)": round(task.effort_days * brd.daily_working_hours, 1),
                "Story Points": max(1, int(task.effort_days)),
                "Priority": "Medium" if task.uplift_tag == "NONE" else "High",
                "Component": task.phase_code,
                "Acceptance Criteria": f"Verified implementation of {task.task_name} against {brd.delivery_tier} specifications."
            })
            
    return output_path

def generate_pdf_brd(brd: BRDDocument, output_path: str) -> str:
    """Generates an executive-ready, corporate-grade PDF BRD document per reference.txt."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        alignment=1, # Center
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0E7490'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'SecBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("BUSINESS REQUIREMENTS DOCUMENT (BRD)", title_style))
    story.append(Paragraph(f"{brd.project_title.upper()}", title_style))
    story.append(Paragraph(f"Client: {brd.client_name} &nbsp;|&nbsp; Delivery Tier: {brd.delivery_tier} ({brd.tier_kind}) &nbsp;|&nbsp; Duration: {brd.total_duration_weeks:.1f} Weeks", subtitle_style))
    story.append(Spacer(1, 8))

    # Summary Stats Table
    stats_data = [
        [
            Paragraph("<b>Total Effort:</b>", table_cell_style),
            Paragraph(f"{brd.total_person_days:.1f} Person-Days ({brd.total_person_hours:.0f} hrs)", table_cell_style),
            Paragraph("<b>Total Labour Cost:</b>", table_cell_style),
            Paragraph(f"{brd.currency_symbol}{brd.total_labour_cost_usd:,.2f} ({brd.currency_symbol}{brd.blended_hourly_rate:.0f}/hr)", table_cell_style),
        ],
        [
            Paragraph("<b>Working Calendar:</b>", table_cell_style),
            Paragraph(f"{brd.daily_working_hours:.1f} hrs/day, 5 days/wk", table_cell_style),
            Paragraph("<b>Cloud Infrastructure:</b>", table_cell_style),
            Paragraph(f"${brd.sizing_metrics.total_monthly_cloud_cost_usd:,.2f}/mo", table_cell_style),
        ],
        [
            Paragraph("<b>Start / End Dates:</b>", table_cell_style),
            Paragraph(f"{brd.start_date} &rarr; {brd.target_end_date}", table_cell_style),
            Paragraph("<b>Feasibility Status:</b>", table_cell_style),
            Paragraph("FEASIBLE (All constraints satisfied)" if brd.schedule_feasibility.is_feasible else f"STRETCHED (+{brd.schedule_feasibility.resolved_duration_weeks - brd.schedule_feasibility.reference_duration_weeks:.1f} wks)", table_cell_style),
        ]
    ]
    t_stats = Table(stats_data, colWidths=[110, 155, 110, 155])
    t_stats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_stats)
    story.append(Spacer(1, 12))

    # 1. Introduction
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph(
        f"<b>Version:</b> 1.0.0<br/>"
        f"This Business Requirements Document (BRD) outlines the purpose, scope, and objectives of <b>{brd.project_title}</b>. "
        f"It provides a detailed description of business needs and the requirements that the solution must fulfill. "
        f"This document serves as a formal agreement between stakeholders and the project team on the expected deliverables.",
        body_style
    ))
    if brd.executive_summary:
        story.append(Paragraph(brd.executive_summary, body_style))
    story.append(Spacer(1, 6))

    # 2. Project Overview
    story.append(Paragraph("2. Project Overview", h1_style))
    story.append(Paragraph(f"<b>2.1 Business Context & Justification:</b> {brd.problem_statement}", body_style))
    story.append(Paragraph("<b>2.2 Strategic Objectives & Expected Benefits:</b>", body_style))
    for imp in brd.business_impacts:
        story.append(Paragraph(f"&bull; {imp}", body_style))
    story.append(Spacer(1, 6))

    # 3. Scope
    story.append(Paragraph("3. Scope", h1_style))
    scope_data = [[Paragraph("<b>In-Scope Deliverables</b>", table_header_style), Paragraph("<b>Explicitly Out-of-Scope</b>", table_header_style)]]
    max_len = max(len(brd.in_scope), len(brd.out_of_scope))
    for i in range(max_len):
        in_s = brd.in_scope[i] if i < len(brd.in_scope) else ""
        out_s = brd.out_of_scope[i] if i < len(brd.out_of_scope) else ""
        scope_data.append([Paragraph(f"&bull; {in_s}", table_cell_style), Paragraph(f"&bull; {out_s}", table_cell_style)])
    
    t_scope = Table(scope_data, colWidths=[265, 265])
    t_scope.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_scope)
    story.append(Spacer(1, 8))

    # 4. Business Requirements
    story.append(Paragraph("4. Business Requirements (Prioritized by MoSCoW)", h1_style))
    br_pdf_data = [
        [Paragraph("<b>Req ID</b>", table_header_style), Paragraph("<b>Requirement Title & Statement</b>", table_header_style), Paragraph("<b>MoSCoW</b>", table_header_style)],
        [Paragraph("<b>BR-1</b>", table_cell_style), Paragraph("The system shall allow users to securely authenticate using unique corporate credentials and role-based permissions.", table_cell_style), Paragraph("<b>MUST</b>", table_cell_style)],
        [Paragraph("<b>BR-2</b>", table_cell_style), Paragraph("The system shall provide real-time reporting, operational metrics visibility, and KPI tracking dashboards.", table_cell_style), Paragraph("<b>MUST</b>", table_cell_style)],
        [Paragraph("<b>BR-3</b>", table_cell_style), Paragraph("The system shall support multi-tiered user roles (e.g. Employee, Manager, Admin) with granular permission boundaries.", table_cell_style), Paragraph("<b>MUST</b>", table_cell_style)],
        [Paragraph("<b>BR-4</b>", table_cell_style), Paragraph("The system shall enable standardized data import and export capabilities (JSON, CSV, REST APIs).", table_cell_style), Paragraph("<b>SHOULD</b>", table_cell_style)],
        [Paragraph("<b>BR-5</b>", table_cell_style), Paragraph("The system shall ensure compliance with applicable enterprise security, privacy, and statutory regulations.", table_cell_style), Paragraph("<b>MUST</b>", table_cell_style)]
    ]
    t_br = Table(br_pdf_data, colWidths=[50, 420, 60])
    t_br.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_br)
    story.append(Spacer(1, 8))

    # 5. Functional Requirements
    story.append(Paragraph("5. Functional Requirements", h1_style))
    fr_pdf_data = [
        [Paragraph("<b>Req ID</b>", table_header_style), Paragraph("<b>Feature & Functional Behavior Specification</b>", table_header_style)],
        [Paragraph("<b>FR-1</b>", table_cell_style), Paragraph("<b>CRUD Transactions:</b> The system shall allow authorized users to create, read, update, and manage core transaction records.", table_cell_style)],
        [Paragraph("<b>FR-2</b>", table_cell_style), Paragraph("<b>Interactive Dashboard:</b> The system shall provide an interactive dashboard with status widgets, charts, and activity summaries.", table_cell_style)],
        [Paragraph("<b>FR-3</b>", table_cell_style), Paragraph("<b>Automated Notifications:</b> The system shall send automated notifications (email, in-app) triggered by status changes and approvals.", table_cell_style)],
        [Paragraph("<b>FR-4</b>", table_cell_style), Paragraph("<b>Immutable Audit Logs:</b> The system shall maintain comprehensive audit logs of all user actions, timestamped with user ID.", table_cell_style)],
        [Paragraph("<b>FR-5</b>", table_cell_style), Paragraph("<b>Enterprise Integrations:</b> The system shall interface securely with upstream enterprise systems via authenticated REST endpoints.", table_cell_style)]
    ]
    t_fr = Table(fr_pdf_data, colWidths=[50, 480])
    t_fr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_fr)
    story.append(Spacer(1, 8))

    # 6. Non-Functional Requirements
    story.append(Paragraph("6. Non-Functional Requirements", h1_style))
    nfr_items_pdf = [
        ("NFR-1", "Performance & Latency SLA", "The system shall respond to 95% of standard user requests within two (2.0) seconds under peak load."),
        ("NFR-2", "High Availability & Uptime", f"The system shall guarantee {getattr(brd, 'ha_dr_tier', 'Standard High Availability (99.5%)')} uptime availability (99.5% - 99.9%), excluding scheduled maintenance."),
        ("NFR-3", "Regulatory & Security Standards", f"The system shall comply with {getattr(brd, 'compliance_framework', 'ISO 27001 / GDPR / SOC2')} standards and regional data protection regulations."),
        ("NFR-4", "Accessibility & Usability", "The user interface shall support Web Content Accessibility Guidelines (WCAG 2.1 Level AA)."),
        ("NFR-5", "Data Encryption & Protection", "All sensitive data shall be encrypted in-transit (TLS 1.3) and at-rest (AES-256) with secure key management.")
    ]
    for n_id, n_title, n_desc in nfr_items_pdf:
        story.append(Paragraph(f"&bull; <b>{n_id} ({n_title}):</b> {n_desc}", body_style))
    story.append(Spacer(1, 8))

    # 7. Assumptions & Constraints
    story.append(Paragraph("7. Assumptions and Constraints", h1_style))
    story.append(Paragraph(f"&bull; Project assumes active weekly participation of designated business SMEs for validation.", body_style))
    story.append(Paragraph(f"&bull; Deployment executes within designated cloud infrastructure without requiring unapproved firewall exceptions.", body_style))
    story.append(Paragraph(f"&bull; Delivery timeline is calibrated to {brd.total_duration_weeks:.1f} weeks ({brd.delivery_tier} tier) with {brd.buffer_capacity_pct:.0f}% standby capacity.", body_style))
    story.append(Spacer(1, 8))

    # 8. Dependencies
    story.append(Paragraph("8. Dependencies", h1_style))
    story.append(Paragraph("&bull; Enterprise Identity Provider (Azure AD / Okta / SSO) configuration and credentials.", body_style))
    story.append(Paragraph("&bull; Cloud tenant subscription provisioning and database storage allocation.", body_style))
    story.append(Paragraph("&bull; Upstream system schema contracts and test environment data access.", body_style))
    story.append(Spacer(1, 8))

    # 9. Acceptance Criteria
    story.append(Paragraph("9. Acceptance Criteria", h1_style))
    story.append(Paragraph("&bull; 100% of defined business and functional requirements verified against automated test suites.", body_style))
    story.append(Paragraph("&bull; Performance and latency SLA thresholds verified (<2.0s response under peak concurrency).", body_style))
    story.append(Paragraph("&bull; Security VAPT audit and statutory compliance verification passed without critical blockers.", body_style))
    story.append(Paragraph("&bull; Formal User Acceptance Testing (UAT) sign-off completed by executive sponsor.", body_style))
    story.append(Spacer(1, 8))

    # 10. Glossary
    story.append(Paragraph("10. Glossary of Terms", h1_style))
    glossary_pdf = [
        ("BRD", "Business Requirements Document"),
        ("WBS", "Work Breakdown Structure (18-phase standardized decomposition)"),
        ("SLA / RTO / RPO", "Service Level Agreement / Recovery Time & Point Objectives"),
        ("RBAC / SSO", "Role-Based Access Control / Single Sign-On Authentication"),
        ("WCAG / FinOps", "Web Content Accessibility Guidelines / Financial Operations Cloud BoM")
    ]
    for term, definition in glossary_pdf:
        story.append(Paragraph(f"&bull; <b>{term}:</b> {definition}", body_style))
    story.append(Spacer(1, 8))

    # 11. Signatures
    story.append(Paragraph("11. Formal Stakeholder Signatures & Approvals", h1_style))
    sign_pdf_data = [
        [Paragraph("<b>Stakeholder Role</b>", table_header_style), Paragraph("<b>Representative Name</b>", table_header_style), Paragraph("<b>Signature</b>", table_header_style), Paragraph("<b>Date</b>", table_header_style)],
        [Paragraph("Project Sponsor (Executive)", table_cell_style), Paragraph(brd.client_name, table_cell_style), Paragraph("___________________", table_cell_style), Paragraph("____ / ____ / 2026", table_cell_style)],
        [Paragraph("Lead Business Analyst", table_cell_style), Paragraph("AI Practice Business Analysis Lead", table_cell_style), Paragraph("___________________", table_cell_style), Paragraph("____ / ____ / 2026", table_cell_style)],
        [Paragraph("Principal Solutions Architect", table_cell_style), Paragraph("Enterprise Architecture Lead", table_cell_style), Paragraph("___________________", table_cell_style), Paragraph("____ / ____ / 2026", table_cell_style)]
    ]
    t_sign = Table(sign_pdf_data, colWidths=[150, 160, 120, 100])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sign)
    story.append(Spacer(1, 12))

    # 12. 12-Discipline Resource Allocation & Cost
    story.append(Paragraph("12. 12-Discipline Resource Allocation & Cost Plan", h1_style))
    roles_table_data = [[
        Paragraph("<b>Code</b>", table_header_style),
        Paragraph("<b>Discipline Role</b>", table_header_style),
        Paragraph("<b>Days</b>", table_header_style),
        Paragraph("<b>Hours</b>", table_header_style),
        Paragraph("<b>Rate</b>", table_header_style),
        Paragraph("<b>Cost</b>", table_header_style),
        Paragraph("<b>FTE</b>", table_header_style)
    ]]
    for r in brd.role_efforts:
        roles_table_data.append([
            Paragraph(r.role_code, table_cell_style),
            Paragraph(r.role, table_cell_style),
            Paragraph(f"{r.days:.1f} d", table_cell_style),
            Paragraph(f"{r.hours:.0f} h", table_cell_style),
            Paragraph(f"${r.rate_hourly:.0f}/h", table_cell_style),
            Paragraph(f"${r.cost:,.0f}", table_cell_style),
            Paragraph(f"{r.total_assigned_fte:.2f}", table_cell_style),
        ])
    roles_table_data.append([
        Paragraph("<b>TOTAL</b>", table_cell_style),
        Paragraph("<b>12 Disciplines Standardized</b>", table_cell_style),
        Paragraph(f"<b>{brd.total_person_days:.1f} d</b>", table_cell_style),
        Paragraph(f"<b>{brd.total_person_hours:.0f} h</b>", table_cell_style),
        Paragraph(f"<b>${brd.blended_hourly_rate:.0f}/h</b>", table_cell_style),
        Paragraph(f"<b>${brd.total_labour_cost_usd:,.0f}</b>", table_cell_style),
        Paragraph("-", table_cell_style),
    ])
    t_roles = Table(roles_table_data, colWidths=[40, 160, 55, 55, 55, 80, 85])
    t_roles.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_roles)
    story.append(Spacer(1, 10))

    # 13. Cloud Infrastructure Bill of Materials
    story.append(Paragraph("13. Cloud Infrastructure Bill of Materials (BoM)", h1_style))
    bom_data = [[
        Paragraph("<b>Component</b>", table_header_style),
        Paragraph("<b>SKU / Service</b>", table_header_style),
        Paragraph("<b>Tier</b>", table_header_style),
        Paragraph("<b>Monthly (USD)</b>", table_header_style),
        Paragraph("<b>Justification</b>", table_header_style)
    ]]
    for b in brd.sizing_bom:
        bom_data.append([
            Paragraph(b.component, table_cell_style),
            Paragraph(b.sku_or_service, table_cell_style),
            Paragraph(b.tier, table_cell_style),
            Paragraph(f"${b.monthly_cost_usd:,.2f}", table_cell_style),
            Paragraph(b.justification, table_cell_style)
        ])
    t_bom = Table(bom_data, colWidths=[80, 140, 80, 70, 160])
    t_bom.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_bom)
    story.append(Spacer(1, 10))

    # 14. Technical Components
    story.append(Paragraph("14. Technical Architecture Components", h1_style))
    comp_data = [[
        Paragraph("<b>ID</b>", table_header_style),
        Paragraph("<b>Name</b>", table_header_style),
        Paragraph("<b>Technology</b>", table_header_style),
        Paragraph("<b>Key Design Decisions & Security</b>", table_header_style)
    ]]
    for c in brd.technical_components:
        comp_data.append([
            Paragraph(c.id, table_cell_style),
            Paragraph(c.name, table_cell_style),
            Paragraph(c.technology_choice or c.technology, table_cell_style),
            Paragraph(f"{c.key_design_decisions} | {c.security_rai_controls}", table_cell_style)
        ])
    t_comp = Table(comp_data, colWidths=[40, 120, 120, 250])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E7490')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_comp)

    doc.build(story)
    return output_path

def generate_structured_brd_json(
    brd: BRDDocument,
    session: ProjectSession,
    output_dir: str = "exports"
) -> Tuple[str, Dict[str, Any]]:
    """
    Generates a structured, machine-readable JSON document conforming to the
    AI Project BRD Questionnaire & Output Template schema (AWS, Azure, GCP, IBM Cloud).
    Saves to disk with project name and version format: {safe_project_name}_{version}_brd.json
    """
    import re
    import json
    
    os.makedirs(output_dir, exist_ok=True)
    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', brd.project_title.lower()).strip('_')[:50].rstrip('_')
    ver_str = getattr(brd, "version", "1.0.0") or "1.0.0"
    ver_tag = str(ver_str).replace(".", "_")
    filename = f"{safe_title}_v{ver_tag}_brd.json"
    file_path = os.path.join(output_dir, filename)

    
    conf_score = getattr(session.confidence, "score", 96.5) if hasattr(session, "confidence") and session.confidence else 96.5
    
    # Structure matching ai_brd_questionnaire_template.json output schema
    structured_doc = {
        "template_name": "AI Project BRD Questionnaire & Output Template (AWS, Azure, GCP, IBM Cloud)",
        "template_version": "2.0.0",
        "document_control": {
            "project_name": brd.project_title,
            "project_slug": safe_title,
            "client_name": brd.client_name,
            "version": ver_str,
            "generation_timestamp": datetime.now().isoformat(),
            "delivery_tier": getattr(brd, "delivery_tier", "PoC"),
            "cloud_provider": brd.cloud_platform,
            "target_geography": getattr(brd, "target_geography", "India"),
            "agent_confidence_score": round(conf_score, 1),
            "confidence_gate_passed": conf_score >= 95.0,
            "governance_status": "APPROVED_FOR_SYNTHESIS" if conf_score >= 95.0 else "IN_DISCOVERY"
        },
        "executive_summary": {
            "summary_text": brd.executive_summary,
            "business_problem": brd.problem_statement,
            "solution_summary": brd.solution_summary_six_sentences,
            "in_scope_domains": getattr(brd, "in_scope", []),
            "target_tier": getattr(brd, "delivery_tier", "PoC")
        },
        "project_requirements": {
            "problem_statement": getattr(brd, "problem_statement", ""),
            "business_objectives": getattr(brd, "business_impacts", []),
            "in_scope_scope_boundaries": getattr(brd, "in_scope", []),
            "out_of_scope_boundaries": getattr(brd, "out_of_scope", []),
            "user_personas": [
                {
                    "persona": p.get("persona") or p.get("role") or str(p) if isinstance(p, dict) else getattr(p, "persona", getattr(p, "role", str(p))),
                    "need": p.get("need") or p.get("description") or "" if isinstance(p, dict) else getattr(p, "need", getattr(p, "description", ""))
                } for p in getattr(brd, "user_personas", [])
            ],
            "system_capabilities": [
                {
                    "capability_id": c.get("capability_id", "") if isinstance(c, dict) else getattr(c, "capability_id", ""),
                    "category": c.get("category", "") if isinstance(c, dict) else getattr(c, "category", ""),
                    "name": c.get("name", "") if isinstance(c, dict) else getattr(c, "name", ""),
                    "description": c.get("description", "") if isinstance(c, dict) else getattr(c, "description", ""),
                    "scope_status": c.get("scope_status", "IN_SCOPE") if isinstance(c, dict) else getattr(c, "scope_status", "IN_SCOPE"),
                    "architecture_components": c.get("architecture_components", []) if isinstance(c, dict) else getattr(c, "architecture_components", []),
                    "applicable_wbs_tasks": c.get("applicable_wbs_tasks", []) if isinstance(c, dict) else getattr(c, "applicable_wbs_tasks", [])
                } for c in getattr(brd, "capabilities", [])
            ],
            "functional_requirements": [
                {
                    "requirement_id": req.get("requirement_id", "") if isinstance(req, dict) else getattr(req, "requirement_id", ""),
                    "type": req.get("type", "FUNCTIONAL") if isinstance(req, dict) else getattr(req, "type", "FUNCTIONAL"),
                    "statement": req.get("statement", "") if isinstance(req, dict) else getattr(req, "statement", ""),
                    "actor": req.get("actor", "System") if isinstance(req, dict) else getattr(req, "actor", "System"),
                    "capability": req.get("capability", "General") if isinstance(req, dict) else getattr(req, "capability", "General"),
                    "priority": req.get("priority", "MUST") if isinstance(req, dict) else getattr(req, "priority", "MUST"),
                    "source": req.get("source", "CLIENT") if isinstance(req, dict) else getattr(req, "source", "CLIENT"),
                    "status": req.get("status", "CONFIRMED") if isinstance(req, dict) else getattr(req, "status", "CONFIRMED"),
                    "acceptance_criteria": req.get("acceptance_criteria", []) if isinstance(req, dict) else getattr(req, "acceptance_criteria", [])
                } for req in getattr(brd, "canonical_requirements", []) if (req.get("type") if isinstance(req, dict) else getattr(req, "type", "FUNCTIONAL")) == "FUNCTIONAL"
            ],
            "non_functional_requirements": [
                {
                    "requirement_id": req.get("requirement_id", "") if isinstance(req, dict) else getattr(req, "requirement_id", ""),
                    "type": req.get("type", "NFR") if isinstance(req, dict) else getattr(req, "type", "NFR"),
                    "statement": req.get("statement", "") if isinstance(req, dict) else getattr(req, "statement", ""),
                    "actor": req.get("actor", "System") if isinstance(req, dict) else getattr(req, "actor", "System"),
                    "capability": req.get("capability", "General") if isinstance(req, dict) else getattr(req, "capability", "General"),
                    "priority": req.get("priority", "MUST") if isinstance(req, dict) else getattr(req, "priority", "MUST"),
                    "status": req.get("status", "CONFIRMED") if isinstance(req, dict) else getattr(req, "status", "CONFIRMED"),
                    "acceptance_criteria": req.get("acceptance_criteria", []) if isinstance(req, dict) else getattr(req, "acceptance_criteria", [])
                } for req in getattr(brd, "canonical_requirements", []) if (req.get("type") if isinstance(req, dict) else getattr(req, "type", "FUNCTIONAL")) != "FUNCTIONAL"
            ],
            "responsible_ai_and_governance": getattr(brd, "responsible_ai_governance", [])
        },
        "system_architecture_and_cloud_inventory": {
            "target_cloud": getattr(brd, "cloud_platform", "Microsoft Azure"),
            "architecture_narrative": getattr(brd, "target_architecture_narrative", ""),
            "data_flow_narrative": getattr(brd, "data_flow_narrative", ""),
            "cloud_service_inventory": [
                {
                    "component": b.get("component", "") if isinstance(b, dict) else getattr(b, "component", ""),
                    "sku_service": b.get("sku_or_service", "") if isinstance(b, dict) else getattr(b, "sku_or_service", ""),
                    "tier": b.get("tier", "") if isinstance(b, dict) else getattr(b, "tier", ""),
                    "monthly_cost_usd": b.get("monthly_cost_usd", 0.0) if isinstance(b, dict) else getattr(b, "monthly_cost_usd", 0.0),
                    "justification": b.get("justification", "") if isinstance(b, dict) else getattr(b, "justification", "")
                } for b in getattr(brd, "sizing_bom", [])
            ],
            "technical_components": [
                {
                    "id": c.get("id", "") if isinstance(c, dict) else getattr(c, "id", ""),
                    "name": c.get("name", "") if isinstance(c, dict) else getattr(c, "name", ""),
                    "technology": (c.get("technology_choice") or c.get("technology", "")) if isinstance(c, dict) else (getattr(c, "technology_choice", "") or getattr(c, "technology", "")),
                    "key_design_decisions": c.get("key_design_decisions", "") if isinstance(c, dict) else getattr(c, "key_design_decisions", ""),
                    "security_controls": c.get("security_rai_controls", "") if isinstance(c, dict) else getattr(c, "security_rai_controls", ""),
                    "scalability": c.get("scalability_performance", "") if isinstance(c, dict) else getattr(c, "scalability_performance", "")
                } for c in getattr(brd, "technical_components", [])
            ],
            "monthly_infrastructure_total_usd": round(getattr(brd.sizing_metrics, "total_monthly_cloud_cost_usd", 0.0) if hasattr(brd, "sizing_metrics") and brd.sizing_metrics else 0.0, 2),
            "three_year_cloud_tco_usd": round((getattr(brd.sizing_metrics, "total_monthly_cloud_cost_usd", 0.0) if hasattr(brd, "sizing_metrics") and brd.sizing_metrics else 0.0) * 36, 2)
        },
        "estimations_and_delivery_plan": {
            "delivery_tier": getattr(brd, "delivery_tier", "PoC"),
            "tier_kind": getattr(brd, "tier_kind", "Base"),
            "headline_weight": getattr(brd, "headline_weight", 0.289),
            "duration_weeks": getattr(brd, "total_duration_weeks", 6.0),
            "reference_duration_weeks": getattr(brd, "reference_duration_weeks", 6.0),
            "start_date": getattr(brd, "start_date", ""),
            "target_end_date": getattr(brd, "target_end_date", ""),
            "total_person_days": getattr(brd, "total_person_days", 0.0),
            "total_person_hours": getattr(brd, "total_person_hours", 0.0),
            "blended_hourly_rate_usd": getattr(brd, "blended_hourly_rate", 28.13),
            "total_labour_cost_usd": getattr(brd, "total_labour_cost_usd", 0.0),
            "monthly_cloud_cost_usd": round(getattr(brd.sizing_metrics, "total_monthly_cloud_cost_usd", 0.0) if hasattr(brd, "sizing_metrics") and brd.sizing_metrics else 0.0, 2),
            "three_year_cloud_tco_usd": round((getattr(brd.sizing_metrics, "total_monthly_cloud_cost_usd", 0.0) if hasattr(brd, "sizing_metrics") and brd.sizing_metrics else 0.0) * 36, 2),
            "eighteen_phase_wbs_roadmap": [
                {
                    "phase_code": p.get("phase_code", "") if isinstance(p, dict) else getattr(p, "phase_code", ""),
                    "name": p.get("phase_name", "") if isinstance(p, dict) else getattr(p, "phase_name", ""),
                    "duration_weeks": p.get("weeks", 0.0) if isinstance(p, dict) else getattr(p, "weeks", 0.0),
                    "effort_days": p.get("effort_days", 0.0) if isinstance(p, dict) else getattr(p, "effort_days", 0.0),
                    "deliverables": p.get("key_deliverables", []) if isinstance(p, dict) else getattr(p, "key_deliverables", []),
                    "roles": p.get("roles_involved", []) if isinstance(p, dict) else getattr(p, "roles_involved", [])
                } for p in getattr(brd, "project_phases", [])
            ],
            "twelve_disciplines_resource_loading": [
                {
                    "role_code": r.get("role_code", "") if isinstance(r, dict) else getattr(r, "role_code", ""),
                    "role_name": r.get("role", "") if isinstance(r, dict) else getattr(r, "role", ""),
                    "person_days": r.get("days", 0.0) if isinstance(r, dict) else getattr(r, "days", 0.0),
                    "person_hours": r.get("hours", 0.0) if isinstance(r, dict) else getattr(r, "hours", 0.0),
                    "cost_usd": r.get("cost", 0.0) if isinstance(r, dict) else getattr(r, "cost", 0.0),
                    "assigned_fte": r.get("total_assigned_fte", 0.0) if isinstance(r, dict) else getattr(r, "total_assigned_fte", 0.0)
                } for r in getattr(brd, "role_efforts", [])
            ]
        },
        "governance_compliance_and_risks": {
            "assumptions": [
                {
                    "id": a.get("id", "") if isinstance(a, dict) else getattr(a, "id", ""),
                    "statement": a.get("statement", "") if isinstance(a, dict) else getattr(a, "statement", ""),
                    "impact": a.get("impact_if_wrong", "") if isinstance(a, dict) else getattr(a, "impact_if_wrong", ""),
                    "confidence": a.get("confidence", "Medium") if isinstance(a, dict) else getattr(a, "confidence", "Medium")
                } for a in getattr(brd, "assumptions", [])
            ],
            "ai_act_classification": getattr(brd, "ai_act_classification", {"risk_tier": "Minimal / Specific Transparency"}),
            "security_frameworks": ["ISO 42001", "EU AI Act", "SOC 2 Type II", "TLS 1.3", "RBAC", "CMEK"]
        },
        "questionnaire_answers_store": {
            k: {
                "question_id": v.question_id,
                "question_title": v.question_title,
                "answer": v.answer,
                "is_default": v.is_default
            } for k, v in session.answers.items()
        }
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(structured_doc, f, indent=2, ensure_ascii=False)

        
    return file_path, structured_doc


