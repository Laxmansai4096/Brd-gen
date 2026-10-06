import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.models import (
    QuestionItem, QuestionOption, AnswerItem, ProjectSession, ChatMessage,
    DiscoveryConfidence, DimensionScore, PersonaReview, PMQueryItem, TripartyMessage, EscalatedTopicItem
)
from backend.admin_store import get_admin_defaults, get_calendar_for_geography, DELIVERY_TIERS
from backend.llm_gateway import LLMGateway

STATIC_QUESTIONS: List[QuestionItem] = [
    # 1. Project Timeline & Scheduling Factors
    QuestionItem(
        id="q_client",
        title="Client & Engagement Name",
        prompt="Who is the client/account, and what is the working title for this initiative?",
        type="dropdown",
        options=[
            QuestionOption(value="Contract Intelligence & Risk Visibility Platform", label="PVR INOX | Contract Intelligence & Risk Visibility Platform (Recommended)", description="Automated contract risk classification and clause extraction"),
            QuestionOption(value="Enterprise Retail | AI-Powered Customer Support & Virtual Agent Cockpit", label="Enterprise Retail | AI Support & Agent Cockpit", description="Omnichannel customer support resolution and CRM integration"),
            QuestionOption(value="Global Banking Corp | Intelligent AML & Financial Fraud Detection System", label="Global Bank | Financial Fraud & AML Detection", description="Real-time transaction risk scoring and compliance tracking"),
            QuestionOption(value="Healthcare System | Intelligent Clinical Document Extraction Platform", label="Healthcare | Clinical Document Extraction", description="Layout-aware medical record and claims extraction"),
            QuestionOption(value="SaaS Tech Corp | Enterprise Knowledge Base & Neural Search Accelerator", label="SaaS Enterprise | Neural Search & Knowledge Base", description="High-throughput hybrid vector retrieval engine")
        ],
        default_value="PVR INOX | Contract Intelligence & Risk Visibility Platform",
        category="Scope",
        priority="Blocker",
        help_text="Select an enterprise template or pick 'Custom Input' to type your exact client and project title."
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
        type="dropdown",
        options=[
            QuestionOption(
                value="Limited visibility into contractual risk exposure across contracts and business functions. Manual review by scarce legal experts is slow, disconnected, and lacks traceability. The solution must extract clauses across 6 legal categories (Lease, Vendor, Service, Facilities, Technology, Marketing), assess them against category principles (Agree, Agree with Management Approval, Not Agree), and produce a centralized contract risk register with bounding-box coordinate traceability.",
                label="Contract Risk & Legal Bottlenecks (Recommended)",
                description="Extract clauses across 6 categories, 2-pass principle evaluation, centralized risk register"
            ),
            QuestionOption(
                value="High volume of tier-1 customer inquiries causing long wait times, operational overhead, and inconsistent support responses. Manual handling slows resolution and causes agent fatigue. The solution must automate customer deflection via grounded conversational AI, provide human support agent assist, and execute CRM workflows with sub-2-second latency.",
                label="Customer Support & Omnichannel Deflection",
                description="Automate tier-1 inquiries, real-time agent-assist, CRM tool calling"
            ),
            QuestionOption(
                value="Manual document ingestion and data extraction across invoices, receipts, and claim forms causes high defect rates, processing delays, and compliance risks. The solution must execute layout-aware OCR extraction, validate business rules, and export structured outputs with 100% audit provenance.",
                label="Intelligent Document & Invoice Extraction",
                description="Automated layout-aware OCR parsing, validation gates, structured database persistence"
            ),
            QuestionOption(
                value="Enterprise knowledge is fragmented across disparate wikis, file drives, and databases, forcing employees to spend hours locating accurate information. The solution must provide a secure hybrid neural search engine with semantic embeddings, BM25 keyword matching, and strict RBAC.",
                label="Enterprise Knowledge Base & Neural Search",
                description="Hybrid vector and keyword search across enterprise document repositories"
            )
        ],
        default_value="Limited visibility into contractual risk exposure across contracts and business functions. Manual review by scarce legal experts is slow, disconnected, and lacks traceability. The solution must extract clauses across 6 legal categories (Lease, Vendor, Service, Facilities, Technology, Marketing), assess them against category principles (Agree, Agree with Management Approval, Not Agree), and produce a centralized contract risk register with bounding-box coordinate traceability.",
        category="Scope",
        priority="Blocker",
        help_text="Detail who is impacted, bottlenecks, and what decision or action this solution enables."
    ),
    QuestionItem(
        id="q_legal_categories",
        title="In-Scope Functional Domains & Capabilities",
        prompt="Which functional domains, capabilities, or business categories are in scope for this AI solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Lease, Vendor, Service, Facilities, Technology, Marketing", label="Contract Risk & Document Intelligence (Recommended)", description="Clause extraction and compliance scoring across 6 contract categories"),
            QuestionOption(value="Customer Support, IT Helpdesk, Knowledge Retrieval, Automated Triage", label="Conversational AI & Enterprise Copilot", description="Multi-turn user assistance, intelligent search, and ticket automation"),
            QuestionOption(value="Transaction Monitoring, Fraud Detection, KYC Verification, AML Alerts", label="Financial Crime, AML & Predictive ML", description="Real-time transaction scoring, behavioral anomaly alerts, and KYC verification"),
            QuestionOption(value="Clinical Documentation, EHR Summarization, ICD/CPT Coding, Lab Triage", label="Healthcare & Clinical AI Assistant", description="Clinical note summarization, medical coding, and diagnostic triage"),
            QuestionOption(value="Multi-Agent Task Routing, Autonomous Tool Calling, Code Synthesis, RPA", label="Autonomous Multi-Agent Workflow System", description="Cross-system action orchestration, dynamic tool selection, and execution"),
            QuestionOption(value="Enterprise Knowledge Base, Semantic Search, Policy Q&A, Research Synthesis", label="Enterprise RAG & Knowledge Hub", description="Vector-indexed organizational documentation and verifiable QA"),
            QuestionOption(value="Enterprise Procurement, NDAs, Master Service Agreements", label="Enterprise Procurement & MSAs", description="Procurement, NDAs, and vendor agreements")
        ],
        default_value="Lease, Vendor, Service, Facilities, Technology, Marketing",
        category="Scope",
        priority="High",
        help_text="Defines the business domains or capabilities handled by the AI platform (Contract Risk, Copilot, AML, Clinical, Agentic, or RAG)."
    ),
    QuestionItem(
        id="q_duration",
        title="Reference Duration (Weeks)",
        prompt="What is the targeted reference duration for this phase in calendar weeks?",
        type="dropdown",
        options=[
            QuestionOption(value="4.0", label="4.0 Weeks", description="Aggressive 4-week sprint (20 working days)"),
            QuestionOption(value="6.0", label="6.0 Weeks (Standard Baseline)", description="Standard 6-week baseline (30 working days)"),
            QuestionOption(value="8.0", label="8.0 Weeks", description="Extended 8-week PoC / Pilot (40 working days)"),
            QuestionOption(value="12.0", label="12.0 Weeks", description="MVP Standard 12-week build (60 working days)"),
            QuestionOption(value="16.0", label="16.0 Weeks", description="Full Production Grade 16-week delivery (80 working days)")
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
        type="dropdown",
        options=[
            QuestionOption(value="2026-09-30", label="2026-09-30 (Scheduled Baseline)", description="Start without external procurement lag"),
            QuestionOption(value="2026-10-05", label="2026-10-05 (Q4 Kick-Off)", description="Beginning of October"),
            QuestionOption(value="2026-10-15", label="2026-10-15 (Mid-October)", description="Mid-month start"),
            QuestionOption(value="2026-11-02", label="2026-11-02 (November Sprint)", description="Beginning of November")
        ],
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
        type="dropdown",
        options=[
            QuestionOption(value="1 Use Case (Standard Baseline - 1.000x)", label="1 Use Case (Standard Baseline - 1.000x)", description="Single primary capability: Contract Risk & Principle Extraction"),
            QuestionOption(value="2 Use Cases (Factor 1.250x)", label="2 Use Cases (Factor 1.250x)", description="Two distinct functional capabilities"),
            QuestionOption(value="3 Use Cases (Factor 1.500x)", label="3 Use Cases (Factor 1.500x)", description="Three business capabilities"),
            QuestionOption(value="5 Use Cases (Factor 2.000x)", label="5 Use Cases (Factor 2.000x)", description="Multi-department enterprise capabilities")
        ],
        default_value="1 Use Case (Standard Baseline - 1.000x)",
        category="Scale",
        priority="High",
        help_text="1 for Contract Risk & Principle Extraction Intelligence (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_personas_count",
        title="User Personas Count",
        prompt="How many distinct user personas or stakeholder roles will interact with the system? (Baseline is 2)",
        type="dropdown",
        options=[
            QuestionOption(value="4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)", label="4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)", description="Legal Counsel, Procurement Lead, Risk Officer, Executive Sponsor (Elasticity: 0.45)"),
            QuestionOption(value="2 Personas (Standard Baseline - Factor 1.000)", label="2 Personas (Standard Baseline - Factor 1.000)", description="Primary business user and administrator"),
            QuestionOption(value="1 Persona (Single Role - Factor 0.775)", label="1 Persona (Single Role - Factor 0.775)", description="Single designated user type"),
            QuestionOption(value="6 Personas (Enterprise Cross-Functional - Factor 1.900)", label="6 Personas (Enterprise Cross-Functional - Factor 1.900)", description="Broad stakeholder group across legal, ops, audit, and execs")
        ],
        default_value="4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)",
        category="Scale",
        priority="High",
        help_text="4 active personas: Legal Counsel, Procurement Lead, Risk Officer, Executive Sponsor (Factor: 1.450, Elasticity: 0.45)."
    ),
    QuestionItem(
        id="q_integrations_count",
        title="System Integrations Count",
        prompt="How many inbound/outbound enterprise system integrations are required in this phase? (Baseline is 2)",
        type="dropdown",
        options=[
            QuestionOption(value="0 Integrations (Manual Upload / Blob Storage - Floor 0.500x)", label="0 Integrations (Manual Upload / Blob Storage - Floor 0.500x)", description="Manual PDF uploads directly to Azure Blob Storage (Scaled to floor factor 0.500)"),
            QuestionOption(value="1 Integration (Factor 0.675x)", label="1 Integration (Factor 0.675x)", description="Single REST API / ERP connector"),
            QuestionOption(value="2 Integrations (Standard Baseline - Factor 1.000x)", label="2 Integrations (Standard Baseline - Factor 1.000x)", description="Two external system connectors"),
            QuestionOption(value="4 Integrations (Factor 1.650x)", label="4 Integrations (Factor 1.650x)", description="Four enterprise integrations (CRM, ERP, Document Store, Auth)")
        ],
        default_value="0 Integrations (Manual Upload / Blob Storage - Floor 0.500x)",
        category="Scale",
        priority="High",
        help_text="0 external interfaces for PoC manual upload (Scaled to floor factor 0.500, Elasticity: 0.65)."
    ),
    QuestionItem(
        id="q_datasources_count",
        title="Distinct Data Sources",
        prompt="How many distinct data sources or document repositories feed into this solution? (Baseline is 2)",
        type="dropdown",
        options=[
            QuestionOption(value="2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)", label="2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)", description="Azure Blob Storage contract repository + historical risk register spreadsheet"),
            QuestionOption(value="1 Data Source (Single Repository - Factor 0.750x)", label="1 Data Source (Single Repository - Factor 0.750x)", description="Single digital PDF upload repository"),
            QuestionOption(value="3 Data Sources (Factor 1.250x)", label="3 Data Sources (Factor 1.250x)", description="Blob Storage, SQL Database, and SharePoint repository"),
            QuestionOption(value="5 Data Sources (Enterprise Data Lake - Factor 1.750x)", label="5 Data Sources (Enterprise Data Lake - Factor 1.750x)", description="Enterprise data lake, CRM, ERP, Blob, and Wiki")
        ],
        default_value="2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)",
        category="Scale",
        priority="High",
        help_text="Blob Storage contract repository + historical risk register spreadsheet (Total: 2, Factor: 1.000)."
    ),
    QuestionItem(
        id="q_channels_count",
        title="Delivery Channels",
        prompt="How many user-facing delivery channels are in scope (e.g., Web Cockpit, Mobile, Teams Bot, REST API)?",
        type="dropdown",
        options=[
            QuestionOption(value="1 Channel (Web Cockpit UI - Baseline 1.000x)", label="1 Channel (Web Cockpit UI - Baseline 1.000x)", description="Interactive browser-based demonstration and review cockpit"),
            QuestionOption(value="2 Channels (Web Cockpit + Microsoft Teams Bot - Factor 1.300x)", label="2 Channels (Web Cockpit + Microsoft Teams Bot - Factor 1.300x)", description="Web browser app and integrated Teams bot"),
            QuestionOption(value="3 Channels (Web + Mobile App + REST API - Factor 1.600x)", label="3 Channels (Web + Mobile App + REST API - Factor 1.600x)", description="Web, iOS/Android mobile client, and public REST API")
        ],
        default_value="1 Channel (Web Cockpit UI - Baseline 1.000x)",
        category="Scale",
        priority="Medium",
        help_text="1 for single Web Cockpit UI (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_languages_count",
        title="Languages Supported",
        prompt="How many languages must be processed by the document intelligence engine?",
        type="dropdown",
        options=[
            QuestionOption(value="1 Language (English Digital Documents - Baseline 1.000x)", label="1 Language (English Digital Documents - Baseline 1.000x)", description="Clean English digital PDFs only"),
            QuestionOption(value="2 Languages (English + Regional / European - Factor 1.350x)", label="2 Languages (English + Regional / European - Factor 1.350x)", description="Bilingual document processing"),
            QuestionOption(value="5 Languages (Multilingual Enterprise - Factor 2.000x)", label="5 Languages (Multilingual Enterprise - Factor 2.000x)", description="Global multilingual extraction")
        ],
        default_value="1 Language (English Digital Documents - Baseline 1.000x)",
        category="Scale",
        priority="Medium",
        help_text="1 for English-only clean digital PDFs (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_envs_count",
        title="Deployment Environments",
        prompt="How many isolated cloud environments must be provisioned (e.g., Dev, Test, Prod)?",
        type="dropdown",
        options=[
            QuestionOption(value="3 Environments (Dev, Test, Prod - Baseline 1.000x)", label="3 Environments (Dev, Test, Prod - Baseline 1.000x)", description="Development, Test/QA, and Production subscriptions"),
            QuestionOption(value="2 Environments (Dev, Prod - Factor 0.800x)", label="2 Environments (Dev, Prod - Factor 0.800x)", description="Development and Production only"),
            QuestionOption(value="4 Environments (Dev, Test, Staging/UAT, Prod - Factor 1.200x)", label="4 Environments (Dev, Test, Staging/UAT, Prod - Factor 1.200x)", description="Development, Test, Staging, and Production")
        ],
        default_value="3 Environments (Dev, Test, Prod - Baseline 1.000x)",
        category="Scale",
        priority="High",
        help_text="3 for Dev, Test, and Prod / UAT (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_components_count",
        title="Architecture Components Count",
        prompt="How many distinct deployable architecture components carry the target solution? (Baseline is 6)",
        type="dropdown",
        options=[
            QuestionOption(value="6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)", label="6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)", description="6 microservices: Landing/Ingestion, Search Index, LLM Engine, Database, Eval Harness, UI Cockpit"),
            QuestionOption(value="4 Components (Lean Pipeline - Factor 0.800x)", label="4 Components (Lean Pipeline - Factor 0.800x)", description="Ingestion, Search, LLM Engine, UI Cockpit"),
            QuestionOption(value="8 Components (Enterprise Scaled Microservices - Factor 1.300x)", label="8 Components (Enterprise Scaled Microservices - Factor 1.300x)", description="Comprehensive enterprise distributed architecture")
        ],
        default_value="6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)",
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
        prompt="Which foundation model reasoning tier will power the AI solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)", label="Azure OpenAI Reasoning Tier (GPT-5 Thinking/Reasoning)", description="Optimized for multi-pass reasoning, synthesis, and deep verification"),
            QuestionOption(value="Azure OpenAI GPT-4o Standard", label="Azure OpenAI GPT-4o Standard", description="General-purpose high-speed multimodal reasoning"),
            QuestionOption(value="Anthropic Claude 3.5 Sonnet", label="Anthropic Claude 3.5 Sonnet", description="Long-context retrieval, coding, and structured extraction engine"),
            QuestionOption(value="Google Gemini 2.5 Pro", label="Google Gemini 2.5 Pro", description="Deep multi-document reasoning and native multimodal comprehension"),
            QuestionOption(value="Open-Source Meta Llama 3.3 (Self-Hosted / vLLM)", label="Open-Source Meta Llama 3.3 (Self-Hosted / vLLM)", description="Private on-premise or cloud-hosted open weights for strict data sovereignty")
        ],
        default_value="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)",
        category="AI & RAG",
        priority="High",
        help_text="Selects the primary foundation model family and reasoning profile for generation and synthesis."
    ),
    QuestionItem(
        id="q_grounding_mode",
        title="Grounding & Surface Mode",
        prompt="What grounding boundary controls model retrieval access?",
        type="dropdown",
        options=[
            QuestionOption(value="Work (Tenant Data Only)", label="Work (Tenant Data Only, Public Web Disabled)", description="Grounding strictly locked to enterprise tenant corpus; zero public web leakage"),
            QuestionOption(value="Hybrid (Tenant Data + Selective Public Web)", label="Hybrid (Tenant Data + Selective Public Web)", description="Enables external regulatory lookup alongside internal documents")
        ],
        default_value="Work (Tenant Data Only)",
        category="AI & RAG",
        priority="High",
        help_text="Locked to 'Work' grounding, preventing external public web retrieval."
    ),
    QuestionItem(
        id="q_doc_processing",
        title="Data Ingestion & Multimodal Processing Pipeline",
        prompt="What data processing or multimodal ingestion technology parses incoming input streams?",
        type="dropdown",
        options=[
            QuestionOption(value="Azure AI Document Intelligence Layout API", label="Document & Layout Intelligence (Layout API)", description="Extracts text, tables, and bounding-box coordinates from PDF/scanned documents"),
            QuestionOption(value="Multi-Turn Conversational & Streaming API Pipeline", label="Conversational & Streaming Text/Audio Intake", description="WebSockets / SSE streaming pipeline for low-latency dialogue and voice interactions"),
            QuestionOption(value="Semantic Chunking & Dense/Hybrid Vector Ingestion", label="Enterprise Knowledge Base & Vector Indexing", description="Document chunking, dense embeddings, and hybrid BM25 index creation"),
            QuestionOption(value="Real-Time Event Stream & Tabular Feature Pipeline", label="Real-Time Event Bus & Feature Store", description="Kafka / Event Hub streams and database CDC for predictive ML & fraud detection"),
            QuestionOption(value="Computer Vision & Multimodal Image Processing", label="Multimodal Vision & Object Detection Engine", description="Image analysis, OCR bounding boxes, and visual defect inspection"),
            QuestionOption(value="Standard OCR Text Extraction", label="Standard OCR Text Extraction", description="Basic flat-text extraction without coordinate bounding boxes")
        ],
        default_value="Azure AI Document Intelligence Layout API",
        category="AI & RAG",
        priority="High",
        help_text="Specifies the ingestion pipeline: Document OCR, Conversational stream, Vector embeddings, or Event stream."
    ),
    QuestionItem(
        id="q_named_users",
        title="Total Named Users",
        prompt="How many total named users are entitled to access the platform?",
        type="dropdown",
        options=[
            QuestionOption(value="200 Named Users (Standard Baseline)", label="200 Named Users (Standard Baseline)", description="200 named legal, procurement, and risk reviewers"),
            QuestionOption(value="50 Named Users (Pilot Cohort)", label="50 Named Users (Pilot Cohort)", description="Initial business team"),
            QuestionOption(value="500 Named Users (Department-Wide)", label="500 Named Users (Department-Wide)", description="Expanded division rollout"),
            QuestionOption(value="1,000 Named Users (Enterprise Scale)", label="1,000 Named Users (Enterprise Scale)", description="Full enterprise legal community")
        ],
        default_value="200 Named Users (Standard Baseline)",
        category="Sizing",
        priority="Medium",
        help_text="200 named legal, procurement, and risk reviewers."
    ),
    QuestionItem(
        id="q_concurrent_users",
        title="Peak Concurrent Users",
        prompt="What is the maximum number of simultaneous users active during peak hours?",
        type="dropdown",
        options=[
            QuestionOption(value="50 Peak Concurrent Users (Standard Baseline)", label="50 Peak Concurrent Users (Standard Baseline)", description="50 simultaneous active sessions during peak hours"),
            QuestionOption(value="20 Peak Concurrent Users (Pilot)", label="20 Peak Concurrent Users (Pilot)", description="Controlled concurrency"),
            QuestionOption(value="100 Peak Concurrent Users (High Concurrency)", label="100 Peak Concurrent Users (High Concurrency)", description="High peak traffic demand"),
            QuestionOption(value="250 Peak Concurrent Users (Enterprise Peak)", label="250 Peak Concurrent Users (Enterprise Peak)", description="High-scale concurrent review workflows")
        ],
        default_value="50 Peak Concurrent Users (Standard Baseline)",
        category="Sizing",
        priority="Medium",
        help_text="50 peak concurrent users driving API concurrency."
    ),
    QuestionItem(
        id="q_daily_requests",
        title="Model Requests per Day",
        prompt="What is the estimated volume of document processing/analysis requests per day?",
        type="dropdown",
        options=[
            QuestionOption(value="2,000 Requests / Day (Peak 3.00 RPS Baseline)", label="2,000 Requests / Day (Peak 3.00 RPS Baseline)", description="2,000 requests per day with peak processing speed of 3.00 RPS"),
            QuestionOption(value="500 Requests / Day (Lean Volume)", label="500 Requests / Day (Lean Volume)", description="Light daily batch traffic"),
            QuestionOption(value="5,000 Requests / Day (High Throughput)", label="5,000 Requests / Day (High Throughput)", description="High daily document turnover"),
            QuestionOption(value="10,000 Requests / Day (Enterprise Processing)", label="10,000 Requests / Day (Enterprise Processing)", description="Continuous heavy document processing")
        ],
        default_value="2,000 Requests / Day (Peak 3.00 RPS Baseline)",
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

# --- Section: 32 Architecture & Business Domains Master Template Registry ---
MASTER_DOMAIN_TEMPLATE: Dict[str, Dict[str, Any]] = {
    "q_client": {
        "title": "Client & Engagement Name",
        "category": "Scope",
        "required_fields": ["client_account_name", "initiative_title"],
        "description": "Enterprise client entity and formal working initiative title"
    },
    "q_tier": {
        "title": "Delivery Tier",
        "category": "Scope",
        "required_fields": ["delivery_tier_name", "headline_weight_code"],
        "description": "Target delivery tier (PoC, Pilot, MVP, Production Grade, etc.)"
    },
    "q_problem": {
        "title": "Problem Statement & Business Challenge",
        "category": "Scope",
        "required_fields": ["pain_points", "target_users", "core_objectives"],
        "description": "Detailed business bottlenecks, affected roles, and intended transformation"
    },
    "q_legal_categories": {
        "title": "In-Scope Business & Legal Categories",
        "category": "Scope",
        "required_fields": ["in_scope_contract_categories", "principle_hierarchy"],
        "description": "Specific contract or document categories in scope (e.g. Lease, Vendor, Service, Facilities, Tech, Marketing)"
    },
    "q_duration": {
        "title": "Reference Duration (Weeks)",
        "category": "Timeline",
        "required_fields": ["calendar_weeks", "working_days"],
        "description": "Target timeline in calendar weeks for schedule calibration"
    },
    "q_start_date": {
        "title": "Project Target Start Date",
        "category": "Timeline",
        "required_fields": ["kickoff_date_iso"],
        "description": "Exact target start date (YYYY-MM-DD) for regional holiday calendar mapping"
    },
    "q_buffer_strategy": {
        "title": "Resource Standby & Backup Strategy",
        "category": "Resourcing",
        "required_fields": ["shadow_engineering_pct", "mitigation_policy"],
        "description": "Standby engineering buffer percentage for sprint resiliency"
    },
    "q_usecases_count": {
        "title": "Distinct Use Cases / Capabilities",
        "category": "Scale",
        "required_fields": ["distinct_capabilities_count"],
        "description": "Number of distinct functional AI capabilities in scope"
    },
    "q_personas_count": {
        "title": "User Personas Count",
        "category": "Scale",
        "required_fields": ["personas_count", "role_titles"],
        "description": "Number and roles of user personas interacting with the solution"
    },
    "q_integrations_count": {
        "title": "System Integrations Count",
        "category": "Scale",
        "required_fields": ["enterprise_integrations_count"],
        "description": "Inbound and outbound enterprise system interfaces"
    },
    "q_datasources_count": {
        "title": "Distinct Data Sources",
        "category": "Scale",
        "required_fields": ["data_sources_count", "repository_types"],
        "description": "Distinct document stores, databases, and APIs ingested"
    },
    "q_channels_count": {
        "title": "Delivery Channels",
        "category": "Scale",
        "required_fields": ["channel_interfaces_count"],
        "description": "User delivery surfaces (Web Cockpit, Teams Bot, REST API, Mobile)"
    },
    "q_languages_count": {
        "title": "Languages Supported",
        "category": "Scale",
        "required_fields": ["supported_languages_count"],
        "description": "Natural languages supported by document intelligence & OCR"
    },
    "q_envs_count": {
        "title": "Deployment Environments",
        "category": "Scale",
        "required_fields": ["cloud_environments_count"],
        "description": "Isolated cloud staging subscriptions (Dev, Test, Prod)"
    },
    "q_components_count": {
        "title": "Architecture Components Count",
        "category": "Scale",
        "required_fields": ["microservices_count", "component_ids"],
        "description": "Microservice decomposition components (C001-C006)"
    },
    "q_complexity": {
        "title": "Technical Complexity Level",
        "category": "Scale",
        "required_fields": ["complexity_rating", "algorithm_depth"],
        "description": "Technical complexity rating (Low, Medium, High, Very High)"
    },
    "q_compliance": {
        "title": "Compliance & Regulatory Posture",
        "category": "Governance",
        "required_fields": ["regulatory_standard", "data_residency"],
        "description": "Statutory audit standard (Internal policy, SOC-2, HIPAA, BFSI)"
    },
    "q_security": {
        "title": "Security Posture & Isolation",
        "category": "Governance",
        "required_fields": ["network_isolation", "key_management"],
        "description": "Network boundary (Standard, Enhanced CMEK/Private Endpoints, Air-Gapped)"
    },
    "q_cloud": {
        "title": "Primary Hyperscaler Platform",
        "category": "Technical",
        "required_fields": ["cloud_hyperscaler_platform"],
        "description": "Sole approved enterprise cloud platform (Microsoft Azure, AWS, GCP)"
    },
    "q_geography": {
        "title": "Deployment Geography & Statutory Holidays",
        "category": "Technical",
        "required_fields": ["region_name", "daily_working_hours"],
        "description": "Deployment region and regional statutory working calendar"
    },
    "q_onprem_footprint": {
        "title": "On-Premises Infrastructure Footprint",
        "category": "Technical",
        "required_fields": ["hybrid_tunnel_required"],
        "description": "Cloud-native vs on-premises hybrid tunnel dependency"
    },
    "q_subscription_isolation": {
        "title": "Subscription & Tenant Isolation",
        "category": "Technical",
        "required_fields": ["subscription_topology"],
        "description": "Dedicated non-production vs shared enterprise subscription"
    },
    "q_hadr_tier": {
        "title": "High Availability & Disaster Recovery (HA/DR)",
        "category": "Technical",
        "required_fields": ["hadr_topology", "redundancy_multiplier"],
        "description": "Availability tier (Single instance, Zone redundant, Region pair)"
    },
    "q_foundation_llm": {
        "title": "Foundation LLM Architecture",
        "category": "AI & RAG",
        "required_fields": ["reasoning_model_tier"],
        "description": "Foundation LLM reasoning tier (GPT-5 Thinking/Reasoning, GPT-4o, Claude 3.5)"
    },
    "q_grounding_mode": {
        "title": "Grounding & Surface Mode",
        "category": "AI & RAG",
        "required_fields": ["retrieval_boundary"],
        "description": "Data grounding boundary (Work tenant data only vs Hybrid)"
    },
    "q_doc_processing": {
        "title": "Document Processing & Layout Complexity",
        "category": "AI & RAG",
        "required_fields": ["ocr_extraction_engine"],
        "description": "Document parsing engine (Azure AI Document Intelligence Layout API)"
    },
    "q_named_users": {
        "title": "Total Named Users",
        "category": "Sizing",
        "required_fields": ["named_seat_count"],
        "description": "Total entitled stakeholder and reviewer accounts"
    },
    "q_concurrent_users": {
        "title": "Peak Concurrent Users",
        "category": "Sizing",
        "required_fields": ["peak_concurrency_count"],
        "description": "Peak simultaneous active users driving API throughput"
    },
    "q_daily_requests": {
        "title": "Model Requests per Day",
        "category": "Sizing",
        "required_fields": ["daily_volume", "peak_rps"],
        "description": "Daily document / prompt processing volume and peak RPS"
    },
    "q_multi_pass_policy": {
        "title": "Multi-Pass Evaluation Logic",
        "category": "Governance",
        "required_fields": ["evaluation_passes_policy"],
        "description": "Multi-pass clause extraction vs flat single-pass evaluation"
    },
    "q_parser_delimiters": {
        "title": "Parser Delimiters & Truncation Thresholds",
        "category": "Governance",
        "required_fields": ["block_delimiters", "cell_char_cap"],
        "description": "Formatting headers, cell character caps, and synonym thresholds"
    },
    "q_approval_gate": {
        "title": "Assumption & Approval Gating",
        "category": "Governance",
        "required_fields": ["governance_gate_protocol"],
        "description": "Strict prerequisite gating before downline schedule execution"
    }
}

DOMAIN_KEYS_ORDER = list(MASTER_DOMAIN_TEMPLATE.keys())

def is_answer_generic(ans_text: str, q: QuestionItem) -> Tuple[bool, str]:
    """
    Evaluates whether an answer provides clear, concrete specification or is vague/generic.
    Returns (is_generic, missing_aspect_description).
    """
    if not ans_text or not str(ans_text).strip():
        return True, q.help_text or f"specific technical parameters for {q.title}"
        
    clean = str(ans_text).strip()
    raw_lower = clean.lower()
    
    # 1. Option match or default value is ALWAYS concrete and confirmed
    if q.options:
        for opt in q.options:
            if raw_lower in [opt.value.lower(), opt.label.lower(), f"{opt.label} — {opt.description}".lower() if opt.description else ""]:
                return False, ""
            if opt.value.lower() in raw_lower or opt.label.lower() in raw_lower:
                return False, ""
                
    if clean == q.default_value or raw_lower == q.default_value.lower():
        return False, ""
        
    # 2. Check for explicit vague phrases (when NOT matching an option)
    explicit_vague = [
        "dont know", "don't know", "not sure", "dunno", "no idea", "not decided",
        "haven't decided", "havent decided", "idk", "none_unknown", "whatever", "random",
        "help me decide", "you decide", "any cloud", "some cloud", "any bot", "some bot",
        "some data", "whatever works", "not clear"
    ]
    if raw_lower in ["na", "none", "unknown", "tbd", "idk", "n/a", "?"] or any(v in raw_lower for v in explicit_vague):
        return True, q.help_text or f"specific technical parameters for {q.title}"
        
    # 3. Numeric validation
    if q.type == "number":
        import re
        nums = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', clean)
        if not nums:
            return True, f"a valid numeric value (e.g., {q.default_value})"
        return False, ""
        
    # 4. Domain-specific checks
    if q.id == "q_problem" and len(clean.split()) < 4 and not any(k in raw_lower for k in ["contract", "intelligence", "support", "invoice", "extraction", "search", "compliance", "procurement", "fraud", "aml", "agent", "assistant", "model", "ai"]):
        return True, "specific business pain points, impacted user roles, and core objectives"
        
    if q.id == "q_legal_categories" and len(clean.split(',')) < 2 and len(clean.split()) < 2:
        return True, "the in-scope functional capabilities or business domains (e.g. Contract Risk, Customer Support, AML, RAG, or Agentic Workflows)"
        
    return False, ""

def evaluate_domain_completeness(session: ProjectSession) -> Dict[str, Any]:
    """
    Evaluates the 32 core architecture & business domains against the Master Domain Template.
    Determines which domains are confirmed, generic/vague, missing, or escalated.
    """
    total_domains = len(STATIC_QUESTIONS)
    confirmed_domains: List[str] = []
    generic_domains: List[Dict[str, Any]] = []
    missing_domains: List[QuestionItem] = []
    escalated_domains: List[str] = []
    
    # Check escalated topics in workflow
    escalated_q_ids = set()
    if hasattr(session, "workflow") and session.workflow:
        for esc in session.workflow.escalated_topics:
            escalated_q_ids.add(esc.question_id)
            if esc.status == "RESOLVED":
                confirmed_domains.append(esc.question_id)
            else:
                escalated_domains.append(esc.question_id)
                
    for q in STATIC_QUESTIONS:
        q_id = q.id
        if q_id in escalated_q_ids:
            continue
            
        if q_id in session.answers and session.answers[q_id].answer:
            ans_text = str(session.answers[q_id].answer).strip()
            is_generic, missing_aspect = is_answer_generic(ans_text, q)
            
            if is_generic:
                generic_domains.append({
                    "question": q,
                    "previous_answer": ans_text,
                    "missing_aspect": missing_aspect
                })
            else:
                confirmed_domains.append(q_id)
        else:
            missing_domains.append(q)
            
    # Calculate completion rate
    total_accounted = len(confirmed_domains) + len(escalated_domains)
    completion_rate = round((total_accounted / total_domains) * 100.0, 1)
    is_gate_passed = completion_rate >= 95.0
    
    # Construct master domain statuses for transparency
    master_statuses = {}
    for q_id, meta in MASTER_DOMAIN_TEMPLATE.items():
        if q_id in confirmed_domains:
            st = "CONFIRMED"
        elif q_id in escalated_domains:
            st = "ESCALATED"
        elif any(g["question"].id == q_id for g in generic_domains):
            st = "GENERIC_NEEDS_CLARIFICATION"
        else:
            st = "MISSING"
        master_statuses[q_id] = {
            "title": meta["title"],
            "category": meta["category"],
            "status": st,
            "current_value": session.answers[q_id].answer if q_id in session.answers else None
        }
    
    return {
        "total_domains": total_domains,
        "confirmed_count": len(confirmed_domains),
        "generic_count": len(generic_domains),
        "missing_count": len(missing_domains),
        "escalated_count": len(escalated_domains),
        "completion_rate": completion_rate,
        "is_gate_passed": is_gate_passed,
        "confirmed_domains": confirmed_domains,
        "generic_domains": generic_domains,
        "missing_domains": missing_domains,
        "escalated_domains": escalated_domains,
        "master_domain_statuses": master_statuses
    }

def get_current_question(session: ProjectSession) -> Optional[QuestionItem]:
    """
    Dynamic Question Generator:
    1. Returns None if >= 95% of the 32 domains are filled and clear.
    2. If any domain is generic/vague, generates a targeted clarification question asking exactly what is missing.
    3. Otherwise, returns the next missing domain in priority order.
    """
    comp = evaluate_domain_completeness(session)
    if comp["is_gate_passed"]:
        return None
        
    # 1. Check for targeted clarifications on generic answers
    if comp["generic_domains"]:
        target = comp["generic_domains"][0]
        base_q = target["question"]
        prev_ans = target["previous_answer"]
        aspect = target["missing_aspect"]
        
        clarification_prompt = (
            f"🔍 **Clarification Needed on {base_q.title}:**\n\n"
            f"You previously provided: *'{prev_ans}'*, which is somewhat generic.\n\n"
            f"To calibrate the engineering estimation and BRD with high precision, could you clarify: **{aspect}**?"
        )
        return QuestionItem(
            id=f"{base_q.id}_clarification",
            title=f"Clarification: {base_q.title}",
            prompt=clarification_prompt,
            type=base_q.type,
            options=base_q.options,
            default_value=base_q.default_value,
            category=base_q.category,
            priority="Blocker",
            help_text=f"Please provide specific details for {base_q.title} or select an exact enterprise option below."
        )
        
    # 2. Pick next highest-priority missing domain
    if comp["missing_domains"]:
        return comp["missing_domains"][0]
        
    return None

def normalize_answer_value(user_input: str, q: QuestionItem) -> str:
    if not user_input or not str(user_input).strip():
        return q.default_value
    text = str(user_input).strip()
    
    if q.type == "number":
        import re
        nums = re.findall(r'[-+]?(?:\d*\.\d+|\d+)', text)
        if nums:
            return nums[0]
        return q.default_value
        
    if q.type == "dropdown" and q.options:
        raw = text.lower()
        for opt in q.options:
            full_opt_text = f"{opt.label} — {opt.description}" if opt.description else opt.label
            if raw == opt.value.lower() or raw == opt.label.lower() or raw == full_opt_text.lower():
                return full_opt_text
        for opt in q.options:
            full_opt_text = f"{opt.label} — {opt.description}" if opt.description else opt.label
            if opt.value.lower() in raw or raw in opt.value.lower() or opt.label.lower() in raw or raw in opt.label.lower():
                return text if len(text) > len(opt.value) else full_opt_text
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
    "random", "whatever", "any bot", "just chatbot", "some chatbot", "a chatbot",
    "standard", "default", "standard cloud", "some data", "whatever works"
]

ARCHITECT_ADVICE_MAP: Dict[str, Dict[str, Any]] = {
    "q_cloud": {
        "value": "Microsoft Azure",
        "label": "Microsoft Azure (Sole Approved Enterprise Platform)",
        "quote": "As Solutions Architect, I recommend **Microsoft Azure**. Azure AI Document Intelligence provides specialized layout-aware coordinate OCR for multi-page legal and financial documents, and Azure OpenAI Service allows zero-data-retention private endpoints inside your enterprise VNet."
    },
    "q_foundation_llm": {
        "value": "Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)",
        "label": "Azure OpenAI Reasoning Tier (GPT-5 Thinking/Reasoning)",
        "quote": "For analyzing nuanced, open-textured legal clauses and multi-pass principle evaluations, we should select an advanced reasoning tier like **Azure OpenAI GPT-5 Thinking / GPT-4o** with structured JSON output enforcement."
    },
    "q_doc_processing": {
        "value": "Azure AI Document Intelligence Layout API",
        "label": "Azure AI Document Intelligence (Layout-Aware API)",
        "quote": "We should mandate **Azure AI Document Intelligence Layout API**. Standard OCR drops table boundaries and bounding box coordinates; the Layout API preserves full pixel coordinate provenance for 100% auditability."
    },
    "q_security": {
        "value": "Enhanced",
        "label": "Enhanced (Private Endpoints, CMEK & RBAC)",
        "quote": "I advise configuring **Enhanced Security** — deploying all Azure Cognitive Services behind Private Endpoints with Customer-Managed Keys (CMEK), Managed Identities, and strict RBAC."
    },
    "q_compliance": {
        "value": "Regulated - moderate",
        "label": "Regulated - Moderate (SOC-2 / ISO-27001)",
        "quote": "Given that enterprise contract documents contain commercially sensitive clauses and vendor data, we should enforce **Regulated - Moderate** controls with automated audit logging."
    },
    "q_hadr_tier": {
        "value": "Zone redundant",
        "label": "Zone Redundant (Multi-AZ in Primary Region)",
        "quote": "For high enterprise availability without doubling baseline compute costs, **Zone Redundant (Multi-AZ)** within the primary geography offers 99.99% availability."
    },
    "q_multi_pass_policy": {
        "value": "Two-Pass Evaluation (Agree / Agree with Mgmt Approval / Not Agree)",
        "label": "Two-Pass Evaluation (3-Tier Risk Hierarchy)",
        "quote": "I strongly recommend **Two-Pass Agentic Extraction**: Pass 1 isolates exact candidate clauses; Pass 2 evaluates them against the category principles with deterministic bounding box citations."
    },
    "q_complexity": {
        "value": "Medium",
        "label": "Medium (1.000 Baseline Multiplier)",
        "quote": "The solution entails multi-modal document extraction, hybrid vector search indexing, and structured evaluation. Graded as **Medium Complexity**."
    },
    "q_components_count": {
        "value": "6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)",
        "label": "6 Deployable Components",
        "quote": "Architecture is structured into 6 core microservices: Ingestion Pipeline, Search Index, LLM Reasoning Engine, Metadata DB, Eval Harness, and Web Cockpit."
    },
    "q_buffer_strategy": {
        "value": "15% Shadow / Backup Capacity (Recommended)",
        "label": "15% Shadow / Backup Capacity",
        "quote": "To absorb attrition risk and critical role single-point-of-failure across 12 disciplines, a 15% shadow engineering capacity ensures zero timeline slippage."
    },
    "q_subscription_isolation": {
        "value": "Dedicated Non-Production Subscription",
        "label": "Dedicated Non-Production Subscription",
        "quote": "A dedicated non-prod subscription ensures network-level boundary isolation from existing corporate workloads during evaluation and testing."
    },
    "q_onprem_footprint": {
        "value": "No (Zero On-Premises Footprint)",
        "label": "No (Zero On-Premises Footprint, 100% Cloud Native)",
        "quote": "A 100% cloud-native architecture avoids ExpressRoute/VPN provisioning lead times and keeps the initial deployment rapid."
    }
}

def get_architect_technical_advice(question_id: str, question_title: str = "") -> Dict[str, Any]:
    clean_id = question_id.replace("_clarification", "")
    if clean_id in ARCHITECT_ADVICE_MAP:
        return ARCHITECT_ADVICE_MAP[clean_id]
    return {
        "value": "Standard Enterprise Baseline",
        "label": "Standard Enterprise Baseline",
        "quote": f"As Solutions Architect, I recommend adopting the standard enterprise architectural baseline for **{question_title or clean_id}** to ensure stability and maintainability."
    }

def extract_and_fill_domains_from_text(session: ProjectSession, text: str) -> List[str]:
    """
    Multi-field extraction: Scans the user's input across all 32 architecture & business domains
    and extracts all matching parameters in a single conversational turn.
    """
    filled_keys = []
    raw = text.lower()
    
    # 1. Cloud Hyperscaler
    if "azure" in raw or "microsoft" in raw:
        session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Microsoft Azure")
        filled_keys.append("q_cloud")
    elif "aws" in raw or "amazon" in raw or "bedrock" in raw:
        session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Amazon Web Services")
        filled_keys.append("q_cloud")
    elif "gcp" in raw or "google" in raw or "vertex" in raw:
        session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Google Cloud Platform")
        filled_keys.append("q_cloud")
        
    # 2. Delivery Tier
    if "poc" in raw or "proof of concept" in raw:
        session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Tier", answer="PoC")
        filled_keys.append("q_tier")
    elif "pilot" in raw:
        session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Tier", answer="Pilot")
        filled_keys.append("q_tier")
    elif "mvp" in raw or "minimum viable" in raw:
        session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Tier", answer="MVP")
        filled_keys.append("q_tier")
    elif "production" in raw or "prod grade" in raw:
        session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Tier", answer="Production Grade")
        filled_keys.append("q_tier")
        
    # 3. Timeline / Duration Weeks
    dur_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:weeks?|wks?)', raw)
    if dur_match:
        dur_val = f"{float(dur_match[0]):.1f}"
        session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer=dur_val)
        filled_keys.append("q_duration")
        
    # 4. Corpus Volume & Daily Requests
    doc_match = re.findall(r'(\d[\d,]*)\s*(?:docs?|documents?|contracts?|files?)', raw)
    if doc_match:
        doc_count = doc_match[0].replace(',', '')
        session.answers["q_corpus_docs"] = AnswerItem(question_id="q_corpus_docs", question_title="Corpus Volume", answer=doc_count)
        filled_keys.append("q_corpus_docs")
        
    req_match = re.findall(r'(\d[\d,]*)\s*(?:queries|requests|reqs|evals?)\s*(?:per\s*day|/day|daily)', raw)
    if req_match:
        req_count = req_match[0].replace(',', '')
        session.answers["q_reqs_per_day"] = AnswerItem(question_id="q_reqs_per_day", question_title="Daily Queries", answer=req_count)
        filled_keys.append("q_reqs_per_day")
        
    # 5. Capabilities & Functional Domains
    if any(k in raw for k in ["customer", "support", "ticket", "helpdesk", "deflection", "chatbot"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Customer Support, IT Helpdesk, Knowledge Retrieval, Automated Triage"
        )
        filled_keys.append("q_legal_categories")
    elif any(k in raw for k in ["fraud", "aml", "anti-money", "kyc", "fintech"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Transaction Monitoring, Fraud Detection, KYC Verification, AML Alerts"
        )
        filled_keys.append("q_legal_categories")
    elif any(k in raw for k in ["clinical", "medical", "patient", "doctor", "health", "ehr"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Clinical Documentation, EHR Summarization, ICD/CPT Coding, Lab Triage"
        )
        filled_keys.append("q_legal_categories")
    elif any(k in raw for k in ["agent", "agentic", "tool", "workflow", "autonomous", "rpa"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Multi-Agent Task Routing, Autonomous Tool Calling, Code Synthesis, RPA"
        )
        filled_keys.append("q_legal_categories")
    elif any(k in raw for k in ["rag", "search", "knowledge", "wiki", "retrieval"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Enterprise Knowledge Base, Semantic Search, Policy Q&A, Research Synthesis"
        )
        filled_keys.append("q_legal_categories")
    elif any(k in raw for k in ["lease", "vendor", "facilities", "marketing", "6 categories", "six categories", "contract"]):
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Functional Domains & Capabilities",
            answer="Lease, Vendor, Service, Facilities, Technology, Marketing"
        )
        filled_keys.append("q_legal_categories")

    # 6. Standby Buffer Strategy
    if "15%" in raw or "standby" in raw or "shadow" in raw:
        session.answers["q_buffer_strategy"] = AnswerItem(
            question_id="q_buffer_strategy",
            question_title="Resource Standby & Backup Strategy",
            answer="15% Shadow / Backup Capacity (Recommended)"
        )
        filled_keys.append("q_buffer_strategy")

    # 7. Geography / Working Calendar
    if "india" in raw or "9.0 hrs" in raw or "9 hrs" in raw:
        session.answers["q_geography"] = AnswerItem(
            question_id="q_geography",
            question_title="Deployment Geography & Statutory Holidays",
            answer="India"
        )
        filled_keys.append("q_geography")
    elif "united states" in raw or "usa" in raw.split() or "us" in raw.split():
        session.answers["q_geography"] = AnswerItem(
            question_id="q_geography",
            question_title="Deployment Geography & Statutory Holidays",
            answer="United States"
        )
        filled_keys.append("q_geography")

    # 8. Start Date
    date_match = re.findall(r'(202\d-\d{2}-\d{2})', raw)
    if date_match:
        session.answers["q_start_date"] = AnswerItem(
            question_id="q_start_date",
            question_title="Project Target Start Date",
            answer=date_match[0]
        )
        filled_keys.append("q_start_date")

    # 9. Architecture Components
    if "6 components" in raw or "c001" in raw or "landing, search" in raw:
        session.answers["q_components_count"] = AnswerItem(
            question_id="q_components_count",
            question_title="Architecture Components Count",
            answer="6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)"
        )
        filled_keys.append("q_components_count")

    # 10. Foundation LLM
    if any(k in raw for k in ["claude", "anthropic", "sonnet"]):
        session.answers["q_foundation_llm"] = AnswerItem(
            question_id="q_foundation_llm",
            question_title="Foundation LLM Architecture",
            answer="Anthropic Claude 3.5 Sonnet"
        )
        filled_keys.append("q_foundation_llm")
    elif any(k in raw for k in ["gemini", "vertex"]):
        session.answers["q_foundation_llm"] = AnswerItem(
            question_id="q_foundation_llm",
            question_title="Foundation LLM Architecture",
            answer="Google Gemini 2.5 Pro"
        )
        filled_keys.append("q_foundation_llm")
    elif any(k in raw for k in ["llama", "vllm", "open source"]):
        session.answers["q_foundation_llm"] = AnswerItem(
            question_id="q_foundation_llm",
            question_title="Foundation LLM Architecture",
            answer="Open-Source Meta Llama 3.3 (Self-Hosted / vLLM)"
        )
        filled_keys.append("q_foundation_llm")
    elif "gpt-5" in raw or "reasoning" in raw or "thinking" in raw or "openai" in raw:
        session.answers["q_foundation_llm"] = AnswerItem(
            question_id="q_foundation_llm",
            question_title="Foundation LLM Architecture",
            answer="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)"
        )
        filled_keys.append("q_foundation_llm")

    # 11. Ingestion & Processing Pipeline
    if any(k in raw for k in ["stream", "chat", "voice", "audio", "websocket", "sse"]):
        session.answers["q_doc_processing"] = AnswerItem(
            question_id="q_doc_processing",
            question_title="Data Ingestion & Multimodal Processing Pipeline",
            answer="Multi-Turn Conversational & Streaming API Pipeline"
        )
        filled_keys.append("q_doc_processing")
    elif any(k in raw for k in ["vector", "embedding", "chunk", "rag", "retrieval"]):
        session.answers["q_doc_processing"] = AnswerItem(
            question_id="q_doc_processing",
            question_title="Data Ingestion & Multimodal Processing Pipeline",
            answer="Semantic Chunking & Dense/Hybrid Vector Ingestion"
        )
        filled_keys.append("q_doc_processing")
    elif any(k in raw for k in ["kafka", "event", "cdc", "feature", "tabular"]):
        session.answers["q_doc_processing"] = AnswerItem(
            question_id="q_doc_processing",
            question_title="Data Ingestion & Multimodal Processing Pipeline",
            answer="Real-Time Event Stream & Tabular Feature Pipeline"
        )
        filled_keys.append("q_doc_processing")
    elif any(k in raw for k in ["vision", "image", "camera", "video", "multimodal"]):
        session.answers["q_doc_processing"] = AnswerItem(
            question_id="q_doc_processing",
            question_title="Data Ingestion & Multimodal Processing Pipeline",
            answer="Computer Vision & Multimodal Image Processing"
        )
        filled_keys.append("q_doc_processing")
    elif "layout" in raw or "ocr" in raw or "document intelligence" in raw:
        session.answers["q_doc_processing"] = AnswerItem(
            question_id="q_doc_processing",
            question_title="Data Ingestion & Multimodal Processing Pipeline",
            answer="Azure AI Document Intelligence Layout API"
        )
        filled_keys.append("q_doc_processing")

    # 12. Client & Project Title
    if "pvr" in raw or "inox" in raw or "contract intelligence" in raw:
        session.answers["q_client"] = AnswerItem(
            question_id="q_client",
            question_title="Client & Engagement Name",
            answer="PVR INOX | Contract Intelligence & Risk Visibility Platform"
        )
        filled_keys.append("q_client")
        
    return filled_keys

def calculate_discovery_confidence(session: ProjectSession) -> DiscoveryConfidence:
    comp = evaluate_domain_completeness(session)
    total_score = comp["completion_rate"]
    
    # Check if confidence threshold is reached
    is_ready = comp["is_gate_passed"] or total_score >= 95.0
    if is_ready:
        total_score = max(total_score, 98.0)
        
    dims_config = [
        {"name": "Business Scope & Boundaries", "category": "Scope", "weight": 20.0, "keys": ["q_client", "q_problem", "q_tier", "q_legal_categories"]},
        {"name": "Timeline & Engineering Capacity", "category": "Timeline", "weight": 15.0, "keys": ["q_duration", "q_start_date", "q_buffer_strategy"]},
        {"name": "Scale Drivers & Sizing Multipliers", "category": "Scale", "weight": 25.0, "keys": ["q_usecases_count", "q_personas_count", "q_integrations_count", "q_datasources_count", "q_channels_count", "q_languages_count", "q_envs_count", "q_components_count"]},
        {"name": "Cloud Infra & Sizing BoM", "category": "Technical", "weight": 20.0, "keys": ["q_complexity", "q_rag_pattern", "q_cloud", "q_corpus_docs", "q_reqs_per_day", "q_named_users"]},
        {"name": "Commercial, Security & AI Governance", "category": "Governance", "weight": 20.0, "keys": ["q_geography", "q_blended_rate", "q_compliance", "q_accuracy_sla", "q_security_level", "q_eval_harness", "q_sla_uptime", "q_l2_support", "q_governance_framework", "q_dr_strategy", "q_cost_model"]}
    ]
    
    dim_scores = []
    missing_items = [q.title for q in comp["missing_domains"]]
    
    for d in dims_config:
        keys = d["keys"]
        answered_cnt = sum(1 for k in keys if k in session.answers and session.answers[k].answer)
        ratio = answered_cnt / len(keys) if keys else 1.0
        earned = round(ratio * d["weight"], 1)
        status = "GROUNDED" if ratio >= 0.9 else ("PARTIAL" if ratio > 0 else "MISSING")
        
        captured_vals = [f"{k}: {session.answers[k].answer[:18]}..." for k in keys if k in session.answers and session.answers[k].answer]
        dim_scores.append(DimensionScore(
            name=d["name"],
            category=d["category"],
            weight=d["weight"],
            score=earned,
            status=status,
            captured_value=", ".join(captured_vals) if captured_vals else "Pending discovery",
            impact="High"
        ))
        
    recommendation = (
        f"🎯 95%+ Domain Gate Passed ({total_score}%)! All 32 architectural & business domains confirmed across Client and Architect. Ready for Dual Sign-off."
        if is_ready else
        f"Discovery in progress: {comp['confirmed_count'] + comp['escalated_count']} of 32 domains completed ({total_score}%). {comp['missing_count']} domains remaining."
    )
    
    next_q = get_current_question(session)
    
    conf = DiscoveryConfidence(
        score=total_score,
        is_ready_for_brd=is_ready,
        threshold=95.0,
        dimensions=dim_scores,
        missing_items=missing_items,
        recommendation=recommendation,
        next_question=next_q,
        summary_dossier={
            "confirmed_domains_count": comp["confirmed_count"],
            "escalated_domains_count": comp["escalated_count"],
            "total_domains": comp["total_domains"],
            "completion_rate": total_score,
            "clarification_needed_count": comp["generic_count"],
            "is_gate_passed": is_ready
        }
    )
    session.confidence = conf
    if hasattr(session, "workflow") and session.workflow:
        session.workflow.confidence_score = total_score
        session.workflow.is_confidence_reached = is_ready
    return conf

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

    # 1. If user answer matches one of the defined options (e.g. 'None', 'N/A', 'Not Applicable'), it is fully confirmed!
    if q.options:
        for opt in q.options:
            val_lower = str(opt.value).strip().lower()
            lbl_lower = str(opt.label).strip().lower()
            if text == val_lower or text == lbl_lower or text in val_lower or val_lower in text:
                return False, "", []
    if q.default_value and text == str(q.default_value).strip().lower():
        return False, "", []

    # 2. Allow explicit N/A or None for questions where absence of component is valid
    if text in ["na", "n/a", "none", "not applicable", "zero", "0"]:
        if any(keyword in q.id for keyword in ["grounding", "rag", "integration", "onprem", "hadr", "compliance", "security", "buffer"]):
            return False, "", []

    if q.type == "number":
        if text.replace('.', '', 1).isdigit():
            return False, "", []
        return True, f"Please enter a valid numeric value for **{q.title}**.", [q.default_value]
        
    if len(text) < 2 or text in ["unknown", "none_unknown", "idk", "not sure", "dunno", "maybe", "whatever", "later"] or text in GREETING_WORDS:
        return True, f"Your answer '{answer_text}' is too brief or ambiguous for **{q.title}**.", [q.default_value]
    return False, "", []

def process_user_answer(session: ProjectSession, user_input: str, persona: str = "CLIENT") -> Tuple[ChatMessage, bool]:
    q = get_current_question(session)
    raw_lower = user_input.strip().lower()
    
    # 0. Multi-Field Extraction: Auto-extract any mentioned parameters across all 32 domains
    extract_and_fill_domains_from_text(session, user_input)
    
    # 1. Check if user is asking the Solutions Architect or delegating
    is_architect_delegation = any(k in raw_lower for k in [
        "ask architect", "ask the architect", "architect decide", "architect recommendation",
        "let architect answer", "technical architect", "delegate", "not sure ask tech", "architect should answer"
    ])
    
    if is_architect_delegation and q:
        clean_id = q.id.replace("_clarification", "")
        # Construct rich context for Solutions Architect
        advice = get_architect_technical_advice(clean_id, q.title)
        adv_val = advice["value"]
        adv_quote = advice["quote"]
        
        # Build client context summary
        client_name = session.answers.get("q_client", AnswerItem(question_id="q_client", question_title="Client", answer="Contract Intelligence Platform")).answer
        tier_name = session.answers.get("q_tier", AnswerItem(question_id="q_tier", question_title="Tier", answer="PoC")).answer
        duration_name = session.answers.get("q_duration", AnswerItem(question_id="q_duration", question_title="Duration", answer="6.0 Weeks")).answer
        client_context = f"Client Lead | Project: {client_name} | Tier: {tier_name} | Timeline: {duration_name}"
        
        why_needed = q.help_text or q.why_it_matters or f"Needed to calibrate technical architecture, sizing BoM, and engineering person-days for {q.title}."
        
        # Create or update escalation queue item
        esc_id = f"ESC-{len(session.workflow.escalated_topics) + 1:03d}" if hasattr(session, "workflow") and session.workflow else f"ESC-{clean_id}"
        esc_options = [{"value": opt.value, "label": opt.label, "desc": opt.description or ""} for opt in (q.options or [])]
        
        esc_item = EscalatedTopicItem(
            id=esc_id,
            question_id=clean_id,
            topic_title=q.title,
            question_text=q.prompt,
            why_needed=why_needed,
            client_context=client_context,
            category=q.category or "Technical Architecture",
            options=esc_options,
            default_recommendation=adv_val,
            status="PENDING_ARCHITECT",
            architect_answer=adv_val,
            architect_notes=adv_quote,
            escalated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if hasattr(session, "workflow") and session.workflow:
            session.workflow.escalated_topics = [e for e in session.workflow.escalated_topics if e.question_id != clean_id]
            session.workflow.escalated_topics.append(esc_item)
            
        # Save provisional recommendation by architect
        session.answers[clean_id] = AnswerItem(
            question_id=clean_id,
            question_title=q.title,
            answer=adv_val,
            is_default=False,
            ambiguity_count=0,
            hitl_confirmed=True,
            notes=f"Escalated to Solutions Architect — {why_needed}"
        )
        
        comp = evaluate_domain_completeness(session)
        conf = calculate_discovery_confidence(session)
        next_q = get_current_question(session)
        
        arch_msg_content = (
            f"🏗️ **Principal Solutions Architect — Escalation Briefing:**\n\n"
            f"📌 **Topic:** `{q.title}` *(Ref: {esc_id})*\n"
            f"🔍 **Why This Is Needed:** {why_needed}\n"
            f"💡 **Context Provided:** {client_context}\n\n"
            f"> \"{adv_quote}\"\n\n"
            f"**Recommended Decision:** `{adv_val}` *(Queued in Architect Workspace on Port :8082)*"
        )
        session.messages.append(ChatMessage(
            sender="architect",
            persona="SOLUTIONS_ARCHITECT",
            persona_badge="🏗️ Solutions Architect",
            is_architect_input=True,
            content=arch_msg_content,
            timestamp=datetime.now().strftime("%I:%M %p")
        ))
        
        if comp["is_gate_passed"] or not next_q:
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=f"🎯 **Discovery Complete with {conf.score}% Confidence!** All 32 architectural & business domains confirmed across Client and Architect. Synthesizing full BRD for Dual-Review...",
                timestamp=datetime.now().strftime("%I:%M %p")
            )
            return msg, True
        else:
            domain_idx = comp["confirmed_count"] + comp["escalated_count"] + 1
            if next_q.id.endswith("_clarification"):
                header = f"### 🔍 Targeted Clarification: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
            else:
                header = f"### 📋 Domain {domain_idx} of 32: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
                
            content = (
                f"✅ **Escalated '{q.title}' to Solutions Architect with technical context.**\n"
                f"*Continuing client discovery interview...*\n\n"
                f"---\n\n"
                f"{header}\n\n"
                f"**{next_q.prompt}**\n\n"
                f"*(Example: {next_q.help_text})*"
            )
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=content,
                timestamp=datetime.now().strftime("%I:%M %p"),
                question_context=next_q
            )
            return msg, False

    if not q:
        # Discovery is completed - handle adjustments or reviews
        if any(w in raw_lower for w in ["not satisfied", "unsatisfied", "dislike", "change", "modify", "adjust", "update", "reduce", "increase", "wrong", "different"]):
            response_text = (
                "🤝 **I understand! Let's tailor the project plan to your exact satisfaction.**\n\n"
                "You can tell me what you would like to adjust, such as:\n"
                "• **Timeline / Sprints:** *'Change duration to 8 weeks'* or *'Reduce duration to 4 weeks'*\n"
                "• **Delivery Tier:** *'Switch tier to MVP'* or *'Make it Pilot'* or *'Production Grade'*\n"
                "• **Cloud Platform:** *'Switch to Google Cloud Platform'*, *'Switch to AWS'*, or *'Switch to Azure'*\n"
                "• **Scale & Concurrency:** *'Set 500 named users and 5 integrations'* or *'Complexity high'*\n"
                "• **Commercial Rate:** *'Change rate to $35/hr'*\n\n"
                "💡 *You can also use the **'Dual Review'** or **'PM Review'** modules to submit structured feedback.*"
            )
            
            modified = False
            if "aws" in raw_lower or "amazon" in raw_lower:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Amazon Web Services")
                modified = True
            elif "gcp" in raw_lower or "google" in raw_lower:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Google Cloud Platform")
                modified = True
            elif "azure" in raw_lower or "microsoft" in raw_lower:
                session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Microsoft Azure")
                modified = True
                
            nums = re.findall(r'(\d+(?:\.\d+)?)\s*(?:weeks?|wks?)', raw_lower)
            if nums:
                session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer=f"{nums[0]}")
                modified = True
                
            if "mvp" in raw_lower:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="MVP")
                modified = True
            elif "pilot" in raw_lower:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Pilot")
                modified = True
            elif "production" in raw_lower:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="Production Grade")
                modified = True
            elif "poc" in raw_lower:
                session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="PoC")
                modified = True
                
            if modified:
                response_text = f"🔄 **Updated Plan with your adjustments!** Re-synthesized BRD workbench with: `{user_input}`."
                
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=response_text,
                timestamp="Just now"
            )
            return msg, True
            
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=f"💬 **Noted:** *\"{user_input}\"*. You can inspect all details across the review panes or propose specific revisions.",
            timestamp="Just now"
        )
        return msg, True

    clean_target_id = q.id.replace("_clarification", "")

    # Check greetings
    if is_greeting_or_chit_chat(user_input):
        comp = evaluate_domain_completeness(session)
        domain_idx = comp["confirmed_count"] + comp["escalated_count"] + 1
        if q.id.endswith("_clarification"):
            header = f"### 🔍 Targeted Clarification: **{q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
        else:
            header = f"### 📋 Domain {domain_idx} of 32: **{q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
            
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=(
                f"👋 **Hello! Great to connect with you.**\n\n"
                f"I am here to capture your project requirements across the 32 architecture domains and synthesize a complete Business Requirements Document (BRD).\n\n"
                f"---\n\n"
                f"{header}\n\n"
                f"**{q.prompt}**\n\n"
                f"*(Example: {q.help_text})*"
            ),
            timestamp="Just now",
            question_context=q
        )
        return msg, False

    # Handle active clarification state
    if session.clarification_state and session.clarification_state.get("question_id") in [q.id, clean_target_id]:
        initial_input = session.clarification_state.get("initial_input", "")
        clarification_answer = user_input.strip()
        
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
                short_tokens = [w for w in clarification_answer.lower().split() if w.strip()]
                is_generic_audience = any(clarification_answer.lower() == g for g in [
                    "regular customers", "customers", "users", "clients", "employees", "everyone", "people", 
                    "internal", "external", "all", "consumer", "consumers", "end users", "public"
                ])
                is_too_brief = len(short_tokens) < 4
                
                # If user input is underspecified (e.g. only named the user group 'regular customers' without functionality or systems)
                if (is_generic_audience or is_too_brief) and "option" not in clarification_answer.lower():
                    session.clarification_state["target_audience"] = clarification_answer
                    session.clarification_state["step"] = session.clarification_state.get("step", 1) + 1
                    
                    prompt_audience = clarification_answer
                    clarification_content = (
                        f"Got it — target users are **{prompt_audience}**.\n\n"
                        f"To define the exact requirement without making assumptions or hallucinating details:\n\n"
                        f"1️⃣ **What primary task, pain point, or service should the AI handle for {prompt_audience}?** *(e.g., answering support questions, checking order status, account self-service)*\n"
                        f"2️⃣ **What channels or systems will they use?** *(e.g., Web chat widget, Mobile App, WhatsApp, CRM)*\n\n"
                        f"*(Please describe your exact use case or select one of the tailored options below:)*"
                    )
                    
                    tailored_options = [
                        QuestionOption(
                            value=f"24/7 conversational support agent for {prompt_audience} to answer product questions, handle FAQs, and route escalations to support staff.",
                            label=f"Customer Support & Inquiries for {prompt_audience.title()}",
                            description=f"Automated 24/7 support resolving common queries and routing escalations"
                        ),
                        QuestionOption(
                            value=f"Self-service assistant enabling {prompt_audience} to check order status, update account details, and process service requests.",
                            label=f"Self-Service Account & Order Management for {prompt_audience.title()}",
                            description=f"Direct self-service for accounts, orders, and standard requests"
                        ),
                        QuestionOption(
                            value=f"Intelligent conversational guide assisting {prompt_audience} with personalized product recommendations and purchasing guidance.",
                            label=f"Product Guidance & Recommendation for {prompt_audience.title()}",
                            description=f"Conversational advisory assisting with discovery and purchasing"
                        )
                    ]
                    
                    msg = ChatMessage(
                        sender="agent",
                        persona="AI_AGENT",
                        content=clarification_content,
                        timestamp=datetime.now().strftime("%I:%M %p"),
                        question_context=QuestionItem(
                            id=f"{clean_target_id}_clarification",
                            title=f"Clarification: {q.title}",
                            prompt=clarification_content,
                            type="dropdown",
                            options=tailored_options,
                            default_value=tailored_options[0].value,
                            category=q.category,
                            priority=q.priority,
                            help_text="Select a blueprint or provide your exact functional requirements."
                        ),
                        hitl_options=[{"label": opt.label, "value": opt.value} for opt in tailored_options]
                    )
                    return msg, False
                else:
                    target_audience = session.clarification_state.get("target_audience")
                    if target_audience and target_audience.lower() not in clarification_answer.lower():
                        final_synthesized_requirement = f"AI Solution for {target_audience}: {clarification_answer}"
                    else:
                        final_synthesized_requirement = clarification_answer

        session.clarification_state = None
        session.answers[clean_target_id] = AnswerItem(
            question_id=clean_target_id,
            question_title=q.title.replace("Clarification: ", ""),
            answer=final_synthesized_requirement,
            is_default=False,
            ambiguity_count=0,
            hitl_confirmed=True,
            notes=f"Synthesized from user input '{initial_input}' and clarification '{clarification_answer}'."
        )
        comp = evaluate_domain_completeness(session)
        conf = calculate_discovery_confidence(session)
        next_q = get_current_question(session)
        
        if comp["is_gate_passed"] or not next_q:
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=f"🎯 **Discovery Complete with {conf.score}% Confidence!** All 32 architectural & business domains confirmed across Client and Architect. Synthesizing full BRD for Dual-Review...",
                timestamp=datetime.now().strftime("%I:%M %p")
            )
            return msg, True
        else:
            domain_idx = comp["confirmed_count"] + comp["escalated_count"] + 1
            if next_q.id.endswith("_clarification"):
                header = f"### 🔍 Targeted Clarification: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
            else:
                header = f"### 📋 Domain {domain_idx} of 32: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
                
            content = (
                f"✅ **Recorded for {q.title}:**\n> *\"{final_synthesized_requirement}\"*\n\n"
                f"---\n\n"
                f"{header}\n\n"
                f"**{next_q.prompt}**\n\n"
                f"*(Example: {next_q.help_text})*"
            )
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=content,
                timestamp=datetime.now().strftime("%I:%M %p"),
                question_context=next_q
            )
            return msg, False

    # Check if this initial answer needs follow-up clarification
    needs_follow_up, follow_up_prompt, follow_up_options = check_requires_follow_up(user_input, q)
    if needs_follow_up:
        session.clarification_state = {
            "question_id": clean_target_id,
            "initial_input": user_input,
            "step": 1
        }
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=follow_up_prompt,
            timestamp="Just now",
            question_context=q,
            hitl_options=follow_up_options
        )
        return msg, False

    is_option_match = False
    if q.options:
        for opt in q.options:
            if user_input.strip().lower() in [str(opt.value).strip().lower(), str(opt.label).strip().lower()]:
                is_option_match = True
                break
    if user_input.strip().lower() == str(q.default_value).strip().lower():
        is_option_match = True

    ai_clarify = None
    if not is_option_match:
        ai_clarify = LLMGateway.clarify_user_input(
            question_title=q.title,
            question_prompt=q.prompt,
            user_input=user_input,
            current_answer=q.default_value,
            category=q.category
        )
        if ai_clarify and ai_clarify.get("clarification_needed") and ai_clarify.get("follow_up_prompt"):
            opts = ai_clarify.get("suggested_options") or []
            session.clarification_state = {
                "question_id": clean_target_id,
                "initial_input": user_input,
                "step": 1
            }
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=f"🤖 **Requirements Clarification:**\n\n{ai_clarify['follow_up_prompt']}",
                timestamp="Just now",
                question_context=q,
                hitl_options=opts
            )
            return msg, False

    normalized_input = normalize_answer_value(user_input, q)
    if ai_clarify and ai_clarify.get("normalized_value") and len(ai_clarify["normalized_value"]) > 3:
        normalized_input = ai_clarify["normalized_value"]

    is_ambiguous, reason, suggestions = check_answer_ambiguity(normalized_input, q)
    current_strikes = session.ambiguity_tracker.get(clean_target_id, 0)

    if is_ambiguous:
        current_strikes += 1
        session.ambiguity_tracker[clean_target_id] = current_strikes

        if current_strikes >= 2:
            session.answers[clean_target_id] = AnswerItem(
                question_id=clean_target_id,
                question_title=q.title.replace("Clarification: ", ""),
                answer=q.default_value,
                is_default=True,
                ambiguity_count=current_strikes,
                hitl_confirmed=True,
                notes="Adopted default value after ambiguity fallback."
            )
            comp = evaluate_domain_completeness(session)
            conf = calculate_discovery_confidence(session)
            next_q = get_current_question(session)
            
            if comp["is_gate_passed"] or not next_q:
                msg = ChatMessage(
                    sender="agent",
                    persona="AI_AGENT",
                    content=f"🎯 **Discovery Complete with {conf.score}% Confidence!** All 32 architectural & business domains confirmed across Client and Architect. Synthesizing full BRD for Dual-Review...",
                    timestamp="Just now"
                )
                return msg, True
            else:
                domain_idx = comp["confirmed_count"] + comp["escalated_count"] + 1
                if next_q.id.endswith("_clarification"):
                    header = f"### 🔍 Targeted Clarification: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
                else:
                    header = f"### 📋 Domain {domain_idx} of 32: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
                    
                content = (
                    f"⚠️ *Ambiguity detected.* I have recorded standard enterprise default: **\"{q.default_value}\"**.\n\n"
                    f"---\n\n"
                    f"{header}\n\n"
                    f"**{next_q.prompt}**\n\n"
                    f"*(Example: {next_q.help_text})*"
                )
                msg = ChatMessage(
                    sender="agent",
                    persona="AI_AGENT",
                    content=content,
                    timestamp="Just now",
                    question_context=next_q,
                    is_hitl_confirmation=True,
                    hitl_default_value=q.default_value
                )
                return msg, False
        else:
            content = (
                f"⚠️ **Clarification needed for {q.title}**:\n"
                f"{reason}\n\n"
                f"Please provide specific details, pick from recommended baseline: **{q.default_value}**, or type **'ask architect'** for technical guidance."
            )
            msg = ChatMessage(
                sender="agent",
                persona="AI_AGENT",
                content=content,
                timestamp="Just now",
                question_context=q,
                is_ambiguity_warning=True,
                ambiguity_strike=current_strikes
            )
            return msg, False

    # Valid answer received
    session.answers[clean_target_id] = AnswerItem(
        question_id=clean_target_id,
        question_title=q.title.replace("Clarification: ", ""),
        answer=normalized_input,
        is_default=False,
        ambiguity_count=current_strikes,
        hitl_confirmed=True
    )
    
    comp = evaluate_domain_completeness(session)
    conf = calculate_discovery_confidence(session)
    next_q = get_current_question(session)

    if comp["is_gate_passed"] or not next_q:
        content = (
            f"🎉 **Discovery Completed with {conf.score}% Grounded Confidence! (95%+ Gate Passed)**\n\n"
            f"All {comp['confirmed_count'] + comp['escalated_count']} of 32 architectural and business parameters captured. "
            "Synthesizing complete BRD for Dual-Review..."
        )
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=content,
            timestamp="Just now"
        )
        return msg, True
    else:
        domain_idx = comp["confirmed_count"] + comp["escalated_count"] + 1
        tech_note = ""
        if next_q.category in ["Technical", "AI & RAG", "Sizing", "Scale"] or next_q.id in ["q_cloud", "q_foundation_llm", "q_security", "q_compliance", "q_hadr_tier"]:
            tech_note = "\n\n💡 *Tip: If you'd like technical recommendations on this, you can click **'Ask Architect 🏗️'**.*"
            
        if next_q.id.endswith("_clarification"):
            header = f"### 🔍 Targeted Clarification: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
        else:
            header = f"### 📋 Domain {domain_idx} of 32: **{next_q.title}** *(Domain Coverage: {comp['confirmed_count'] + comp['escalated_count']}/32 • {comp['completion_rate']}% | Gate: 95%)*"
            
        content = (
            f"✅ **Recorded for {q.title}:**\n> *\"{normalized_input}\"*\n\n"
            f"---\n\n"
            f"{header}\n\n"
            f"**{next_q.prompt}**\n\n"
            f"*(Example: {next_q.help_text})*{tech_note}"
        )
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=content,
            timestamp="Just now",
            question_context=next_q
        )
        return msg, False

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
    """0-Click Document Auto-Discovery: Parses uploaded RFP/SOW/specs using Real-Time AI & Heuristics."""
    # Attempt Real-Time AI Extraction via connected Cloud AI Provider
    ai_extracted = LLMGateway.extract_rfp_intelligence(text)
    if ai_extracted and ai_extracted.get("client_name"):
        c_name = ai_extracted.get("client_name", "Enterprise Client")
        p_title = ai_extracted.get("project_title", "AI Platform")
        tier_val = ai_extracted.get("delivery_tier", "PoC")
        prob_val = ai_extracted.get("problem_statement", f"Extracted from {filename}")
        cloud_val = ai_extracted.get("cloud_platform", "Microsoft Azure")
        
        discovered = {
            "q_client": AnswerItem(question_id="q_client", question_title="Client & Engagement Name", answer=f"{c_name} | {p_title}", is_default=False, notes=f"Live AI-extracted from {filename}"),
            "q_tier": AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer=tier_val if tier_val in DELIVERY_TIERS else "PoC", is_default=False),
            "q_problem": AnswerItem(question_id="q_problem", question_title="Problem Statement & Challenge", answer=prob_val, is_default=False),
            "q_duration": AnswerItem(question_id="q_duration", question_title="Reference Duration (Weeks)", answer=str(ai_extracted.get("estimated_weeks", 6.0)), is_default=False),
            "q_cloud": AnswerItem(question_id="q_cloud", question_title="Primary Hyperscaler Platform", answer=cloud_val, is_default=False),
            "q_geography": AnswerItem(question_id="q_geography", question_title="Deployment Geography", answer="India", is_default=False),
            "q_complexity": AnswerItem(question_id="q_complexity", question_title="Complexity Level", answer="Medium", is_default=False),
            "q_compliance": AnswerItem(question_id="q_compliance", question_title="Compliance Posture", answer=ai_extracted.get("compliance_posture", "Internal policy only"), is_default=False),
            "q_security": AnswerItem(question_id="q_security", question_title="Security Posture", answer=ai_extracted.get("security_posture", "Standard"), is_default=False),
            "q_named_users": AnswerItem(question_id="q_named_users", question_title="Total Named Users", answer=str(ai_extracted.get("named_users", 250)), is_default=False),
            "q_concurrent_users": AnswerItem(question_id="q_concurrent_users", question_title="Peak Concurrent Users", answer=str(ai_extracted.get("concurrent_users", 50)), is_default=False),
            "q_daily_requests": AnswerItem(question_id="q_daily_requests", question_title="Model Requests per Day", answer=str(ai_extracted.get("daily_requests", 2500)), is_default=False),
        }
        session.answers.update(discovered)
        session.current_question_index = len(STATIC_QUESTIONS)
        return {
            "client_name": c_name,
            "project_title": p_title,
            "delivery_tier": tier_val,
            "cloud_platform": cloud_val,
            "ai_extracted": True,
            "confidence_score": 98.0
        }

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

def get_brd_template_sheet(session: ProjectSession) -> Dict[str, Any]:
    """
    Returns the comprehensive Universal Enterprise AI BRD Document Template Sheet with standard fields,
    subfields, topics, subtopics, completion status, and 95% gate calculation.
    Supports all AI archetypes: Conversational AI, Enterprise RAG, Document Intelligence,
    Predictive ML/AML, Autonomous Multi-Agent Systems, and Computer Vision.
    """
    ans = session.answers
    brd = session.brd

    # Topic 1: Business Objectives & Functional Scope (Client Business Lead)
    t1_fields = [
        {
            "id": "client_name",
            "question_id": "q_client",
            "title": "Enterprise Account & Client",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_client" in ans and ans["q_client"].answer else "PENDING",
            "value": ans["q_client"].answer.split("|")[0].strip() if "q_client" in ans and "|" in ans["q_client"].answer else (ans["q_client"].answer if "q_client" in ans else None),
            "subtopic": "Account Identification",
            "description": "Enterprise client or organization name sponsoring the AI initiative"
        },
        {
            "id": "project_title",
            "question_id": "q_client",
            "title": "Initiative & AI Solution Title",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_client" in ans and ans["q_client"].answer else "PENDING",
            "value": ans["q_client"].answer.split("|")[-1].strip() if "q_client" in ans and "|" in ans["q_client"].answer else (ans.get("q_client").answer if "q_client" in ans else None),
            "subtopic": "Solution Identity",
            "description": "Descriptive title for the AI system, assistant, copilot, or platform"
        },
        {
            "id": "problem_statement",
            "question_id": "q_problem",
            "title": "Business Problem & AI Opportunity",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_problem" in ans and len(ans["q_problem"].answer or "") > 15 else "PENDING",
            "value": ans["q_problem"].answer if "q_problem" in ans else None,
            "subtopic": "Strategic Context",
            "description": "Operational bottlenecks, user friction, manual overhead, and business challenge"
        },
        {
            "id": "delivery_tier",
            "question_id": "q_tier",
            "title": "Target Delivery Tier",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_tier" in ans and ans["q_tier"].answer else "PENDING",
            "value": ans["q_tier"].answer if "q_tier" in ans else "PoC",
            "subtopic": "Delivery Scope",
            "description": "Target release maturity: PoC, Pilot, MVP, or Full Production Grade"
        },
        {
            "id": "target_personas",
            "question_id": "q_personas_count",
            "title": "Target User Personas",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_personas_count" in ans and ans["q_personas_count"].answer else "PENDING",
            "value": f"{ans['q_personas_count'].answer} Active Personas" if "q_personas_count" in ans else None,
            "subtopic": "Stakeholder Model",
            "description": "Target end-users, operators, administrators, and customer roles"
        },
        {
            "id": "functional_scope",
            "question_id": "q_legal_categories",
            "title": "In-Scope Capabilities & Domains",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_legal_categories" in ans and ans["q_legal_categories"].answer else "PENDING",
            "value": ans["q_legal_categories"].answer if "q_legal_categories" in ans else None,
            "subtopic": "Functional Boundaries",
            "description": "In-scope AI functional domains, capability modules, or business categories"
        }
    ]

    # Topic 2: AI Solution Architecture & Systems Engineering (Solutions Architect)
    t2_fields = [
        {
            "id": "cloud_platform",
            "question_id": "q_cloud",
            "title": "Primary Hyperscaler Cloud",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_cloud" in ans and ans["q_cloud"].answer else "PENDING",
            "value": ans["q_cloud"].answer if "q_cloud" in ans else None,
            "subtopic": "Infrastructure Tier",
            "description": "Microsoft Azure, AWS, Google Cloud Platform, or Hybrid On-Premise"
        },
        {
            "id": "tech_components",
            "question_id": "q_components_count",
            "title": "Modular Architecture Components",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_components_count" in ans and ans["q_components_count"].answer else "PENDING",
            "value": f"{ans['q_components_count'].answer} Canonical Blocks" if "q_components_count" in ans else "6 Blocks",
            "subtopic": "Architecture Blueprint",
            "description": "Data Ingestion, Vector/Index, LLM Reasoning, Database/State, API/Telemetry, Security"
        },
        {
            "id": "foundation_model",
            "question_id": "q_foundation_llm",
            "title": "Foundation Model & Reasoning Tier",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if ("q_foundation_llm" in ans and ans["q_foundation_llm"].answer) or ("q_cloud" in ans and ans["q_cloud"].answer) else "PENDING",
            "value": (
                ans["q_foundation_llm"].answer if "q_foundation_llm" in ans and ans["q_foundation_llm"].answer
                else ("Anthropic Claude 3.5 Sonnet" if "q_cloud" in ans and "AWS" in (ans["q_cloud"].answer or "")
                else ("Google Gemini 2.5 Pro" if "q_cloud" in ans and "Google" in (ans["q_cloud"].answer or "")
                else ("Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)" if "q_cloud" in ans and "Azure" in (ans["q_cloud"].answer or "")
                else None)))
            ),
            "subtopic": "Model & Reasoning Strategy",
            "description": "Selected LLM/SLM reasoning tier, thinking budget, and inference orchestration"
        },
        {
            "id": "grounding_mode",
            "question_id": "q_grounding_mode",
            "title": "Knowledge Grounding & Retrieval Strategy",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_grounding_mode" in ans and ans["q_grounding_mode"].answer else "PENDING",
            "value": ans["q_grounding_mode"].answer if "q_grounding_mode" in ans else None,
            "subtopic": "Context & Retrieval",
            "description": "Tenant data isolation, hybrid BM25 + dense vector indexing, API tool grounding"
        },
        {
            "id": "doc_processing",
            "question_id": "q_doc_processing",
            "title": "Data Ingestion & Processing Pipeline",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": False,
            "status": "FILLED" if "q_doc_processing" in ans and ans["q_doc_processing"].answer else "PENDING",
            "value": ans["q_doc_processing"].answer if "q_doc_processing" in ans else "Document / Multi-Modal Stream Pipeline",
            "subtopic": "Data Intake & Processing",
            "description": "Document parsing, conversational streaming, tabular CDC, or multimodal intake"
        },
        {
            "id": "security_posture",
            "question_id": "q_security",
            "title": "Security, Governance & AI Guardrails",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_security" in ans and ans["q_security"].answer else "PENDING",
            "value": ans["q_security"].answer if "q_security" in ans else None,
            "subtopic": "Cybersecurity & Governance",
            "description": "Data encryption, zero-trust RBAC, PII redaction, audit logging & EU AI Act guardrails"
        }
    ]

    # Topic 3: Scale, Sizing & Operational Constraints (Joint Client & Architect)
    t3_fields = [
        {
            "id": "duration_weeks",
            "question_id": "q_duration",
            "title": "Reference Execution Duration",
            "owner": "JOINT",
            "is_key": True,
            "status": "FILLED" if "q_duration" in ans and ans["q_duration"].answer else "PENDING",
            "value": f"{ans['q_duration'].answer} Weeks" if "q_duration" in ans else None,
            "subtopic": "Schedule & Timeline",
            "description": "Reference project delivery timeline in calendar weeks"
        },
        {
            "id": "start_date",
            "question_id": "q_start_date",
            "title": "Target Kick-Off Date",
            "owner": "JOINT",
            "is_key": False,
            "status": "FILLED" if "q_start_date" in ans and ans["q_start_date"].answer else "PENDING",
            "value": ans["q_start_date"].answer if "q_start_date" in ans else None,
            "subtopic": "Schedule & Timeline",
            "description": "Target project kick-off date mapped against statutory working calendar"
        },
        {
            "id": "named_users",
            "question_id": "q_named_users",
            "title": "Total Entitled User Base",
            "owner": "CLIENT",
            "is_key": True,
            "status": "FILLED" if "q_named_users" in ans and ans["q_named_users"].answer else "PENDING",
            "value": ans["q_named_users"].answer if "q_named_users" in ans else None,
            "subtopic": "User Concurrency & Sizing",
            "description": "Total licensed or registered user base entitled to access the AI system"
        },
        {
            "id": "concurrent_users",
            "question_id": "q_concurrent_users",
            "title": "Peak Concurrent Users",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_concurrent_users" in ans and ans["q_concurrent_users"].answer else "PENDING",
            "value": ans["q_concurrent_users"].answer if "q_concurrent_users" in ans else None,
            "subtopic": "User Concurrency & Sizing",
            "description": "Simultaneous peak active user or agent sessions"
        },
        {
            "id": "daily_requests",
            "question_id": "q_daily_requests",
            "title": "Daily Request Throughput (RPS)",
            "owner": "SOLUTIONS_ARCHITECT",
            "is_key": True,
            "status": "FILLED" if "q_daily_requests" in ans and ans["q_daily_requests"].answer else "PENDING",
            "value": ans["q_daily_requests"].answer if "q_daily_requests" in ans else None,
            "subtopic": "Transaction Throughput",
            "description": "Daily transactions, query volume, and peak inference throughput"
        },
        {
            "id": "geography",
            "question_id": "q_geography",
            "title": "Deployment Geography & Working Calendar",
            "owner": "JOINT",
            "is_key": True,
            "status": "FILLED" if "q_geography" in ans and ans["q_geography"].answer else "PENDING",
            "value": ans["q_geography"].answer if "q_geography" in ans else None,
            "subtopic": "Regulatory & Working Calendar",
            "description": "Deployment hosting region and statutory working holiday schedule"
        },
        {
            "id": "buffer_strategy",
            "question_id": "q_buffer_strategy",
            "title": "Contingency Buffer & Standby Resourcing",
            "owner": "JOINT",
            "is_key": True,
            "status": "FILLED" if "q_buffer_strategy" in ans and ans["q_buffer_strategy"].answer else "PENDING",
            "value": ans["q_buffer_strategy"].answer if "q_buffer_strategy" in ans else None,
            "subtopic": "Risk & Resourcing Buffer",
            "description": "Shadow resourcing and contingency buffer allocation to guarantee delivery schedule"
        }
    ]

    # Topic 4: Calculated Financial Estimates & Resource Allocation (Agentic Synthesis Engine)
    t4_fields = [
        {
            "id": "person_days",
            "title": "Total Engineering Effort",
            "owner": "AGENT",
            "is_key": False,
            "status": "FILLED" if brd else "PENDING",
            "value": f"{brd.total_person_days:.1f} Person-Days ({brd.total_person_hours:.0f} hrs)" if brd else "Calculated upon 95% Gate",
            "subtopic": "Effort & Loading",
            "description": "Deterministic effort back-solved from task graph and role loading"
        },
        {
            "id": "labour_cost",
            "title": "Total Labor Investment",
            "owner": "AGENT",
            "is_key": False,
            "status": "FILLED" if brd else "PENDING",
            "value": f"${brd.total_labour_cost_usd:,.2f} (@ ${brd.blended_hourly_rate:.2f}/hr)" if brd else "Calculated upon 95% Gate",
            "subtopic": "Commercial Model",
            "description": "Deterministic blended engineering rate across 12 disciplines"
        },
        {
            "id": "cloud_bom",
            "title": "Monthly Cloud & Token BoM",
            "owner": "AGENT",
            "is_key": False,
            "status": "FILLED" if brd else "PENDING",
            "value": f"${brd.sizing_metrics.total_monthly_cloud_cost_usd:,.2f} / month" if brd else "Calculated upon 95% Gate",
            "subtopic": "Cloud Sizing",
            "description": "Hyperscaler hosting, storage, vector database, and token inference budget"
        },
        {
            "id": "canonical_reqs",
            "title": "Formal Requirements Catalog",
            "owner": "AGENT",
            "is_key": False,
            "status": "FILLED" if brd else "PENDING",
            "value": f"{len(brd.canonical_requirements)} Formal Requirements" if brd else "17 Canonical Requirements",
            "subtopic": "Requirements Catalog",
            "description": "17 Functional & Non-Functional traceable requirements with MoSCoW tags"
        }
    ]

    topics = [
        {
            "id": "topic_business",
            "title": "1. Business Objectives & Functional Scope",
            "icon": "📌",
            "primary_persona": "Client Business Lead",
            "description": "Business problem, AI opportunity, user personas, and target capabilities defined by the Client",
            "fields": t1_fields
        },
        {
            "id": "topic_architecture",
            "title": "2. AI Solution Architecture & Systems Engineering",
            "icon": "🏗️",
            "primary_persona": "Solutions Architect",
            "description": "Hyperscaler cloud, modular blocks, foundation models, grounding, and security guardrails",
            "fields": t2_fields
        },
        {
            "id": "topic_sizing",
            "title": "3. Scale, Sizing & Operational Constraints",
            "icon": "☁️",
            "primary_persona": "Joint (Client + Architect)",
            "description": "User concurrency, RPS transaction volumes, statutory calendar, and contingency buffer",
            "fields": t3_fields
        },
        {
            "id": "topic_estimates",
            "title": "4. Calculated Financial Estimates & Resource Allocation",
            "icon": "💰",
            "primary_persona": "Agentic Synthesis Engine",
            "description": "Deterministic person-days, labor costs, 12 disciplines, and cloud BoM",
            "fields": t4_fields
        }
    ]

    all_inputs = t1_fields + t2_fields + t3_fields
    filled_count = sum(1 for f in all_inputs if f["status"] == "FILLED")
    key_fields = [f for f in all_inputs if f["is_key"]]
    key_filled = sum(1 for f in key_fields if f["status"] == "FILLED")
    
    # Calculate percentage based on key fields (17 total key required fields)
    completion_rate = round((key_filled / len(key_fields)) * 100, 1) if key_fields else 0.0
    
    # Check 95% Gate (all 17 key fields required to reach 100% and satisfy >= 95% gate)
    is_gate_passed = (completion_rate >= 95.0) and (key_filled == len(key_fields))
    
    missing_key = [f["title"] for f in key_fields if f["status"] != "FILLED"]

    return {
        "topics": topics,
        "total_fields": len(all_inputs),
        "filled_fields": filled_count,
        "key_fields_total": len(key_fields),
        "key_fields_filled": key_filled,
        "missing_key_fields": missing_key,
        "completion_rate": completion_rate,
        "is_gate_passed": is_gate_passed,
        "gate_threshold": 95.0,
        "has_synthesized_brd": brd is not None
    }
