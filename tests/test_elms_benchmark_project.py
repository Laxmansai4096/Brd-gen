import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.models import ProjectSession, AnswerItem, BRDDocument, RequirementItem
from backend.agent_discovery import (
    process_user_answer,
    extract_and_fill_domains_from_text,
    calculate_discovery_confidence
)
from backend.agent_planner import (
    generate_brd,
    generate_task_estimates,
    aggregate_role_efforts,
    build_project_phases,
    evaluate_schedule_feasibility,
    generate_technical_components_dynamic,
    generate_sizing_and_bom_dynamic,
    generate_day_wise_schedule
)
from backend.canonical_generator import (
    build_canonical_requirements,
    build_capabilities_catalog,
    build_canonical_data_flows,
    build_calculation_ledger
)
from backend.export_generator import (
    generate_word_brd,
    generate_pdf_brd,
    generate_excel_financial_model,
    generate_jira_backlog_csv
)
from backend.pptx_generator import create_presentation_deck
import os

def test_elms_benchmark_project_full_flow():
    """
    Test Case: Employee Leave Management System (ELMS)
    - 500 employees, 100 peak concurrent users
    - Web application on Microsoft Azure (India Geography, 9.0 hrs/day)
    - MVP Tier, 8 weeks target duration
    - 25 Functional Requirements (FR-001 to FR-025)
    - 15 Business Rules (BR-001 to BR-015)
    - 12 Assumptions (A-001 to A-012 with A-011 Needs Verification)
    - 8 Risks, 8 Dependencies, 4 User Personas, 2 Integrations
    """
    session = ProjectSession(session_id="elms-benchmark-session")
    
    # 1. Provide Domain 1: Client & Project Initiative
    process_user_answer(session, "Employee Leave Management System (ELMS)", persona="CLIENT")
    
    # 2. Provide Domain 2: Problem Statement & Core Business Objectives
    prob_text = (
        "Build a web-based leave management system for a 500-employee company. "
        "The system will allow employees to request and track leave, managers to approve/reject requests, "
        "and HR to manage leave policies, company holidays, and compliance reporting."
    )
    process_user_answer(session, prob_text, persona="CLIENT")
    
    # 3. Provide Domain 3: In-Scope Functional Capabilities & Workflows
    scope_text = (
        "The solution will cover the end-to-end employee leave management lifecycle, including employee leave balance and history, "
        "leave request creation, leave validation, manager approval/rejection, leave cancellation, leave policy and leave-type administration, "
        "holiday calendar management, leave balance updates, email notifications, HR reporting, search/filtering, role-based access control, "
        "and audit logging.\n\n"
        "The primary workflows in scope are:\n"
        "1. Employee views leave balance and history\n"
        "2. Employee submits a leave request\n"
        "3. System validates leave dates, balance, and overlapping requests\n"
        "4. Manager reviews and approves/rejects the request with comments\n"
        "5. System updates leave balance after approval\n"
        "6. Employee cancels an eligible request\n"
        "7. HR configures leave types, policies, and holidays\n"
        "8. HR searches and reports on leave activity\n"
        "9. System sends email notifications for leave events\n"
        "10. System records all relevant leave transactions for audit purposes\n\n"
        "Out of scope: payroll processing, salary calculation, attendance tracking, recruitment, performance management, "
        "native mobile application, biometric integration, travel/expense management, external customer access, and AI chatbot."
    )
    process_user_answer(session, scope_text, persona="CLIENT")
    
    # Fill remaining configuration parameters
    session.answers["q_client"] = AnswerItem(question_id="q_client", question_title="Client", answer="Enterprise Client | Employee Leave Management System (ELMS)")
    session.answers["q_problem"] = AnswerItem(question_id="q_problem", question_title="Problem", answer=prob_text)
    session.answers["q_legal_categories"] = AnswerItem(question_id="q_legal_categories", question_title="Capabilities", answer=scope_text)
    session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Delivery Tier", answer="MVP")
    session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer="Microsoft Azure")
    session.answers["q_geography"] = AnswerItem(question_id="q_geography", question_title="Geography", answer="India")
    session.answers["q_duration"] = AnswerItem(question_id="q_duration", question_title="Duration", answer="8.0")
    session.answers["q_named_users"] = AnswerItem(question_id="q_named_users", question_title="Named Users", answer="500")
    session.answers["q_concurrent_users"] = AnswerItem(question_id="q_concurrent_users", question_title="Concurrent Users", answer="100")
    session.answers["q_integrations"] = AnswerItem(question_id="q_integrations", question_title="Integrations", answer="2 Integrations (INT-001 Corporate Identity SSO, INT-002 Corporate Email)")
    
    # Generate BRD
    brd = generate_brd(session)
    
    # Assertions on Metadata & Scope
    assert "Employee Leave Management" in brd.project_title or "ELMS" in brd.project_title
    assert brd.delivery_tier == "MVP"
    assert brd.cloud_platform == "Microsoft Azure"
    assert len(brd.technical_components) == 6
    assert len(brd.sizing_bom) >= 5
    assert len(brd.project_phases) == 18
    assert len(brd.role_efforts) == 12
    
    # Assertions on Schedule & Feasibility
    assert brd.reference_duration_weeks == 8.0
    assert brd.schedule_feasibility.is_feasible is True
    assert brd.total_person_days > 0
    assert brd.total_labour_cost_usd > 0
    
    # Export Generation Verification
    os.makedirs("exports", exist_ok=True)
    docx_path = generate_word_brd(brd, "exports/elms_brd.docx")
    assert os.path.exists(docx_path)
    
    pdf_path = generate_pdf_brd(brd, "exports/elms_brd.pdf")
    assert os.path.exists(pdf_path)
    
    xlsx_path = generate_excel_financial_model(brd, "exports/elms_financial.xlsx")
    assert os.path.exists(xlsx_path)
    
    pptx_path = create_presentation_deck(brd, "exports/elms_pitch.pptx")
    assert os.path.exists(pptx_path)
    
    jira_path = generate_jira_backlog_csv(brd, "exports/elms_jira.csv")
    assert os.path.exists(jira_path)
    
    print("\n--- ELMS BENCHMARK TEST PASSED SUCCESSFULLY ---")
    print(f"Project Title: {brd.project_title}")
    print(f"Delivery Tier: {brd.delivery_tier} | Cloud: {brd.cloud_platform} | Geography: India (9.0 hrs/day)")
    print(f"Total Effort: {brd.total_person_days} Person-Days | Total Cost: ${brd.total_labour_cost_usd:,.2f}")
    print(f"Duration: {brd.total_duration_weeks} Weeks | Feasibility: {brd.schedule_feasibility.binding_constraint}")
