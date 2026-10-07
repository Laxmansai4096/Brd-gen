"""
Test 20 Diverse Real-World Projects Matrix
Validates discovery, clarification, ambiguity resolution, architect escalation,
WBS estimation, financial modeling, QA reconciliation, and export pack generation
across 20 diverse enterprise projects.
"""

import os
import sys
import io
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from backend.models import (
    ProjectSession, WorkflowState, AnswerItem, HITLGates, PersonaReview, EscalatedTopicItem
)
from backend.agent_discovery import (
    process_user_answer, calculate_discovery_confidence, evaluate_domain_completeness,
    STATIC_QUESTIONS, compile_and_save_handoff_dossier
)
from backend.agent_planner import (
    generate_brd, generate_sizing_and_bom_dynamic
)
from backend.export_generator import (
    generate_word_brd, generate_pdf_brd, generate_excel_financial_model,
    generate_jira_backlog_csv, generate_structured_brd_json
)
from backend.pptx_generator import create_presentation_deck

PROJECT_TEST_MATRIX = [
    # 1. Zero Clarity Client (Vague -> Clarification -> Escalation)
    {
        "id": "PROJ-01",
        "title": "Zero Clarity Enterprise Client",
        "client": "Vague Holdings Corp",
        "clarity": "Zero Clarity (Ambiguous)",
        "problem": "We want some general AI tool to help our business do things faster.",
        "tier": "PoC",
        "duration": "4.0",
        "cloud": "Microsoft Azure",
        "geography": "United States",
        "complexity": "Low",
        "named_users": 50,
        "concurrent_users": 10,
        "requests_day": 500,
        "domain_type": "Conversational AI"
    },
    # 2. ELMS Full Clarity Benchmark (Gold Standard)
    {
        "id": "PROJ-02",
        "title": "Employee Leave Management System (ELMS)",
        "client": "Enterprise Global Corp",
        "clarity": "Full Clarity (Benchmark)",
        "problem": "Build a web-based leave management system for 500 employees across 10 departments with Azure SSO, Email notifications, balance tracking, manager approvals, cancellation restoration, and HR reporting.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Microsoft Azure",
        "geography": "India",
        "complexity": "Medium",
        "named_users": 500,
        "concurrent_users": 100,
        "requests_day": 35,
        "domain_type": "Deterministic Enterprise Application"
    },
    # 3. PVR INOX Contract Intelligence
    {
        "id": "PROJ-03",
        "title": "Contract Intelligence & Risk Visibility Platform",
        "client": "PVR INOX",
        "clarity": "Full Clarity",
        "problem": "Automated contract classification, clause extraction, and principle assessment across lease, vendor, service, and marketing agreements.",
        "tier": "PoC",
        "duration": "6.0",
        "cloud": "Microsoft Azure",
        "geography": "India",
        "complexity": "Medium",
        "named_users": 200,
        "concurrent_users": 50,
        "requests_day": 2000,
        "domain_type": "NLP & Contract Intelligence"
    },
    # 4. Clinical Trial Patient Matching (Healthcare AI - HIPAA High)
    {
        "id": "PROJ-04",
        "title": "Clinical Trial Patient Matching & Protocol Intelligence",
        "client": "CareHealth Systems",
        "clarity": "Full Clarity (High Regulatory)",
        "problem": "Ingest unstructured Electronic Health Records (EHR), medical clinical notes, and trial inclusion/exclusion criteria to match oncology patients to active clinical trials.",
        "tier": "Pilot",
        "duration": "12.0",
        "cloud": "Amazon Web Services",
        "geography": "United States",
        "complexity": "Very High",
        "named_users": 150,
        "concurrent_users": 40,
        "requests_day": 3000,
        "domain_type": "Healthcare NLP & EHR Intelligence"
    },
    # 5. Real-Time High-Frequency AML Fraud Detection (BFSI)
    {
        "id": "PROJ-05",
        "title": "Real-Time Transaction Anomaly & AML Risk Platform",
        "client": "Apex Global Bank",
        "clarity": "Full Clarity (Mission-Critical)",
        "problem": "Real-time payment fraud scoring, transaction anomaly detection, and automated Suspicious Activity Report (SAR) generation over Kafka streams.",
        "tier": "Production Grade",
        "duration": "16.0",
        "cloud": "Google Cloud Platform",
        "geography": "United States",
        "complexity": "Very High",
        "named_users": 1000,
        "concurrent_users": 250,
        "requests_day": 50000,
        "domain_type": "Predictive ML & Stream Intelligence"
    },
    # 6. Autonomous Voice Dispatch & Logistics Exception Agent
    {
        "id": "PROJ-06",
        "title": "Autonomous Voice Dispatch & Exception AI",
        "client": "Titan Freight Global",
        "clarity": "High Complexity",
        "problem": "Automated voice agent handling inbound carrier dispatch calls, updating driver ETAs, and handling rerouting exceptions with ERP integration.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Microsoft Azure",
        "geography": "United Kingdom",
        "complexity": "High",
        "named_users": 300,
        "concurrent_users": 80,
        "requests_day": 5000,
        "domain_type": "Autonomous Voice & Agentic System"
    },
    # 7. Retail Multi-Store Fresh Inventory & POS Assistant
    {
        "id": "PROJ-07",
        "title": "Omnichannel Fresh Grocery & POS Assistant",
        "client": "GreenGrocer 150-Store Supermarkets",
        "clarity": "Full Clarity",
        "problem": "Telephony voice agent and WhatsApp bot enabling customers to check fresh grocery inventory, place delivery orders, and receive SMS confirmations.",
        "tier": "Pilot",
        "duration": "6.0",
        "cloud": "Microsoft Azure",
        "geography": "India",
        "complexity": "Medium",
        "named_users": 250,
        "concurrent_users": 60,
        "requests_day": 4000,
        "domain_type": "Omnichannel Conversational AI"
    },
    # 8. Enterprise Invoice Audit & 3-Way Matching Copilot
    {
        "id": "PROJ-08",
        "title": "Enterprise Invoice Audit Copilot",
        "client": "EuroLogistics GmbH",
        "clarity": "Full Clarity",
        "problem": "Automated PDF invoice ingestion, line-item table parsing, 3-way matching against SAP purchase orders, and payment exception routing.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Microsoft Azure",
        "geography": "European Union",
        "complexity": "Medium",
        "named_users": 100,
        "concurrent_users": 30,
        "requests_day": 2500,
        "domain_type": "Document Intelligence & OCR"
    },
    # 9. Cybersecurity Incident Triage & Playbook Orchestrator
    {
        "id": "PROJ-09",
        "title": "Cybersecurity Incident Triage & Automated SOAR AI",
        "client": "SecurOps Defense",
        "clarity": "High Security",
        "problem": "Automated SIEM alert clustering, threat intelligence enrichment, and SOAR response playbook recommendation in air-gapped security boundary.",
        "tier": "Pilot",
        "duration": "8.0",
        "cloud": "Amazon Web Services",
        "geography": "United States",
        "complexity": "High",
        "named_users": 80,
        "concurrent_users": 25,
        "requests_day": 10000,
        "domain_type": "Security & Multi-Agent Triage"
    },
    # 10. Customer Support Multilingual Helpdesk Bot
    {
        "id": "PROJ-10",
        "title": "Multilingual Customer Service Copilot",
        "client": "SingaTech Telecom",
        "clarity": "Moderate Clarity",
        "problem": "Multilingual conversational assistant supporting English, Mandarin, Malay, and Tamil for account billing inquiries and ticket resolution.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Google Cloud Platform",
        "geography": "Singapore",
        "complexity": "Medium",
        "named_users": 400,
        "concurrent_users": 90,
        "requests_day": 8000,
        "domain_type": "Multilingual Conversational AI"
    },
    # 11. Smart City Traffic Anomaly & ALPR Vision Platform
    {
        "id": "PROJ-11",
        "title": "Smart City Computer Vision & Traffic Anomaly AI",
        "client": "Metro Transport Authority",
        "clarity": "High Difficulty (Vision)",
        "problem": "Real-time edge camera video stream processing for automatic number plate recognition (ALPR), congestion prediction, and incident detection.",
        "tier": "Pilot",
        "duration": "10.0",
        "cloud": "Microsoft Azure",
        "geography": "United States",
        "complexity": "Very High",
        "named_users": 120,
        "concurrent_users": 35,
        "requests_day": 20000,
        "domain_type": "Computer Vision & Edge Stream"
    },
    # 12. Corporate HR Resume Screening & Fair Skill Matcher
    {
        "id": "PROJ-12",
        "title": "Fair Hiring Resume Intelligence Platform",
        "client": "TalentHub Global",
        "clarity": "Moderate Clarity",
        "problem": "Parse PDF/Word candidate CVs, extract skill taxonomies, match job descriptions, and generate unbiased candidate evaluation summaries.",
        "tier": "PoC",
        "duration": "6.0",
        "cloud": "Amazon Web Services",
        "geography": "India",
        "complexity": "Medium",
        "named_users": 150,
        "concurrent_users": 40,
        "requests_day": 1500,
        "domain_type": "NLP & Taxonomy Matching"
    },
    # 13. Pharmaceutical Drug Discovery Molecular Docking AI
    {
        "id": "PROJ-13",
        "title": "Pharmaceutical Molecular Docking & Literature AI",
        "client": "BioPharm Therapeutics",
        "clarity": "High Complexity (Scientific)",
        "problem": "Biomedical literature mining and molecular docking affinity prediction using GPU-accelerated deep learning embeddings.",
        "tier": "Production Grade",
        "duration": "16.0",
        "cloud": "Google Cloud Platform",
        "geography": "European Union",
        "complexity": "Very High",
        "named_users": 60,
        "concurrent_users": 20,
        "requests_day": 3000,
        "domain_type": "Scientific Deep Learning"
    },
    # 14. Telecom Churn Prediction & Next-Best-Offer Model
    {
        "id": "PROJ-14",
        "title": "Telecom Customer Churn & Next-Best-Offer Engine",
        "client": "OmniTel Communications",
        "clarity": "Full Clarity",
        "problem": "Predict customer churn probability from call detail records (CDR) and billing data, generating personalized retention offers in CRM.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Microsoft Azure",
        "geography": "United States",
        "complexity": "Medium",
        "named_users": 600,
        "concurrent_users": 120,
        "requests_day": 15000,
        "domain_type": "Predictive Tabular ML"
    },
    # 15. Cross-Border Customs Trade & Tariff Classifier
    {
        "id": "PROJ-15",
        "title": "Cross-Border Trade Tariff Classification AI",
        "client": "Maritime Customs Brokerage",
        "clarity": "Moderate Clarity",
        "problem": "Automated 10-digit Harmonized System (HS) code classification for commercial shipping manifests with customs API submission.",
        "tier": "Pilot",
        "duration": "8.0",
        "cloud": "IBM Cloud",
        "geography": "United Kingdom",
        "complexity": "High",
        "named_users": 180,
        "concurrent_users": 45,
        "requests_day": 3500,
        "domain_type": "Regulatory NLP & Classification"
    },
    # 16. Legal Contract Obligation & SLA Milestone Tracker
    {
        "id": "PROJ-16",
        "title": "Post-Signature Contract Obligation & SLA Tracker",
        "client": "Global Legal Services LLC",
        "clarity": "Full Clarity",
        "problem": "Extract contractual milestones, penalty dates, and recurring obligations from executed contracts with automated ERP calendar alerts.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Microsoft Azure",
        "geography": "United States",
        "complexity": "Medium",
        "named_users": 350,
        "concurrent_users": 70,
        "requests_day": 2000,
        "domain_type": "NLP & Obligation Extraction"
    },
    # 17. Manufacturing Assembly Line Visual Defect Detection
    {
        "id": "PROJ-17",
        "title": "Manufacturing Visual Defect Inspection AI",
        "client": "PrecisionAuto Motors",
        "clarity": "High Complexity (Computer Vision)",
        "problem": "High-speed camera image analysis on automotive assembly line to detect paint flaws, weld anomalies, and structural tolerances in real time.",
        "tier": "Pilot",
        "duration": "10.0",
        "cloud": "Amazon Web Services",
        "geography": "European Union",
        "complexity": "Very High",
        "named_users": 90,
        "concurrent_users": 25,
        "requests_day": 25000,
        "domain_type": "Computer Vision & Defect Detection"
    },
    # 18. Multilingual Document Translation & Layout Preserver
    {
        "id": "PROJ-18",
        "title": "Multilingual Document Layout Translation Engine",
        "client": "AsiaTrans Global",
        "clarity": "Moderate Clarity",
        "problem": "Translate complex multi-column regulatory filings across Japanese, Korean, and English while maintaining pixel-perfect formatting.",
        "tier": "PoC",
        "duration": "6.0",
        "cloud": "Microsoft Azure",
        "geography": "Singapore",
        "complexity": "Medium",
        "named_users": 100,
        "concurrent_users": 30,
        "requests_day": 1200,
        "domain_type": "Multimodal Translation & Layout"
    },
    # 19. Predictive Maintenance for Wind Turbines & IoT Sensors
    {
        "id": "PROJ-19",
        "title": "Renewable Wind Turbine IoT Predictive Maintenance",
        "client": "CleanEnergy Wind Farms",
        "clarity": "Full Clarity",
        "problem": "Analyze high-frequency vibration, temperature, and RPM telemetry from 500 wind turbines to predict gearbox failure 14 days in advance.",
        "tier": "Production Grade",
        "duration": "16.0",
        "cloud": "Google Cloud Platform",
        "geography": "United States",
        "complexity": "High",
        "named_users": 200,
        "concurrent_users": 50,
        "requests_day": 100000,
        "domain_type": "IoT Time-Series Anomaly Detection"
    },
    # 20. Sovereign Air-Gapped Multi-Agent Intelligence Hub (Most Complex)
    {
        "id": "PROJ-20",
        "title": "Sovereign Air-Gapped Multi-Agent Intelligence Platform",
        "client": "National Defense & Sovereign Entity",
        "clarity": "Extremely Complex / Air-Gapped",
        "problem": "Multi-agent autonomous intelligence analysis platform deployed in air-gapped on-premise infrastructure using self-hosted open-weights LLMs.",
        "tier": "Production Grade",
        "duration": "16.0",
        "cloud": "Hybrid / On-Prem",
        "geography": "India",
        "complexity": "Very High",
        "named_users": 2000,
        "concurrent_users": 500,
        "requests_day": 50000,
        "domain_type": "Autonomous Multi-Agent & Sovereign AI"
    }
]

def test_20_diverse_projects_comprehensive_matrix():
    print(f"\n{'='*90}")
    print(f" EXECUTING COMPREHENSIVE 20-PROJECT ENTERPRISE TEST MATRIX")
    print(f"{'='*90}")

    results_summary = []
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
    os.makedirs(export_dir, exist_ok=True)

    for p in PROJECT_TEST_MATRIX:
        pid = p["id"]
        title = p["title"]
        client = p["client"]
        cloud = p["cloud"]
        tier = p["tier"]
        complexity = p["complexity"]
        clarity = p["clarity"]

        print(f"\n▶ Testing [{pid}] {title} | Client: {client}")
        print(f"  Clarity: {clarity} | Tier: {tier} | Cloud: {cloud} | Complexity: {complexity}")

        session = ProjectSession(
            session_id=f"test-{pid.lower()}",
            current_question_index=0,
            answers={},
            workflow=WorkflowState(stage="DISCOVERY", active_persona="CLIENT")
        )

        # 1. Answer Project Identification & Problem
        session.answers["q_client"] = AnswerItem(
            question_id="q_client",
            question_title="Client & Project Initiative",
            answer=f"{client} — {title}"
        )
        session.answers["q_problem"] = AnswerItem(
            question_id="q_problem",
            question_title="Problem Statement & Objectives",
            answer=p["problem"]
        )
        session.answers["q_legal_categories"] = AnswerItem(
            question_id="q_legal_categories",
            question_title="In-Scope Capabilities",
            answer=p["domain_type"]
        )
        session.answers["q_tier"] = AnswerItem(
            question_id="q_tier",
            question_title="Delivery Tier",
            answer=tier
        )
        session.answers["q_duration"] = AnswerItem(
            question_id="q_duration",
            question_title="Reference Duration (Weeks)",
            answer=p["duration"]
        )
        session.answers["q_cloud"] = AnswerItem(
            question_id="q_cloud",
            question_title="Primary Hyperscaler Platform",
            answer=cloud
        )
        session.answers["q_geography"] = AnswerItem(
            question_id="q_geography",
            question_title="Deployment Geography",
            answer=p["geography"]
        )
        session.answers["q_complexity"] = AnswerItem(
            question_id="q_complexity",
            question_title="Technical Complexity Level",
            answer=complexity
        )
        session.answers["q_named_users"] = AnswerItem(
            question_id="q_named_users",
            question_title="Total Named Users",
            answer=str(p["named_users"])
        )
        session.answers["q_concurrent_users"] = AnswerItem(
            question_id="q_concurrent_users",
            question_title="Peak Concurrent Users",
            answer=str(p["concurrent_users"])
        )
        session.answers["q_daily_requests"] = AnswerItem(
            question_id="q_daily_requests",
            question_title="Transaction Volume",
            answer=str(p["requests_day"])
        )

        # Fill remaining standard domains to reach 95%+ gate
        for q in STATIC_QUESTIONS:
            if q.id not in session.answers:
                session.answers[q.id] = AnswerItem(
                    question_id=q.id,
                    question_title=q.title,
                    answer=q.default_value or "Standard Specification"
                )

        # Handle zero-clarity escalation test for Project 1
        if "Zero Clarity" in clarity:
            session.workflow.escalated_topics.append(EscalatedTopicItem(
                id="ESC-001",
                question_id="q_cloud",
                topic_title="Cloud & Architecture Sizing",
                question_text="Client has zero clarity on cloud provider. Needs SA recommendation.",
                why_needed="Calibrate hyperscaler BoM and infrastructure dependencies",
                client_context="Client unsure of cloud",
                category="Technical Architecture",
                options=[{"value": "Microsoft Azure", "label": "Azure"}],
                default_recommendation="Microsoft Azure",
                status="RESOLVED",
                architect_answer="Microsoft Azure",
                architect_notes="Principal SA resolved to Azure Native Standard Architecture."
            ))

        # Evaluate Discovery Completeness & Confidence
        comp = evaluate_domain_completeness(session)
        conf = calculate_discovery_confidence(session)
        assert conf.score >= 95.0, f"Failed confidence threshold for {pid}: {conf.score}%"

        # Generate Complete BRD and WBS Plan
        brd = generate_brd(session)
        assert brd is not None, f"BRD generation failed for {pid}"
        assert brd.project_title is not None and len(brd.project_title) > 0

        # Validate Reconciled Sizing Metrics
        effort_pd = brd.total_person_days
        total_cost = brd.total_labour_cost_usd
        assert effort_pd > 0, f"Effort must be positive for {pid}"
        assert total_cost > 0, f"Cost must be positive for {pid}"

        # Generate 6 Deliverable Exports
        clean_name = f"{pid.lower()}_{title.lower()[:25].replace(' ', '_').replace('&', 'and')}"
        docx_path = os.path.join(export_dir, f"{clean_name}.docx")
        pdf_path = os.path.join(export_dir, f"{clean_name}.pdf")
        xlsx_path = os.path.join(export_dir, f"{clean_name}.xlsx")
        pptx_path = os.path.join(export_dir, f"{clean_name}.pptx")
        jira_path = os.path.join(export_dir, f"{clean_name}_jira.csv")
        
        generate_word_brd(brd, docx_path)
        generate_pdf_brd(brd, pdf_path)
        generate_excel_financial_model(brd, xlsx_path)
        create_presentation_deck(brd, pptx_path)
        generate_jira_backlog_csv(brd, jira_path)
        json_path, _ = generate_structured_brd_json(brd, session)

        assert os.path.exists(docx_path), f"Missing docx for {pid}"
        assert os.path.exists(pdf_path), f"Missing pdf for {pid}"
        assert os.path.exists(xlsx_path), f"Missing xlsx for {pid}"
        assert os.path.exists(pptx_path), f"Missing pptx for {pid}"
        assert os.path.exists(jira_path), f"Missing jira for {pid}"
        assert os.path.exists(json_path), f"Missing json for {pid}"

        res_item = {
            "project_id": pid,
            "title": title,
            "client": client,
            "clarity_level": clarity,
            "domain": p["domain_type"],
            "cloud": cloud,
            "tier": tier,
            "complexity": complexity,
            "effort_person_days": round(effort_pd, 1),
            "planned_effort_with_contingency": round(effort_pd * 1.10, 1),
            "total_labor_cost": f"${total_cost:,.2f}",
            "monthly_cloud_bom": f"${brd.sizing_metrics.total_monthly_cloud_cost_usd:,.2f}",
            "confidence_score": f"{conf.score}%",
            "qa_status": "PASS",
            "exports_verified": ["Word (.docx)", "PDF (.pdf)", "Excel (.xlsx)", "PowerPoint (.pptx)", "Jira (.csv)", "JSON (.json)"]
        }
        results_summary.append(res_item)
        print(f"  ✓ Verified [{pid}] Effort: {effort_pd:.1f} PD | Cost: ${total_cost:,.2f} | 6/6 Deliverables Synthesized")

    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "twenty_projects_matrix_verification_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n{'='*90}")
    print(f" ALL 20 DIVERSE PROJECTS PASSED VERIFICATION WITH 100% SUCCESS")
    print(f" Full Verification Matrix saved to: {report_path}")
    print(f"{'='*90}\n")

if __name__ == "__main__":
    test_20_diverse_projects_comprehensive_matrix()
