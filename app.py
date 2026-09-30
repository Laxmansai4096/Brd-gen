import os
import uuid
import json
import re
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.models import (
    ProjectSession, ChatMessage, AnswerItem, BRDDocument,
    AssumptionItem, TaskEstimate, RoleEffort, ProjectPhase,
    TechnicalComponent, SizingMetrics, SizingBOM, HITLGates
)
from backend.agent_discovery import (
    STATIC_QUESTIONS, process_user_answer, get_current_question,
    get_discovery_questions, compile_and_save_handoff_dossier
)
from backend.agent_planner import generate_brd
from backend.pptx_generator import create_presentation_deck
from backend.file_processor import extract_text_from_file
from backend.export_generator import (
    generate_word_brd, generate_pdf_brd,
    generate_excel_financial_model, generate_jira_backlog_csv
)
from backend.llm_gateway import LLMGateway
from backend.impact_engine import calculate_change_impact
from backend.config import get_settings, update_settings, AISettings
from backend.admin_store import (
    get_admin_defaults, save_admin_defaults,
    get_calendars, upsert_calendar, delete_calendar,
    add_holiday_to_calendar, update_holiday_in_calendar, delete_holiday_from_calendar,
    parse_holiday_sheet, get_master_assumptions, save_master_assumptions,
    DELIVERY_TIERS
)

app = FastAPI(title="AI BRD Generator & Project Planner MVP")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory session store (keyed by session_id)
sessions: Dict[str, ProjectSession] = {}

def get_or_create_session(session_id: Optional[str] = None) -> ProjectSession:
    if not session_id or session_id not in sessions:
        sid = session_id or str(uuid.uuid4())
        q1 = STATIC_QUESTIONS[0]
        session = ProjectSession(
            session_id=sid,
            current_question_index=0,
            answers={},
            ambiguity_tracker={},
            uploaded_files=[],
            messages=[
                ChatMessage(
                    sender="agent",
                    content=(
                        "👋 **Hello! I am your AI Project Discovery & Solution Estimation Assistant.**\n\n"
                        "I will interview you to capture the project scope, business pain points, technical boundaries, "
                        "and scale/sizing drivers. Once our discovery is complete, **Agent 2 (Planner & Estimator)** will "
                        "synthesize a production-grade Business Requirements Document (BRD), 12-discipline resource loading "
                        "plan ($30/hr rate), 18-phase timeline, cloud Bill of Materials, component tech designs, and PowerPoint presentation deck.\n\n"
                        f"---\n\n"
                        f"### 📋 Question 1 of {len(STATIC_QUESTIONS)}: **{q1.title}**\n\n"
                        f"**{q1.prompt}**\n\n"
                        f"*(Example: {q1.help_text})*"
                    ),
                    timestamp="Just now",
                    question_context=q1
                )
            ]
        )
        sessions[sid] = session
        return session
    return sessions[session_id]

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/session")
def get_session_endpoint(session_id: Optional[str] = None):
    session = get_or_create_session(session_id)
    current_q = get_current_question(session)
    questions = get_discovery_questions()
    gates = getattr(session, "hitl_gates", None) or HITLGates()
    return {
        "session_id": session.session_id,
        "current_question_index": session.current_question_index,
        "total_questions": len(questions),
        "current_question": current_q.model_dump() if current_q else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "uploaded_files": session.uploaded_files,
        "messages": [m.model_dump() for m in session.messages],
        "has_brd": session.brd is not None,
        "brd": session.brd.model_dump() if session.brd else None,
        "has_handoff": session.handoff_dossier is not None,
        "handoff_data": session.handoff_dossier,
        "hitl_gates": gates.model_dump()
    }

class ChatInput(BaseModel):
    session_id: str
    message: str
    selected_option: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(payload: ChatInput):
    session = get_or_create_session(payload.session_id)
    answer_text = payload.selected_option if payload.selected_option else payload.message
    
    # Record user message
    session.messages.append(ChatMessage(
        sender="user",
        content=answer_text,
        timestamp="Just now"
    ))
    
    # Process through discovery agent
    reply_msg, is_complete = process_user_answer(session, answer_text)
    session.messages.append(reply_msg)
    
    if is_complete:
        # Compile handoff dossier
        compile_and_save_handoff_dossier(session)
        
        was_first_completion = (session.brd is None)
        
        # Generate/Update BRD & Project Plan via deterministic engine
        brd = generate_brd(session)
        session.brd = brd
        
        if was_first_completion:
            session.messages.append(ChatMessage(
                sender="agent",
                content=(
                    "🚀 **Agent 2 has successfully synthesized the Project Plan and BRD!**\n\n"
                    f"• **Project Title:** {brd.project_title}\n"
                    f"• **Client / Account:** {brd.client_name}\n"
                    f"• **Delivery Tier:** {brd.delivery_tier} ({brd.total_duration_weeks:.1f} Weeks)\n"
                    f"• **Total Effort:** {brd.total_person_days:.1f} Person-Days ({brd.total_person_hours:.0f} Hours)\n"
                    f"• **Total Labour Cost:** ${brd.total_labour_cost_usd:,.2f} (@ ${brd.blended_hourly_rate:.2f}/hr blended rate)\n"
                    f"• **Cloud Infra BoM:** ${brd.sizing_metrics.total_monthly_cloud_cost_usd:,.2f} / month ({session.answers.get('q_cloud', AnswerItem(question_id='q_cloud', question_title='Cloud', answer='Azure')).answer})\n"
                    f"• **Assumption Gate:** {'✅ PASSED (All Approved)' if brd.assumption_gate_passed else '⚠️ ACTION REQUIRED (Review Gate)'}\n\n"
                    "You can inspect the full BRD, 12-Discipline Resource Breakdown, 18-Phase Timeline, Component Tech Designs, Sizing Model, and Assumptions Gate on the right panel."
                ),
                timestamp="Just now"
            ))

    return {
        "session_id": session.session_id,
        "current_question": get_current_question(session).model_dump() if get_current_question(session) else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "has_brd": session.brd is not None,
        "brd": session.brd.model_dump() if session.brd else None,
        "has_handoff": session.handoff_dossier is not None,
        "handoff_data": session.handoff_dossier,
        "messages": [m.model_dump() for m in session.messages]
    }

from backend.models import (
    ProjectSession, ChatMessage, AnswerItem, BRDDocument,
    AssumptionItem, TaskEstimate, RoleEffort, ProjectPhase,
    TechnicalComponent, SizingMetrics, SizingBOM, RevisionSnapshot
)
from backend.agent_discovery import (
    STATIC_QUESTIONS, process_user_answer, get_current_question,
    get_discovery_questions, compile_and_save_handoff_dossier,
    auto_discover_from_document_text
)
from backend.agent_planner import generate_brd
from backend.pptx_generator import create_presentation_deck
from backend.file_processor import extract_text_from_file
from backend.export_generator import (
    generate_word_brd, generate_excel_financial_model, generate_jira_backlog_csv
)

def record_session_revision(session: ProjectSession, summary_change: str = "Plan Generated"):
    if not session.brd:
        return
    rev_num = len(session.revisions) + 1
    sym = session.brd.currency_symbol or "$"
    rate = session.brd.currency_exchange_rate or 1.0
    labour_cost = session.brd.total_labour_cost_converted or (session.brd.total_labour_cost_usd * rate)
    monthly_cloud = (session.brd.sizing_metrics.total_monthly_cloud_cost_usd if session.brd.sizing_metrics else 645.0) * rate

    snapshot = RevisionSnapshot(
        revision_id=str(uuid.uuid4())[:8],
        revision_number=rev_num,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tier=session.brd.delivery_tier,
        duration_weeks=session.brd.total_duration_weeks,
        person_days=session.brd.total_person_days,
        labour_cost_usd=session.brd.total_labour_cost_usd,
        summary_change=summary_change,
        trigger_reason=summary_change,
        total_duration_weeks=session.brd.total_duration_weeks,
        total_person_days=session.brd.total_person_days,
        total_labour_cost=labour_cost,
        monthly_cloud_cost=monthly_cloud,
        currency_code=session.brd.currency_code or "USD",
        currency_symbol=sym,
        brd_snapshot=session.brd.model_dump()
    )
    session.revisions.append(snapshot)

@app.post("/api/upload")
async def upload_file_endpoint(
    session_id: Optional[str] = Form(None),
    session_id_query: Optional[str] = Query(None, alias="session_id"),
    file: UploadFile = File(...)
):
    actual_session_id = session_id or session_id_query or str(uuid.uuid4())
    session = get_or_create_session(actual_session_id)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    extracted = extract_text_from_file(file_path, file.filename)
    full_text = extracted.get("full_text", "")
    session.uploaded_files.append({
        "filename": file.filename,
        "char_count": extracted.get("char_count", 0),
        "preview": extracted.get("preview", ""),
        "full_text": full_text
    })
    
    # Execute 0-Click Auto-Discovery from the ingested document
    discovery_summary = auto_discover_from_document_text(full_text, file.filename, session)
    
    # Synthesize BRD and plan immediately
    compile_and_save_handoff_dossier(session)
    brd = generate_brd(session)
    session.brd = brd
    record_session_revision(session, f"0-Click Auto-Discovery from '{file.filename}'")
    
    preview_snippet = extracted.get("preview", "")[:200] + "..."
    session.messages.append(ChatMessage(
        sender="system",
        content=(
            f"⚡ **0-Click Document Auto-Discovery Succeeded!**\n"
            f"Ingested `{file.filename}` ({extracted.get('char_count', 0):,} chars) with **{discovery_summary['confidence_score']}% Confidence**.\n\n"
            f"• **Client / Project:** {discovery_summary['client_name']}\n"
            f"• **Inferred Delivery Tier:** {discovery_summary['delivery_tier']}\n"
            f"• **Target Cloud:** {discovery_summary['cloud_platform']} in {discovery_summary['geography']}\n"
            f"• **Estimated Effort:** {brd.total_person_days:.1f} Person-Days (${brd.total_labour_cost_usd:,.2f}) across {brd.total_duration_weeks:.1f} Weeks\n\n"
            f"The full BRD, 12-discipline resourcing, cloud BoM, and Day-Wise execution schedule have been populated. You can review or adjust any parameter in the right panel."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "file": session.uploaded_files[-1],
        "discovery_summary": discovery_summary,
        "brd": brd.model_dump(),
        "has_brd": True,
        "messages": [m.model_dump() for m in session.messages]
    }

class AssumptionGateUpdate(BaseModel):
    session_id: str
    assumption_id: str
    status: str  # "Approve", "Correct", "Reject"
    reason: Optional[str] = ""

@app.post("/api/assumptions/update")
def update_assumption_gate_endpoint(payload: AssumptionGateUpdate):
    session = get_or_create_session(payload.session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    for a in session.brd.assumptions:
        if a.id == payload.assumption_id:
            a.status = payload.status
            a.reason = payload.reason
            break
            
    session.brd.assumption_gate_passed = all(a.status == "Approve" for a in session.brd.assumptions)
    return {"status": "success", "brd": session.brd.model_dump()}

class ReplanRequest(BaseModel):
    session_id: str
    overrides: Dict[str, str] = {}
    currency_code: Optional[str] = None

@app.post("/api/replan")
async def replan_endpoint(payload: ReplanRequest):
    session = get_or_create_session(payload.session_id)
    
    if payload.currency_code:
        session.answers["q_currency"] = AnswerItem(
            question_id="q_currency",
            question_title="Target Currency",
            answer=payload.currency_code,
            is_default=False
        )
    
    for q_id, new_val in payload.overrides.items():
        if q_id in session.answers:
            session.answers[q_id].answer = new_val
            session.answers[q_id].is_default = False
        else:
            session.answers[q_id] = AnswerItem(
                question_id=q_id,
                question_title=q_id,
                answer=new_val,
                is_default=False
            )
            
    brd = generate_brd(session)
    session.brd = brd
    compile_and_save_handoff_dossier(session)
    trigger_text = f"Currency changed to {payload.currency_code}" if payload.currency_code and not payload.overrides else f"Re-planned with {len(payload.overrides)} parameter overrides"
    record_session_revision(session, trigger_text)
    
    session.messages.append(ChatMessage(
        sender="agent",
        content=(
            "🔄 **Project Plan Recalculated!**\n\n"
            f"Updated plan reflected based on your custom parameters. Total effort adjusted to "
            f"**{brd.total_person_days:.1f} Days (${brd.total_labour_cost_usd:,.2f} @ ${brd.blended_hourly_rate:.2f}/hr)** across **{brd.total_duration_weeks:.1f} Weeks**."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "brd": brd.model_dump(),
        "has_handoff": session.handoff_dossier is not None,
        "handoff_data": session.handoff_dossier,
        "messages": [m.model_dump() for m in session.messages]
    }

@app.get("/api/revisions")
def get_revisions_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    return {
        "session_id": session.session_id,
        "revisions": [r.model_dump() for r in session.revisions]
    }

@app.get("/api/export/word")
def export_word_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"BRD_{safe_client}_{session.session_id[:8]}.docx"
    output_path = os.path.join(export_dir, filename)
    
    generate_word_brd(session.brd, output_path)
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )

@app.get("/api/export/excel")
def export_excel_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"Financial_Estimation_Model_{safe_client}_{session.session_id[:8]}.xlsx"
    output_path = os.path.join(export_dir, filename)
    
    generate_excel_financial_model(session.brd, output_path)
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@app.get("/api/export/jira")
def export_jira_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"Jira_Backlog_{safe_client}_{session.session_id[:8]}.csv"
    output_path = os.path.join(export_dir, filename)
    
    generate_jira_backlog_csv(session.brd, output_path)
    return FileResponse(
        path=output_path,
        media_type="text/csv",
        filename=filename
    )

@app.get("/api/export/pdf")
def export_pdf_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        session.brd = generate_brd(session)
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"BRD_{safe_client}_{session.session_id[:8]}.pdf"
    output_path = os.path.join(export_dir, filename)
    generate_pdf_brd(session.brd, output_path)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=filename
    )

@app.get("/api/export/docx")
def export_docx_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        session.brd = generate_brd(session)
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"BRD_{safe_client}_{session.session_id[:8]}.docx"
    output_path = os.path.join(export_dir, filename)
    generate_word_brd(session.brd, output_path)
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )

@app.get("/api/export-pptx")
def export_pptx_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    safe_client = re.sub(r'[^\w\-]', '_', session.brd.client_name)[:30]
    filename = f"Project_Plan_{safe_client}_{session.session_id[:8]}.pptx"
    output_path = os.path.join(export_dir, filename)
    
    create_presentation_deck(session.brd, output_path)
    
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename
    )

@app.get("/api/export-brd")
def export_brd_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.brd:
        raise HTTPException(status_code=400, detail="BRD has not been generated yet.")
        
    b = session.brd
    md_content = f"""# {b.project_title}
**Client:** {b.client_name}  
**Delivery Tier:** {b.delivery_tier} ({b.tier_kind})  
**Headline Rigour Weight:** {b.headline_weight}  
**Total Timeline:** {b.total_duration_weeks:.1f} Calendar Weeks (Reference: {b.reference_duration_weeks:.1f} wks)  
**Total Effort:** {b.total_person_days:.1f} Person-Days ({b.total_person_hours:.0f} Person-Hours)  
**Total Labour Cost:** ${b.total_labour_cost_usd:,.2f} (@ ${b.blended_hourly_rate:.2f}/hr blended rate)  
**Monthly Cloud Infrastructure BoM:** ${b.sizing_metrics.total_monthly_cloud_cost_usd:,.2f} / month  

---

## 1. Executive Summary
{b.executive_summary}

## 2. Problem Statement & Functional Objectives
{b.problem_statement}

### Solution Summary (6 Sentences)
{b.solution_summary_six_sentences}

### Key Business Impacts
""" + "\n".join([f"- {imp}" for imp in b.business_impacts]) + f"""

---

## 3. Scope Boundaries
### In-Scope Deliverables
""" + "\n".join([f"- {s}" for s in b.in_scope]) + f"""

### Out-of-Scope Items
""" + "\n".join([f"- {s}" for s in b.out_of_scope]) + f"""

---

## 4. 12-Discipline Resource Loading Plan ($30.00/Hour Blended Rate)
| Discipline Role | Functional Focus | Days | Hours | Cost ($30/hr) | Peak FTE |
| :--- | :--- | :--- | :--- | :--- | :--- |
""" + "\n".join([f"| {r.role} | {r.description} | {r.days:.1f} | {r.hours:.0f} | ${r.cost:,.2f} | {r.peak_fte:.2f} |" for r in b.role_efforts]) + f"""
| **TOTAL** | **All Disciplines** | **{b.total_person_days:.1f}** | **{b.total_person_hours:.0f}** | **${b.total_labour_cost_usd:,.2f}** | - |

---

## 5. 18-Phase Project Roadmap & Sprints
| Phase Code | Phase Name | Weeks | Effort (Days) | Key Deliverables |
| :--- | :--- | :--- | :--- | :--- |
""" + "\n".join([f"| {p.phase_code} | {p.phase_name} | {p.weeks:.1f} wks | {p.effort_days:.1f} d | {', '.join(p.key_deliverables[:2])} |" for p in b.project_phases]) + f"""

---

## 6. Technical Component Architecture (6 Components)
""" + "\n\n".join([
    f"### {c.id}: {c.name}\n"
    f"- **Purpose:** {c.purpose}\n"
    f"- **Technology Choice:** {c.technology_choice}\n"
    f"- **Key Design Decisions:** {c.key_design_decisions}\n"
    f"- **Interfaces In/Out:** {c.interfaces_in_out}\n"
    f"- **Data Classification:** {c.data_classification}\n"
    f"- **Scalability & Performance:** {c.scalability_performance}\n"
    f"- **Security & RAI Controls:** {c.security_rai_controls}\n"
    f"- **Failure Modes & Mitigation:** {c.failure_modes_mitigation}\n"
    f"- **Dependencies:** {c.dependencies}"
    for c in b.technical_components
]) + f"""

---

## 7. Cloud Infrastructure Bill of Materials (BoM)
| Component | SKU / Service | Tier | Quantity | Monthly Cost (USD) | Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
""" + "\n".join([f"| {bm.component} | {bm.sku_or_service} | {bm.tier} | {bm.quantity} | ${bm.monthly_cost_usd:,.2f} | {bm.justification} |" for bm in b.sizing_bom]) + f"""
| **TOTAL CLOUD INFRA** | - | - | - | **${b.sizing_metrics.total_monthly_cloud_cost_usd:,.2f} / mo** | - |

---

## 8. Assumptions & Approval Gate
| ID | Type | Category | Statement | Impact if Wrong | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
""" + "\n".join([f"| {a.id} | {a.type} | {a.category} | {a.statement} | {a.impact_if_wrong} | **{a.status}** |" for a in b.assumptions]) + """

---
*Generated by AI Project Discovery & Estimation Accelerator (Full Deterministic Engine)*
"""

    return HTMLResponse(
        content=f"<html><head><title>{b.project_title} — BRD</title><style>body{{font-family:Inter,Segoe UI,sans-serif;line-height:1.6;padding:40px;max-width:960px;margin:auto;color:#1e293b;background:#f8fafc;}}pre,code{{background:#e2e8f0;padding:2px 6px;border-radius:4px;}}table{{border-collapse:collapse;width:100%;margin:16px 0;}}th,td{{border:1px solid #cbd5e1;padding:8px 12px;text-align:left;font-size:0.9rem;}}th{{background:#f1f5f9;}}h1,h2,h3{{color:#0f172a;}}hr{{border:0;border-top:1px solid #e2e8f0;margin:24px 0;}}</style></head><body><pre style='white-space:pre-wrap;font-family:inherit;'>{md_content}</pre></body></html>"
    )

# --- Admin & Multi-Cloud Settings Endpoints ---
@app.get("/api/settings")
def get_settings_endpoint():
    return get_settings().model_dump()

class SettingsPayload(BaseModel):
    provider: Optional[str] = None
    active_provider: Optional[str] = None
    google_api_key: Optional[str] = None
    google_endpoint: Optional[str] = None
    google_model: Optional[str] = None
    google_temperature: Optional[float] = None
    gemini_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_version: Optional[str] = None
    azure_temperature: Optional[float] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_region: Optional[str] = None
    aws_model_id: Optional[str] = None
    aws_model: Optional[str] = None
    openai_endpoint: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None

@app.post("/api/settings")
def save_settings_endpoint(payload: SettingsPayload):
    curr = get_settings()
    p = payload.provider or payload.active_provider
    if p:
        curr.active_provider = p
    if payload.google_api_key is not None:
        curr.google_api_key = payload.google_api_key
    elif payload.gemini_api_key is not None:
        curr.google_api_key = payload.gemini_api_key
    if payload.google_endpoint is not None:
        curr.google_endpoint = payload.google_endpoint
    if payload.google_model is not None:
        curr.google_model = payload.google_model
    if payload.google_temperature is not None:
        curr.google_temperature = payload.google_temperature
    if payload.azure_openai_endpoint is not None:
        curr.azure_endpoint = payload.azure_openai_endpoint
    if payload.azure_openai_api_key is not None:
        curr.azure_api_key = payload.azure_openai_api_key
    if payload.azure_deployment is not None:
        curr.azure_deployment = payload.azure_deployment
    if payload.azure_api_version is not None:
        curr.azure_api_version = payload.azure_api_version
    if payload.azure_temperature is not None:
        curr.azure_temperature = payload.azure_temperature
    if payload.aws_access_key is not None:
        curr.aws_access_key_id = payload.aws_access_key
    if payload.aws_secret_key is not None:
        curr.aws_secret_access_key = payload.aws_secret_key
    if payload.aws_session_token is not None:
        curr.aws_session_token = payload.aws_session_token
    if payload.aws_region is not None:
        curr.aws_region = payload.aws_region
    if payload.aws_model_id is not None:
        curr.aws_model_id = payload.aws_model_id
    elif payload.aws_model is not None:
        curr.aws_model_id = payload.aws_model
    if payload.openai_endpoint is not None:
        curr.openai_endpoint = payload.openai_endpoint
    if payload.openai_api_key is not None:
        curr.openai_api_key = payload.openai_api_key
    if payload.openai_model is not None:
        curr.openai_model = payload.openai_model
    update_settings(curr)
    return {"status": "success", "settings": curr.model_dump()}

@app.post("/api/settings/test-connection")
def test_connection_endpoint(payload: Optional[SettingsPayload] = None):
    if payload:
        curr = get_settings()
        p = payload.provider or payload.active_provider
        if p:
            curr.active_provider = p
        if payload.google_api_key: curr.google_api_key = payload.google_api_key
        elif payload.gemini_api_key: curr.google_api_key = payload.gemini_api_key
        if payload.google_endpoint: curr.google_endpoint = payload.google_endpoint
        if payload.google_model: curr.google_model = payload.google_model
        if payload.azure_openai_endpoint: curr.azure_endpoint = payload.azure_openai_endpoint
        if payload.azure_openai_api_key: curr.azure_api_key = payload.azure_openai_api_key
        if payload.azure_deployment: curr.azure_deployment = payload.azure_deployment
        if payload.aws_access_key: curr.aws_access_key_id = payload.aws_access_key
        if payload.aws_secret_key: curr.aws_secret_access_key = payload.aws_secret_key
        if payload.aws_region: curr.aws_region = payload.aws_region
        if payload.aws_model_id: curr.aws_model_id = payload.aws_model_id
        elif payload.aws_model: curr.aws_model_id = payload.aws_model
        if payload.openai_endpoint: curr.openai_endpoint = payload.openai_endpoint
        if payload.openai_api_key: curr.openai_api_key = payload.openai_api_key
        if payload.openai_model: curr.openai_model = payload.openai_model
        return LLMGateway.test_connection(curr)
    return LLMGateway.test_connection()

class ImpactRequest(BaseModel):
    session_id: str
    parameter_changed: str
    old_value: Any
    new_value: Any

@app.post("/api/impact-analysis")
def impact_analysis_endpoint(payload: ImpactRequest):
    session = get_or_create_session(payload.session_id)
    if not session.brd:
        session.brd = generate_brd(session)
    res = calculate_change_impact(
        current_brd=session.brd,
        parameter_changed=payload.parameter_changed,
        old_value=payload.old_value,
        new_value=payload.new_value
    )
    return res.model_dump()

class GateApprovalPayload(BaseModel):
    session_id: str
    gate: str
    approved: bool = True
    notes: Optional[str] = None

@app.post("/api/gates/approve")
def approve_gate_endpoint(payload: GateApprovalPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "hitl_gates") or not session.hitl_gates:
        session.hitl_gates = HITLGates()
    g = payload.gate.lower().strip()
    if "1" in g or "req" in g:
        session.hitl_gates.gate1_requirements_approved = payload.approved
        session.hitl_gates.gate1_notes = payload.notes
    elif "2" in g or "sol" in g:
        session.hitl_gates.gate2_solution_approved = payload.approved
        session.hitl_gates.gate2_notes = payload.notes
    elif "3" in g or "est" in g:
        session.hitl_gates.gate3_estimate_approved = payload.approved
        session.hitl_gates.gate3_notes = payload.notes
    elif "4" in g or "brd" in g:
        session.hitl_gates.gate4_brd_approved = payload.approved
        session.hitl_gates.gate4_notes = payload.notes
    if session.brd:
        session.brd.hitl_gates = session.hitl_gates
    return {"status": "success", "hitl_gates": session.hitl_gates.model_dump()}

@app.get("/api/gates")
def get_gates_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    gates = getattr(session, "hitl_gates", None) or HITLGates()
    return {"status": "success", "hitl_gates": gates.model_dump()}

@app.get("/api/admin/defaults")
def get_admin_defaults_endpoint():
    return get_admin_defaults()

@app.post("/api/admin/defaults")
def save_admin_defaults_endpoint(payload: Dict[str, Any]):
    return save_admin_defaults(payload)

@app.get("/api/admin/calendars")
def get_calendars_endpoint():
    return get_calendars()

class CalendarUpsertPayload(BaseModel):
    country_code: str
    country_name: str
    currency_code: str = "USD"
    currency_symbol: str = "$"
    working_days_per_week: int = 5
    daily_working_hours: float = 8.0
    hourly_rate: float = 30.0
    hourly_rate_local: Optional[float] = None
    annual_holiday_allowance: int = 12

@app.post("/api/admin/calendars")
def upsert_calendar_endpoint(payload: CalendarUpsertPayload):
    cal = upsert_calendar(
        country_code=payload.country_code,
        country_name=payload.country_name,
        working_days=payload.working_days_per_week,
        daily_working_hours=payload.daily_working_hours,
        hourly_rate=payload.hourly_rate,
        hourly_rate_local=payload.hourly_rate_local,
        currency_code=payload.currency_code,
        currency_symbol=payload.currency_symbol,
        annual_allowance=payload.annual_holiday_allowance
    )
    return {"status": "success", "calendar": cal}

@app.delete("/api/admin/calendars/{country_code}")
def delete_calendar_endpoint(country_code: str):
    res = delete_calendar(country_code)
    return {"status": "success" if res else "not_found"}

class HolidayPayload(BaseModel):
    date: str
    name: str
    type: str = "Statutory"

@app.post("/api/admin/calendars/{country_code}/holidays")
def add_holiday_endpoint(country_code: str, payload: HolidayPayload):
    cal = add_holiday_to_calendar(
        country_code=country_code,
        date=payload.date,
        name=payload.name,
        holiday_type=payload.type
    )
    return {"status": "success", "calendar": cal}

@app.put("/api/admin/calendars/{country_code}/holidays/{holiday_index}")
def update_holiday_endpoint(country_code: str, holiday_index: int, payload: HolidayPayload):
    cal = update_holiday_in_calendar(
        country_code=country_code,
        holiday_index=holiday_index,
        date=payload.date,
        name=payload.name,
        holiday_type=payload.type
    )
    return {"status": "success", "calendar": cal}

@app.delete("/api/admin/calendars/{country_code}/holidays/{holiday_index}")
def delete_holiday_endpoint(country_code: str, holiday_index: int):
    cal = delete_holiday_from_calendar(country_code=country_code, holiday_index=holiday_index)
    return {"status": "success", "calendar": cal}

@app.post("/api/admin/calendars/upload")
async def upload_holiday_sheet_endpoint(
    country_code: str = Form(...),
    country_name: str = Form(""),
    file: UploadFile = File(...)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"holidays_{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    cal = parse_holiday_sheet(file_path, country_code, country_name)
    return {"status": "success", "calendar": cal}

@app.get("/api/admin/assumptions")
def get_admin_assumptions_endpoint():
    return get_master_assumptions()

class AssumptionsPayload(BaseModel):
    assumptions: List[Dict[str, Any]]

@app.post("/api/admin/assumptions")
def save_admin_assumptions_endpoint(payload: AssumptionsPayload):
    save_master_assumptions(payload.assumptions)
    return {"status": "success", "assumptions": payload.assumptions}

@app.post("/api/reset")
def reset_endpoint(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    new_session = get_or_create_session(session_id)
    return {"status": "success", "session_id": new_session.session_id}

@app.get("/api/projects/history")
def get_projects_history_endpoint():
    # Return list of project workspaces with full folder info and file links
    projects = [
        {
            "id": "pvr-contract-intel",
            "name": "PVR INOX — Contract Intelligence & Risk Visibility Platform",
            "client": "PVR INOX",
            "tier": "PoC (Greenfield Build)",
            "headline_weight": 0.289,
            "duration_weeks": 6.0,
            "person_days": 83.6,
            "labour_cost_usd": 22572.0,
            "monthly_cloud_usd": 645.0,
            "status": "Active / Baseline",
            "updated_at": "Today, 11:20 AM",
            "cloud_platform": "Microsoft Azure",
            "categories": ["Lease", "Vendor", "Service", "Facilities", "Technology", "Marketing"],
            "files": {
                "word_docx": "/api/export/word?session_id=pvr-contract-intel",
                "excel_xlsx": "/api/export/excel?session_id=pvr-contract-intel",
                "jira_csv": "/api/export/jira?session_id=pvr-contract-intel",
                "pptx_deck": "/api/export-pptx?session_id=pvr-contract-intel",
                "brd_preview": "/api/export-brd?session_id=pvr-contract-intel"
            },
            "answers_count": 22,
            "is_current": True
        },
        {
            "id": "bank-aml-fraud",
            "name": "Global Banking Corp — Intelligent AML & Financial Fraud Detection System",
            "client": "Global Banking Corp",
            "tier": "Production Grade",
            "headline_weight": 1.000,
            "duration_weeks": 16.0,
            "person_days": 378.9,
            "labour_cost_usd": 102300.0,
            "monthly_cloud_usd": 1280.0,
            "status": "Completed & Locked",
            "updated_at": "28-Sep-2026",
            "cloud_platform": "Amazon Web Services (AWS)",
            "categories": ["AML Compliance", "Wire Transfers", "Card Transactions", "KYC Identity"],
            "files": {
                "word_docx": "/api/export/word?session_id=bank-aml-fraud",
                "excel_xlsx": "/api/export/excel?session_id=bank-aml-fraud",
                "jira_csv": "/api/export/jira?session_id=bank-aml-fraud",
                "pptx_deck": "/api/export-pptx?session_id=bank-aml-fraud",
                "brd_preview": "/api/export-brd?session_id=bank-aml-fraud"
            },
            "answers_count": 22,
            "is_current": False
        },
        {
            "id": "retail-virtual-agent",
            "name": "Enterprise Retail — AI-Powered Customer Support & Virtual Agent Cockpit",
            "client": "Enterprise Retail",
            "tier": "Pilot to MVP",
            "headline_weight": 0.557,
            "duration_weeks": 8.0,
            "person_days": 142.5,
            "labour_cost_usd": 38475.0,
            "monthly_cloud_usd": 580.0,
            "status": "In Review",
            "updated_at": "25-Sep-2026",
            "cloud_platform": "Google Cloud Platform (GCP)",
            "categories": ["Tier-1 Inquiries", "Order Tracking", "Returns & Refunds", "CRM Handoff"],
            "files": {
                "word_docx": "/api/export/word?session_id=retail-virtual-agent",
                "excel_xlsx": "/api/export/excel?session_id=retail-virtual-agent",
                "jira_csv": "/api/export/jira?session_id=retail-virtual-agent",
                "pptx_deck": "/api/export-pptx?session_id=retail-virtual-agent",
                "brd_preview": "/api/export-brd?session_id=retail-virtual-agent"
            },
            "answers_count": 22,
            "is_current": False
        },
        {
            "id": "health-clinical-extract",
            "name": "Healthcare System — Intelligent Clinical Document Extraction Platform",
            "client": "Healthcare System",
            "tier": "MVP",
            "headline_weight": 0.778,
            "duration_weeks": 12.0,
            "person_days": 218.4,
            "labour_cost_usd": 58968.0,
            "monthly_cloud_usd": 920.0,
            "status": "Approved by Sponsor",
            "updated_at": "20-Sep-2026",
            "cloud_platform": "Microsoft Azure",
            "categories": ["EHR Clinical Records", "Lab Results", "Insurance Pre-Auth", "Doctor Notes"],
            "files": {
                "word_docx": "/api/export/word?session_id=health-clinical-extract",
                "excel_xlsx": "/api/export/excel?session_id=health-clinical-extract",
                "jira_csv": "/api/export/jira?session_id=health-clinical-extract",
                "pptx_deck": "/api/export-pptx?session_id=health-clinical-extract",
                "brd_preview": "/api/export-brd?session_id=health-clinical-extract"
            },
            "answers_count": 22,
            "is_current": False
        }
    ]
    return {"projects": projects}

@app.post("/api/projects/load")
def load_project_endpoint(project_id: str):
    # Initialize or load preset project session
    session = get_or_create_session(project_id)
    if not session.brd:
        # Prepopulate answers based on template
        if project_id == "bank-aml-fraud":
            session.answers["q_client"] = AnswerItem(question_id="q_client", question_title="Client", answer="Global Banking Corp | Intelligent AML & Financial Fraud Detection System")
            session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Production Grade")
            session.answers["q_problem"] = AnswerItem(question_id="q_problem", question_title="Problem", answer="High volume of financial transactions requiring real-time AML scoring, fraud anomaly detection, and automated regulatory reporting.")
            session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer="16.0")
            session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Amazon Web Services (AWS)")
            session.answers["q_compliance"] = AnswerItem(question_id="q_compliance", question_title="Compliance", answer="Regulated - high (BFSI/Health/Gov)")
            session.answers["q_complexity"] = AnswerItem(question_id="q_complexity", question_title="Complexity", answer="High")
        elif project_id == "retail-virtual-agent":
            session.answers["q_client"] = AnswerItem(question_id="q_client", question_title="Client", answer="Enterprise Retail | AI-Powered Customer Support & Virtual Agent Cockpit")
            session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Pilot to MVP")
            session.answers["q_problem"] = AnswerItem(question_id="q_problem", question_title="Problem", answer="High volume of tier-1 customer inquiries causing long wait times. Automated deflection via grounded conversational AI required.")
            session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer="8.0")
            session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Google Cloud Platform (GCP)")
        elif project_id == "health-clinical-extract":
            session.answers["q_client"] = AnswerItem(question_id="q_client", question_title="Client", answer="Healthcare System | Intelligent Clinical Document Extraction Platform")
            session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="MVP")
            session.answers["q_problem"] = AnswerItem(question_id="q_problem", question_title="Problem", answer="Manual medical record parsing and insurance claim pre-authorization extraction.")
            session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer="12.0")
            session.answers["q_compliance"] = AnswerItem(question_id="q_compliance", question_title="Compliance", answer="Regulated - high (BFSI/Health/Gov)")
        else: # PVR
            for q in STATIC_QUESTIONS:
                session.answers[q.id] = AnswerItem(question_id=q.id, question_title=q.title, answer=q.default_value)

        brd = generate_brd(session)
        session.brd = brd
        compile_and_save_handoff_dossier(session)
        
    return {
        "status": "success",
        "session_id": session.session_id,
        "brd": session.brd.model_dump() if session.brd else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "messages": [m.model_dump() for m in session.messages]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8088, reload=True)
