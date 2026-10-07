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
from backend.json_questionnaire_engine import JSONQuestionnaireEngine
from backend.worked_example_data import MASTER_CLARIFICATION_QUESTIONS_52

TEMPLATE_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_brd_questionnaire_template.json")

def get_brd_questionnaire_template() -> Dict[str, Any]:
    return JSONQuestionnaireEngine.get_template()

STATIC_QUESTIONS: List[QuestionItem] = [
    # 1. Project Vision & Core Objectives
    QuestionItem(
        id="q_client",
        title="Client & Project Initiative",
        prompt="Who is the client / organization, and what is the working title for this AI project initiative?",
        type="text",
        options=[],
        default_value="Enterprise Client | AI Automation Platform",
        category="Scope",
        priority="Blocker",
        help_text="Type your organization/client name and project title (e.g. Acme Corp — AI Billing Automation Platform or CareHealth — Clinical Trial Matching)."
    ),
    QuestionItem(
        id="q_problem",
        title="Problem Statement & Core Business Objectives",
        prompt="What specific business problem, manual bottlenecks, and key objectives must this AI solution solve? (2-5 sentences)",
        type="text",
        options=[],
        default_value="Manual workflows and disconnected data sources cause operational bottlenecks, long turnaround times, and lack of consolidated visibility. The AI solution must automate extraction, validation, and decision-support with enterprise integration.",
        category="Scope",
        priority="Blocker",
        help_text="Detail who is impacted, current bottlenecks, and what automated decision or action this solution enables."
    ),
    QuestionItem(
        id="q_legal_categories",
        title="In-Scope Functional Capabilities & Workflows",
        prompt="Which functional capabilities, business workflows, or domain categories are in scope for this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Employee Leave Management Lifecycle (Leave balance, applications, manager approval/rejection, cancellation, policy config, holiday calendar, HR reports)", label="Employee Leave Management System (ELMS Benchmark)", description="End-to-end leave lifecycle: balance tracking, validations, approvals, cancellation restoration, policy admin, and audit trail"),
            QuestionOption(value="Customer Support, IT Helpdesk, Knowledge Retrieval, Automated Triage", label="Conversational AI & Enterprise Support Copilot", description="Multi-turn user assistance, intelligent search, and ticket automation"),
            QuestionOption(value="Clinical Documentation, EHR Summarization, ICD/CPT Coding, Protocol Matching", label="Healthcare & Clinical AI Intelligence", description="Clinical note summarization, medical protocol matching, and triage"),
            QuestionOption(value="Lease, Vendor, Service, Facilities, Technology, Marketing", label="Contract Risk & Document Intelligence", description="Clause extraction and compliance scoring across contract categories"),
            QuestionOption(value="Transaction Monitoring, Fraud Detection, KYC Verification, AML Alerts", label="Financial Crime, AML & Predictive ML", description="Real-time transaction scoring, behavioral anomaly alerts, and KYC verification"),
            QuestionOption(value="Multi-Agent Task Routing, Autonomous Tool Calling, Code Synthesis, RPA", label="Autonomous Multi-Agent Workflow System", description="Cross-system action orchestration, dynamic tool selection, and execution"),
            QuestionOption(value="Enterprise Knowledge Base, Semantic Search, Policy Q&A, Research Synthesis", label="Enterprise RAG & Knowledge Hub", description="Vector-indexed organizational documentation and verifiable QA")
        ],
        default_value="Employee Leave Management Lifecycle (Leave balance, applications, manager approval/rejection, cancellation, policy config, holiday calendar, HR reports)",
        category="Scope",
        priority="High",
        help_text="Defines the specific functional modules handled by the platform."
    ),
    QuestionItem(
        id="q_tier",
        title="Delivery Tier",
        prompt="What is the targeted delivery tier for this engagement?",
        type="dropdown",
        options=[
            QuestionOption(value="MVP", label="Minimum Viable Product (MVP) [Base 0.778]", description="Production-grade core slice, real users, automated CI/CD"),
            QuestionOption(value="PoC", label="Proof of Concept (PoC) [Base 0.289]", description="Throwaway build, happy path, sampled data, single env, headline weight 0.289"),
            QuestionOption(value="Pilot", label="Pilot Trial [Base 0.525]", description="Limited live trial with controlled cohort, real data, ring-fenced"),
            QuestionOption(value="Production Grade", label="Production Grade [Base 1.000]", description="Full enterprise readiness, enforced NFRs, full HA/DR"),
            QuestionOption(value="PoC to Pilot", label="PoC to Pilot [Transition 0.320]", description="Uplift existing PoC to controlled live trial with rework uplift"),
            QuestionOption(value="PoC to MVP", label="PoC to MVP [Transition 0.612]", description="Uplift existing PoC directly to releasable MVP slice"),
            QuestionOption(value="PoC to Production Grade", label="PoC to Production Grade [Transition 0.867]", description="Uplift existing PoC straight to full production grade"),
            QuestionOption(value="Pilot to MVP", label="Pilot to MVP [Transition 0.342]", description="Uplift running pilot into releasable MVP"),
            QuestionOption(value="Pilot to Production Grade", label="Pilot to Production Grade [Transition 0.597]", description="Uplift running pilot to full production grade"),
            QuestionOption(value="MVP to Production Grade", label="MVP to Production Grade [Transition 0.305]", description="Harden live MVP to full production grade"),
            QuestionOption(value="Incremental Production Grade", label="Incremental Production Grade [Delta 0.300]", description="Delta release on live solution (30% scope share)")
        ],
        default_value="MVP",
        category="Scope",
        priority="Blocker",
        help_text="Select from the 11 delivery tiers to set phase multipliers."
    ),

    QuestionItem(
        id="q_duration",
        title="Reference Duration (Weeks)",
        prompt="What is the targeted reference duration for this phase in calendar weeks?",
        type="dropdown",
        options=[
            QuestionOption(value="8.0", label="8.0 Weeks (Standard MVP Benchmark)", description="Standard 8-week MVP delivery (40 working days)"),
            QuestionOption(value="4.0", label="4.0 Weeks", description="Aggressive 4-week sprint (20 working days)"),
            QuestionOption(value="6.0", label="6.0 Weeks", description="Standard 6-week baseline (30 working days)"),
            QuestionOption(value="12.0", label="12.0 Weeks", description="Extended 12-week build (60 working days)"),
            QuestionOption(value="16.0", label="16.0 Weeks", description="Full Production Grade 16-week delivery (80 working days)")
        ],
        default_value="8.0",
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
            QuestionOption(value="1 Use Case (Standard Baseline - 1.000x)", label="1 Use Case (Standard Baseline - 1.000x)", description="Single primary capability: Leave Management Lifecycle or Principle Extraction"),
            QuestionOption(value="2 Use Cases (Factor 1.250x)", label="2 Use Cases (Factor 1.250x)", description="Two distinct functional capabilities"),
            QuestionOption(value="3 Use Cases (Factor 1.500x)", label="3 Use Cases (Factor 1.500x)", description="Three business capabilities"),
            QuestionOption(value="5 Use Cases (Factor 2.000x)", label="5 Use Cases (Factor 2.000x)", description="Multi-department enterprise capabilities")
        ],
        default_value="1 Use Case (Standard Baseline - 1.000x)",
        category="Scale",
        priority="High",
        help_text="1 for Primary Business Capability (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_personas_count",
        title="User Personas Count",
        prompt="How many distinct user personas or stakeholder roles will interact with the system? (Baseline is 4)",
        type="dropdown",
        options=[
            QuestionOption(value="4 Personas (Employee, Manager, HR Administrator, HR Manager)", label="4 Personas (Employee, Manager, HR Admin, HR Manager - Benchmark)", description="4 roles: Employee (apply/cancel/view), Manager (approve/reject direct reports), HR Admin (policies/holidays), HR Manager (reports)"),
            QuestionOption(value="4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)", label="4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)", description="Legal Counsel, Procurement Lead, Risk Officer, Executive Sponsor (Elasticity: 0.45)"),
            QuestionOption(value="2 Personas (Standard Baseline - Factor 1.000)", label="2 Personas (Standard Baseline - Factor 1.000)", description="Primary business user and administrator"),
            QuestionOption(value="1 Persona (Single Role - Factor 0.775)", label="1 Persona (Single Role - Factor 0.775)", description="Single designated user type"),
            QuestionOption(value="6 Personas (Enterprise Cross-Functional - Factor 1.900)", label="6 Personas (Enterprise Cross-Functional - Factor 1.900)", description="Broad stakeholder group across legal, ops, audit, and execs")
        ],
        default_value="4 Personas (Employee, Manager, HR Administrator, HR Manager)",
        category="Scale",
        priority="High",
        help_text="4 active personas: Employee, Manager, HR Administrator, HR Manager (Factor: 1.450)."
    ),
    QuestionItem(
        id="q_integrations_count",
        title="System Integrations Count",
        prompt="How many inbound/outbound enterprise system integrations are required in this phase? (Baseline is 2)",
        type="dropdown",
        options=[
            QuestionOption(value="2 Integrations (INT-001 Corporate SSO Identity + INT-002 Corporate Email Notifications)", label="2 Integrations (INT-001 Corporate SSO + INT-002 Corporate Email)", description="INT-001: Corporate Identity/Directory for employee & manager hierarchy | INT-002: Corporate Email for leave event notifications"),
            QuestionOption(value="0 Integrations (Manual Upload / Blob Storage - Floor 0.500x)", label="0 Integrations (Manual Upload / Blob Storage - Floor 0.500x)", description="Manual PDF uploads directly to Azure Blob Storage (Scaled to floor factor 0.500)"),
            QuestionOption(value="1 Integration (Factor 0.675x)", label="1 Integration (Factor 0.675x)", description="Single REST API / ERP connector"),
            QuestionOption(value="4 Integrations (Factor 1.650x)", label="4 Integrations (Factor 1.650x)", description="Four enterprise integrations (CRM, ERP, Document Store, Auth)")
        ],
        default_value="2 Integrations (INT-001 Corporate SSO Identity + INT-002 Corporate Email Notifications)",
        category="Scale",
        priority="High",
        help_text="2 enterprise integrations: INT-001 Corporate SSO and INT-002 Corporate Email (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_datasources_count",
        title="Distinct Data Sources",
        prompt="How many distinct data sources or document repositories feed into this solution? (Baseline is 2)",
        type="dropdown",
        options=[
            QuestionOption(value="2 Data Sources (Corporate Employee Directory / HRMS Database + Holiday Calendar Data)", label="2 Data Sources (Employee Directory + Holiday Calendar)", description="Data Source 1: Corporate Employee Directory/HRMS | Data Source 2: Annual Company Holiday Calendar"),
            QuestionOption(value="2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)", label="2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)", description="Azure Blob Storage contract repository + historical risk register spreadsheet"),
            QuestionOption(value="1 Data Source (Single Repository - Factor 0.750x)", label="1 Data Source (Single Repository - Factor 0.750x)", description="Single digital upload repository"),
            QuestionOption(value="3 Data Sources (Factor 1.250x)", label="3 Data Sources (Factor 1.250x)", description="Blob Storage, SQL Database, and SharePoint repository"),
            QuestionOption(value="5 Data Sources (Enterprise Data Lake - Factor 1.750x)", label="5 Data Sources (Enterprise Data Lake - Factor 1.750x)", description="Enterprise data lake, CRM, ERP, Blob, and Wiki")
        ],
        default_value="2 Data Sources (Corporate Employee Directory / HRMS Database + Holiday Calendar Data)",
        category="Scale",
        priority="High",
        help_text="2 distinct data sources (Employee Directory + Holiday Calendar, Factor: 1.000)."
    ),
    QuestionItem(
        id="q_channels_count",
        title="Delivery Channels",
        prompt="How many user-facing delivery channels are in scope (e.g., Web App, Mobile, Teams Bot, REST API)?",
        type="dropdown",
        options=[
            QuestionOption(value="1 Channel (Web Application UI - Baseline 1.000x)", label="1 Channel (Web Application UI - Benchmark Standard)", description="Browser-based web application (Chrome, Edge, Safari latest 2 versions)"),
            QuestionOption(value="2 Channels (Web App + Microsoft Teams Bot - Factor 1.300x)", label="2 Channels (Web App + Microsoft Teams Bot - Factor 1.300x)", description="Web browser app and integrated Teams bot"),
            QuestionOption(value="3 Channels (Web + Mobile App + REST API - Factor 1.600x)", label="3 Channels (Web + Mobile App + REST API - Factor 1.600x)", description="Web, iOS/Android mobile client, and public REST API")
        ],
        default_value="1 Channel (Web Application UI - Baseline 1.000x)",
        category="Scale",
        priority="Medium",
        help_text="1 for single Web Application UI (Factor: 1.000; native mobile out of scope per A-006)."
    ),
    QuestionItem(
        id="q_languages_count",
        title="Languages Supported",
        prompt="How many languages must be processed by the application?",
        type="dropdown",
        options=[
            QuestionOption(value="1 Language (English Only - Baseline 1.000x)", label="1 Language (English Only - Benchmark Standard)", description="English is the only language required for MVP per A-004"),
            QuestionOption(value="2 Languages (English + Regional / European - Factor 1.350x)", label="2 Languages (English + Regional / European - Factor 1.350x)", description="Bilingual document processing"),
            QuestionOption(value="5 Languages (Multilingual Enterprise - Factor 2.000x)", label="5 Languages (Multilingual Enterprise - Factor 2.000x)", description="Global multilingual support")
        ],
        default_value="1 Language (English Only - Baseline 1.000x)",
        category="Scale",
        priority="Medium",
        help_text="1 for English-only MVP scope per A-004 (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_envs_count",
        title="Deployment Environments",
        prompt="How many isolated cloud environments must be provisioned (e.g., Dev, Test, Prod)?",
        type="dropdown",
        options=[
            QuestionOption(value="3 Environments (Dev, Test, Prod - Baseline 1.000x)", label="3 Environments (Dev, Test, Prod - Benchmark Standard)", description="Development, Test/QA, and Production subscriptions"),
            QuestionOption(value="2 Environments (Dev, Prod - Factor 0.800x)", label="2 Environments (Dev, Prod - Factor 0.800x)", description="Development and Production only"),
            QuestionOption(value="4 Environments (Dev, Test, Staging/UAT, Prod - Factor 1.200x)", label="4 Environments (Dev, Test, Staging/UAT, Prod - Factor 1.200x)", description="Development, Test, Staging, and Production")
        ],
        default_value="3 Environments (Dev, Test, Prod - Baseline 1.000x)",
        category="Scale",
        priority="High",
        help_text="3 for Dev, Test, and Prod (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_components_count",
        title="Architecture Components Count",
        prompt="How many distinct deployable architecture components carry the target solution? (Baseline is 6)",
        type="dropdown",
        options=[
            QuestionOption(value="6 Components (UI, API Gateway, Leave Engine, DB, Email Service, Audit Logger)", label="6 Components (UI, API, Leave Engine, DB, Email Service, Audit - Benchmark)", description="6 microservices: Web UI, API Gateway, Leave Policy & Calculation Engine, PostgreSQL DB, Email Integration Service, Audit Logger"),
            QuestionOption(value="6 Components (Landing, Search, Reasoning, DB, Eval, UI - Baseline 1.000x)", label="6 Components (Landing, Search, Reasoning, DB, Eval, UI - AI Baseline)", description="6 microservices: Landing/Ingestion, Search Index, LLM Engine, Database, Eval Harness, UI Cockpit"),
            QuestionOption(value="4 Components (Lean Pipeline - Factor 0.800x)", label="4 Components (Lean Pipeline - Factor 0.800x)", description="Ingestion, Search, LLM Engine, UI Cockpit"),
            QuestionOption(value="8 Components (Enterprise Scaled Microservices - Factor 1.300x)", label="8 Components (Enterprise Scaled Microservices - Factor 1.300x)", description="Comprehensive enterprise distributed architecture")
        ],
        default_value="6 Components (UI, API Gateway, Leave Engine, DB, Email Service, Audit Logger)",
        category="Scale",
        priority="High",
        help_text="6 components for UI, API, Leave Engine, DB, Email, and Audit (Factor: 1.000)."
    ),
    QuestionItem(
        id="q_complexity",
        title="Technical Complexity Level",
        prompt="What is the overall technical complexity of the domain and algorithms?",
        type="dropdown",
        options=[
            QuestionOption(value="Medium", label="Medium (1.000 Baseline - Benchmark Standard)", description="Moderate multi-step validation logic, policy matrix, working-day calculations"),
            QuestionOption(value="Low", label="Low (0.850 Multiplier)", description="Standard CRUD, structured documents, straightforward schemas"),
            QuestionOption(value="High", label="High (1.250 Multiplier)", description="Deep agentic reasoning, cross-document reasoning"),
            QuestionOption(value="Very High", label="Very High (1.500 Multiplier)", description="Custom model fine-tuning, complex multi-modal pipelines")
        ],
        default_value="Medium",
        category="Scale",
        priority="High",
        help_text="Graded as Medium (1.000 baseline) for multi-step approval hierarchy, holiday deduction, and balance restoration."
    ),
    QuestionItem(
        id="q_compliance",
        title="Non-Functional: Regulatory Compliance & Statutory Standards (NFR-3)",
        prompt="What regulatory compliance, data privacy, and statutory governance standards must this solution satisfy (e.g. GDPR, HIPAA, SOC2 Type II, ISO 27001, PCI-DSS, RBI Guidelines)?",
        type="dropdown",
        options=[
            QuestionOption(value="Internal Security & Privacy Policy (A-011 Verification Gate for External Statutory Standards)", label="Internal Security Policy (A-011 Verification Gate - Benchmark)", description="Internal corporate data privacy/security policy; A-011 tagged as 'Needs Verification' for external statutory regulations"),
            QuestionOption(value="GDPR / DPDP & Data Privacy (EU / India)", label="GDPR / DPDP Privacy Compliance (1.150x)", description="Strict personal data protection, consent tracking, right-to-erasure workflows"),
            QuestionOption(value="HIPAA & HITECH (Healthcare Protected Health Information)", label="HIPAA Compliance (1.300x)", description="Protected Health Information (PHI) safeguarding, strict BAA agreements, access logs"),
            QuestionOption(value="SOC2 Type II & ISO 27001 Certified Governance", label="SOC2 Type II & ISO 27001 (1.150x)", description="Independent security control certification, continuous vulnerability scanning"),
            QuestionOption(value="BFSI / RBI / PCI-DSS Financial Regulatory Grade", label="BFSI / RBI / PCI-DSS Financial Grade (1.300x)", description="Financial transaction auditing, tamper-proof logs, regulatory reporting gates")
        ],
        default_value="Internal Security & Privacy Policy (A-011 Verification Gate for External Statutory Standards)",
        category="Scale",
        priority="High",
        help_text="Bound by Internal Security/Privacy policy with A-011 statutory verification gate (NFR-3)."
    ),
    QuestionItem(
        id="q_security",
        title="Non-Functional: Security, Corporate SSO & CMEK Encryption (NFR-5)",
        prompt="What authentication (SSO/MFA), authorization (RBAC), and encryption standards (TLS 1.3 / AES-256 / CMEK) are mandated for this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Corporate SSO (Azure AD / Entra ID) + Role-Based Access Control + Encryption in Transit & Rest", label="Corporate SSO + RBAC + Encryption at Rest/Transit (Benchmark Security)", description="Corporate SSO (OAuth2/OIDC), strict RBAC data isolation between roles, TLS 1.3 in-transit, and AES-256 at-rest"),
            QuestionOption(value="Enhanced CMEK + VNet Private Endpoints", label="Enhanced CMEK + Private Endpoints (1.120x)", description="VNet injection, Private Endpoints, Customer-Managed Keys (CMEK) via Key Vault / KMS"),
            QuestionOption(value="Restricted / Air-Gapped Zero-Trust Architecture", label="Restricted / Air-Gapped Zero-Trust (1.300x)", description="Zero internet ingress/egress, air-gapped network isolation, mTLS mutual authentication"),
            QuestionOption(value="Standard Enterprise IAM", label="Standard Enterprise IAM (1.000 Baseline)", description="HTTPS, standard RBAC, platform-managed keys, Managed Identities")
        ],
        default_value="Corporate SSO (Azure AD / Entra ID) + Role-Based Access Control + Encryption in Transit & Rest",
        category="Scale",
        priority="High",
        help_text="Corporate SSO (Azure AD/Entra ID) with RBAC and encryption in transit/at rest (NFR-5, FR-001, FR-023)."
    ),
    # 3. Technology Stack, Cloud & Infrastructure Factors
    QuestionItem(
        id="q_cloud",
        title="Primary Hyperscaler Platform",
        prompt="Which cloud platform will host this solution?",
        type="dropdown",
        options=[
            QuestionOption(value="Microsoft Azure", label="Microsoft Azure (Approved Platform - A-009)", description="Azure App Services / Container Apps, Azure SQL / PostgreSQL, Azure AD SSO"),
            QuestionOption(value="Google Cloud Platform", label="Google Cloud Platform (GCP)", description="Google Cloud Run, Cloud SQL, Google Workspace Identity"),
            QuestionOption(value="Amazon Web Services", label="Amazon Web Services (AWS)", description="AWS ECS/Fargate, Aurora PostgreSQL, AWS IAM / Cognito")
        ],
        default_value="Microsoft Azure",
        category="Technical",
        priority="Blocker",
        help_text="Microsoft Azure is the approved platform per A-009."
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
        help_text="India region locks 5 days/wk, 9.0 hrs/day and regional statutory holidays (BR-011)."
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
        title="Non-Functional: High Availability SLA & Disaster Recovery (NFR-2)",
        prompt="What High Availability (HA) uptime SLA percentage (99.5%–99.99%) and Disaster Recovery (DR) RTO/RPO targets must be guaranteed?",
        type="dropdown",
        options=[
            QuestionOption(value="High Availability (99.5% Monthly Uptime) + Daily Backup (RPO 24h, RTO 8h)", label="99.5% Monthly Availability + Daily Backup (RPO 24h, RTO 8h - Benchmark)", description="Target availability 99.5% monthly; daily automated database backups with RPO 24h and RTO 8h"),
            QuestionOption(value="99.9% Zone-Redundant HA + Automated RPO 1h / RTO 4h", label="99.9% Zone-Redundant (RPO 1h, RTO 4h - 1.350x)", description="Multi-Availability Zone redundancy within primary region with hourly snapshot backups"),
            QuestionOption(value="99.95% Region Pair Active-Passive + RPO 15m / RTO 1h", label="99.95% Region Pair Active-Passive (RPO 15m, RTO 1h - 1.600x)", description="Secondary failover region with automated geo-replication and warm standby"),
            QuestionOption(value="99.99% Multi-Region Active-Active Global Resilience", label="99.99% Multi-Region Active-Active (Zero Downtime - 2.000x)", description="Dual active regions with global traffic routing and cross-region consensus replication"),
            QuestionOption(value="Basic Single Instance (99.0% Uptime)", label="Basic Single Instance (99.0% - 1.000x Baseline)", description="Standard single-instance hosting without multi-zone failover")
        ],
        default_value="High Availability (99.5% Monthly Uptime) + Daily Backup (RPO 24h, RTO 8h)",
        category="Technical",
        priority="Medium",
        help_text="99.5% monthly availability with daily backups (RPO 24h, RTO 8h per NFR-2)."
    ),
    # 4. Engine, Processing & Sizing Factors
    QuestionItem(
        id="q_foundation_llm",
        title="Core Engine & Business Rules Processing",
        prompt="What core processing engine evaluates business rules, policy calculations, and validations?",
        type="dropdown",
        options=[
            QuestionOption(value="Business Rules & Validation Engine (Working Day Calculation, Balance Check, Overlap Prevention)", label="Deterministic Business Rules & Validation Engine (Benchmark Standard)", description="Executes BR-001 to BR-015: past date block, balance validation, overlap check, holiday exclusions"),
            QuestionOption(value="Azure OpenAI Reasoning (GPT-5 Thinking/Reasoning)", label="Azure OpenAI Reasoning Tier (GPT-5 Thinking/Reasoning)", description="Optimized for multi-pass reasoning, synthesis, and deep verification"),
            QuestionOption(value="Azure OpenAI GPT-4o Standard", label="Azure OpenAI GPT-4o Standard", description="General-purpose high-speed multimodal reasoning"),
            QuestionOption(value="Anthropic Claude 3.5 Sonnet", label="Anthropic Claude 3.5 Sonnet", description="Long-context retrieval, coding, and structured extraction engine")
        ],
        default_value="Business Rules & Validation Engine (Working Day Calculation, Balance Check, Overlap Prevention)",
        category="AI & RAG",
        priority="High",
        help_text="Enforces deterministic business rules (BR-001 to BR-015) and policy validation."
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
        title="Data Ingestion & Migration Scope",
        prompt="What data ingestion pipeline or historical migration is required for this phase?",
        type="dropdown",
        options=[
            QuestionOption(value="Direct Database Ingestion (Historical Leave Migration Out of Scope per A-012)", label="Direct DB Ingestion (Historical Migration Out of Scope - Benchmark A-012)", description="Direct SQL ingestion of active employee records and policies; historical leave data migration is OUT OF SCOPE"),
            QuestionOption(value="Azure AI Document Intelligence Layout API", label="Document & Layout Intelligence (Layout API)", description="Extracts text, tables, and bounding-box coordinates from PDF/scanned documents"),
            QuestionOption(value="Multi-Turn Conversational & Streaming API Pipeline", label="Conversational & Streaming Text/Audio Intake", description="WebSockets / SSE streaming pipeline for low-latency dialogue and voice interactions"),
            QuestionOption(value="Semantic Chunking & Dense/Hybrid Vector Ingestion", label="Enterprise Knowledge Base & Vector Indexing", description="Document chunking, dense embeddings, and hybrid BM25 index creation")
        ],
        default_value="Direct Database Ingestion (Historical Leave Migration Out of Scope per A-012)",
        category="AI & RAG",
        priority="High",
        help_text="Direct database ingestion; historical data migration is out of scope per A-012."
    ),
    QuestionItem(
        id="q_named_users",
        title="Total Named Users",
        prompt="How many total named employees / users are entitled to access the platform?",
        type="dropdown",
        options=[
            QuestionOption(value="500 Named Users (500 Employees Initial, Scalable to 2,000)", label="500 Named Users (500 Employees Initial, Scalable to 2,000 - Benchmark)", description="500 employees initial rollout; architecture supports growth to 2,000 without fundamental redesign"),
            QuestionOption(value="200 Named Users (Standard Baseline)", label="200 Named Users (Standard Baseline)", description="200 named reviewers"),
            QuestionOption(value="50 Named Users (Pilot Cohort)", label="50 Named Users (Pilot Cohort)", description="Initial business team"),
            QuestionOption(value="1,000 Named Users (Enterprise Scale)", label="1,000 Named Users (Enterprise Scale)", description="Full enterprise community")
        ],
        default_value="500 Named Users (500 Employees Initial, Scalable to 2,000)",
        category="Sizing",
        priority="Medium",
        help_text="500 employees initially, scalable to 2,000 per benchmark scalability NFR."
    ),
    QuestionItem(
        id="q_concurrent_users",
        title="Peak Concurrent Users",
        prompt="What is the maximum number of simultaneous users active during peak hours?",
        type="dropdown",
        options=[
            QuestionOption(value="100 Peak Concurrent Users (Benchmark Concurrency Baseline)", label="100 Peak Concurrent Users (Benchmark Concurrency Baseline)", description="100 simultaneous active users during peak hours across 10 departments"),
            QuestionOption(value="50 Peak Concurrent Users (Standard Baseline)", label="50 Peak Concurrent Users (Standard Baseline)", description="50 simultaneous active sessions during peak hours"),
            QuestionOption(value="20 Peak Concurrent Users (Pilot)", label="20 Peak Concurrent Users (Pilot)", description="Controlled concurrency"),
            QuestionOption(value="250 Peak Concurrent Users (Enterprise Peak)", label="250 Peak Concurrent Users (Enterprise Peak)", description="High-scale concurrent workflows")
        ],
        default_value="100 Peak Concurrent Users (Benchmark Concurrency Baseline)",
        category="Sizing",
        priority="Medium",
        help_text="100 peak concurrent users driving API concurrency."
    ),
    QuestionItem(
        id="q_daily_requests",
        title="Non-Functional: Performance SLA, Latency & Throughput (NFR-1)",
        prompt="What are the performance latency targets (e.g. page load <2.0s, API response <500ms, AI processing <5s) and expected throughput?",
        type="dropdown",
        options=[
            QuestionOption(value="8,000 Requests / Year (Annual Benchmark Volume • SLAs: <3s Page Load, <5s Submit, <10s Reports)", label="8,000 Requests/Year (~35/Day • SLAs: <3s Page, <5s Submit, <10s Report)", description="8,000 annual leave transactions with strict NFRs: 95% page loads <3s, leave submission <5s, reports <10s"),
            QuestionOption(value="Strict SLA: <2.0s Page Load, <500ms API Response (p95), 2,000 Requests/Day", label="Strict Enterprise SLA (<2.0s Page, <500ms API, 2,000 Req/Day)", description="Sub-2-second response time for 95% of user requests under peak load"),
            QuestionOption(value="High-Throughput Streaming: <100ms Ingestion Latency, 50,000+ Events/Day", label="High-Throughput Streaming (<100ms Latency, 50,000+ Events/Day)", description="Real-time event processing with high-frequency streaming throughput"),
            QuestionOption(value="Batch Processing: 500 Requests / Day (Turnaround < 1 Hour)", label="Batch Processing (500 Req/Day, <1h Turnaround)", description="Light daily batch traffic with scheduled execution windows")
        ],
        default_value="8,000 Requests / Year (Annual Benchmark Volume • SLAs: <3s Page Load, <5s Submit, <10s Reports)",
        category="Sizing",
        priority="Medium",
        help_text="Performance SLA: <2.0-3.0s response latency, <500ms API response, and throughput sizing (NFR-1)."
    ),
    # 5. Data Governance & Parser Contract Factors
    QuestionItem(
        id="q_multi_pass_policy",
        title="Approval Hierarchy & Cancellation Policy",
        prompt="What approval hierarchy and balance restoration rules govern leave requests?",
        type="dropdown",
        options=[
            QuestionOption(value="Manager Approval Hierarchy with Balance Validation & Cancellation Restoration (BR-001 to BR-015)", label="Manager Approval Lifecycle & Balance Restoration (BR-001 - BR-015)", description="BR-001 to BR-015: Direct manager approval, no self-approval, balance reduction on approval, restoration on cancellation"),
            QuestionOption(value="Two-Pass Evaluation (Agree / Agree with Mgmt Approval / Not Agree)", label="Two-Pass Evaluation (3 Status Levels: Agree, Mgmt Approval, Not Agree)", description="Pass 1 extracts standard clauses; Pass 2 evaluates ambiguous terms to assign one of 3 statuses"),
            QuestionOption(value="Single-Pass Flat Extraction", label="Single-Pass Flat Extraction", description="Single prompt pass without iterative disambiguation")
        ],
        default_value="Manager Approval Hierarchy with Balance Validation & Cancellation Restoration (BR-001 to BR-015)",
        category="Governance",
        priority="High",
        help_text="Direct manager approval hierarchy; manager cannot self-approve; cancellation restores balance (BR-004, BR-005, BR-008)."
    ),
    QuestionItem(
        id="q_parser_delimiters",
        title="Non-Functional: Immutable Audit Trail & Decision Logging",
        prompt="What audit trail specifications, user action logging, and event traceability standards must be enforced?",
        type="dropdown",
        options=[
            QuestionOption(value="Structured Audit Event Logging (Actor, Action, Timestamp, Previous Status, New Status, Request ID)", label="Audit Trail & Transaction Logging (Actor, Action, Timestamp, Status Delta)", description="Immutable audit record: Who, What, Date/Time, Previous Status, New Status, Request ID (FR-022, NFR Audit)"),
            QuestionOption(value="Comprehensive SIEM / Splunk / Sentinel Real-Time Forwarding (7-Year Retention)", label="Enterprise SIEM Forwarding & 7-Year Retention", description="Real-time structured JSON event streaming to central SIEM with 7-year statutory archive"),
            QuestionOption(value="Block Headers (<<<BEGIN:NAME>>>) & Pipe (|), 30k Char Cap, 0.72 Synonym Threshold", label="Standard Format (<<<BEGIN:NAME>>> & Pipe |, 30k Char Cap, 0.72 Confidence)", description="30,000 char cell cap (>32k quarantined), 0.72 synonym confidence threshold, NOT PROVIDED placeholder")
        ],
        default_value="Structured Audit Event Logging (Actor, Action, Timestamp, Previous Status, New Status, Request ID)",
        category="Governance",
        priority="High",
        help_text="Immutable audit trail recording Who, What, When, Prev Status, New Status, Request ID (FR-022)."
    ),
    QuestionItem(
        id="q_approval_gate",
        title="Assumption & Approval Gating",
        prompt="What governance gate protocol enforces stakeholder prerequisites before calculation?",
        type="dropdown",
        options=[
            QuestionOption(value="Strict Assumption Gate (Blocks downline effort until all Approved / Verified)", label="Strict Assumption Gate (100% Approval / Verification Required)", description="Downline effort calculations and schedule are blocked until stakeholders approve assumptions (A-011 flagged for verification)"),
            QuestionOption(value="Advisory Assumption Gate", label="Advisory Assumption Gate (Non-blocking)", description="Allows schedule generation with unapproved assumption warnings")
        ],
        default_value="Strict Assumption Gate (Blocks downline effort until all Approved / Verified)",
        category="Governance",
        priority="Blocker",
        help_text="Enforces strict gate: calculations blocked until all assumptions pass verification (A-011 gate)."
    )
]

def _build_reference_doc_questions() -> List[QuestionItem]:
    res = []
    for q in MASTER_CLARIFICATION_QUESTIONS_52:
        qid = q["qid"]
        cat = q.get("category", "Key Decision")
        prio = q.get("priority", "High")
        q_text = q["question"]
        why = q.get("why_it_matters", "")
        who = q.get("who_answers", "")
        default_ans = q.get("suggested_default", q.get("answer", ""))
        
        opts = [
            QuestionOption(
                value=default_ans,
                label=f"Standard Baseline / Recommended ({qid})",
                description=default_ans[:110] + ("..." if len(default_ans) > 110 else "")
            ),
            QuestionOption(
                value=f"Custom Enterprise Specification for {qid}",
                label="Custom Specification",
                description="Provide custom client requirement or escalate to Solutions Architect"
            )
        ]
        
        prompt_text = (
            f"**[{qid}] {q_text}**\n\n"
            f"📌 **Why it matters:** {why}\n"
            f"👤 **Who should answer:** {who}"
        )
        
        res.append(QuestionItem(
            id=f"q_{qid}",
            title=f"[{qid}] {cat}: {q_text[:45]}...",
            prompt=prompt_text,
            type="dropdown",
            options=opts,
            default_value=default_ans,
            category=cat,
            priority=prio,
            help_text=why
        ))
    return res

REFERENCE_DOC_QUESTIONS_52: List[QuestionItem] = _build_reference_doc_questions()

def get_discovery_questions() -> List[QuestionItem]:
    existing_ids = {q.id for q in STATIC_QUESTIONS}
    combined = list(STATIC_QUESTIONS)
    for ref_q in REFERENCE_DOC_QUESTIONS_52:
        if ref_q.id not in existing_ids:
            combined.append(ref_q)
    return combined

def get_all_reference_doc_questions() -> List[QuestionItem]:
    return REFERENCE_DOC_QUESTIONS_52

# --- Section: 32 Architecture & Business Domains Master Template Registry ---
MASTER_DOMAIN_TEMPLATE: Dict[str, Dict[str, Any]] = {
    "q_client": {
        "title": "Client & Project Initiative",
        "category": "Scope",
        "required_fields": ["client_account_name", "initiative_title"],
        "description": "Enterprise client entity and formal working initiative title"
    },
    "q_problem": {
        "title": "Problem Statement & Core Business Objectives",
        "category": "Scope",
        "required_fields": ["pain_points", "target_users", "core_objectives"],
        "description": "Detailed business bottlenecks, affected roles, and intended transformation"
    },
    "q_legal_categories": {
        "title": "In-Scope Functional Capabilities & Workflows",
        "category": "Scope",
        "required_fields": ["in_scope_contract_categories", "principle_hierarchy"],
        "description": "Specific functional modules or capabilities in scope (e.g. Inquiries, Protocol Matching, Risk Analysis)"
    },
    "q_tier": {
        "title": "Delivery Tier",
        "category": "Scope",
        "required_fields": ["delivery_tier_name", "headline_weight_code"],
        "description": "Target delivery tier (PoC, Pilot, MVP, Production Grade, etc.)"
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

# Automatically register all 52 Reference Document Clarification Questions (Q001-Q052)
for _q in MASTER_CLARIFICATION_QUESTIONS_52:
    _qid = _q["qid"]
    _q_key = f"q_{_qid}"
    if _q_key not in MASTER_DOMAIN_TEMPLATE:
        MASTER_DOMAIN_TEMPLATE[_q_key] = {
            "title": f"[{_qid}] {_q.get('category', 'Key Decision')}: {_q['question'][:50]}...",
            "category": _q.get("category", "Technical"),
            "required_fields": [f"field_{_qid.lower()}"],
            "description": _q.get("why_it_matters", "")
        }
    if _qid not in MASTER_DOMAIN_TEMPLATE:
        MASTER_DOMAIN_TEMPLATE[_qid] = MASTER_DOMAIN_TEMPLATE[_q_key]

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

DOMAIN_TO_REFERENCE_QUESTIONS_MAP: Dict[str, List[str]] = {
    "q_client": ["Q044", "Q045", "Q052"],
    "q_problem": ["Q047", "Q019", "Q046"],
    "q_legal_categories": ["Q013", "Q014", "Q016", "Q017"],
    "q_tier": ["Q015", "Q021"],
    "q_duration": ["Q012", "Q048"],
    "q_start_date": ["Q012", "Q048"],
    "q_buffer_strategy": ["Q045", "Q010"],
    "q_usecases_count": ["Q013", "Q018"],
    "q_personas_count": ["Q025"],
    "q_integrations_count": ["Q038", "Q039"],
    "q_datasources_count": ["Q029", "Q030"],
    "q_channels_count": ["Q024"],
    "q_languages_count": ["Q026"],
    "q_envs_count": ["Q011"],
    "q_components_count": ["Q008", "Q022"],
    "q_complexity": ["Q028"],
    "q_compliance": ["Q033", "Q034"],
    "q_security": ["Q009", "Q031", "Q032", "Q036", "Q043"],
    "q_cloud": ["Q001", "Q004", "Q005"],
    "q_geography": ["Q003", "Q007", "Q049"],
    "q_onprem_footprint": ["Q003"],
    "q_subscription_isolation": ["Q002"],
    "q_hadr_tier": ["Q042", "Q010"],
    "q_foundation_llm": ["Q006"],
    "q_grounding_mode": ["Q008"],
    "q_doc_processing": ["Q027"],
    "q_named_users": ["Q037"],
    "q_concurrent_users": ["Q040"],
    "q_daily_requests": ["Q041", "Q019"],
    "q_multi_pass_policy": ["Q018", "Q021"],
    "q_parser_delimiters": ["Q023", "Q035"],
    "q_approval_gate": ["Q044", "Q020", "Q051"]
}

def get_domain_reference_subquestions_status(domain_id: str, session: ProjectSession) -> str:
    """
    Constructs a dynamic markdown status section displaying which reference questions
    (from Sheet 10 Q001-Q052) for this domain have already been answered vs which are pending.
    """
    ref_ids = DOMAIN_TO_REFERENCE_QUESTIONS_MAP.get(domain_id, [])
    if not ref_ids:
        return ""
    
    q_dict = {q["qid"]: q for q in MASTER_CLARIFICATION_QUESTIONS_52}
    
    lines = ["\n\n🔹 **Domain Reference Inquiries (Answered & Pending Status):**"]
    for qid in ref_ids:
        q_meta = q_dict.get(qid, {})
        q_text = q_meta.get("question", qid)
        if len(q_text) > 75:
            q_text = q_text[:72] + "..."
            
        # Check if answered previously
        ans_item = session.answers.get(f"q_{qid}") or session.answers.get(qid)
        if ans_item and ans_item.answer:
            val_str = str(ans_item.answer).strip()
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            lines.append(f"• `[{qid}]` {q_text} &rarr; ✅ *Confirmed:* **\"{val_str}\"**")
        else:
            default_val = q_meta.get("suggested_default", "")
            if len(default_val) > 40:
                default_val = default_val[:37] + "..."
            lines.append(f"• `[{qid}]` {q_text} &rarr; ❓ *Pending* *(Suggested: `{default_val}`)*")
            
    return "\n".join(lines)

def contextualize_question_for_session(base_q: QuestionItem, session: ProjectSession) -> QuestionItem:
    """
    Dynamically tailors the prompt, help text, required answers, and examples 
    of any of the 32 domains based on the user's specific project name, 
    problem statement, delivery tier, cloud, and prior answers.
    """
    if not base_q:
        return base_q

    # Extract current project context
    client_ans = session.answers.get("q_client")
    if client_ans and client_ans.answer:
        full_client_str = str(client_ans.answer).strip()
        proj_name = full_client_str.split("—")[-1].strip() if "—" in full_client_str else full_client_str
        client_org = full_client_str.split("—")[0].strip() if "—" in full_client_str else "Enterprise Client"
    else:
        proj_name = "your project"
        client_org = "Enterprise Client"

    problem_stmt = session.answers.get("q_problem", AnswerItem(question_id="q_problem", question_title="", answer="")).answer
    tier_val = session.answers.get("q_tier", AnswerItem(question_id="q_tier", question_title="", answer="MVP")).answer
    cloud_val = session.answers.get("q_cloud", AnswerItem(question_id="q_cloud", question_title="", answer="Microsoft Azure")).answer
    geo_val = session.answers.get("q_geography", AnswerItem(question_id="q_geography", question_title="", answer="India")).answer
    scope_val = session.answers.get("q_legal_categories", AnswerItem(question_id="q_legal_categories", question_title="", answer="Core Capabilities")).answer
    users_val = session.answers.get("q_named_users", AnswerItem(question_id="q_named_users", question_title="", answer="500")).answer

    # Deep copy question to avoid mutating global template
    q = base_q.model_copy(deep=True)
    qid = q.id.replace("_clarification", "")
    ref_status_block = get_domain_reference_subquestions_status(qid, session)

    # Dynamic tailoring across all 32 domains - strictly ONE focused question per turn
    if qid == "q_client":
        q.prompt = "What is your **Client Enterprise Name** and **Project Initiative Title**?"
        q.help_text = "e.g., 'Enterprise Global Corp — Employee Leave Management System (ELMS)' or 'PVR INOX — Contract Intelligence Platform'."
    elif qid == "q_problem":
        q.prompt = f"For **{proj_name}**, what specific business problem, manual bottlenecks, and strategic objectives must this solution solve?"
        q.help_text = "Detail who is impacted, current manual/inefficient processes, and what automated capability or decision this solution unlocks."
    elif qid == "q_legal_categories":
        q.prompt = f"What are the core functional modules, workflows, and in-scope capabilities required for **{proj_name}**?"
        q.help_text = f"Specify all in-scope capabilities, workflows, and business rules for {proj_name}."
    elif qid == "q_tier":
        q.prompt = f"What is the targeted delivery tier for **{proj_name}** (e.g. PoC, MVP, Pilot, Production Grade)?"
        q.help_text = f"Delivery tier defines engineering phase depth, test coverage rigor, environment isolation, and delivery multipliers for {proj_name}."
    elif qid == "q_duration":
        q.prompt = f"What is the targeted delivery timeline for **{proj_name}** in calendar weeks?"
        q.help_text = f"Standard MVP benchmark is 8.0 Weeks (40 working days). PoC baseline is 4.0-6.0 Weeks, Pilot is 12.0 Weeks, Production Grade is 16.0 Weeks."
    elif qid == "q_start_date":
        q.prompt = f"When is the targeted project kick-off / start date for **{proj_name}**? (YYYY-MM-DD)"
        q.help_text = f"e.g. 2026-09-30 (Used to calculate exact day-wise sprint schedule and regional statutory holidays in {geo_val})."
    elif qid == "q_buffer_strategy":
        q.prompt = f"What resource standby and backup engineering buffer strategy should be provisioned for **{proj_name}**?"
        q.help_text = f"Maintains standby capacity (e.g. 15% Recommended) to absorb sprint spikes, leaves, or blockers without delaying {proj_name} milestones."
    elif qid == "q_usecases_count":
        q.prompt = f"How many distinct functional use cases or AI capabilities are in scope for **{proj_name}**?"
        q.help_text = f"Baseline is 1 primary core initiative. Specify count if multiple distinct business sub-modules are included in this phase."
    elif qid == "q_personas_count":
        q.prompt = f"How many distinct user personas and stakeholder roles will interact with **{proj_name}**?"
        q.help_text = f"Specify total count of distinct user roles and permission tiers. (Standard enterprise benchmark is 4 user personas)."
    elif qid == "q_integrations_count":
        q.prompt = f"How many external enterprise system integrations are required for **{proj_name}**?"
        q.help_text = f"List external systems, protocols (REST API, Webhook, SFTP, Kafka), and auth mechanisms required to connect with {proj_name}."
    elif qid == "q_datasources_count":
        q.prompt = f"How many upstream data sources or document repositories will feed data into **{proj_name}**?"
        q.help_text = f"Specify data source types, schema structures, and data synchronization frequency for {proj_name}."
    elif qid == "q_channels_count":
        q.prompt = f"Through how many delivery channels will users access **{proj_name}** (e.g. Web App, Mobile, Teams Bot)?"
        q.help_text = f"Standard enterprise benchmark is 1 primary channel (Responsive Web Application Portal)."
    elif qid == "q_languages_count":
        q.prompt = f"How many human languages must **{proj_name}** support across the user interface and business operations?"
        q.help_text = f"e.g. 1 Language (English standard benchmark) or multilingual localization."
    elif qid == "q_envs_count":
        q.prompt = f"How many distinct deployment environments are required for **{proj_name}** (e.g., Development, Test/UAT, Production)?"
        q.help_text = f"Standard enterprise benchmark is 3 environments (Development, Test, Production) with isolated VPCs/subscriptions."
    elif qid == "q_components_count":
        q.prompt = f"How many custom microservices, AI pipelines, or architectural subsystems constitute **{proj_name}**?"
        q.help_text = f"Baseline architecture comprises 3 core tiers: Frontend Web App, Backend API Gateway & Business Logic, and Data/Storage Engine."
    elif qid == "q_complexity":
        q.prompt = f"What is the overall technical complexity level for **{proj_name}** considering workflows, algorithms, and integration depth?"
        q.help_text = f"Low (standard CRUD forms), Medium (enterprise business logic + integrations), High (complex workflows/LLM RAG), Very High (streaming/vision/multi-agent)."
    elif qid == "q_compliance":
        q.prompt = f"What regulatory compliance, data privacy, and statutory auditing standards must **{proj_name}** satisfy? (NFR-3)"
        q.help_text = f"e.g. Standard Enterprise Audit Trail & Role Logging, GDPR / DPDP (India/EU), HIPAA (Healthcare PHI), SOC2 Type II, RBI Guidelines, PCI-DSS."
    elif qid == "q_security":
        q.prompt = f"What authentication (SSO/MFA), authorization (RBAC), and encryption standards (TLS 1.3 / AES-256 / CMEK) are required for **{proj_name}**? (NFR-5)"
        q.help_text = f"e.g. Enterprise Corporate SSO ({cloud_val} Entra ID / Okta / SAML), Role-Based Access Control (RBAC), Key Vault secret management, and CMEK encryption at rest/transit."
    elif qid == "q_cloud":
        q.prompt = f"Which primary hyperscaler cloud platform or infrastructure will host **{proj_name}**?"
        q.help_text = f"e.g. Microsoft Azure, Amazon Web Services (AWS), Google Cloud Platform (GCP), IBM Cloud, or Hybrid/On-Premise."
    elif qid == "q_geography":
        q.prompt = f"In which primary delivery and deployment geography will **{proj_name}** be operated and hosted?"
        q.help_text = f"e.g. India, United States, United Kingdom, European Union, APAC, or Middle East. (Determines statutory holiday calendars and data residency boundaries)."
    elif qid == "q_onprem_footprint":
        q.prompt = f"Does **{proj_name}** require connectivity or hybrid integration with on-premise servers, local databases, or edge networks?"
        q.help_text = f"e.g. Pure Cloud (Zero on-prem lag), Hybrid VPN / ExpressRoute / DirectConnect, or Fully Air-Gapped On-Premise."
    elif qid == "q_subscription_isolation":
        q.prompt = f"What cloud subscription / account isolation and tenant architecture is required for **{proj_name}** on {cloud_val}?"
        q.help_text = f"e.g. Dedicated Non-Prod & Prod Subscriptions (Recommended), Shared Existing Subscription, or Multi-Tenant SaaS isolation."
    elif qid == "q_hadr_tier":
        q.prompt = f"What High Availability (HA) uptime SLA percentage (99.5%–99.99%) and Disaster Recovery (DR) RTO/RPO targets must **{proj_name}** guarantee? (NFR-2)"
        q.help_text = f"e.g. Standard HA 99.5% (RTO 4h, RPO 1h), Mission-Critical 99.9%+, Zone Redundancy, or Basic Single-Instance 99.0%."
    elif qid == "q_foundation_llm":
        q.prompt = f"Which AI foundation model, ML engine, or deterministic algorithmic framework will power **{proj_name}**?"
        q.help_text = f"e.g. Azure OpenAI GPT-4o, AWS Bedrock Claude 3.5, GCP Vertex Gemini, Self-Hosted Open-Weights (Llama 3), or Deterministic Business Logic / Rule Engine."
    elif qid == "q_grounding_mode":
        q.prompt = f"What search indexing, vector retrieval, or data grounding architecture will **{proj_name}** utilize on {cloud_val}?"
        q.help_text = f"e.g. Hybrid Vector + BM25 Full-Text Search ({cloud_val} AI Search / OpenSearch / pgvector), Relational SQL Indexing, or Direct API Fetching."
    elif qid == "q_doc_processing":
        q.prompt = f"What document parsing, file OCR, or structured data ingestion pipeline is required for **{proj_name}**?"
        q.help_text = f"e.g. Digital PDF & Office Forms, Scanned OCR Multi-Page Vision Processing, CSV/Parquet Batches, or Pure REST API Payloads."
    elif qid == "q_named_users":
        q.prompt = f"How many total named employees, internal operators, and stakeholders will have active accounts in **{proj_name}**?"
        q.help_text = f"e.g., 500 Total Employees (Standard Enterprise Benchmark), 200 Users, 1,000 Users, or 10,000+ Enterprise Scale."
    elif qid == "q_concurrent_users":
        q.prompt = f"What is the expected peak concurrent user load during high-traffic windows for **{proj_name}**?"
        q.help_text = f"e.g., 100 Peak Concurrent Users (Standard 20% concurrency ratio benchmark for {users_val} named users)."
    elif qid == "q_daily_requests":
        q.prompt = f"What performance latency SLA (<2.0s response) and daily transaction throughput are required for **{proj_name}**? (NFR-1)"
        q.help_text = f"e.g., Strict SLA (<2.0s Page Load, <500ms API response, 95% requests), Standard (35-100 actions/day for HR tools), or High-Throughput (50,000+ req/day)."
    elif qid == "q_multi_pass_policy":
        q.prompt = f"What multi-pass verification, business rule validation, or guardrail policy should **{proj_name}** enforce?"
        q.help_text = f"e.g. Dual-Pass Verification on critical approval actions, Deterministic Business Validation Rules, or Single-Pass with Fallback."
    elif qid == "q_parser_delimiters":
        q.prompt = f"What immutable audit trail logging and event traceability standards must **{proj_name}** enforce? (NFR-6)"
        q.help_text = f"e.g. Structured Immutable Audit Logs (Actor, Action, Timestamp, Previous Status, New Status, Request ID), SIEM forwarding, and 7-year retention."
    elif qid == "q_approval_gate":
        q.prompt = f"Who is the designated Executive Sponsor and Business SME sign-off authority for **{proj_name}** gate approvals?"
        q.help_text = f"Identifies the single named decision-maker authority for {proj_name} BRD sign-off and milestone delivery handover."

    return q

def get_current_question(session: ProjectSession) -> Optional[QuestionItem]:
    """
    Dynamic Question Generator:
    1. Returns None if >= 95% of the 32 domains are filled and clear.
    2. If any domain is generic/vague, generates a targeted clarification question asking exactly what is missing.
    3. Otherwise, returns the next missing domain in priority order, dynamically contextualized for the project.
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
        q_clar = QuestionItem(
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
        return contextualize_question_for_session(q_clar, session)
        
    # 2. Pick next highest-priority missing domain and contextualize dynamically
    if comp["missing_domains"]:
        return contextualize_question_for_session(comp["missing_domains"][0], session)
        
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
    "standard", "default", "standard cloud", "some data", "whatever works",
    "some ai", "some tool", "a tool", "for our company", "for our business", "we want some"
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
        
    # 13. Reference Document Clarification Questions (Q001-Q052)
    # Q002: Cloud Account / Subscription
    if "existing account" in raw or "non production" in raw or "non-prod" in raw:
        session.answers["q_Q002"] = AnswerItem(question_id="q_Q002", question_title="[Q002] Cloud Account / Subscription", answer="Existing Account is present. It's PoC so we are going to use only non-production subscription.")
        session.answers["Q002"] = session.answers["q_Q002"]
        filled_keys.append("q_Q002")
        
    # Q007: Data Residency Sign-off
    if "india" in raw and ("residency" in raw or "region" in raw):
        session.answers["q_Q007"] = AnswerItem(question_id="q_Q007", question_title="[Q007] Data Residency Sign-Off", answer="India-based regions only, signed off by Legal.")
        session.answers["Q007"] = session.answers["q_Q007"]
        filled_keys.append("q_Q007")
        
    # Q008: Search Product
    if "azure ai search" in raw or "managed search" in raw or "vector store" in raw:
        session.answers["q_Q008"] = AnswerItem(question_id="q_Q008", question_title="[Q008] Search Product", answer="The selection is open, and a managed search and vector store native to Microsoft Azure (Azure AI Search) is used.")
        session.answers["Q008"] = session.answers["q_Q008"]
        filled_keys.append("q_Q008")
        
    # Q009: Secret & Key Management
    if "key vault" in raw or "platform-managed" in raw or "cmk" in raw:
        session.answers["q_Q009"] = AnswerItem(question_id="q_Q009", question_title="[Q009] Secret & Key Management", answer="Platform-managed encryption with Azure Key Vault; customer-managed keys deferred to production.")
        session.answers["Q009"] = session.answers["q_Q009"]
        filled_keys.append("q_Q009")

    # Q011: Staging Environments
    if "dev, test" in raw or "uat" in raw:
        session.answers["q_Q011"] = AnswerItem(question_id="q_Q011", question_title="[Q011] Environments Scope", answer="Dev, Test and UAT environments are needed in non-production subscription.")
        session.answers["Q011"] = session.answers["q_Q011"]
        filled_keys.append("q_Q011")

    # Q012: Procurement Wait
    if "3 days" in raw or "waiting time" in raw:
        session.answers["q_Q012"] = AnswerItem(question_id="q_Q012", question_title="[Q012] Procurement Wait", answer="Waiting time is 3 Days. Completed before planned start date.")
        session.answers["Q012"] = session.answers["q_Q012"]
        filled_keys.append("q_Q012")

    # Q014: Sample Contracts Volume
    if "100 for each category" in raw or "100 samples" in raw or "600 total" in raw or "100 per category" in raw:
        session.answers["q_Q014"] = AnswerItem(question_id="q_Q014", question_title="[Q014] Sample Contracts Volume", answer="100 for each category (approx 600 total), covering standard, negotiated, and known problem contracts.")
        session.answers["Q014"] = session.answers["q_Q014"]
        filled_keys.append("q_Q014")

    # Q018: 3-Tier Status Arbiter
    if "agree" in raw and ("management approval" in raw or "not agree" in raw or "arbiter" in raw):
        session.answers["q_Q018"] = AnswerItem(question_id="q_Q018", question_title="[Q018] Status Arbiter Authority", answer="A nominated legal lead at PVR INOX is the final arbiter for assessment classification (Agree, Agree with Mgmt Approval, Not Agree).")
        session.answers["Q018"] = session.answers["q_Q018"]
        filled_keys.append("q_Q018")

    # Q019: Acceptance Definition
    if "95%" in raw or "traceability" in raw:
        session.answers["q_Q019"] = AnswerItem(question_id="q_Q019", question_title="[Q019] Acceptance Criteria", answer="Technical success metrics: ≥95% classification/extraction accuracy and 100% clause traceability.")
        session.answers["Q019"] = session.answers["q_Q019"]
        filled_keys.append("q_Q019")

    # Q021: Human Review Assistant Mode
    if "human checking" in raw or "human review" in raw or "assistant" in raw:
        session.answers["q_Q021"] = AnswerItem(question_id="q_Q021", question_title="[Q021] Human Review Policy", answer="All findings in this phase are reviewed by a person; the solution is treated as an assistant, not an autonomous decision maker.")
        session.answers["Q021"] = session.answers["q_Q021"]
        filled_keys.append("q_Q021")

    # Q027: Machine-Readable Digital vs Scanned OCR
    if "searchable digital" in raw or "digital files" in raw or "digital and machine-readable" in raw:
        session.answers["q_Q027"] = AnswerItem(question_id="q_Q027", question_title="[Q027] Document Digitization Format", answer="Contracts are digital and machine-readable; scanned or handwritten originals are out of scope for this phase.")
        session.answers["Q027"] = session.answers["q_Q027"]
        filled_keys.append("q_Q027")

    # Q036: Corporate SSO
    if "single sign-on" in raw or "sso" in raw or "entra id" in raw:
        session.answers["q_Q036"] = AnswerItem(question_id="q_Q036", question_title="[Q036] Single Sign-On Identity", answer="Corporate single sign-on (Microsoft Entra ID) is used for the demonstration interface.")
        session.answers["Q036"] = session.answers["q_Q036"]
        filled_keys.append("q_Q036")

    # Q044: Executive Sponsor SPOC
    if "nithin" in raw or "arora" in raw or "executive sponsor" in raw:
        session.answers["q_Q044"] = AnswerItem(question_id="q_Q044", question_title="[Q044] Executive Sponsor", answer="Nithin Arora is the executive sponsor and single signatory for decision gate acceptance.")
        session.answers["Q044"] = session.answers["q_Q044"]
        filled_keys.append("q_Q044")

    # Q045: Workshop SME SPOC
    if "jitender" in raw or "verma" in raw or "sme spoc" in raw:
        session.answers["q_Q045"] = AnswerItem(question_id="q_Q045", question_title="[Q045] Workshop SME SPOC", answer="For all queries Jitender Verma will act as the SPOC, coordinating legal and procurement SME availability.")
        session.answers["Q045"] = session.answers["q_Q045"]
        filled_keys.append("q_Q045")

    # Q052: Governance SPOC
    if "gaurav" in raw or "governance spoc" in raw or "approvals spoc" in raw:
        session.answers["q_Q052"] = AnswerItem(question_id="q_Q052", question_title="[Q052] Governance Approvals SPOC", answer="Gaurav is the SPOC for IT governance, security, and data access approvals.")
        session.answers["Q052"] = session.answers["q_Q052"]
        filled_keys.append("q_Q052")
        
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
    
    tpl_conf = JSONQuestionnaireEngine.calculate_template_confidence(session.answers)
    
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
            "is_gate_passed": is_ready,
            "template_confidence_score": tpl_conf.get("score", total_score),
            "template_confidence_band": tpl_conf.get("band", "Ready for review"),
            "total_applicable_template_questions": tpl_conf.get("total_applicable_questions", 0)
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
        is_vague_client = has_vague_marker or any(w in text for w in [
            "some ai", "some tool", "a tool", "for our company", "for our business", 
            "we want some", "ai tool", "an ai", "help us", "build something", "make an ai"
        ]) or text in ["unknown", "na", "none", "tbd", "idk"] or len(text) < 3
        
        if is_vague_client:
            return True, "🏢 **Could you share the company / client name or working project title?** *(e.g., 'Apex Logistics — Cargo Tracking AI' or 'PVR INOX — Contract Intelligence')*", [
                {"label": "Use Standard Working Title", "value": "Enterprise Client — AI Automation Platform"}
            ]
        return False, "", []
        
    if q.id == "q_problem":
        words = text.split()
        if len(words) < 3 or text in ["unknown", "na", "none", "tbd", "idk"]:
            return True, "🎯 **Could you describe the main business problem, manual bottlenecks, and objectives for this project?** *(e.g., 'Employees manually apply for leave in spreadsheets causing slow HR approvals and lack of visibility')*", []
        return False, "", []

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
        "escalat", "ask architect", "ask the architect", "architect decide", "architect recommendation",
        "let architect answer", "technical architect", "solutions architect", "delegate", "not sure ask tech",
        "architect should answer", "forward to architect", "send to architect", "let tech decide",
        "let architect decide", "architect review", "architect advice"
    ]) or raw_lower.strip() in ["architect", "solutions architect", "technical architect"]
    
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

    # Check if user specifically wants to review/ask all questions from the reference document (Sheet 10 Q001-Q052)
    is_ref_doc_query = any(k in raw_lower for k in [
        "all the possible questions", "all possible questions", "questions mentioned in reference",
        "reference document", "sheet 10", "q001", "clarification questions", "ask all questions",
        "ask me all questions", "all 52 questions", "52 questions", "more details about project"
    ])

    if is_ref_doc_query:
        unanswered_ref_q = None
        for ref_q in REFERENCE_DOC_QUESTIONS_52:
            clean_ref_id = ref_q.id.replace("q_", "")
            if ref_q.id not in session.answers and clean_ref_id not in session.answers:
                unanswered_ref_q = ref_q
                break
        if not unanswered_ref_q:
            unanswered_ref_q = REFERENCE_DOC_QUESTIONS_52[0]
            
        content = (
            "📋 **Reference Document Clarification Questionnaire (Q001–Q052 Activated):**\n\n"
            "I have loaded all **52 granular clarifying and scoping questions** from the reference document (*Sheet `10 QUESTIONS`*) and the **36-section questionnaire template** to elicit deep, rigorous project specifications for your BRD and deterministic effort calculation:\n\n"
            "🔹 **1. Key Decision Gates & Cloud Boundaries (Blockers & High Priority: Q001–Q012, Q038, Q039, Q044–Q046):**\n"
            "• `Q001`: Approved & mandated cloud platform(s)\n"
            "• `Q002`: Existing cloud account/subscription container vs new dedicated non-prod\n"
            "• `Q003` & `Q007`: Country data residency boundaries & legal sign-off authority\n"
            "• `Q004` & `Q005`: Multi-cloud role division, private network links & egress transfer cost\n"
            "• `Q006`: Approved AI model vendor list & third-party restrictions\n"
            "• `Q008`: Mandated search index product (Azure AI Search, OpenSearch, etc.)\n"
            "• `Q010`: Post-handover operational support team & platform familiarity\n"
            "• `Q011`: Staging environment count & isolation (Dev, Test, UAT, Prod, DR)\n"
            "• `Q012`: Procurement, licensing & commercial waiting period lead time\n"
            "• `Q044`: Single named executive sponsor for decision gate sign-off *(e.g. Nithin Arora)*\n"
            "• `Q045`: Named legal/business SMEs & weekly workshop commitment *(e.g. Jitender Verma)*\n"
            "• `Q046`: Accuracy vs human review effort & timeline trade-off authority\n\n"
            "🔹 **2. Functional Scope & Document Intelligence (Q013–Q030):**\n"
            "• `Q013` & `Q014`: In-scope contract categories & sample count per category *(100/category)*\n"
            "• `Q015`: Validation sample volume vs eventual live production corpus *(50,000 documents)*\n"
            "• `Q016` & `Q017`: Contract clauses to extract & contracting principles documentation status\n"
            "• `Q018`: Single named arbiter for 3-tier classification (*Agree, Agree with Mgmt Approval, Not Agree*)\n"
            "• `Q019` & `Q020`: Acceptance accuracy benchmark (≥95%) & golden test dataset confirmation\n"
            "• `Q021` & `Q022`: 100% human review policy & unreadable document exception handling\n"
            "• `Q023` & `Q024`: Risk register format & Day-1 risk dashboard reporting questions\n"
            "• `Q025` & `Q026`: 4 user persona roles & language support scope\n"
            "• `Q027` & `Q028`: Machine-readable digital PDFs vs scanned OCR & parent-child amendment linking\n"
            "• `Q029` & `Q030`: Authoritative repository location & sample dataset release authorization\n\n"
            "🔹 **3. Non-Functional Requirements, Security & Compliance (Q009, Q031–Q037, Q040–Q043):**\n"
            "• `Q009`: Secret management & Platform-managed vs Customer-Managed Keys (CMEK)\n"
            "• `Q031` & `Q032`: PII masking policy & data confidentiality classification\n"
            "• `Q033` & `Q034`: External regulatory obligations & source clause traceability retention\n"
            "• `Q035` & `Q036`: 12-month data retention schedule & Corporate SSO login (Entra ID)\n"
            "• `Q037` & `Q038`: Multi-tenant business function data segregation & blob ingestion connectivity\n"
            "• `Q040`, `Q041`, `Q042`: Dashboard concurrency, batch processing SLA & single-instance failover\n"
            "• `Q043`: Security review / VAPT prerequisites before data ingestion\n\n"
            "🔹 **4. Operations, FinOps BoM & Phase 2 Roadmap (Q047–Q052):**\n"
            "• `Q047`: Existing spreadsheet / disconnected document process baseline\n"
            "• `Q048` & `Q049`: Business calendar blackout dates & remote delivery constraints\n"
            "• `Q050`: Live solution cloud operating cost estimate FinOps BoM ($645/mo)\n"
            "• `Q051`: Phase 2 vision (workflow automation, approval routing, production integrations)\n"
            "• `Q052`: Prerequisite data access, security & governance approvals SPOC *(e.g. Gaurav)*\n\n"
            "---\n\n"
            f"### 🎯 Let's begin with **{unanswered_ref_q.title}**:\n\n"
            f"**{unanswered_ref_q.prompt}**\n\n"
            f"*(Suggested Default: `{unanswered_ref_q.default_value}`)*"
        )
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=content,
            timestamp=datetime.now().strftime("%I:%M %p"),
            question_context=unanswered_ref_q,
            hitl_options=[{"label": opt.label, "value": opt.value} for opt in unanswered_ref_q.options]
        )
        return msg, False

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

    # Handle active clarification or requirement accumulation state
    if session.clarification_state and session.clarification_state.get("question_id") in [q.id, clean_target_id]:
        clarification_mode = session.clarification_state.get("mode")
        
        # 1. Human-Centric Multi-Turn Requirement Accumulation
        if clarification_mode == "ACCUMULATING_REQUIREMENTS":
            accumulated_items: List[str] = session.clarification_state.get("items", [])
            clean_input = user_input.strip()
            lower_input = clean_input.lower()
            
            is_end_signal = any(p in lower_input for p in [
                "that covers all requirements", "that covers everything", "that covers it", 
                "that's all", "thats all", "that is all", "that's it", "thats it", "that is it",
                "no more", "no other", "end of requirements", "it is end", "done", "continue",
                "next", "proceed", "no", "nope", "nothing else", "all set", "ready", "finish",
                "covers all", "covers everything", "end"
            ]) and not any(add_kw in lower_input for add_kw in ["also", "plus", "additionally", "another", "and we need", "as well"])
            
            is_add_prompt_click = any(w in lower_input for w in ["add another requirement", "add another", "add more", "plus requirement", "enter another"])
            
            if is_add_prompt_click and not len(clean_input.split()) > 4:
                # User clicked "Add another requirement" button - prompt them gently
                content = (
                    f"👉 **Please enter your next functional requirement, workflow, or feature for {q.title}:**\n\n"
                    f"*(e.g., 'Real-time inventory lookup via ERP REST API' or 'Store opening hours and directions FAQ')*"
                )
                msg = ChatMessage(
                    sender="agent",
                    persona="AI_AGENT",
                    content=content,
                    timestamp=datetime.now().strftime("%I:%M %p"),
                    question_context=q
                )
                return msg, False
            
            if is_end_signal:
                # Finalize all accumulated requirements
                if len(accumulated_items) > 1:
                    final_synthesized_requirement = "; ".join(accumulated_items)
                    bullets_summary = "\n".join([f"• *{item}*" for item in accumulated_items])
                elif accumulated_items:
                    final_synthesized_requirement = accumulated_items[0]
                    bullets_summary = f"• *{accumulated_items[0]}*"
                else:
                    final_synthesized_requirement = q.default_value
                    bullets_summary = f"• *{q.default_value}*"
                
                session.clarification_state = None
                session.answers[clean_target_id] = AnswerItem(
                    question_id=clean_target_id,
                    question_title=q.title.replace("Clarification: ", ""),
                    answer=final_synthesized_requirement,
                    is_default=False,
                    ambiguity_count=0,
                    hitl_confirmed=True,
                    notes=f"Synthesized from {len(accumulated_items)} accumulated user requirements."
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
                        f"✅ **Recorded complete scope for {q.title} ({len(accumulated_items)} requirements):**\n"
                        f"{bullets_summary}\n\n"
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
            else:
                # Add this new requirement to accumulation list
                cleaned_item = clean_input
                # Strip leading prefixes like "also", "and", "plus" if present
                cleaned_item = re.sub(r'^(also|plus|and|additionally|we also need|we need|requirement:)\s+', '', cleaned_item, flags=re.IGNORECASE).strip()
                if cleaned_item and cleaned_item not in accumulated_items:
                    accumulated_items.append(cleaned_item)
                session.clarification_state["items"] = accumulated_items
                
                formatted_list = "\n".join([f"📌 **{i+1}.** *\"{item}\"*" for i, item in enumerate(accumulated_items)])
                content = (
                    f"👍 **Added to requirements!** Here is what we have captured so far for **{q.title}**:\n\n"
                    f"{formatted_list}\n\n"
                    f"❓ **Do you have more functional requirements, features, or workflows to add, or does this cover the scope for now?**"
                )
                hitl_opts = [
                    {"label": "✅ That covers all requirements / Continue", "value": "That covers all requirements / Continue"},
                    {"label": "➕ Add another requirement", "value": "➕ Add another requirement"}
                ]
                msg = ChatMessage(
                    sender="agent",
                    persona="AI_AGENT",
                    content=content,
                    timestamp=datetime.now().strftime("%I:%M %p"),
                    question_context=QuestionItem(
                        id=f"{clean_target_id}_clarification",
                        title=f"Requirements Scope: {q.title}",
                        prompt=content,
                        type="dropdown",
                        options=[
                            QuestionOption(value="That covers all requirements / Continue", label="✅ That covers all requirements / Continue", description="Proceed to next domain"),
                            QuestionOption(value="➕ Add another requirement", label="➕ Add another requirement", description="Enter additional functional requirement or feature")
                        ],
                        default_value="That covers all requirements / Continue",
                        category=q.category,
                        priority=q.priority,
                        help_text="Confirm if this is the full scope or add more requirements."
                    ),
                    hitl_options=hitl_opts
                )
                return msg, False
        
        # 2. General Ambiguity Clarification
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
                        f"✅ **Recorded Target Users:** *{prompt_audience}*\n\n"
                        f"---\n\n"
                        f"🎯 **Primary Capability:**\n\n"
                        f"**What primary task or service should the AI handle for {prompt_audience}?**\n\n"
                        f"*(Please select a capability below or describe your custom requirement:)*"
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

    # If this is a requirement/scope question and user gave a custom statement, ask if they have more requirements before moving on
    if clean_target_id in ["q_problem", "q_legal_categories"] and not is_option_match and len(user_input.split()) < 35:
        session.clarification_state = {
            "mode": "ACCUMULATING_REQUIREMENTS",
            "question_id": clean_target_id,
            "items": [normalized_input]
        }
        content = (
            f"Got it! I've noted that requirement for **{q.title}**:\n\n"
            f"📌 **1.** *\"{normalized_input}\"*\n\n"
            f"❓ **Do you have more functional requirements, features, or workflows to add, or does this cover the scope for now?**"
        )
        hitl_opts = [
            {"label": "✅ That covers all requirements / Continue", "value": "That covers all requirements / Continue"},
            {"label": "➕ Add another requirement", "value": "➕ Add another requirement"}
        ]
        msg = ChatMessage(
            sender="agent",
            persona="AI_AGENT",
            content=content,
            timestamp=datetime.now().strftime("%I:%M %p"),
            question_context=QuestionItem(
                id=f"{clean_target_id}_clarification",
                title=f"Requirements Scope: {q.title}",
                prompt=content,
                type="dropdown",
                options=[
                    QuestionOption(value="That covers all requirements / Continue", label="✅ That covers all requirements / Continue", description="Proceed to next domain"),
                    QuestionOption(value="➕ Add another requirement", label="➕ Add another requirement", description="Enter additional functional requirement or feature")
                ],
                default_value="That covers all requirements / Continue",
                category=q.category,
                priority=q.priority,
                help_text="Confirm if this is the full scope or add more requirements."
            ),
            hitl_options=hitl_opts
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
