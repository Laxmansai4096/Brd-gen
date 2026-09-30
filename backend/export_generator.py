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

    doc.add_heading("1. Executive Summary & Problem Context", level=1)
    doc.add_paragraph(brd.executive_summary)
    
    doc.add_heading("1.1 Problem Statement & Manual Bottlenecks", level=2)
    doc.add_paragraph(brd.problem_statement)

    doc.add_heading("1.2 Business Value & Expected Impacts", level=2)
    for imp in brd.business_impacts:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(imp)

    doc.add_heading("2. Solution Architecture & Scope Demarcation", level=1)
    doc.add_paragraph(brd.solution_summary_six_sentences)
    doc.add_paragraph(brd.target_architecture_narrative)

    doc.add_heading("2.1 In-Scope Deliverables", level=2)
    for item in brd.in_scope:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    doc.add_heading("2.2 Explicitly Out-of-Scope", level=2)
    for item in brd.out_of_scope:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    doc.add_heading("3. 12-Discipline Resource Allocation & Budget", level=1)
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

    doc.add_heading("4. Cloud Infrastructure Bill of Materials (BoM)", level=1)
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

    doc.add_heading("5. Regulatory, Security & Responsible AI Governance", level=1)
    for gov in brd.responsible_ai_governance:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(gov)

    doc.add_heading("6. Formal Stakeholder Sign-Off & Approvals", level=1)
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
        ("Client Executive Sponsor", brd.client_name),
        ("Lead Solutions Architect", "AI Practice Architecture Team"),
        ("Project Delivery Manager", "TCS Enterprise Delivery Lead")
    ]
    for s_idx, (s_role, s_name) in enumerate(sign_roles):
        row = sign_table.rows[s_idx + 1]
        row.cells[0].text = s_role
        row.cells[1].text = s_name
        row.cells[2].text = "___________________"
        row.cells[3].text = "____ / ____ / 2026"
        for cell in row.cells:
            set_cell_margins(cell, 120, 120, 80, 80)

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
