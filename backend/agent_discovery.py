import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.models import QuestionItem, QuestionOption, AnswerItem, ProjectSession, ChatMessage
from backend.admin_store import get_admin_defaults, get_calendar_for_geography, DELIVERY_TIERS

STATIC_QUESTIONS: List[QuestionItem] = [
    QuestionItem(
        id="q_client",
        title="Client & Engagement Name",
        prompt="Who is the client/account, and what is the working title for this initiative?",
        type="text",
        default_value="PVR INOX | Contract Intelligence & Risk Visibility Platform",
        category="Scope",
        priority="Blocker",
        help_text="e.g., PVR INOX — Contract Intelligence & Risk Visibility Platform"
    ),
    QuestionItem(
        id="q_tier",
        title="Delivery Tier",
        prompt="What is the targeted delivery tier for this engagement?",
        type="dropdown",
        options=[
            QuestionOption(value="PoC", label="Proof of Concept (PoC) [Base]", description="Throwaway build, happy path, sampled data, single env"),
            QuestionOption(value="Pilot", label="Pilot Trial [Base]", description="Limited live trial with controlled cohort, real data, ring-fenced"),
            QuestionOption(value="MVP", label="Minimum Viable Product (MVP) [Base]", description="Production-grade core slice, real users, automated CI/CD"),
            QuestionOption(value="Production Grade", label="Production Grade [Base]", description="Full enterprise readiness, enforced NFRs, full HA/DR"),
            QuestionOption(value="PoC to Pilot", label="PoC to Pilot [Transition]", description="Uplift existing PoC to controlled live trial with rework uplift"),
            QuestionOption(value="PoC to MVP", label="PoC to MVP [Transition]", description="Uplift existing PoC directly to releasable MVP slice"),
            QuestionOption(value="PoC to Production Grade", label="PoC to Production Grade [Transition]", description="Uplift existing PoC straight to full production grade"),
            QuestionOption(value="Pilot to MVP", label="Pilot to MVP [Transition]", description="Uplift running pilot into releasable MVP"),
            QuestionOption(value="Pilot to Production Grade", label="Pilot to Production Grade [Transition]", description="Uplift running pilot to full production grade"),
            QuestionOption(value="MVP to Production Grade", label="MVP to Production Grade [Transition]", description="Harden live MVP to full production grade"),
            QuestionOption(value="Incremental Production Grade", label="Incremental Production Grade [Delta]", description="Delta release on live solution (30% scope share)")
        ],
        default_value="PoC",
        category="Scope",
        priority="Blocker",
        help_text="Select from the 11 delivery tiers to set phase multipliers."
    ),
    QuestionItem(
        id="q_problem",
        title="Problem Statement & Business Challenge",
        prompt="Describe the business problem, manual bottlenecks, and key objectives in 2 to 5 sentences.",
        type="text",
        default_value="Limited visibility into contractual risk exposure across contracts and business functions. Manual review by scarce legal experts is slow, disconnected, and lacks traceability. The solution must extract clauses across categories, assess them against category principles (Agree, Agree with Management Approval, Not Agree), and produce a centralized contract risk register.",
        category="Scope",
        priority="Blocker",
        help_text="Detail who is impacted, bottlenecks, and what decision or action this solution enables."
    ),
    QuestionItem(
        id="q_duration",
        title="Reference Duration (Weeks)",
        prompt="What is the targeted reference duration for this phase in calendar weeks?",
        type="dropdown",
        options=[
            QuestionOption(value="4.0", label="4 Weeks", description="Aggressive sprint"),
            QuestionOption(value="6.0", label="6 Weeks (Standard Baseline)", description="Standard 6-week baseline"),
            QuestionOption(value="8.0", label="8 Weeks", description="Extended PoC / Pilot"),
            QuestionOption(value="12.0", label="12 Weeks", description="MVP Standard"),
            QuestionOption(value="16.0", label="16 Weeks", description="Full Production Grade")
        ],
        default_value="6.0",
        category="Scope",
        priority="High",
        help_text="Reference duration for back-solving required team loading."
    ),
    QuestionItem(
        id="q_start_date",
        title="Project Target Start Date",
        prompt="When is the targeted project kick-off / start date? (YYYY-MM-DD)",
        type="date",
        default_value="2026-10-05",
        category="Scope",
        priority="High",
        help_text="e.g. 2026-10-05 (Used to map exact day-wise working dates and regional statutory holidays)."
    ),
    QuestionItem(
        id="q_cloud",
        title="Primary Hyperscaler Platform",
        prompt="Which cloud platform will host this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Microsoft Azure", label="Microsoft Azure (Recommended)", description="Azure AI Document Intelligence, Azure OpenAI, AI Search, Blob Storage"),
            QuestionOption(value="Google Cloud Platform", label="Google Cloud Platform (GCP)", description="Vertex AI, Gemini, Document AI, Cloud Storage"),
            QuestionOption(value="Amazon Web Services", label="Amazon Web Services (AWS)", description="AWS Bedrock, Textract, OpenSearch, S3")
        ],
        default_value="Microsoft Azure",
        category="Technical",
        priority="Blocker",
        help_text="Primary hyperscaler drives technical component architecture and SKU BoM."
    ),
    QuestionItem(
        id="q_geography",
        title="Deployment Geography & Residency",
        prompt="What is the primary deployment geography and statutory calendar location?",
        type="dropdown",
        options=[
            QuestionOption(value="India", label="India (Central / South)", description="9.0 hrs/day capacity • 12 statutory holidays allowance"),
            QuestionOption(value="United States", label="United States (East / West)", description="8.0 hrs/day capacity • 11 statutory holidays allowance"),
            QuestionOption(value="United Kingdom", label="United Kingdom", description="7.0 hrs/day capacity • 8 statutory holidays allowance"),
            QuestionOption(value="European Union", label="European Union (GDPR)", description="7.5 hrs/day capacity • 10 statutory holidays allowance"),
            QuestionOption(value="Singapore", label="Singapore / APAC", description="8.5 hrs/day capacity • 11 statutory holidays allowance"),
            QuestionOption(value="United Arab Emirates", label="United Arab Emirates", description="8.0 hrs/day capacity • 14 statutory holidays allowance"),
            QuestionOption(value="Australia", label="Australia", description="7.5 hrs/day capacity • 11 statutory holidays allowance"),
            QuestionOption(value="Canada", label="Canada", description="8.0 hrs/day capacity • 10 statutory holidays allowance"),
            QuestionOption(value="Japan", label="Japan", description="8.0 hrs/day capacity • 16 statutory holidays allowance")
        ],
        default_value="India",
        category="Technical",
        priority="Blocker",
        help_text="Determines statutory calendar, daily working capacity, and data residency boundaries."
    ),
    QuestionItem(
        id="q_buffer_strategy",
        title="Resource Standby & Backup Strategy",
        prompt="What backup/shadow engineering capacity should be maintained on standby for critical roles?",
        type="dropdown",
        options=[
            QuestionOption(value="15% Shadow / Backup Capacity (Recommended)", label="15% Standby Backup Capacity (Recommended)", description="Maintains 15% shadow engineers on standby to absorb sick leaves, attrition, and sudden sprint spikes"),
            QuestionOption(value="10% Standard Staffing Buffer", label="10% Standard Staffing Buffer", description="Standard 10% contingency buffer"),
            QuestionOption(value="5% Lean Staffing", label="5% Lean Staffing", description="Minimal backup buffer (higher risk of milestone slippage)")
        ],
        default_value="15% Shadow / Backup Capacity (Recommended)",
        category="Resourcing",
        priority="High",
        help_text="Ensures zero delivery delay in case of resource leaves or unexpected technical blockers."
    ),
    # Granular Scale Drivers
    QuestionItem(
        id="q_usecases_count",
        title="Distinct Use Cases / Capabilities",
        prompt="How many distinct AI/business use cases or capabilities are in scope for this phase? (Baseline is 1)",
        type="number",
        default_value="1",
        category="Scale",
        priority="High",
        help_text="Count genuinely distinct business capabilities (e.g. 1 for Contract Risk Intelligence)."
    ),
    QuestionItem(
        id="q_personas_count",
        title="User Personas Count",
        prompt="How many distinct user personas or stakeholder roles will interact with the system? (Baseline is 2)",
        type="number",
        default_value="4",
        category="Scale",
        priority="High",
        help_text="e.g., Legal Counsel, Procurement Lead, Risk Officer, Executive Sponsor (Total: 4)."
    ),
    QuestionItem(
        id="q_integrations_count",
        title="System Integrations Count",
        prompt="How many inbound/outbound enterprise system integrations are required in this phase? (Baseline is 2)",
        type="number",
        default_value="0",
        category="Scale",
        priority="High",
        help_text="Enter 0 for PoC manual upload, or count external ERP/CLM/IAM systems."
    ),
    QuestionItem(
        id="q_datasources_count",
        title="Distinct Data Sources",
        prompt="How many distinct data sources or document repositories feed into this solution? (Baseline is 2)",
        type="number",
        default_value="2",
        category="Scale",
        priority="High",
        help_text="e.g., Blob Storage contract repository + historical risk register spreadsheet (Total: 2)."
    ),
    QuestionItem(
        id="q_channels_count",
        title="Delivery Channels",
        prompt="How many user-facing delivery channels are in scope (e.g., Web Cockpit, Mobile, Teams Bot, REST API)?",
        type="number",
        default_value="1",
        category="Scale",
        priority="Medium",
        help_text="Enter 1 for single Web Cockpit UI."
    ),
    QuestionItem(
        id="q_languages_count",
        title="Languages Supported",
        prompt="How many languages must be processed by the document intelligence engine?",
        type="number",
        default_value="1",
        category="Scale",
        priority="Medium",
        help_text="Enter 1 for English-only contracts."
    ),
    QuestionItem(
        id="q_envs_count",
        title="Deployment Environments",
        prompt="How many isolated cloud environments must be provisioned (e.g., Dev, Test, Prod)?",
        type="number",
        default_value="3",
        category="Scale",
        priority="High",
        help_text="Enter 3 for Dev, Test, and Prod / UAT."
    ),
    QuestionItem(
        id="q_components_count",
        title="Architecture Components Count",
        prompt="How many distinct deployable architecture components carry the target solution? (Baseline is 6)",
        type="number",
        default_value="6",
        category="Scale",
        priority="High",
        help_text="Enter 6 for Landing, Search Index, Reasoning Engine, Database, Eval Harness, UI Cockpit."
    ),
    QuestionItem(
        id="q_complexity",
        title="Technical Complexity Level",
        prompt="What is the overall technical complexity of the domain and algorithms?",
        type="dropdown",
        options=[
            QuestionOption(value="Low", label="Low (0.85x Multiplier)", description="Standard RAG, structured documents, straightforward schemas"),
            QuestionOption(value="Medium", label="Medium (1.00x Baseline)", description="Moderate multi-step extraction and custom ontologies"),
            QuestionOption(value="High", label="High (1.25x Multiplier)", description="Deep agentic reasoning, cross-document reasoning"),
            QuestionOption(value="Very High", label="Very High (1.50x Multiplier)", description="Custom model fine-tuning, complex multi-modal pipelines")
        ],
        default_value="Low",
        category="Scale",
        priority="High",
        help_text="Applies a flat multiplier across all task library estimates."
    ),
    QuestionItem(
        id="q_compliance",
        title="Compliance & Regulatory Posture",
        prompt="What is the compliance posture governing this system's data and operations?",
        type="dropdown",
        options=[
            QuestionOption(value="None", label="None (1.00x)", description="No specific regulatory governance"),
            QuestionOption(value="Internal policy only", label="Internal Policy Only (1.05x)", description="Company data governance and confidentiality standards"),
            QuestionOption(value="Regulated - moderate", label="Regulated - Moderate (1.15x)", description="Standard industry regulatory audit requirements"),
            QuestionOption(value="Regulated - high (BFSI/Health/Gov)", label="Regulated - High (1.30x)", description="Strict statutory audits (BFSI, HIPAA, Government)")
        ],
        default_value="Internal policy only",
        category="Scale",
        priority="High",
        help_text="Uplifts compliance-flagged (COMP) engineering tasks."
    ),
    QuestionItem(
        id="q_security",
        title="Security Posture & Isolation",
        prompt="What security posture and network isolation is mandated for this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Standard", label="Standard (1.00x)", description="HTTPS, RBAC, platform-managed encryption"),
            QuestionOption(value="Enhanced", label="Enhanced (1.12x)", description="VNet injection, Private Endpoints, Customer-Managed Keys"),
            QuestionOption(value="Restricted / Air-gapped", label="Restricted / Air-Gapped (1.30x)", description="Zero internet ingress/egress, strict isolation")
        ],
        default_value="Standard",
        category="Scale",
        priority="High",
        help_text="Uplifts security-flagged (SEC) engineering tasks."
    ),
    # Granular Sizing Drivers
    QuestionItem(
        id="q_named_users",
        title="Total Named Users",
        prompt="How many total named users are entitled to access the platform?",
        type="number",
        default_value="200",
        category="Sizing",
        priority="Medium",
        help_text="Total legal, procurement, and risk reviewers with accounts."
    ),
    QuestionItem(
        id="q_concurrent_users",
        title="Peak Concurrent Users",
        prompt="What is the maximum number of simultaneous users active during peak hours?",
        type="number",
        default_value="50",
        category="Sizing",
        priority="Medium",
        help_text="Drives API concurrency and App Service sizing."
    ),
    QuestionItem(
        id="q_daily_requests",
        title="Model Requests per Day",
        prompt="What is the estimated volume of document processing/analysis requests per day?",
        type="number",
        default_value="2000",
        category="Sizing",
        priority="Medium",
        help_text="Used to estimate LLM token throughput and Document Intelligence API calls."
    ),
    QuestionItem(
        id="q_hadr_tier",
        title="High Availability & Disaster Recovery (HA/DR)",
        prompt="What High Availability and Disaster Recovery footprint tier is required for hosting?",
        type="dropdown",
        options=[
            QuestionOption(value="None (single instance)", label="None (Single Instance - 1.00x)", description="Standard single-region deployment for PoC/Pilot"),
            QuestionOption(value="Zone redundant", label="Zone Redundant (1.35x)", description="Multi-Availability Zone redundancy within primary region"),
            QuestionOption(value="Region pair - active/passive", label="Region Pair - Active/Passive (1.60x)", description="Secondary failover region for disaster recovery"),
            QuestionOption(value="Region pair - active/active", label="Region Pair - Active/Active (2.00x)", description="Dual active regions with global traffic routing")
        ],
        default_value="None (single instance)",
        category="Sizing",
        priority="Medium",
        help_text="Multiplies infrastructure cloud footprint and BoM costs."
    ),
    QuestionItem(
        id="q_multi_pass_policy",
        title="Extraction Pass Policy & Nuanced Terms",
        prompt="How should ambiguous, vague, or negotiated contract terms be handled during extraction?",
        type="dropdown",
        options=[
            QuestionOption(value="Multi-Pass Agentic Extraction", label="Multi-Pass Agentic Extraction (Recommended)", description="Pass 1: standard clauses; Pass 2+: targeted retrieval for vague terms, capped at 3 passes before exception routing"),
            QuestionOption(value="Single-Pass Extraction", label="Single-Pass Extraction Only", description="Single prompt extraction per document"),
            QuestionOption(value="Strict Manual Flagging", label="Strict Manual Flagging", description="Route any non-standard clause directly to human review")
        ],
        default_value="Multi-Pass Agentic Extraction",
        category="Governance",
        priority="High",
        help_text="Multi-pass balances precision with token limits and bounding-box provenance."
    ),
    QuestionItem(
        id="q_approval_gate",
        title="Human-in-the-Loop Decision Gate",
        prompt="What governance protocol controls principle assessment and assumption approvals?",
        type="dropdown",
        options=[
            QuestionOption(value="Human-in-the-Loop Assistive Gate", label="Assistive AI with 100% Human Sign-Off (Recommended)", description="AI produces Agree / Agree with Approval / Not Agree; humans retain approval authority"),
            QuestionOption(value="Autonomous Approval with Audit Log", label="Autonomous Automated Approval (High Risk)", description="AI directly approves without pre-execution human gate")
        ],
        default_value="Human-in-the-Loop Assistive Gate",
        category="Governance",
        priority="Blocker",
        help_text="Ensures Responsible AI compliance and eliminates unauthorized legal liability."
    )
]

def get_discovery_questions() -> List[QuestionItem]:
    return STATIC_QUESTIONS

def get_current_question(session: ProjectSession) -> Optional[QuestionItem]:
    if session.current_question_index < len(STATIC_QUESTIONS):
        return STATIC_QUESTIONS[session.current_question_index]
    return None

def normalize_answer_value(user_input: str, q: QuestionItem) -> str:
    if not user_input or not str(user_input).strip():
        return q.default_value
    text = str(user_input).strip()
    
    if q.type == "number":
        # Extract numeric characters or float
        import re
        nums = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', text)
        if nums:
            return nums[0]
        return q.default_value
        
    if q.type == "dropdown" and q.options:
        raw = text.lower()
        for opt in q.options:
            if raw == opt.value.lower() or raw == opt.label.lower():
                return opt.value
        for opt in q.options:
            if opt.value.lower() in raw or raw in opt.value.lower() or opt.label.lower() in raw or raw in opt.label.lower():
                return opt.value
    return text

GREETING_WORDS = {
    "hi", "hii", "hiii", "hello", "helloo", "hey", "heyy", "heya", "hola", "howdy",
    "good morning", "good afternoon", "good evening", "good day",
    "what's up", "sup", "yo", "namaste", "vanakkam", "help", "start", "restart",
    "who are you", "what can you do", "test"
}

def is_greeting_or_chit_chat(text: str) -> bool:
    clean = re.sub(r'[^\w\s]', '', text.strip().lower())
    words = clean.split()
    if clean in GREETING_WORDS:
        return True
    if len(words) <= 2 and all(w in GREETING_WORDS for w in words):
        return True
    return False

def check_answer_ambiguity(answer_text: str, q: QuestionItem) -> Tuple[bool, str, List[str]]:
    text = answer_text.strip().lower()
    if q.type == "number":
        # Any valid number string is never ambiguous
        if text.replace('.', '', 1).isdigit():
            return False, "", []
        return True, f"Please enter a valid numeric value for **{q.title}**.", [q.default_value]
        
    if len(text) < 2 or text in ["na", "none", "unknown", "none_unknown", "idk", "not sure", "dunno", "maybe", "whatever", "later"] or text in GREETING_WORDS:
        return True, f"Your answer '{answer_text}' is too brief or ambiguous for **{q.title}**.", [q.default_value]
    return False, "", []

def process_user_answer(session: ProjectSession, user_input: str) -> Tuple[ChatMessage, bool]:
    q = get_current_question(session)
    if not q:
        # Discovery is already finished, handle conversational feedback / refinements!
        raw = user_input.strip().lower()
        
        # Check if user expressed dissatisfaction or requested changes
        if any(w in raw for w in ["not satisfied", "unsatisfied", "dislike", "change", "modify", "adjust", "update", "reduce", "increase", "wrong", "different"]):
            response_text = (
                "🤝 **I understand! Let's tailor the project plan to your exact satisfaction.**\n\n"
                "You can tell me what you would like to adjust, such as:\n"
                "• **Timeline / Sprints:** *'Change duration to 8 weeks'* or *'Reduce duration to 4 weeks'*\n"
                "• **Delivery Tier:** *'Switch tier to MVP'* or *'Make it Pilot'* or *'Production Grade'*\n"
                "• **Cloud Platform:** *'Switch to Google Cloud Platform'*, *'Switch to AWS'*, or *'Switch to Azure'*\n"
                "• **Scale & Concurrency:** *'Set 500 named users and 5 integrations'* or *'Complexity high'*\n"
                "• **Commercial Rate:** *'Change rate to $35/hr'* in Admin Console\n\n"
                "💡 *You can also use the **'Assumptions Gate'** tab on the right to approve, correct, or reject specific design decisions, or click **'Review / Modify Q&A Responses'** to update any setting.*"
            )
            
            # Apply direct parameter changes if mentioned
            modified = False
            if "aws" in raw or "amazon" in raw:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Amazon Web Services")
                modified = True
            elif "gcp" in raw or "google" in raw:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Google Cloud Platform")
                modified = True
            elif "azure" in raw or "microsoft" in raw:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Microsoft Azure")
                modified = True
                
            nums = re.findall(r'(\d+(?:\.\d+)?)\s*(?:weeks?|wks?)', raw)
            if nums:
                session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer=f"{nums[0]}")
                modified = True
                
            if "mvp" in raw:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="MVP")
                modified = True
            elif "pilot" in raw:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Pilot")
                modified = True
            elif "production" in raw:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Production Grade")
                modified = True
            elif "poc" in raw:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="PoC")
                modified = True
                
            if modified:
                response_text = f"🔄 **Updated Plan with your adjustments!** Re-synthesized BRD workbench with: `{user_input}`."
                
            msg = ChatMessage(
                sender="agent",
                content=response_text,
                timestamp="Just now"
            )
            return msg, True
            
        msg = ChatMessage(
            sender="agent",
            content=f"💬 **Noted:** *\"{user_input}\"*. You can explore all detailed sections on the right workbench, click **'Review / Modify Q&A Responses'** to update answers, or type any specific modifications you'd like to make to the plan!",
            timestamp="Just now"
        )
        return msg, True

    # Check if user sent a casual greeting or chit-chat
    if is_greeting_or_chit_chat(user_input):
        msg = ChatMessage(
            sender="agent",
            content=(
                f"👋 **Hello! Great to connect with you.**\n\n"
                f"I am here to capture your project requirements and synthesize a complete Business Requirements Document (BRD) and Day-Wise execution schedule.\n\n"
                f"---\n\n"
                f"### 📋 Question {session.current_question_index + 1} of {len(STATIC_QUESTIONS)}: **{q.title}**\n\n"
                f"**{q.prompt}**\n\n"
                f"*(Example: {q.help_text})*"
            ),
            timestamp="Just now",
            question_context=q
        )
        return msg, False

    normalized_input = normalize_answer_value(user_input, q)
    is_ambiguous, reason, suggestions = check_answer_ambiguity(normalized_input, q)
    current_strikes = session.ambiguity_tracker.get(q.id, 0)

    if is_ambiguous:
        current_strikes += 1
        session.ambiguity_tracker[q.id] = current_strikes

        if current_strikes >= 2:
            session.answers[q.id] = AnswerItem(
                question_id=q.id,
                question_title=q.title,
                answer=q.default_value,
                is_default=True,
                ambiguity_count=current_strikes,
                hitl_confirmed=True,
                notes="Adopted default value after ambiguity fallback."
            )
            session.current_question_index += 1
            next_q = get_current_question(session)
            
            if next_q:
                content = (
                    f"⚠️ *Ambiguity detected.* I have recorded the standard enterprise default: **\"{q.default_value}\"**.\n\n"
                    f"---\n\n"
                    f"### 📋 Question {session.current_question_index + 1} of {len(STATIC_QUESTIONS)}: **{next_q.title}**\n\n"
                    f"**{next_q.prompt}**\n\n"
                    f"*(Example: {next_q.help_text})*"
                )
                msg = ChatMessage(
                    sender="agent",
                    content=content,
                    timestamp="Just now",
                    question_context=next_q,
                    is_hitl_confirmation=True,
                    hitl_default_value=q.default_value
                )
                return msg, False
            else:
                msg = ChatMessage(
                    sender="agent",
                    content="🎯 **Discovery Complete!** Synthesizing BRD & Project Plan...",
                    timestamp="Just now"
                )
                return msg, True
        else:
            content = (
                f"⚠️ **Clarification needed for {q.title}**:\n"
                f"{reason}\n\n"
                f"Please provide specific details or pick from recommended baseline: **{q.default_value}**"
            )
            msg = ChatMessage(
                sender="agent",
                content=content,
                timestamp="Just now",
                question_context=q,
                is_ambiguity_warning=True,
                ambiguity_strike=current_strikes
            )
            return msg, False

    # Valid answer received
    session.answers[q.id] = AnswerItem(
        question_id=q.id,
        question_title=q.title,
        answer=normalized_input,
        is_default=False,
        ambiguity_count=current_strikes,
        hitl_confirmed=True
    )
    session.current_question_index += 1
    next_q = get_current_question(session)

    if next_q:
        content = (
            f"✅ **Recorded for {q.title}:** `{normalized_input}`\n\n"
            f"---\n\n"
            f"### 📋 Question {session.current_question_index + 1} of {len(STATIC_QUESTIONS)}: **{next_q.title}**\n\n"
            f"**{next_q.prompt}**\n\n"
            f"*(Example: {next_q.help_text})*"
        )
        msg = ChatMessage(
            sender="agent",
            content=content,
            timestamp="Just now",
            question_context=next_q
        )
        return msg, False
    else:
        content = (
            "🎉 **Discovery Interview Completed!**\n\n"
            "All parameters have been captured individually across delivery tiers, 18-phase rigour framework, "
            "12 disciplines, and parametric cloud infrastructure sizing. Synthesizing full BRD workbench..."
        )
        msg = ChatMessage(
            sender="agent",
            content=content,
            timestamp="Just now"
        )
        return msg, True

def compile_and_save_handoff_dossier(session: ProjectSession) -> Dict[str, Any]:
    tier = session.answers.get("q_tier", AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="PoC")).answer
    geo = session.answers.get("q_geography", AnswerItem(question_id="q_geography", question_title="Deployment Geography", answer="India")).answer
    cal = get_calendar_for_geography(geo)
    
    dossier = {
        "session_id": session.session_id,
        "timestamp": datetime.now().isoformat(),
        "delivery_tier": tier,
        "tier_metadata": DELIVERY_TIERS.get(tier, DELIVERY_TIERS["PoC"]),
        "calendar": cal,
        "requirements": {qid: a.model_dump() for qid, a in session.answers.items()},
        "uploaded_files": session.uploaded_files,
        "status": "APPROVED_FOR_AGENT_2"
    }
    session.handoff_dossier = dossier
    return dossier
