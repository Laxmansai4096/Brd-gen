import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app
from backend.agent_discovery import MASTER_DOMAIN_TEMPLATE, evaluate_domain_completeness

client = TestClient(app)

def test_dynamic_master_template_and_clarification_gate():
    print("\n--- TEST: DYNAMIC DISCOVERY ENGINE & 95% GATE VALIDATION ---")
    
    # 1. Verify Master Domain Template contains all 32 domains
    assert len(MASTER_DOMAIN_TEMPLATE) == 32, f"Expected 32 domains in master template, got {len(MASTER_DOMAIN_TEMPLATE)}"
    print("[OK] Master Domain Template contains exactly 32 architecture & business domains.")

    # 2. Initialize new session
    res = client.get('/api/session')
    assert res.status_code == 200
    session_id = res.json()['session_id']
    print(f"[OK] Session initialized: {session_id}")

    # 3. Test Vague Answer -> Targeted Clarification Trigger
    chat_res1 = client.post('/api/chat', json={
        "session_id": session_id,
        "message": "dunno maybe some chatbot",
        "persona": "CLIENT"
    })
    assert chat_res1.status_code == 200
    data1 = chat_res1.json()
    cur_q1 = data1.get("current_question")
    assert cur_q1 is not None, "Expected clarification question for vague answer"
    print(f"[OK] Vague answer correctly triggered dynamic clarification on: '{cur_q1.get('title')}'")

    # 4. Test Multi-Field Simultaneous Extraction
    rich_statement = (
        "We are PVR INOX building a Contract Intelligence platform on Microsoft Azure in 6.0 weeks "
        "covering 6 categories including Lease, Vendor, Service, Facilities, Technology, Marketing "
        "with 6 components C001-C006 and 15% standby capacity in India."
    )
    chat_res2 = client.post('/api/chat', json={
        "session_id": session_id,
        "message": rich_statement,
        "persona": "CLIENT"
    })
    assert chat_res2.status_code == 200
    data2 = chat_res2.json()
    answers = data2.get("answers", {})
    
    assert "q_cloud" in answers and answers["q_cloud"]["answer"] == "Microsoft Azure"
    assert "q_legal_categories" in answers and "Lease" in answers["q_legal_categories"]["answer"]
    assert "q_duration" in answers and "6.0" in answers["q_duration"]["answer"]
    assert "q_buffer_strategy" in answers and "15%" in answers["q_buffer_strategy"]["answer"]
    assert "q_geography" in answers and "India" in answers["q_geography"]["answer"]
    
    print(f"[OK] Multi-field extraction filled {len(answers)} domains in one single turn!")
    print(f"     Coverage: {data2['confidence']['score']}%")

    # 5. Progressively answer remaining domains to test 95% Completion Gate
    for turn in range(35):
        sess_data = client.get(f'/api/session?session_id={session_id}').json()
        cur_q = sess_data.get('current_question')
        if not cur_q or sess_data.get('has_brd'):
            break
        
        q_id = cur_q.get('id', '')
        if 'arch' in q_id or 'sec' in q_id:
            del_res = client.post('/api/workflow/delegate-architect', json={
                "session_id": session_id,
                "question_id": q_id
            })
            assert del_res.status_code == 200
        else:
            opt_val = cur_q.get('default_value') or (cur_q.get('options', [{}])[0].get('value')) or "Confirmed standard requirement"
            chat_res = client.post('/api/chat', json={
                "session_id": session_id,
                "message": opt_val,
                "persona": "CLIENT"
            })
            assert chat_res.status_code == 200

    # 6. Verify 95%+ Gate Passed and BRD generated
    final_sess = client.get(f'/api/session?session_id={session_id}').json()
    assert final_sess['has_brd'] is True, "Expected BRD to be automatically generated upon 95% gate pass"
    assert final_sess['confidence']['score'] >= 95.0, f"Expected confidence >= 95.0%, got {final_sess['confidence']['score']}%"
    
    print(f"[OK] 95%+ Completion Gate Successfully Passed ({final_sess['confidence']['score']}%)!")
    print(f"[OK] BRD Title: {final_sess['brd']['project_title']} | Effort: {final_sess['brd']['total_person_days']} Person-Days")
    print("\n--- ALL DYNAMIC DISCOVERY & GATING TESTS PASSED WITH 100% SUCCESS ---")

if __name__ == "__main__":
    test_dynamic_master_template_and_clarification_gate()
