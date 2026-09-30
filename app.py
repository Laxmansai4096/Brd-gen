import os
import uuid
import json
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.models import (
    ProjectSession, ChatMessage, AnswerItem, BRDDocument,
    AssumptionItem, TaskEstimate, RoleEffort, ProjectPhase,
    TechnicalComponent, SizingMetrics, SizingBOM
)
from backend.agent_discovery import (
    STATIC_QUESTIONS, process_user_answer, get_current_question,
    get_discovery_questions, compile_and_save_handoff_dossier
)
from backend.agent_planner import generate_brd
from backend.pptx_generator import create_presentation_deck
from backend.file_processor import extract_text_from_file
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
        "handoff_data": session.handoff_dossier
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

@app.post("/api/upload")
async def upload_file_endpoint(session_id: str = Form(...), file: UploadFile = File(...)):
    session = get_or_create_session(session_id)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    extracted = extract_text_from_file(file_path, file.filename)
    session.uploaded_files.append({
        "filename": file.filename,
        "char_count": extracted.get("char_count", 0),
        "preview": extracted.get("preview", ""),
        "full_text": extracted.get("full_text", "")
    })
    
    preview_snippet = extracted.get("preview", "")[:250] + "..."
    session.messages.append(ChatMessage(
        sender="system",
        content=(
            f"📎 **Attached Document Ingested:** `{file.filename}` ({extracted.get('char_count', 0):,} characters).\n"
            f"**Context Extracted:**\n> {preview_snippet}\n\n"
            f"This content is now available to Agent 1 and Agent 2 to enrich the requirements and BRD specifications."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "file": session.uploaded_files[-1],
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
    overrides: Dict[str, str]

@app.post("/api/replan")
async def replan_endpoint(payload: ReplanRequest):
    session = get_or_create_session(payload.session_id)
    
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
    provider: str
    gemini_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = None

@app.post("/api/settings")
def save_settings_endpoint(payload: SettingsPayload):
    curr = get_settings()
    curr.active_provider = payload.provider
    if payload.gemini_api_key is not None:
        curr.gemini_api_key = payload.gemini_api_key
    if payload.azure_openai_endpoint is not None:
        curr.azure_openai_endpoint = payload.azure_openai_endpoint
    if payload.azure_openai_api_key is not None:
        curr.azure_openai_api_key = payload.azure_openai_api_key
    if payload.aws_access_key is not None:
        curr.aws_access_key = payload.aws_access_key
    if payload.aws_secret_key is not None:
        curr.aws_secret_key = payload.aws_secret_key
    if payload.aws_region is not None:
        curr.aws_region = payload.aws_region
    update_settings(curr)
    return {"status": "success", "settings": curr.model_dump()}

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
    working_days_per_week: int = 5
    daily_working_hours: float = 8.0
    annual_holiday_allowance: int = 12

@app.post("/api/admin/calendars")
def upsert_calendar_endpoint(payload: CalendarUpsertPayload):
    cal = upsert_calendar(
        country_code=payload.country_code,
        country_name=payload.country_name,
        working_days=payload.working_days_per_week,
        daily_working_hours=payload.daily_working_hours,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8088, reload=True)
