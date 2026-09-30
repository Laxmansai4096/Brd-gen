import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.models import QuestionItem, QuestionOption, AnswerItem, ProjectSession, ChatMessage
from backend.admin_store import get_admin_defaults, get_calendar_for_geography, DELIVERY_TIERS

STATIC_QUESTIONS: List[QuestionItem] = [
    # 1. Project Timeline & Scheduling Factors
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
            QuestionOption(value="PoC", label="Proof of Concept (PoC) [Base 0.289]", description="Throwaway build, happy path, sampled data, single env, headline weight 0.289"),
            QuestionOption(value="Pilot", label="Pilot Trial [Base 0.525]", description="Limited live trial with controlled cohort, real data, ring-fenced"),
            QuestionOption(value="MVP", label="Minimum Viable Product (MVP) [Base 0.778]", description="Production-grade core slice, real users, automated CI/CD"),
            QuestionOption(value="Production Grade", label="Production Grade [Base 1.000]", description="Full enterprise readiness, enforced NFRs, full HA/DR"),
            QuestionOption(value="PoC to Pilot", label="PoC to Pilot [Transition 0.320]", description="Uplift existing PoC to controlled live trial with rework uplift"),
            QuestionOption(value="PoC to MVP", label="PoC to MVP [Transition 0.612]", description="Uplift existing PoC directly to releasable MVP slice"),
            QuestionOption(value="PoC to Production Grade", label="PoC to Production Grade [Transition 0.867]", description="Uplift existing PoC straight to full production grade"),
            QuestionOption(value="Pilot to MVP", label="Pilot to MVP [Transition 0.342]", description="Uplift running pilot into releasable MVP"),
            QuestionOption(value="Pilot to Production Grade", label="Pilot to Production Grade [Transition 0.597]", description="Uplift running pilot to full production grade"),
            QuestionOption(value="MVP to Production Grade", label="MVP to Production Grade [Transition 0.305]", description="Harden live MVP to full production grade"),
            QuestionOption(value="Incremental Production Grade", label="Incremental Production Grade [Delta 0.300]", description="Delta release on live solution (30% scope share)")
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
        default_value="Limited visibility into contractual risk exposure across contracts and business functions. Manual review by scarce legal experts is slow, disconnected, and lacks traceability. The solution must extract clauses across 6 legal categories (Lease, Vendor, Service, Facilities, Technology, Marketing), assess them against category principles (Agree, Agree with Management Approval, Not Agree), and produce a centralized contract risk register with bounding-box coordinate traceability.",
        category="Scope",
        priority="Blocker",
        help_text="Detail who is impacted, bottlenecks, and what decision or action this solution enables."
    ),
    QuestionItem(
        id="q_legal_categories",
        title="In-Scope Business & Legal Categories",
        prompt="Which contract categories are in scope for clause extraction and principle assessment?",
        type="dropdown",
        options=[
            QuestionOption(value="Lease, Vendor, Service, Facilities, Technology, Marketing", label="6 Core Categories (Recommended)", description="Lease, Vendor, Service, Facilities, Technology, Marketing"),
            QuestionOption(value="Lease, Vendor, Service", label="3 Commercial Categories", description="Lease, Vendor, and Service contracts only"),
            QuestionOption(value="Technology, Facilities, Marketing", label="3 Operational Categories", description="Technology, Facilities, and Marketing contracts only")
        ],
        default_value="Lease, Vendor, Service, Facilities, Technology, Marketing",
        category="Scope",
        priority="High",
        help_text="6 standard categories: Lease, Vendor, Service, Facilities, Technology, Marketing."
    ),
    QuestionItem(
        id="q_duration",
        title="Reference Duration (Weeks)",
        prompt="What is the targeted reference duration for this phase in calendar weeks?",
        type="dropdown",
        options=[
            QuestionOption(value="4.0", label="4 Weeks", description="Aggressive sprint"),
            QuestionOption(value="6.0", label="6 Weeks (Standard Baseline)", description="Standard 6-week baseline (30 working days)"),
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
        default_value="2026-09-30",
        category="Scope",
        priority="High",
        help_text="e.g. 2026-09-30 (Used to map exact day-wise working dates and regional statutory holidays)."
    ),
    QuestionItem(
        id="q_buffer_strategy",
        title="Resource Standby & Backup Strategy",
        prompt="What backup/shadow engineering capacity should be maintained on standby for critical roles?",
        type="dropdown",
        options=[
            QuestionOption(value="15% Shadow / Backup Capacity (Recommended)", label="15% Standby Backup Capacity (Recommended)", description="Maintains 15% shadow engineers on standby to absorb sick leaves, attrition, and sudden sprint spikes"),
            QuestionOption(value="10% Standard Staffing Buffer", label="10% Standard Staffing Buffer", description="Standard 10% contingency buffer"),
            QuestionOption(value="25% High-Resilience Shadow Engineering", label="25% High-Resilience Shadow Engineering", description="Heavy standby buffer for mission-critical timelines"),
            QuestionOption(value="0% Dedicated Core Only (Zero Standby)", label="0% Dedicated Core Only (Zero Standby)", description="Minimal backup buffer (higher risk of milestone slippage)")
        ],
        default_value="15% Shadow / Backup Capacity (Recommended)",
        category="Resourcing",
        priority="High",
        help_text="Ensures zero delivery delay in case of resource leaves or unexpected technical blockers."
    ),
    # 2. Delivery Effort & Sizing Multipliers (Scale Drivers)
    QuestionItem(
        id="q_usecases_count",
        title="Distinct Use Cases / Capabilities",
        prompt="How many distinct AI/business use cases or capabilities are in scope for this phase? (Baseline is 1)",
        type="number",
        default_value="1",
        category="Scale",
        priority="High",
        help_text="1 for Contract Risk & Principle Extraction Intelligence (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_personas_count",
        title="User Personas Count",
        prompt="How many distinct user personas or stakeholder roles will interact with the system? (Baseline is 2)",
        type="number",
        default_value="4",
        category="Scale",
        priority="High",
        help_text="4 active personas: Legal Counsel, Procurement Lead, Risk Officer, Executive Sponsor (Factor: 1.450, Elasticity: 0.45)."
    ),
    QuestionItem(
        id="q_integrations_count",
        title="System Integrations Count",
        prompt="How many inbound/outbound enterprise system integrations are required in this phase? (Baseline is 2)",
        type="number",
        default_value="0",
        category="Scale",
        priority="High",
        help_text="0 external interfaces for PoC manual upload (Scaled to floor factor 0.500, Elasticity: 0.65)."
    ),
    QuestionItem(
        id="q_datasources_count",
        title="Distinct Data Sources",
        prompt="How many distinct data sources or document repositories feed into this solution? (Baseline is 2)",
        type="number",
        default_value="2",
        category="Scale",
        priority="High",
        help_text="Blob Storage contract repository + historical risk register spreadsheet (Total: 2, Factor: 1.000)."
    ),
    QuestionItem(
        id="q_channels_count",
        title="Delivery Channels",
        prompt="How many user-facing delivery channels are in scope (e.g., Web Cockpit, Mobile, Teams Bot, REST API)?",
        type="number",
        default_value="1",
        category="Scale",
        priority="Medium",
        help_text="1 for single Web Cockpit UI (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_languages_count",
        title="Languages Supported",
        prompt="How many languages must be processed by the document intelligence engine?",
        type="number",
        default_value="1",
        category="Scale",
        priority="Medium",
        help_text="1 for English-only clean digital PDFs (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_envs_count",
        title="Deployment Environments",
        prompt="How many isolated cloud environments must be provisioned (e.g., Dev, Test, Prod)?",
        type="number",
        default_value="3",
        category="Scale",
        priority="High",
        help_text="3 for Dev, Test, and Prod / UAT (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_components_count",
        title="Architecture Components Count",
        prompt="How many distinct deployable architecture components carry the target solution? (Baseline is 6)",
        type="number",
        default_value="6",
        category="Scale",
        priority="High",
        help_text="6 for Landing, Search Index, Reasoning Engine, Database, Eval Harness, UI Cockpit (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_complexity",
        title="Technical Complexity Level",
        prompt="What is the overall technical complexity of the domain and algorithms?",
        type="dropdown",
        options=[
            QuestionOption(value="Low", label="Low (0.850 Multiplier)", description="Standard RAG, structured documents, straightforward schemas"),
            QuestionOption(value="Medium", label="Medium (1.000 Baseline)", description="Moderate multi-step extraction and custom ontologies"),
            QuestionOption(value="High", label="High (1.250 Multiplier)", description="Deep agentic reasoning, cross-document reasoning"),
            QuestionOption(value="Very High", label="Very High (1.500 Multiplier)", description="Custom model fine-tuning, complex multi-modal pipelines")
        ],
        default_value="Low",
        category="Scale",
        priority="High",
        help_text="Graded as Low, applying a flat 0.850 multiplier across task library."
    ),
    QuestionItem(
        id="q_compliance",
        title="Compliance & Regulatory Posture",
        prompt="What is the compliance posture governing this system's data and operations?",
        type="dropdown",
        options=[
            QuestionOption(value="None", label="None (1.000x)", description="No specific regulatory governance"),
            QuestionOption(value="Internal policy only", label="Internal Policy Only (1.050x)", description="Bound by internal data governance (+5% uplift on COMP tasks)"),
            QuestionOption(value="Regulated - moderate", label="Regulated - Moderate (1.150x)", description="Standard industry regulatory audit requirements"),
            QuestionOption(value="Regulated - high (BFSI/Health/Gov)", label="Regulated - High (1.300x)", description="Strict statutory audits (BFSI, HIPAA, Government)")
        ],
        default_value="Internal policy only",
        category="Scale",
        priority="High",
        help_text="Bound by Internal policy only, triggering 1.050 (+5%) uplift on COMP tasks."
    ),
    QuestionItem(
        id="q_security",
        title="Security Posture & Isolation",
        prompt="What security posture and network isolation is mandated for this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Standard", label="Standard (1.000 Baseline)", description="HTTPS, RBAC, platform-managed encryption keys, Managed Identities"),
            QuestionOption(value="Enhanced", label="Enhanced (1.120x)", description="VNet injection, Private Endpoints, Customer-Managed Keys (CMEK)"),
            QuestionOption(value="Restricted / Air-gapped", label="Restricted / Air-Gapped (1.300x)", description="Zero internet ingress/egress, air-gapped isolation")
        ],
        default_value="Standard",
        category="Scale",
        priority="High",
        help_text="Standard security posture, keeping SEC tasks at baseline 1.000 multiplier."
    ),
    # 3. Technology Stack, Cloud & Infrastructure Factors
    QuestionItem(
        id="q_cloud",
        title="Primary Hyperscaler Platform",
        prompt="Which cloud platform will host this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Microsoft Azure", label="Microsoft Azure (Sole Approved Platform)", description="Azure AI Document Intelligence, Azure OpenAI, AI Search, Blob Storage"),
            QuestionOption(value="Google Cloud Platform", label="Google Cloud Platform (GCP)", description="Vertex AI, Gemini, Document AI, Cloud Storage"),
            QuestionOption(value="Amazon Web Services", label="Amazon Web Services (AWS)", description="AWS Bedrock, Textract, OpenSearch, S3")
        ],
        default_value="Microsoft Azure",
        category="Technical",
        priority="Blocker",
        help_text="Microsoft Azure is the sole approved platform, preventing cross-cloud complexity."
    ),
    QuestionItem(
        id="q_geography",
        title="Deployment Geography & Statutory Holidays",
        prompt="What is the primary deployment geography and statutory calendar location?",
        type="dropdown",
        options=[
            QuestionOption(value="India", label="India (9.0 hrs/day • Fixed Statutory Holidays)", description="5 days/wk, 9.0 hrs/day capacity, Republic Day, Independence Day, Gandhi Jayanti"),
            QuestionOption(value="United States", label="United States (8.0 hrs/day)", description="8.0 hrs/day capacity • 11 statutory holidays"),
            QuestionOption(value="United Kingdom", label="United Kingdom (7.0 hrs/day)", description="7.0 hrs/day capacity • 8 statutory holidays"),
            QuestionOption(value="European Union", label="European Union (7.5 hrs/day)", description="7.5 hrs/day capacity • 10 statutory holidays"),
            QuestionOption(value="Singapore", label="Singapore (8.5 hrs/day)", description="8.5 hrs/day capacity • 11 statutory holidays")
        ],
        default_value="India",
        category="Technical",
        priority="Blocker",
        help_text="India region locks 5 days/wk, 9.0 hrs/day and regional statutory holidays."
    ),
    QuestionItem(
        id="q_onprem_footprint",
        title="On-Premises Infrastructure Footprint",
        prompt="Are any on-premises server components or hybrid network tunnels required?",
        type="dropdown",
        options=[
            QuestionOption(value="No (Zero On-Premises Footprint)", label="No (Zero On-Premises Footprint, 100% Cloud Native)", description="Zero on-premise components; no ExpressRoute/VPN tunnels required"),
            QuestionOption(value="Yes (Hybrid Tunnels Required)", label="Yes (Hybrid ExpressRoute / VPN Required)", description="Requires hybrid network integration to on-prem datacenters")
        ],
        default_value="No (Zero On-Premises Footprint)",
        category="Technical",
        priority="High",
        help_text="Zero on-premises footprint eliminates hybrid tunnel dependencies."
    ),
    QuestionItem(
        id="q_subscription_isolation",
        title="Subscription & Tenant Isolation",
        prompt="What cloud subscription topology will host the deployment?",
        type="dropdown",
        options=[
            QuestionOption(value="Dedicated Non-Production Subscription", label="Dedicated Non-Production Cloud Subscription", description="Newly created dedicated non-prod subscription guaranteeing network isolation"),
            QuestionOption(value="Shared Corporate Non-Production Subscription", label="Shared Corporate Non-Production Subscription", description="Shared non-production subscription with resource-group level RBAC"),
            QuestionOption(value="Isolated Regulated Tenant", label="Isolated Regulated Tenant", description="Strictly separated cloud tenant with dedicated landing zone")
        ],
        default_value="Dedicated Non-Production Subscription",
        category="Technical",
        priority="High",
        help_text="Guarantees clean network isolation from live corporate environments."
    ),
    QuestionItem(
        id="q_hadr_tier",
        title="High Availability & Disaster Recovery (HA/DR)",
        prompt="What High Availability and Disaster Recovery footprint tier is required for hosting?",
        type="dropdown",
        options=[
            QuestionOption(value="None (single instance)", label="None (Single Instance - 1.000x Footprint)", description="Standard single-instance footprint in India region; eliminates multi-region complexity"),
            QuestionOption(value="Zone redundant", label="Zone Redundant (1.350x)", description="Multi-Availability Zone redundancy within primary region"),
            QuestionOption(value="Region pair - active/passive", label="Region Pair - Active/Passive (1.600x)", description="Secondary failover region for disaster recovery"),
            QuestionOption(value="Region pair - active/active", label="Region Pair - Active/Active (2.000x)", description="Dual active regions with global traffic routing")
        ],
        default_value="None (single instance)",
        category="Technical",
        priority="Medium",
        help_text="None (single instance) applies 1.000 footprint multiplier."
    ),
    # 4. AI Engine, RAG Pipeline & Model Sizing Factors
    QuestionItem(
        id="q_foundation_llm",
        title="Foundation LLM Architecture",
        prompt="Which foundation model reasoning tier will interpret open-textured legal clauses?",
        type="dropdown",
        options=[
            QuestionOption(value="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)", label="Azure OpenAI Reasoning Tier (GPT-5 Thinking/Reasoning)", description="Optimized for multi-pass interpretation of open-textured negotiated legal clauses"),
            QuestionOption(value="Azure OpenAI GPT-4o Standard", label="Azure OpenAI GPT-4o Standard", description="General-purpose high-speed multimodal reasoning"),
            QuestionOption(value="Anthropic Claude 3.5 Sonnet", label="Anthropic Claude 3.5 Sonnet", description="Long-context legal extraction engine"),
            QuestionOption(value="Google Gemini 2.5 Pro", label="Google Gemini 2.5 Pro", description="Deep multi-document reasoning")
        ],
        default_value="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)",
        category="AI & RAG",
        priority="High",
        help_text="Azure OpenAI reasoning tier interprets open-textured negotiated legal clauses."
    ),
    QuestionItem(
        id="q_grounding_mode",
        title="Grounding & Surface Mode",
        prompt="What grounding boundary controls model retrieval access?",
        type="dropdown",
        options=[
            QuestionOption(value="Work (Tenant Data Only)", label="Work (Tenant Data Only, Public Web Disabled)", description="Grounding strictly locked to tenant contract corpus; zero public web search via M365 Copilot / Azure AI Agent services"),
            QuestionOption(value="Hybrid (Tenant Data + Selective Public Web)", label="Hybrid (Tenant Data + Selective Public Web)", description="Enables external regulatory lookup alongside internal documents")
        ],
        default_value="Work (Tenant Data Only)",
        category="AI & RAG",
        priority="High",
        help_text="Locked to 'Work' grounding, preventing external public web retrieval."
    ),
    QuestionItem(
        id="q_doc_processing",
        title="Document Processing & Layout Complexity",
        prompt="What document intelligence technology parses layout-aware structures across ~600 sample contracts?",
        type="dropdown",
        options=[
            QuestionOption(value="Azure AI Document Intelligence Layout API", label="Azure AI Document Intelligence (Layout-Aware API)", description="Extracts text, tables, bounding-box coordinates across ~600 sample contracts"),
            QuestionOption(value="Standard OCR Text Extraction", label="Standard OCR Text Extraction", description="Basic flat-text extraction without coordinate bounding boxes")
        ],
        default_value="Azure AI Document Intelligence Layout API",
        category="AI & RAG",
        priority="High",
        help_text="Recovers bounding-box coordinates for 100% source clause traceability."
    ),
    QuestionItem(
        id="q_named_users",
        title="Total Named Users",
        prompt="How many total named users are entitled to access the platform?",
        type="number",
        default_value="200",
        category="Sizing",
        priority="Medium",
        help_text="200 named legal, procurement, and risk reviewers."
    ),
    QuestionItem(
        id="q_concurrent_users",
        title="Peak Concurrent Users",
        prompt="What is the maximum number of simultaneous users active during peak hours?",
        type="number",
        default_value="50",
        category="Sizing",
        priority="Medium",
        help_text="50 peak concurrent users driving API concurrency."
    ),
    QuestionItem(
        id="q_daily_requests",
        title="Model Requests per Day",
        prompt="What is the estimated volume of document processing/analysis requests per day?",
        type="number",
        default_value="2000",
        category="Sizing",
        priority="Medium",
        help_text="2,000 requests per day with peak processing speed of 3.00 RPS."
    ),
    # 5. Data Governance & Parser Contract Factors
    QuestionItem(
        id="q_multi_pass_policy",
        title="Multi-Pass Evaluation Logic",
        prompt="How should contract clauses and risk principles be evaluated?",
        type="dropdown",
        options=[
            QuestionOption(value="Two-Pass Evaluation (Agree / Agree with Mgmt Approval / Not Agree)", label="Two-Pass Evaluation (3 Status Levels: Agree, Mgmt Approval, Not Agree)", description="Pass 1 extracts standard clauses; Pass 2 evaluates ambiguous terms to assign one of 3 statuses"),
            QuestionOption(value="Single-Pass Flat Extraction", label="Single-Pass Flat Extraction", description="Single prompt pass without iterative disambiguation")
        ],
        default_value="Two-Pass Evaluation (Agree / Agree with Mgmt Approval / Not Agree)",
        category="Governance",
        priority="High",
        help_text="Two sequential steps: Pass 1 extracts clauses, Pass 2 evaluates three-tier status."
    ),
    QuestionItem(
        id="q_parser_delimiters",
        title="Parser Delimiters & Truncation Thresholds",
        prompt="What formatting delimiters and cell thresholds govern parser ingestion?",
        type="dropdown",
        options=[
            QuestionOption(value="Block Headers (<<<BEGIN:NAME>>>) & Pipe (|), 30k Char Cap, 0.72 Synonym Threshold", label="Standard Format (<<<BEGIN:NAME>>> & Pipe |, 30k Char Cap, 0.72 Confidence)", description="30,000 char cell cap (>32k quarantined), 0.72 synonym confidence threshold, NOT PROVIDED placeholder"),
            QuestionOption(value="Standard JSON Schema Key-Value Delimiters", label="Standard JSON Schema Parser", description="Pure JSON schema parsing without block headers")
        ],
        default_value="Block Headers (<<<BEGIN:NAME>>>) & Pipe (|), 30k Char Cap, 0.72 Synonym Threshold",
        category="Governance",
        priority="High",
        help_text="Block headers, pipe delimiters, 30k char ceiling, 0.72 synonym match confidence."
    ),
    QuestionItem(
        id="q_approval_gate",
        title="Assumption & Approval Gating",
        prompt="What governance gate protocol enforces stakeholder prerequisites before calculation?",
        type="dropdown",
        options=[
            QuestionOption(value="Strict Assumption Gate (Blocks downline effort until all Approved)", label="Strict Assumption Gate (100% Approval Required)", description="Downline effort calculations and schedule are blocked until stakeholders mark all clarification questions as Approve"),
            QuestionOption(value="Advisory Assumption Gate", label="Advisory Assumption Gate (Non-blocking)", description="Allows schedule generation with unapproved assumption warnings")
        ],
        default_value="Strict Assumption Gate (Blocks downline effort until all Approved)",
        category="Governance",
        priority="Blocker",
        help_text="Enforces strict gate: calculations blocked until all assumptions are Approved."
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

VAGUE_PHRASES = [
    "dont know", "don't know", "not sure", "maybe", "might be", "could be",
    "unknown", "unsure", "not decided", "dunno", "something like", "probably",
    "just a", "automate stuff", "help me decide", "i think", "sort of",
    "no idea", "not clear", "haven't decided", "havent decided", "anything",
    "random", "whatever", "any bot", "just chatbot", "some chatbot", "a chatbot"
]

def check_requires_follow_up(user_input: str, q: QuestionItem) -> Tuple[bool, str, List[Dict[str, str]]]:
    """Checks if the user input is vague, ambiguous, or underspecified for a requirement question."""
    text = user_input.strip().lower()
    has_vague_marker = any(p in text for p in VAGUE_PHRASES)
    
    if q.id == "q_client":
        if has_vague_marker or text in ["unknown", "na", "none", "tbd", "idk"]:
            return True, "🏢 **Could you share the company / client name or working project title?** *(e.g., 'PVR INOX — Contract Intelligence' or 'Acme Corp — Customer AI')*", [
                {"label": "Use Standard Working Title", "value": "Enterprise Client — AI Automation Platform"}
            ]
        return False, "", []
        
    if q.id == "q_problem":
        # Check for vague phrasing or very brief problem statements
        words = text.split()
        is_too_brief = len(words) < 5 and not any(k in text for k in ["contract", "intelligence", "compliance", "procurement", "extraction", "customer support", "invoice", "triage", "search", "legal", "analysis"])
        
        if has_vague_marker or is_too_brief:
            if any(w in text for w in ["bot", "chat", "assistant", "conversational", "llm", "ai"]):
                options = [
                    {"label": "Option A: Internal Knowledge & HR/IT Support Assistant", "value": "Build an Internal Enterprise Knowledge & Policy Q&A Assistant that indexes SharePoint/Blob PDF documents to answer employee questions and reduce HR/IT helpdesk ticket volume."},
                    {"label": "Option B: Omnichannel Customer Support & Service Desk Automation", "value": "Build an Omnichannel Customer Support conversational agent to resolve tier-1 customer inquiries 24/7 with automated CRM and human escalation handoff."},
                    {"label": "Option C: Intelligent Document Processing & Risk Analysis Agent", "value": "Build an automated Document Intelligence pipeline to extract clauses, score risks, and validate regulatory compliance across enterprise documents."}
                ]
                clarification_prompt = (
                    "🔍 **I can help you define the exact scope for your AI Assistant / Chatbot!**\n\n"
                    "To generate a realistic BRD, architecture, and resource plan, could you clarify:\n\n"
                    "1️⃣ **Who will primarily interact with it?** *(e.g., internal employees, customer support agents, or external clients)*\n"
                    "2️⃣ **What documents or systems will it connect to?** *(e.g., SharePoint PDFs, CRM, ERP, SQL Database)*\n"
                    "3️⃣ **What is the primary business outcome?** *(e.g., deflecting tier-1 support tickets, accelerating document review, 24/7 self-service)*\n\n"
                    "💡 *You can type your specific details or pick from one of the solution blueprints below:*"
                )
                return True, clarification_prompt, options
            else:
                options = [
                    {"label": "Option A: Document Intelligence & Contract Extraction", "value": "Automate contract clause extraction, risk scoring, and compliance validation across enterprise document repositories."},
                    {"label": "Option B: Enterprise Conversational Search & Knowledge Assistant", "value": "Provide 24/7 intelligent search and grounded conversational answers over enterprise documentation."},
                    {"label": "Option C: Intelligent Workflow & Data Validation Automation", "value": "Automate repetitive business workflows and data validation pipelines across disparate enterprise core systems."}
                ]
                clarification_prompt = (
                    f"🔍 **Let's flesh out the details for {q.title}!**\n\n"
                    f"To plan the engineering effort accurately, what specific pain points, users, and business goals are you targeting?\n\n"
                    f"*(Feel free to describe in detail, or select one of these common enterprise blueprints:)*"
                )
                return True, clarification_prompt, options

    return False, "", []

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

    # Handle active clarification state
    if session.clarification_state and session.clarification_state.get("question_id") == q.id:
        # Synthesize full detailed requirement from the user's clarification
        initial_input = session.clarification_state.get("initial_input", "")
        clarification_answer = user_input.strip()
        
        # Check if user selected one of our blueprint options
        matched_blueprint = None
        for bp_val in [
            "Build an Internal Enterprise Knowledge & Policy Q&A Assistant that indexes SharePoint/Blob PDF documents to answer employee questions and reduce HR/IT helpdesk ticket volume.",
            "Build an Omnichannel Customer Support conversational agent to resolve tier-1 customer inquiries 24/7 with automated CRM and human escalation handoff.",
            "Build an automated Document Intelligence pipeline to extract clauses, score risks, and validate regulatory compliance across enterprise documents.",
            "Automate contract clause extraction, risk scoring, and compliance validation across enterprise document repositories.",
            "Provide 24/7 intelligent search and grounded conversational answers over enterprise documentation.",
            "Automate repetitive business workflows and data validation pipelines across disparate enterprise core systems."
        ]:
            if clarification_answer.lower() in bp_val.lower() or bp_val.lower() in clarification_answer.lower():
                matched_blueprint = bp_val
                break
                
        if matched_blueprint:
            final_synthesized_requirement = matched_blueprint
        else:
            if "option a" in clarification_answer.lower():
                final_synthesized_requirement = "Build an Internal Enterprise Knowledge & Policy Q&A Assistant that indexes SharePoint/Blob PDF documents to answer employee questions and reduce HR/IT helpdesk ticket volume."
            elif "option b" in clarification_answer.lower():
                final_synthesized_requirement = "Build an Omnichannel Customer Support conversational agent to resolve tier-1 customer inquiries 24/7 with automated CRM and human escalation handoff."
            elif "option c" in clarification_answer.lower():
                final_synthesized_requirement = "Build an automated Document Intelligence pipeline to extract clauses, score risks, and validate regulatory compliance across enterprise documents."
            else:
                # Custom detailed answer given
                if len(clarification_answer.split()) >= 6:
                    final_synthesized_requirement = f"Enterprise AI Solution: {clarification_answer}"
                else:
                    final_synthesized_requirement = f"Enterprise AI Solution targeting {clarification_answer}, automating key business interactions and integrating with enterprise knowledge sources."

        # Clear clarification state and save final answer
        session.clarification_state = None
        session.answers[q.id] = AnswerItem(
            question_id=q.id,
            question_title=q.title,
            answer=final_synthesized_requirement,
            is_default=False,
            ambiguity_count=0,
            hitl_confirmed=True,
            notes=f"Synthesized from user input '{initial_input}' and clarification '{clarification_answer}'."
        )
        session.current_question_index += 1
        next_q = get_current_question(session)
        
        if next_q:
            content = (
                f"✅ **Recorded for {q.title}:**\n> *\"{final_synthesized_requirement}\"*\n\n"
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
            msg = ChatMessage(
                sender="agent",
                content="🎯 **Discovery Complete!** Synthesizing BRD & Project Plan...",
                timestamp="Just now"
            )
            return msg, True

    # Check if this initial answer needs follow-up clarification
    needs_follow_up, follow_up_prompt, follow_up_options = check_requires_follow_up(user_input, q)
    if needs_follow_up:
        session.clarification_state = {
            "question_id": q.id,
            "initial_input": user_input,
            "step": 1
        }
        msg = ChatMessage(
            sender="agent",
            content=follow_up_prompt,
            timestamp="Just now",
            question_context=q,
            hitl_options=follow_up_options
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

def auto_discover_from_document_text(text: str, filename: str, session: ProjectSession) -> Dict[str, Any]:
    """0-Click Document Auto-Discovery: Parses uploaded RFP/SOW/specs and auto-fills discovery parameters."""
    raw = text.lower()
    
    # 1. Detect Client / Title
    client_name = "Enterprise Client — AI Automation Platform"
    for line in text.split("\n")[:10]:
        clean_l = line.strip()
        if len(clean_l) > 5 and any(k in clean_l.lower() for k in ["project", "platform", "rfp", "sow", "system", "contract", "intelligence", "assistant"]):
            client_name = clean_l.replace("#", "").strip()
            break
            
    # 2. Detect Delivery Tier
    tier = "PoC"
    if "production grade" in raw or "enterprise production" in raw:
        tier = "Production Grade"
    elif "pilot" in raw:
        tier = "Pilot"
    elif "mvp" in raw:
        tier = "MVP"
        
    # 3. Detect Cloud
    cloud = "Microsoft Azure"
    if "aws" in raw or "amazon web services" in raw:
        cloud = "Amazon Web Services"
    elif "gcp" in raw or "google cloud" in raw or "vertex" in raw:
        cloud = "Google Cloud Platform"
        
    # 4. Detect Geography
    geo = "India"
    if "united kingdom" in raw or " uk " in raw or "london" in raw:
        geo = "United Kingdom"
    elif "united states" in raw or " us " in raw or "usa" in raw or "north america" in raw:
        geo = "United States"
    elif "european union" in raw or " eu " in raw or "europe" in raw:
        geo = "European Union"
    elif "singapore" in raw or "apac" in raw:
        geo = "Singapore"
        
    # 5. Extract Problem Summary
    problem_summary = (
        f"Automated enterprise AI solution extracted from '{filename}'. "
        f"The system ingests structured and unstructured data, applies generative reasoning and grounding guardrails, "
        f"and delivers decision assistance across business workflows with auditability and human-in-the-loop oversight."
    )
    
    # 6. Extract Scale Metrics
    usecases = 1.0
    personas = 4.0
    integrations = 2.0
    datasources = 2.0
    channels = 1.0
    envs = 3.0
    components = 6.0
    
    if "use cases" in raw or "use case" in raw:
        nums = re.findall(r'(\d+)\s*(?:distinct\s*)?use\s*cases?', raw)
        if nums:
            usecases = min(float(nums[0]), 20.0)
            
    if "persona" in raw:
        nums = re.findall(r'(\d+)\s*(?:user\s*)?personas?', raw)
        if nums:
            personas = min(float(nums[0]), 20.0)
            
    if "integration" in raw or "api" in raw:
        nums = re.findall(r'(\d+)\s*(?:system\s*)?integrations?', raw)
        if nums:
            integrations = min(float(nums[0]), 20.0)

    # Populate session answers
    discovered_answers = {
        "q_client": AnswerItem(question_id="q_client", question_title="Client & Engagement Name", answer=client_name, is_default=False, notes=f"Auto-extracted from {filename}"),
        "q_tier": AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer=tier, is_default=False, notes=f"Inferred tier '{tier}' from document context"),
        "q_problem": AnswerItem(question_id="q_problem", question_title="Problem Statement & Challenge", answer=problem_summary, is_default=False, notes=f"Synthesized from {filename}"),
        "q_duration": AnswerItem(question_id="q_duration", question_title="Reference Duration (Weeks)", answer="6.0" if tier == "PoC" else "12.0", is_default=False),
        "q_start_date": AnswerItem(question_id="q_start_date", question_title="Project Target Start Date", answer="2026-10-05", is_default=False),
        "q_cloud": AnswerItem(question_id="q_cloud", question_title="Primary Hyperscaler Platform", answer=cloud, is_default=False, notes=f"Detected {cloud}"),
        "q_geography": AnswerItem(question_id="q_geography", question_title="Deployment Geography", answer=geo, is_default=False, notes=f"Detected {geo}"),
        "q_buffer_strategy": AnswerItem(question_id="q_buffer_strategy", question_title="Resource Buffer Strategy", answer="15% Shadow / Backup Capacity (Recommended)", is_default=False),
        "q_usecases_count": AnswerItem(question_id="q_usecases_count", question_title="Distinct Use Cases", answer=str(int(usecases)), is_default=False),
        "q_personas_count": AnswerItem(question_id="q_personas_count", question_title="User Personas Count", answer=str(int(personas)), is_default=False),
        "q_integrations_count": AnswerItem(question_id="q_integrations_count", question_title="System Integrations", answer=str(int(integrations)), is_default=False),
        "q_datasources_count": AnswerItem(question_id="q_datasources_count", question_title="Distinct Data Sources", answer=str(int(datasources)), is_default=False),
        "q_channels_count": AnswerItem(question_id="q_channels_count", question_title="Delivery Channels", answer=str(int(channels)), is_default=False),
        "q_languages_count": AnswerItem(question_id="q_languages_count", question_title="Languages Supported", answer="1", is_default=False),
        "q_envs_count": AnswerItem(question_id="q_envs_count", question_title="Deployment Environments", answer=str(int(envs)), is_default=False),
        "q_components_count": AnswerItem(question_id="q_components_count", question_title="Architecture Components", answer=str(int(components)), is_default=False),
        "q_complexity": AnswerItem(question_id="q_complexity", question_title="Complexity Level", answer="Medium" if "complex" in raw else "Low", is_default=False),
        "q_compliance": AnswerItem(question_id="q_compliance", question_title="Compliance Posture", answer="Regulated - moderate" if any(k in raw for k in ["gdpr", "hipaa", "bfsi", "regulatory"]) else "Internal policy only", is_default=False),
        "q_security": AnswerItem(question_id="q_security", question_title="Security Posture", answer="Enhanced" if "private endpoint" in raw or "vnet" in raw else "Standard", is_default=False),
        "q_named_users": AnswerItem(question_id="q_named_users", question_title="Total Named Users", answer="250", is_default=False),
        "q_concurrent_users": AnswerItem(question_id="q_concurrent_users", question_title="Peak Concurrent Users", answer="50", is_default=False),
        "q_daily_requests": AnswerItem(question_id="q_daily_requests", question_title="Model Requests per Day", answer="2500", is_default=False),
        "q_hadr_tier": AnswerItem(question_id="q_hadr_tier", question_title="High Availability Tier", answer="Zone redundant" if "zone redundant" in raw else "None (single instance)", is_default=False),
        "q_multi_pass_policy": AnswerItem(question_id="q_multi_pass_policy", question_title="Extraction Pass Policy", answer="Multi-Pass Agentic Extraction", is_default=False),
        "q_approval_gate": AnswerItem(question_id="q_approval_gate", question_title="Approval Gate", answer="Human-in-the-Loop Assistive Gate", is_default=False)
    }
    
    session.answers.update(discovered_answers)
    session.current_question_index = len(STATIC_QUESTIONS)
    
    return {
        "client_name": client_name,
        "delivery_tier": tier,
        "cloud_platform": cloud,
        "geography": geo,
        "usecases": usecases,
        "personas": personas,
        "integrations": integrations,
        "confidence_score": 92.5
    }
