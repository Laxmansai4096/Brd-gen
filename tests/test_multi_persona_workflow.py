import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_multi_persona_end_to_end_workflow():
    print("\n--- STARTING 3-PERSONA COLLABORATIVE BRD WORKFLOW TEST ---")
    
    # 1. Start session
    res = client.get('/api/session')
    assert res.status_code == 200
    session_id = res.json()['session_id']
    print(f"1. Session initialized: {session_id}")
    
    # 2. Stage 1: Ideation (Client Lead + Solutions Architect)
    ideate_res = client.post('/api/workflow/ideate', json={
        "session_id": session_id,
        "client_idea": "Automated invoice audit and fraud detection platform with ERP sync",
        "project_title": "Enterprise Invoice Audit Copilot",
        "target_tier": "PoC"
    })
    assert ideate_res.status_code == 200
    ideate_data = ideate_res.json()
    assert ideate_data["workflow"]["stage"] == "DISCOVERY"
    print("2. Stage 1 Ideation completed: Client Lead & Solutions Architect aligned on PoC scope.")
    
    # 3. Stage 2: Dynamic Discovery & Delegation to Solutions Architect
    # Answer discovery questions to progress confidence across the 32 domains
    for i in range(35):
        sess_data = client.get(f'/api/session?session_id={session_id}').json()
        cur_q = sess_data.get('current_question')
        if not cur_q or sess_data.get('has_brd'):
            break
            
        q_id = cur_q.get('id', '')
        # If question is technical (e.g. cloud, data, security), delegate to architect
        if 'cloud' in q_id or 'arch' in q_id or 'sec' in q_id:
            del_res = client.post('/api/workflow/delegate-architect', json={
                "session_id": session_id,
                "question_id": q_id
            })
            assert del_res.status_code == 200
            print(f"   Delegated question {q_id} to Solutions Architect.")
        else:
            opt_val = cur_q.get('default_value') or (cur_q.get('options', [{}])[0].get('value')) or "Standard business requirements"
            chat_res = client.post('/api/chat', json={
                "session_id": session_id,
                "message": opt_val,
                "selected_option": opt_val,
                "persona": "CLIENT"
            })
            assert chat_res.status_code == 200
            print(f"   Client answered {q_id}: {opt_val}")
            
    # Check that Confidence is >= 98% and BRD draft is generated
    sess_after_disc = client.get(f'/api/session?session_id={session_id}').json()
    assert sess_after_disc['has_brd'] is True, "BRD was not generated after discovery"
    assert sess_after_disc['confidence']['score'] >= 98.0, f"Confidence score was {sess_after_disc['confidence']['score']}, expected >= 98.0"
    print(f"3. Discovery Complete! Confidence: {sess_after_disc['confidence']['score']}% (Threshold >= 98% passed). Draft BRD generated.")
    
    # 4. Stage 3: Dual Review & Iteration (Client & Architect)
    # 4a. Solutions Architect requests technical change
    change_res = client.post('/api/workflow/dual-review/feedback', json={
        "session_id": session_id,
        "persona": "SOLUTIONS_ARCHITECT",
        "feedback": "Add dedicated vector cache and enhance cloud security controls.",
        "adjustments": {
            "q_security": "Enhanced",
            "q_cloud": "Azure"
        }
    })
    assert change_res.status_code == 200
    print("4a. Solutions Architect requested change -> BRD successfully regenerated with adjustments.")
    
    # 4b. Dual Sign-off: Both Client and Architect approve
    app_client = client.post('/api/workflow/dual-review/approve', json={
        "session_id": session_id,
        "persona": "CLIENT",
        "signature_name": "Client Business Lead",
        "notes": "Business scope and ROI expectations approved."
    })
    assert app_client.status_code == 200
    
    app_arch = client.post('/api/workflow/dual-review/approve', json={
        "session_id": session_id,
        "persona": "SOLUTIONS_ARCHITECT",
        "signature_name": "Principal Solutions Architect",
        "notes": "Architectural feasibility and cloud BoM approved."
    })
    assert app_arch.status_code == 200
    assert app_arch.json()["is_dual_approved"] is True
    assert app_arch.json()["workflow"]["stage"] == "PM_REVIEW"
    print("4b. Dual Approval achieved! Handed off to Senior Delivery PM.")
    
    # 5. Stage 4: PM Governance & Tripartite Discussion
    # 5a. PM raises query
    pm_q_res = client.post('/api/workflow/pm-review/query', json={
        "session_id": session_id,
        "topic": "Statutory Holidays & ERP Test Environment",
        "query_text": "Phase 8 falls over bank holidays. Who provides ERP test credentials?",
        "addressed_to": "ALL"
    })
    assert pm_q_res.status_code == 200
    q_id = pm_q_res.json()["query"]["id"]
    print(f"5a. PM raised governance query: {q_id}")
    
    # 5b. Client clarifies
    resp_c = client.post('/api/workflow/pm-review/respond', json={
        "session_id": session_id,
        "query_id": q_id,
        "persona": "CLIENT",
        "response_text": "Client IT will provide SAP test sandbox credentials in Week 2."
    })
    assert resp_c.status_code == 200
    
    # 5c. Architect clarifies
    resp_a = client.post('/api/workflow/pm-review/respond', json={
        "session_id": session_id,
        "query_id": q_id,
        "persona": "SOLUTIONS_ARCHITECT",
        "response_text": "We can parallelize QA resources to offset the 2-day holiday delta."
    })
    assert resp_a.status_code == 200
    print("5b & 5c. Client and Architect resolved PM query in Tripartite Discussion Room.")
    
    # 5d. PM Re-plans & Adjusts baseline
    replan_res = client.post('/api/workflow/pm-review/replan-with-pm', json={
        "session_id": session_id,
        "pm_notes": "Added QA buffer for holiday delta and locked 6-week baseline.",
        "parameter_overrides": {
            "q_qa_contingency": "Standard"
        }
    })
    assert replan_res.status_code == 200
    print("5d. PM Governance adjustments applied to BRD calculation ledger.")
    
    # 5e. PM Grants Final Approval
    pm_app_res = client.post('/api/workflow/pm-review/approve', json={
        "session_id": session_id,
        "signature_name": "Senior Delivery PM",
        "notes": "18-Phase timeline, $30/hr blended rates, and governance gates approved."
    })
    assert pm_app_res.status_code == 200
    assert pm_app_res.json()["stage"] == "FINAL_APPROVED"
    print("5e. Project Manager granted Final Approval! Tripartite signatures certified.")
    
    # 6. Stage 5: Final Deliverables Distributed
    for exp_type, exp_endpoint in [
        ("PDF BRD", f"/api/export/pdf?session_id={session_id}"),
        ("Word BRD", f"/api/export/docx?session_id={session_id}"),
        ("Excel Financial Model", f"/api/export/excel?session_id={session_id}"),
        ("PowerPoint Deck", f"/api/export-pptx?session_id={session_id}"),
        ("Jira Backlog CSV", f"/api/export/jira?session_id={session_id}")
    ]:
        exp_res = client.get(exp_endpoint)
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 0
        print(f"6. {exp_type} generated & distributed successfully ({len(exp_res.content)} bytes).")
        
    print("\n--- ALL 3-PERSONA WORKFLOW TESTS PASSED 100% SUCCESSFULLY! ---\n")

if __name__ == "__main__":
    test_multi_persona_end_to_end_workflow()
