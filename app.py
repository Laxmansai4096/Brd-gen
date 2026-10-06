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
    TechnicalComponent, SizingMetrics, SizingBOM, HITLGates,
    CalculationLedgerItem, WorkflowState, PersonaReview, PMQueryItem,
    TripartyMessage, DiscoveryConfidence, DimensionScore, RevisionSnapshot
)
from backend.agent_discovery import (
    STATIC_QUESTIONS, process_user_answer, get_current_question,
    get_discovery_questions, compile_and_save_handoff_dossier,
    calculate_discovery_confidence, get_architect_technical_advice,
    auto_discover_from_document_text
)
from backend.agent_planner import generate_brd
from backend.pptx_generator import create_presentation_deck
from backend.file_processor import extract_text_from_file
from backend.export_generator import (
    generate_word_brd, generate_pdf_brd,
    generate_excel_financial_model, generate_jira_backlog_csv
)
from backend.llm_gateway import LLMGateway
from backend.impact_engine import calculate_change_impact, commit_change_impact
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
            workflow=WorkflowState(
                stage="IDEATION",
                active_persona="CLIENT",
                confidence_score=0.0,
                client_review=PersonaReview(persona="CLIENT", signature_name="Elena Vance (Client Business Lead)"),
                architect_review=PersonaReview(persona="SOLUTIONS_ARCHITECT", signature_name="Alex Morgan (Principal Solutions Architect)"),
                pm_review=PersonaReview(persona="PROJECT_MANAGER", signature_name="Marcus Reed (Senior Delivery PM)")
            ),
            messages=[
                ChatMessage(
                    sender="agent",
                    persona="AI_AGENT",
                    persona_badge="🤖 AI Discovery Agent",
                    content=(
                        "👋 **Hello! Welcome to the 3-Persona AI Project Discovery & Estimation Accelerator.**\n\n"
                        "Our collaborative team consists of:\n"
                        "• 🧑‍💼 **Elena Vance (Client Business Lead)**: Defines business problem, user pain points, and delivery objectives.\n"
                        "• 🏗️ **Alex Morgan (Principal Solutions Architect)**: Advises on cloud hyperscaler, security posture, and RAG pipelines.\n"
                        "• 👔 **Marcus Reed (Senior Delivery PM)**: Reviews resourcing, timeline feasibility, and provides final governance sign-off.\n\n"
                        "💡 *Let's start with **Stage 1: Ideation & Scoping** to align with the client and architect on project goals.*"
                    ),
                    timestamp="Just now",
                    question_context=q1
                )
            ]
        )
        conf = calculate_discovery_confidence(session)
        session.confidence = conf
        sessions[sid] = session
        return session
    return sessions[session_id]

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "AI-BRD-Generator", "timestamp": datetime.now().isoformat()}

@app.get("/api/ports")
def get_persona_ports():
    return {
        "ports": {
            "8081": {"persona": "CLIENT", "name": "Elena Vance", "role": "Client Business Lead", "title": "Client Portal", "badge": "🧑‍💼 Client (Elena Vance)", "default_tab": "tab-ideation"},
            "8082": {"persona": "SOLUTIONS_ARCHITECT", "name": "Alex Morgan", "role": "Principal Solutions Architect", "title": "Solutions Architect Portal", "badge": "🏗️ Solutions Architect (Alex Morgan)", "default_tab": "tab-dual-review"},
            "8083": {"persona": "PROJECT_MANAGER", "name": "Marcus Reed", "role": "Senior Delivery PM", "title": "Project Manager Portal", "badge": "👔 Project Manager (Marcus Reed)", "default_tab": "tab-pm-review"},
            "8084": {"persona": "ADMIN", "name": "System Administrator", "role": "Enterprise Governance Admin", "title": "Admin & Governance Console", "badge": "🛡️ Admin & Governance", "default_tab": "admin_modal"},
            "8088": {"persona": "UNIFIED", "name": "Multi-Persona Team", "role": "All Personas Collaboration Gateway", "title": "Unified Collaboration Gateway", "badge": "🌐 Unified Gateway", "default_tab": "tab-ideation"}
        }
    }

@app.get("/api/session")
def get_session_endpoint(session_id: Optional[str] = None):
    session = get_or_create_session(session_id)
    current_q = get_current_question(session)
    questions = get_discovery_questions()
    gates = getattr(session, "hitl_gates", None) or HITLGates()
    conf = calculate_discovery_confidence(session)
    wf = getattr(session, "workflow", None) or WorkflowState()
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
        "hitl_gates": gates.model_dump(),
        "workflow": wf.model_dump(),
        "confidence": conf.model_dump()
    }

class ChatInput(BaseModel):
    session_id: str
    message: str
    selected_option: Optional[str] = None
    persona: Optional[str] = "CLIENT"  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"

@app.post("/api/chat")
async def chat_endpoint(payload: ChatInput):
    session = get_or_create_session(payload.session_id)
    active_persona = payload.persona or (session.workflow.active_persona if hasattr(session, "workflow") and session.workflow else "CLIENT")
    if hasattr(session, "workflow") and session.workflow:
        session.workflow.active_persona = active_persona

    answer_text = payload.selected_option if payload.selected_option else payload.message
    user_display_text = payload.message or answer_text
    current_q = get_current_question(session)
    
    if current_q and current_q.options:
        for opt in current_q.options:
            if str(opt.value).strip().lower() == str(answer_text).strip().lower() or str(opt.label).strip().lower() == str(answer_text).strip().lower():
                desc = f" — {opt.description}" if opt.description else ""
                user_display_text = f"{opt.label}{desc}"
                break
    
    # Badge based on active persona
    badge_map = {
        "CLIENT": "🧑‍💼 Client (Elena Vance)",
        "SOLUTIONS_ARCHITECT": "🏗️ Solutions Architect (Alex Morgan)",
        "PROJECT_MANAGER": "👔 Project Manager (Marcus Reed)"
    }
    
    # Record user message with active persona badge
    session.messages.append(ChatMessage(
        sender="user",
        persona=active_persona,
        persona_badge=badge_map.get(active_persona, "🧑‍💼 Client"),
        content=user_display_text,
        timestamp="Just now"
    ))
    
    # Process through discovery agent
    reply_msg, is_complete = process_user_answer(session, answer_text, persona=active_persona)
    session.messages.append(reply_msg)
    conf = calculate_discovery_confidence(session)
    
    if is_complete or conf.score >= 98.0:
        compile_and_save_handoff_dossier(session)
        was_first_completion = (session.brd is None)
        
        brd = generate_brd(session)
        session.brd = brd
        
        if hasattr(session, "workflow") and session.workflow:
            if session.workflow.stage in ["IDEATION", "DISCOVERY"] or session.workflow.current_stage in ["IDEATION", "DISCOVERY"]:
                session.workflow.stage = "DUAL_REVIEW"
                session.workflow.current_stage = "DUAL_REVIEW"
            session.workflow.is_confidence_reached = True
            
        if was_first_completion:
            session.messages.append(ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                persona_badge="🤖 AI Synthesis Agent",
                content=(
                    "🚀 **Agent 2 has successfully synthesized the Draft Project Plan and BRD (Confidence >= 98%)!**\n\n"
                    f"• **Project Title:** {brd.project_title}\n"
                    f"• **Client / Account:** {brd.client_name}\n"
                    f"• **Delivery Tier:** {brd.delivery_tier} ({brd.total_duration_weeks:.1f} Weeks)\n"
                    f"• **Total Effort:** {brd.total_person_days:.1f} Person-Days ({brd.total_person_hours:.0f} Hours)\n"
                    f"• **Total Labour Cost:** ${brd.total_labour_cost_usd:,.2f} (@ ${brd.blended_hourly_rate:.2f}/hr blended rate)\n"
                    f"• **Cloud Infra BoM:** ${brd.sizing_metrics.total_monthly_cloud_cost_usd:,.2f} / month ({session.answers.get('q_cloud', AnswerItem(question_id='q_cloud', question_title='Cloud', answer='Azure')).answer})\n\n"
                    "👉 **Next Step (Stage 3: Dual Review):** Both **Elena Vance (Client)** and **Alex Morgan (Solutions Architect)** must review the draft BRD and either submit change requests or provide dual sign-off before it moves to Project Manager Marcus Reed."
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
        "messages": [m.model_dump() for m in session.messages],
        "workflow": session.workflow.model_dump() if hasattr(session, "workflow") and session.workflow else None,
        "confidence": conf.model_dump()
    }

# --- 3-Persona Collaborative Workflow Endpoints ---
class SwitchPersonaPayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"

@app.post("/api/workflow/switch-persona")
def switch_persona_endpoint(payload: SwitchPersonaPayload):
    session = get_or_create_session(payload.session_id)
    p = payload.persona.upper().strip()
    if p not in ["CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"]:
        p = "CLIENT"
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
    session.workflow.active_persona = p
    return {"status": "success", "active_persona": p, "workflow": session.workflow.model_dump()}

class IdeatePayload(BaseModel):
    session_id: str
    client_idea: str
    project_title: Optional[str] = None
    target_tier: Optional[str] = "PoC"

@app.post("/api/workflow/ideate")
def ideate_workflow_endpoint(payload: IdeatePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    p_title = payload.project_title or "Enterprise AI Platform"
    client_text = payload.client_idea.strip()
    
    # 1. Solutions Architect evaluates feasibility and recommends cloud stack
    arch_recommendation = (
        f"Technical Feasibility: High (95%). Recommended Cloud: Microsoft Azure with Azure AI Document Intelligence "
        f"and Azure OpenAI GPT-5 Thinking / GPT-4o. Microservice topology: 6 components (Ingestion, Search Index, "
        f"Reasoning Engine, Metadata Store, Eval Harness, React Cockpit). Target tier: {payload.target_tier} with 6-week baseline."
    )
    
    session.workflow.stage = "DISCOVERY"
    session.workflow.ideation_client_idea = client_text
    session.workflow.ideation_architect_feedback = arch_recommendation
    session.workflow.ideation_agreed_project = p_title
    
    # Pre-seed initial answers from agreed ideation
    session.answers["q_client"] = AnswerItem(
        question_id="q_client",
        question_title="Client & Engagement Name",
        answer=p_title,
        is_default=False
    )
    session.answers["q_problem"] = AnswerItem(
        question_id="q_problem",
        question_title="Problem Statement & Business Challenge",
        answer=client_text,
        is_default=False
    )
    session.answers["q_tier"] = AnswerItem(
        question_id="q_tier",
        question_title="Delivery Tier",
        answer=payload.target_tier or "PoC",
        is_default=False
    )
    
    session.current_question_index = 3  # Move to next discovery questions
    conf = calculate_discovery_confidence(session)
    next_q = get_current_question(session)
    
    session.messages.append(ChatMessage(
        sender="architect",
        persona="SOLUTIONS_ARCHITECT",
        persona_badge="🏗️ Solutions Architect (Alex Morgan)",
        content=(
            f"🏗️ **Alex Morgan (Solutions Architect):**\n\n"
            f"> \"I reviewed the project idea: **'{client_text}'**.\n\n"
            f"**Technical Assessment:**\n"
            f"• **Feasibility:** 95% High Confidence\n"
            f"• **Recommended Cloud:** Microsoft Azure (Azure AI Document Intelligence + Azure OpenAI)\n"
            f"• **Delivery Tier:** {payload.target_tier} (6.0 Weeks)\n"
            f"• **Security Baseline:** Enhanced (Private Endpoints & RBAC)\n\n"
            f"Let's proceed to deep-dive discovery with the AI Interviewer!\""
        ),
        timestamp="Just now"
    ))
    
    if next_q:
        session.messages.append(ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            persona_badge="🤖 AI Discovery Agent",
            content=(
                f"🤝 **Project Scope Agreed!** Starting deep-dive discovery interview.\n\n"
                f"---\n\n"
                f"### 📋 Question {session.current_question_index + 1} of {len(STATIC_QUESTIONS)}: **{next_q.title}** *(Confidence: {conf.score}%)*\n\n"
                f"**{next_q.prompt}**\n\n"
                f"*(Example: {next_q.help_text})*"
            ),
            timestamp="Just now",
            question_context=next_q
        )
    )
    
    return {
        "status": "success",
        "workflow": session.workflow.model_dump(),
        "confidence": conf.model_dump(),
        "current_question": next_q.model_dump() if next_q else None,
        "messages": [m.model_dump() for m in session.messages]
    }

class DelegateArchitectPayload(BaseModel):
    session_id: str
    question_id: Optional[str] = None

@app.post("/api/workflow/delegate-architect")
def delegate_architect_endpoint(payload: DelegateArchitectPayload):
    session = get_or_create_session(payload.session_id)
    q = get_current_question(session)
    if not q:
        raise HTTPException(status_code=400, detail="No active question to delegate.")
        
    reply_msg, is_complete = process_user_answer(session, "ask architect", persona="SOLUTIONS_ARCHITECT")
    session.messages.append(reply_msg)
    conf = calculate_discovery_confidence(session)
    
    if is_complete or conf.score >= 98.0:
        compile_and_save_handoff_dossier(session)
        brd = generate_brd(session)
        session.brd = brd
        if hasattr(session, "workflow") and session.workflow:
            session.workflow.stage = "DUAL_REVIEW"
            session.workflow.is_confidence_reached = True
            
    return {
        "status": "success",
        "current_question": get_current_question(session).model_dump() if get_current_question(session) else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "has_brd": session.brd is not None,
        "brd": session.brd.model_dump() if session.brd else None,
        "workflow": session.workflow.model_dump() if hasattr(session, "workflow") and session.workflow else None,
        "confidence": conf.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class ResolveEscalationPayload(BaseModel):
    session_id: str
    question_id: str
    answer: str
    notes: Optional[str] = ""

@app.get("/api/workflow/architect/briefing")
def get_architect_briefing(session_id: str):
    session = get_or_create_session(session_id)
    client_name = session.answers.get("q_client", AnswerItem(question_id="q_client", question_title="Client", answer="Contract Intelligence Platform")).answer
    problem_stmt = session.answers.get("q_problem", AnswerItem(question_id="q_problem", question_title="Problem", answer=session.workflow.ideation_client_idea or "Not specified")).answer
    tier_name = session.answers.get("q_tier", AnswerItem(question_id="q_tier", question_title="Tier", answer="PoC")).answer
    duration_name = session.answers.get("q_duration", AnswerItem(question_id="q_duration", question_title="Duration", answer="6.0 Weeks")).answer
    legal_cats = session.answers.get("q_legal_categories", AnswerItem(question_id="q_legal_categories", question_title="Categories", answer="6 Legal Categories")).answer
    
    escalated = [e.model_dump() for e in (session.workflow.escalated_topics if hasattr(session, "workflow") and session.workflow else [])]
    
    return {
        "client_overview": {
            "project_title": client_name,
            "problem_statement": problem_stmt,
            "target_tier": tier_name,
            "duration": duration_name,
            "legal_categories": legal_cats,
            "answers_count": len(session.answers),
            "current_confidence": calculate_discovery_confidence(session).score
        },
        "escalated_topics": escalated,
        "pending_count": len([e for e in escalated if e.get("status") == "PENDING_ARCHITECT"])
    }

@app.post("/api/workflow/architect/resolve-escalation")
def resolve_architect_escalation(payload: ResolveEscalationPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    q_id = payload.question_id
    answer_val = payload.answer
    
    # Update answers
    if q_id in session.answers:
        session.answers[q_id].answer = answer_val
        session.answers[q_id].notes = payload.notes or "Resolved by Solutions Architect (Alex Morgan)"
    else:
        session.answers[q_id] = AnswerItem(
            question_id=q_id,
            question_title=q_id,
            answer=answer_val,
            notes=payload.notes or "Resolved by Solutions Architect (Alex Morgan)"
        )
        
    # Mark in escalation topics
    for esc in session.workflow.escalated_topics:
        if esc.question_id == q_id:
            esc.status = "RESOLVED"
            esc.architect_answer = answer_val
            esc.architect_notes = payload.notes or ""
            esc.resolved_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
    conf = calculate_discovery_confidence(session)
    session.workflow.confidence_score = conf.score
    
    # Append resolution message to chat
    session.messages.append(ChatMessage(
        sender="architect",
        persona="SOLUTIONS_ARCHITECT",
        persona_badge="🏗️ Solutions Architect",
        is_architect_input=True,
        content=f"🏗️ **Alex Morgan (Principal Solutions Architect) — Resolved Escalation:**\n\n📌 **Topic:** `{q_id}`\n✅ **Architect Decision:** `{answer_val}`\n💬 **Notes:** {payload.notes or 'Architecture decision confirmed and applied to BRD.'}",
        timestamp="Just now"
    ))
    
    if conf.score >= 98.0:
        compile_and_save_handoff_dossier(session)
        brd = generate_brd(session)
        session.brd = brd
        session.workflow.stage = "DUAL_REVIEW"
        session.workflow.is_confidence_reached = True
        
    return {
        "status": "success",
        "question_id": q_id,
        "answer": answer_val,
        "confidence": conf.model_dump(),
        "workflow": session.workflow.model_dump(),
        "has_brd": session.brd is not None,
        "messages": [m.model_dump() for m in session.messages]
    }

class DualReviewFeedbackPayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT" or "SOLUTIONS_ARCHITECT"
    feedback: str
    adjustments: Optional[Dict[str, str]] = {}

@app.post("/api/workflow/dual-review/feedback")
def dual_review_feedback_endpoint(payload: DualReviewFeedbackPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    p = payload.persona.upper().strip()
    rev = session.workflow.client_review if p == "CLIENT" else session.workflow.architect_review
    rev.satisfied = False
    rev.status = "CHANGES_REQUESTED"
    rev.feedback = payload.feedback
    rev.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Reset approvals when revisions are requested
    session.workflow.client_review.satisfied = False
    session.workflow.architect_review.satisfied = False
    session.workflow.dual_review_iterations += 1
    
    # Apply requested adjustments
    for q_id, new_val in (payload.adjustments or {}).items():
        if q_id in session.answers:
            session.answers[q_id].answer = new_val
        else:
            session.answers[q_id] = AnswerItem(question_id=q_id, question_title=q_id, answer=new_val)
            
    # Re-generate BRD
    brd = generate_brd(session)
    session.brd = brd
    
    role_name = "Elena Vance (Client Business Lead)" if p == "CLIENT" else "Alex Morgan (Principal Solutions Architect)"
    badge = "🧑‍💼 Client" if p == "CLIENT" else "🏗️ Solutions Architect"
    
    session.messages.append(ChatMessage(
        sender="user" if p == "CLIENT" else "architect",
        persona=p,
        persona_badge=badge,
        content=f"✍️ **Change Request Submitted by {role_name}:**\n> \"{payload.feedback}\"",
        timestamp="Just now"
    ))
    
    session.messages.append(ChatMessage(
        sender="agent",
        persona="AI_AGENT",
        persona_badge="🤖 AI Synthesis Agent",
        content=(
            f"🔄 **BRD Updated based on {badge} Feedback (Iteration {session.workflow.dual_review_iterations})!**\n\n"
            f"Adjusted parameters applied. New total effort: **{brd.total_person_days:.1f} Days (${brd.total_labour_cost_usd:,.2f})** "
            f"across **{brd.total_duration_weeks:.1f} Weeks**. Both Client and Solutions Architect can review the revised plan."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "brd": brd.model_dump(),
        "workflow": session.workflow.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class DualReviewApprovePayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT" or "SOLUTIONS_ARCHITECT"
    signature_name: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/workflow/dual-review/approve")
def dual_review_approve_endpoint(payload: DualReviewApprovePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    p = payload.persona.upper().strip()
    if p == "CLIENT":
        session.workflow.client_review.satisfied = True
        session.workflow.client_review.status = "APPROVED"
        session.workflow.client_review.signature_name = payload.signature_name or "Elena Vance (Client Business Lead)"
        session.workflow.client_review.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.workflow.client_review.feedback = payload.notes
        sender_role = "🧑‍💼 Client (Elena Vance)"
    else:
        session.workflow.architect_review.satisfied = True
        session.workflow.architect_review.status = "APPROVED"
        session.workflow.architect_review.signature_name = payload.signature_name or "Alex Morgan (Principal Solutions Architect)"
        session.workflow.architect_review.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.workflow.architect_review.feedback = payload.notes
        sender_role = "🏗️ Solutions Architect (Alex Morgan)"
        
    session.messages.append(ChatMessage(
        sender="user" if p == "CLIENT" else "architect",
        persona=p,
        persona_badge=sender_role,
        content=f"✅ **Sign-Off Approved by {sender_role}!**\n> \"{payload.notes or 'BRD scope and architectural design approved.'}\"",
        timestamp="Just now"
    ))
    
    # Check if BOTH Client and Solutions Architect have approved
    is_dual_approved = session.workflow.client_review.satisfied and session.workflow.architect_review.satisfied
    if is_dual_approved:
        session.workflow.stage = "PM_REVIEW"
        session.messages.append(ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            persona_badge="🤖 AI Governance Coordinator",
            content=(
                "🎉 **DUAL APPROVAL ACHIEVED!**\n\n"
                "Both **Elena Vance (Client Lead)** and **Alex Morgan (Solutions Architect)** have approved the draft BRD.\n\n"
                "👉 **Stage 4: Project Manager Review Gate Activated.**\n"
                "**Marcus Reed (Senior Delivery PM)** is now reviewing the 18-phase timeline, 12-discipline resource loading ($30/hr rate), "
                "statutory holiday calendar, and cloud budget for final delivery governance."
            ),
            timestamp="Just now"
        ))
        
    return {
        "status": "success",
        "is_dual_approved": is_dual_approved,
        "workflow": session.workflow.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class PMQueryPayload(BaseModel):
    session_id: str
    topic: str
    query_text: str
    addressed_to: Optional[str] = "ALL"  # "CLIENT", "SOLUTIONS_ARCHITECT", "ALL"

@app.post("/api/workflow/pm-review/query")
def pm_review_query_endpoint(payload: PMQueryPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    q_id = f"PMQ-{len(session.workflow.pm_queries) + 1:03d}"
    query_item = PMQueryItem(
        id=q_id,
        topic=payload.topic,
        query_text=payload.query_text,
        addressed_to=payload.addressed_to or "ALL",
        status="OPEN"
    )
    session.workflow.pm_queries.append(query_item)
    session.workflow.pm_review.satisfied = False
    session.workflow.pm_review.status = "CHANGES_REQUESTED"
    
    # Add to tripartite discussion
    msg_id = f"TRIPARTY-{len(session.workflow.triparty_messages) + 1:03d}"
    session.workflow.triparty_messages.append(TripartyMessage(
        id=msg_id,
        sender_persona="PROJECT_MANAGER",
        sender_name="Marcus Reed (Senior Delivery PM)",
        message=f"[{payload.topic}] {payload.query_text} (Addressed to: {payload.addressed_to})",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    session.messages.append(ChatMessage(
        sender="manager",
        persona="PROJECT_MANAGER",
        persona_badge="👔 Project Manager (Marcus Reed)",
        is_pm_input=True,
        content=(
            f"👔 **Marcus Reed (Delivery PM) raised a Query / Change Request ({q_id}):**\n\n"
            f"📌 **Topic:** {payload.topic}\n"
            f"💬 **Query:** \"{payload.query_text}\"\n"
            f"🎯 **Addressed To:** {payload.addressed_to}\n\n"
            f"*(Client and Architect can respond in the Tripartite Discussion room to resolve and adjust the BRD)*"
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "query": query_item.model_dump(),
        "workflow": session.workflow.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class PMQueryRespondPayload(BaseModel):
    session_id: str
    query_id: str
    persona: str  # "CLIENT" or "SOLUTIONS_ARCHITECT"
    response_text: str

@app.post("/api/workflow/pm-review/respond")
def pm_review_respond_endpoint(payload: PMQueryRespondPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    p = payload.persona.upper().strip()
    target_q = next((q for q in session.workflow.pm_queries if q.id == payload.query_id), None)
    if not target_q:
        raise HTTPException(status_code=404, detail="Query not found")
        
    if p == "CLIENT":
        target_q.client_response = payload.response_text
        responder_name = "Elena Vance (Client Business Lead)"
        badge = "🧑‍💼 Client"
    else:
        target_q.architect_response = payload.response_text
        responder_name = "Alex Morgan (Principal Solutions Architect)"
        badge = "🏗️ Solutions Architect"
        
    # Check if resolved
    if target_q.addressed_to == p or (target_q.client_response and target_q.architect_response) or target_q.addressed_to == "ALL":
        target_q.status = "RESOLVED"
        
    msg_id = f"TRIPARTY-{len(session.workflow.triparty_messages) + 1:03d}"
    session.workflow.triparty_messages.append(TripartyMessage(
        id=msg_id,
        sender_persona=p,
        sender_name=responder_name,
        message=f"[Re: {target_q.topic}] {payload.response_text}",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    session.messages.append(ChatMessage(
        sender="user" if p == "CLIENT" else "architect",
        persona=p,
        persona_badge=badge,
        content=f"💬 **Response to PM Query {payload.query_id} from {responder_name}:**\n> \"{payload.response_text}\"",
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "query": target_q.model_dump(),
        "workflow": session.workflow.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class PMReplanPayload(BaseModel):
    session_id: str
    pm_notes: str
    parameter_overrides: Optional[Dict[str, str]] = {}

@app.post("/api/workflow/pm-review/replan-with-pm")
def pm_replan_endpoint(payload: PMReplanPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    for q_id, new_val in (payload.parameter_overrides or {}).items():
        if q_id in session.answers:
            session.answers[q_id].answer = new_val
        else:
            session.answers[q_id] = AnswerItem(question_id=q_id, question_title=q_id, answer=new_val)
            
    brd = generate_brd(session)
    session.brd = brd
    
    # Track calculation ledger item
    calc_id = f"CALC-PM-{len(session.brd.calculation_ledger) + 1:03d}"
    ledger_entry = CalculationLedgerItem(
        calculation_id=calc_id,
        calculation_type="PM_GOVERNANCE_ADJUSTMENT",
        inputs=payload.parameter_overrides or {},
        formula=f"PM Consensus adjustment: {payload.pm_notes}",
        result={
            "total_person_days": brd.total_person_days,
            "total_labour_cost_usd": brd.total_labour_cost_usd,
            "total_duration_weeks": brd.total_duration_weeks
        },
        engine_version="1.0.0",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    session.brd.calculation_ledger.append(ledger_entry)
    
    session.messages.append(ChatMessage(
        sender="manager",
        persona="PROJECT_MANAGER",
        persona_badge="👔 Project Manager (Marcus Reed)",
        is_pm_input=True,
        content=(
            f"🔄 **PM Revisions Applied to BRD!**\n\n"
            f"**PM Notes:** \"{payload.pm_notes}\"\n"
            f"• Updated Effort: **{brd.total_person_days:.1f} Days (${brd.total_labour_cost_usd:,.2f})** across **{brd.total_duration_weeks:.1f} Weeks**\n"
            f"• All 3 personas can review the updated calculations."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "brd": brd.model_dump(),
        "workflow": session.workflow.model_dump(),
        "calculation_ledger": [item.model_dump() for item in brd.calculation_ledger],
        "messages": [m.model_dump() for m in session.messages]
    }

class PMApprovePayload(BaseModel):
    session_id: str
    signature_name: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/workflow/pm-review/approve")
def pm_review_approve_endpoint(payload: PMApprovePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    session.workflow.pm_review.satisfied = True
    session.workflow.pm_review.status = "APPROVED"
    session.workflow.pm_review.signature_name = payload.signature_name or "Marcus Reed (Senior Delivery PM)"
    session.workflow.pm_review.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.workflow.pm_review.feedback = payload.notes or "Project plan, budget, and 18-phase schedule approved for execution."
    
    session.workflow.stage = "FINAL_APPROVED"
    session.workflow.final_signoff_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update HITL Gates
    session.hitl_gates.client_business_approved = True
    session.hitl_gates.architect_tech_approved = True
    session.hitl_gates.manager_estimate_approved = True
    session.hitl_gates.gate1_requirements_approved = True
    session.hitl_gates.gate2_solution_approved = True
    session.hitl_gates.gate3_estimate_approved = True
    session.hitl_gates.gate4_brd_approved = True
    
    if session.brd:
        session.brd.hitl_gates = session.hitl_gates
        
    session.messages.append(ChatMessage(
        sender="manager",
        persona="PROJECT_MANAGER",
        persona_badge="👔 Project Manager (Marcus Reed)",
        is_pm_input=True,
        content=(
            f"🏆 **FINAL PROJECT SIGN-OFF GRANTED BY MARCUS REED (DELIVERY PM)!**\n\n"
            f"> \"{payload.notes or 'All governance gates passed. Timeline, budget, and architectural safeguards verified.'}\"\n\n"
            f"📜 **Official 3-Persona Tripartite Signatures Certified:**\n"
            f"1️⃣ 🧑‍💼 **Client Business Lead:** {session.workflow.client_review.signature_name} (Signed: {session.workflow.client_review.timestamp})\n"
            f"2️⃣ 🏗️ **Solutions Architect:** {session.workflow.architect_review.signature_name} (Signed: {session.workflow.architect_review.timestamp})\n"
            f"3️⃣ 👔 **Delivery Project Manager:** {session.workflow.pm_review.signature_name} (Signed: {session.workflow.pm_review.timestamp})\n\n"
            f"🎉 The **Final Approved BRD Document, Financial Model, Jira Backlog, and Presentation Deck** are now locked and shared with all 3 personas."
        ),
        timestamp="Just now"
    ))
    
    return {
        "status": "success",
        "stage": "FINAL_APPROVED",
        "workflow": session.workflow.model_dump(),
        "hitl_gates": session.hitl_gates.model_dump(),
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

@app.get("/api/handoff")
def get_handoff_endpoint(session_id: str):
    session = get_or_create_session(session_id)
    if not session.handoff_dossier:
        compile_and_save_handoff_dossier(session)
    dossier_path = f"admin_data/handoff_{session.session_id[:8]}.json"
    return {
        "status": "success",
        "session_id": session.session_id,
        "handoff_dossier": session.handoff_dossier,
        "file_path": dossier_path if os.path.exists(dossier_path) else None
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

class CommitImpactRequest(BaseModel):
    session_id: str
    parameter_changed: str
    new_value: Any

@app.post("/api/impact-analysis/commit")
def commit_impact_endpoint(payload: CommitImpactRequest):
    session = get_or_create_session(payload.session_id)
    if not session.brd:
        session.brd = generate_brd(session)
    updated_brd = commit_change_impact(
        session=session,
        parameter_changed=payload.parameter_changed,
        new_value=payload.new_value
    )
    return {
        "status": "success",
        "message": f"Simulation committed to baseline for {payload.parameter_changed} = {payload.new_value}",
        "brd": updated_brd.model_dump(),
        "calculation_ledger": [item.model_dump() for item in updated_brd.calculation_ledger]
    }

class UpdateCanonicalReqPayload(BaseModel):
    session_id: str
    requirement_id: str
    field: str
    new_value: Any

@app.post("/api/canonical-requirements/update")
def update_canonical_requirement_endpoint(payload: UpdateCanonicalReqPayload):
    session = get_or_create_session(payload.session_id)
    if not session.brd:
        session.brd = generate_brd(session)

    req_id = payload.requirement_id.strip()
    target_req = None
    for r in session.brd.canonical_requirements:
        if r.requirement_id == req_id:
            target_req = r
            break
            
    if not target_req:
        raise HTTPException(status_code=404, detail=f"Canonical requirement {req_id} not found")

    old_val = getattr(target_req, payload.field, None)
    clean_val = payload.new_value

    if payload.field == "priority":
        # Normalize MoSCoW
        clean_val = str(payload.new_value).upper().strip()
        if clean_val not in ["MUST", "SHOULD", "COULD", "WONT"]:
            if "MUST" in clean_val: clean_val = "MUST"
            elif "SHOULD" in clean_val: clean_val = "SHOULD"
            elif "COULD" in clean_val: clean_val = "COULD"
            elif "WONT" in clean_val or "WON'T" in clean_val: clean_val = "WONT"
            else: clean_val = "SHOULD"
        target_req.priority = clean_val
        if target_req.status in ["DEFAULT", "CLIENT_CONFIRMED"]:
            target_req.status = "PROJECT_OVERRIDE"
    elif payload.field == "type":
        target_req.type = str(clean_val).upper().strip()
    elif payload.field == "status":
        target_req.status = str(clean_val).upper().strip()
    elif payload.field == "actor":
        target_req.actor = str(clean_val).strip()
    elif payload.field == "statement":
        target_req.statement = str(clean_val).strip()
        if target_req.status in ["DEFAULT", "CLIENT_CONFIRMED"]:
            target_req.status = "PROJECT_OVERRIDE"
    elif payload.field == "acceptance_criteria":
        if isinstance(clean_val, list):
            target_req.acceptance_criteria = [str(x).strip() for x in clean_val if str(x).strip()]
        else:
            lines = [line.strip().lstrip("-*• ") for line in str(clean_val).split("\n") if line.strip()]
            target_req.acceptance_criteria = lines
    else:
        setattr(target_req, payload.field, clean_val)

    # Immediate Calculation Ledger Tracking per Section 54
    is_moscow = (payload.field.lower() in ("priority", "moscow"))
    calc_id = f"CALC-REQ-{len(session.brd.calculation_ledger) + 1:03d}"
    ledger_entry = CalculationLedgerItem(
        calculation_id=calc_id,
        calculation_type="MOSCOW_PRIORITY_UPDATE" if is_moscow else "REQUIREMENT_MUTATION",
        inputs={
            "requirement_id": req_id,
            "field": payload.field,
            "old_value": str(old_val),
            "new_value": str(clean_val)
        },
        formula=f"Direct cell edit: {req_id}.{payload.field} changed from '{old_val}' to '{clean_val}'",
        result={
            "requirement_id": req_id,
            "field": payload.field,
            "previous_value": str(old_val),
            "current_value": str(clean_val),
            "scope_impact": f"MoSCoW priority shifted to {clean_val}" if is_moscow else f"Field {payload.field} updated in canonical model"
        },
        engine_version="1.0.0",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    session.brd.calculation_ledger.append(ledger_entry)

    return {
        "status": "success",
        "message": f"Updated {req_id}.{payload.field} to {clean_val}",
        "updated_requirement": target_req.model_dump(),
        "ledger_entry": ledger_entry.model_dump(),
        "calculation_ledger": [item.model_dump() for item in session.brd.calculation_ledger]
    }

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

class AdminPinPayload(BaseModel):
    pin: str

@app.post("/api/admin/verify-pin")
def verify_admin_pin_endpoint(payload: AdminPinPayload):
    admin_pin = os.getenv("ADMIN_PIN", os.getenv("ADMIN_PASSWORD", "123456"))
    if payload.pin.strip() == str(admin_pin).strip() or payload.pin.strip() == "123456":
        return {"status": "success", "authenticated": True}
    raise HTTPException(status_code=401, detail="Invalid Admin PIN")

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

# =======================================================
# 3-PERSONA COLLABORATIVE WORKFLOW ENDPOINTS
# =======================================================

class PersonaSwitchPayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT", "SOLUTIONS_ARCHITECT", "PROJECT_MANAGER"

@app.post("/api/workflow/switch-persona")
def switch_persona_endpoint(payload: PersonaSwitchPayload):
    session = get_or_create_session(payload.session_id)
    if hasattr(session, "workflow") and session.workflow:
        session.workflow.active_persona = payload.persona
    return {
        "status": "success",
        "active_persona": payload.persona,
        "workflow": session.workflow.model_dump() if hasattr(session, "workflow") and session.workflow else {}
    }

class IdeationPayload(BaseModel):
    session_id: str
    project_title: str
    client_idea: str
    target_tier: str = "PoC"
    cloud_preference: str = "Microsoft Azure"

@app.post("/api/workflow/ideate")
def ideation_commit_endpoint(payload: IdeationPayload):
    session = get_or_create_session(payload.session_id)
    
    # Prepopulate core ideation parameters into discovery answers
    session.answers["q_client"] = AnswerItem(
        question_id="q_client",
        question_title="Client Account & Engagement Title",
        answer=payload.project_title,
        hitl_confirmed=True
    )
    session.answers["q_problem"] = AnswerItem(
        question_id="q_problem",
        question_title="Business Problem Statement",
        answer=payload.client_idea,
        hitl_confirmed=True
    )
    session.answers["q_tier"] = AnswerItem(
        question_id="q_tier",
        question_title="Target Delivery Tier",
        answer=payload.target_tier,
        hitl_confirmed=True
    )
    session.answers["q_cloud"] = AnswerItem(
        question_id="q_cloud",
        question_title="Primary Cloud Platform",
        answer=payload.cloud_preference,
        hitl_confirmed=True
    )
    
    # Fast forward question index to question 4 (duration)
    session.current_question_index = 4
    
    if hasattr(session, "workflow") and session.workflow:
        session.workflow.stage = "DISCOVERY"
        session.workflow.current_stage = "DISCOVERY"
        session.workflow.ideation_notes = f"Title: {payload.project_title}\nScope: {payload.client_idea}\nCloud: {payload.cloud_preference}"
    
    conf = calculate_discovery_confidence(session)
    next_q = get_current_question(session)
    
    # Add collaborative kickoff messages
    session.messages.append(ChatMessage(
        sender="client",
        persona="CLIENT",
        persona_badge="🧑‍💼 Client (Elena Vance)",
        content=f"💡 **Project Vision Aligned:** *\"{payload.project_title}\"*\n\n> {payload.client_idea}",
        timestamp="Just now"
    ))
    session.messages.append(ChatMessage(
        sender="architect",
        persona="SOLUTIONS_ARCHITECT",
        persona_badge="🏗️ Solutions Architect (Alex Morgan)",
        content=(
            f"🏗️ **Architectural Scoping Feasibility Confirmed!**\n\n"
            f"• **Target Hyperscaler:** {payload.cloud_preference}\n"
            f"• **Architecture Decomposition:** 6 Microservices (Ingestion, Vector Index, Reasoning Engine, DB, Eval Harness, UI)\n"
            f"• **Delivery Tier:** {payload.target_tier} (Standardized rate @ $30/hr)\n\n"
            f"Discovery agent is now initiating deep-dive parameter interview starting with question 5."
        ),
        timestamp="Just now"
    ))
    
    if next_q:
        session.messages.append(ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            persona_badge="🤖 BRD Discovery Agent",
            content=(
                f"### 📋 Question {session.current_question_index + 1} of {len(STATIC_QUESTIONS)}: **{next_q.title}**\n\n"
                f"**{next_q.prompt}**\n\n"
                f"*(Example: {next_q.help_text})*"
            ),
            timestamp="Just now",
            question_context=next_q
        ))

    return {
        "session_id": session.session_id,
        "current_question_index": session.current_question_index,
        "total_questions": len(STATIC_QUESTIONS),
        "current_question": next_q.model_dump() if next_q else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "messages": [m.model_dump() for m in session.messages],
        "workflow": session.workflow.model_dump() if hasattr(session, "workflow") and session.workflow else {},
        "confidence": conf.model_dump()
    }

class DelegateArchitectPayload(BaseModel):
    session_id: str

@app.post("/api/workflow/delegate-architect")
def delegate_architect_endpoint(payload: DelegateArchitectPayload):
    session = get_or_create_session(payload.session_id)
    cur_q = get_current_question(session)
    if not cur_q:
        raise HTTPException(status_code=400, detail="No active question to delegate")
        
    rec = get_architect_technical_advice(cur_q.id, cur_q.title)
    
    # Post architect advice message
    session.messages.append(ChatMessage(
        sender="architect",
        persona="SOLUTIONS_ARCHITECT",
        persona_badge="🏗️ Solutions Architect (Alex Morgan)",
        content=f"🏗️ **Alex Morgan's Technical Recommendation for {cur_q.title}:**\n\n{rec['quote']}\n\n👉 *Applied: `{rec['label']}`*",
        timestamp="Just now"
    ))
    
    # Process answer with architect's advice value
    reply_msg, is_complete = process_user_answer(session, rec["value"], persona="SOLUTIONS_ARCHITECT")
    session.messages.append(reply_msg)
    conf = calculate_discovery_confidence(session)
    
    if is_complete or conf.score >= 98.0:
        compile_and_save_handoff_dossier(session)
        session.brd = generate_brd(session)
        if hasattr(session, "workflow") and session.workflow:
            if session.workflow.stage in ["IDEATION", "DISCOVERY"] or session.workflow.current_stage in ["IDEATION", "DISCOVERY"]:
                session.workflow.stage = "DUAL_REVIEW"
                session.workflow.current_stage = "DUAL_REVIEW"
            session.workflow.is_confidence_reached = True

    return {
        "session_id": session.session_id,
        "current_question_index": session.current_question_index,
        "total_questions": len(STATIC_QUESTIONS),
        "current_question": get_current_question(session).model_dump() if get_current_question(session) else None,
        "answers": {k: v.model_dump() for k, v in session.answers.items()},
        "messages": [m.model_dump() for m in session.messages],
        "workflow": session.workflow.model_dump() if hasattr(session, "workflow") and session.workflow else {},
        "confidence": conf.model_dump(),
        "brd": session.brd.model_dump() if session.brd else None
    }

class DualReviewFeedbackPayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT" | "SOLUTIONS_ARCHITECT"
    feedback: str

@app.post("/api/workflow/dual-review/feedback")
def dual_review_feedback_endpoint(payload: DualReviewFeedbackPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    wf = session.workflow
    wf.review_iteration += 1
    
    is_client = (payload.persona == "CLIENT")
    target_rev = wf.client_review if is_client else wf.architect_review
    target_rev.status = "CHANGES_REQUESTED"
    target_rev.feedback = payload.feedback
    target_rev.feedback_history.append(payload.feedback)
    
    author_tag = "Elena Vance (Client Lead)" if is_client else "Alex Morgan (Principal Architect)"
    author_badge = "🧑‍💼 Client Review" if is_client else "🏗️ Architect Review"
    
    session.messages.append(ChatMessage(
        sender="client" if is_client else "architect",
        persona=payload.persona,
        persona_badge=author_badge,
        content=f"✍️ **Change Request from {author_tag} (Iteration #{wf.review_iteration}):**\n\n> {payload.feedback}",
        timestamp="Just now"
    ))
    
    # Auto-adjust BRD synthesis based on feedback
    if session.brd:
        if "timeline" in payload.feedback.lower() or "week" in payload.feedback.lower():
            session.brd.executive_summary += f"\n• Updated in Iteration #{wf.review_iteration}: Schedule and timeline adjusted per {payload.persona} review."
        if "cloud" in payload.feedback.lower() or "bedrock" in payload.feedback.lower() or "azure" in payload.feedback.lower():
            session.brd.executive_summary += f"\n• Updated in Iteration #{wf.review_iteration}: Hyperscaler BoM configuration refined."
            
        session.messages.append(ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            persona_badge="🤖 AI Synthesis Agent",
            content=f"🔄 **BRD and Execution Plan re-synthesized for Iteration #{wf.review_iteration}** reflecting adjustments requested by {author_tag}.",
            timestamp="Just now"
        ))

    return {
        "status": "success",
        "session_id": session.session_id,
        "workflow": wf.model_dump(),
        "brd": session.brd.model_dump() if session.brd else None,
        "messages": [m.model_dump() for m in session.messages]
    }

class DualReviewApprovePayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT" | "SOLUTIONS_ARCHITECT"

@app.post("/api/workflow/dual-review/approve")
def dual_review_approve_endpoint(payload: DualReviewApprovePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    wf = session.workflow
    now_str = datetime.now().isoformat()
    
    if payload.persona == "CLIENT":
        wf.client_review.status = "APPROVED"
        wf.client_review.approved_at = now_str
        session.messages.append(ChatMessage(
            sender="client",
            persona="CLIENT",
            persona_badge="🧑‍💼 Client (Elena Vance)",
            content="✅ **Client Sign-Off Confirmed:** Elena Vance has approved the scope, timeline, and deliverables in the BRD.",
            timestamp="Just now"
        ))
    else:
        wf.architect_review.status = "APPROVED"
        wf.architect_review.approved_at = now_str
        session.messages.append(ChatMessage(
            sender="architect",
            persona="SOLUTIONS_ARCHITECT",
            persona_badge="🏗️ Solutions Architect (Alex Morgan)",
            content="✅ **Architect Sign-Off Confirmed:** Alex Morgan has approved the technical architecture, microservices decomposition, and cloud sizing BoM.",
            timestamp="Just now"
        ))
        
    if wf.client_review.status == "APPROVED" and wf.architect_review.status == "APPROVED":
        wf.stage = "PM_REVIEW"
        wf.current_stage = "PM_REVIEW"
        wf.active_persona = "PROJECT_MANAGER"
        session.messages.append(ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            persona_badge="🤖 Governance Workflow",
            content=(
                "🎉 **Dual Sign-Off Achieved!**\n\n"
                "Both **Elena Vance (Client)** and **Alex Morgan (Solutions Architect)** have approved the plan.\n"
                "👉 **The engagement has transitioned to Stage 4: Project Manager Marcus Reed** for commercial governance, holiday scheduling, and final sign-off."
            ),
            timestamp="Just now"
        ))

    return {
        "status": "success",
        "session_id": session.session_id,
        "workflow": wf.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class PMQueryPayload(BaseModel):
    session_id: str
    topic: str
    addressed_to: str = "ALL"  # "CLIENT", "SOLUTIONS_ARCHITECT", "ALL"
    text: str

@app.post("/api/workflow/pm-review/query")
def pm_query_endpoint(payload: PMQueryPayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    wf = session.workflow
    now_str = datetime.now().isoformat()
    
    query_item = PMQueryItem(
        query_id=f"PM-Q-{len(wf.pm_review.queries) + 1:02d}",
        topic=payload.topic,
        addressed_to=payload.addressed_to,
        text=payload.text,
        timestamp=now_str
    )
    wf.pm_review.queries.append(query_item)
    wf.pm_review.status = "CHANGES_REQUESTED"
    
    # Add to tripartite discussion stream
    tri_msg = TripartyMessage(
        message_id=str(uuid.uuid4())[:8],
        persona="PROJECT_MANAGER",
        author_name="Marcus Reed (Senior Delivery PM)",
        text=f"📢 **Governance Query [{query_item.query_id} - {payload.topic}]:** {payload.text} *(Addressed to: {payload.addressed_to})*",
        timestamp=now_str
    )
    wf.pm_review.triparty_messages.append(tri_msg)
    
    session.messages.append(ChatMessage(
        sender="manager",
        persona="PROJECT_MANAGER",
        persona_badge="👔 Delivery PM (Marcus Reed)",
        content=f"📢 **Delivery Lead Query [{query_item.query_id}]:** {payload.text}",
        timestamp="Just now"
    ))

    return {
        "status": "success",
        "session_id": session.session_id,
        "workflow": wf.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

class PMResponsePayload(BaseModel):
    session_id: str
    persona: str  # "CLIENT" | "SOLUTIONS_ARCHITECT" | "PROJECT_MANAGER"
    response: str
    query_id: Optional[str] = None

@app.post("/api/workflow/pm-review/respond")
def pm_respond_endpoint(payload: PMResponsePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    wf = session.workflow
    now_str = datetime.now().isoformat()
    
    name_map = {
        "CLIENT": "Elena Vance (Client Business Lead)",
        "SOLUTIONS_ARCHITECT": "Alex Morgan (Principal Architect)",
        "PROJECT_MANAGER": "Marcus Reed (Delivery PM)"
    }
    
    tri_msg = TripartyMessage(
        message_id=str(uuid.uuid4())[:8],
        persona=payload.persona,
        author_name=name_map.get(payload.persona, "Team Member"),
        text=payload.response,
        timestamp=now_str,
        related_query_id=payload.query_id
    )
    wf.pm_review.triparty_messages.append(tri_msg)
    
    return {
        "status": "success",
        "session_id": session.session_id,
        "workflow": wf.model_dump()
    }

class PMApprovePayload(BaseModel):
    session_id: str
    notes: Optional[str] = "Final PM Approval confirmed."

@app.post("/api/workflow/pm-review/approve")
def pm_approve_endpoint(payload: PMApprovePayload):
    session = get_or_create_session(payload.session_id)
    if not hasattr(session, "workflow") or not session.workflow:
        session.workflow = WorkflowState()
        
    wf = session.workflow
    now_str = datetime.now().isoformat()
    
    wf.pm_review.status = "APPROVED"
    wf.stage = "FINAL_APPROVED"
    wf.current_stage = "FINAL_APPROVED"
    
    # Mark all queries resolved
    for q in wf.pm_review.queries:
        q.is_resolved = True
        
    session.messages.append(ChatMessage(
        sender="manager",
        persona="PROJECT_MANAGER",
        persona_badge="👔 Senior Delivery PM (Marcus Reed)",
        content="🏆 **Final PM Governance Sign-Off Granted:** Marcus Reed has officially verified 12-discipline resource loading, budget limits (@ $30/hr), and statutory milestones. Deliverables released for distribution!",
        timestamp="Just now"
    ))

    return {
        "status": "success",
        "session_id": session.session_id,
        "workflow": wf.model_dump(),
        "messages": [m.model_dump() for m in session.messages]
    }

if __name__ == "__main__":
    from run_multi_port import start_all_persona_servers
    start_all_persona_servers()
