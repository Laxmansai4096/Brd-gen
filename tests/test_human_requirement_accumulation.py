import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_human_like_requirement_accumulation():
    # 1. Initialize session
    res = client.get('/api/session')
    assert res.status_code == 200
    session_id = res.json()['session_id']
    
    # 2. Answer Domain 1 (Client / Project Name)
    res_d1 = client.post('/api/chat', json={
        "session_id": session_id,
        "message": "Retail Store Inc — Automated Ordering & Voice Assistant",
        "persona": "CLIENT"
    })
    assert res_d1.status_code == 200
    
    # 3. User provides Requirement #1 (Single requirement)
    res_req1 = client.post('/api/chat', json={
        "session_id": session_id,
        "message": "We need automated voice calling for taking orders over the phone.",
        "persona": "CLIENT"
    })
    assert res_req1.status_code == 200
    data_req1 = res_req1.json()
    last_msg1 = data_req1['messages'][-1]['content']
    
    assert "Do you have more functional requirements" in last_msg1 or "cover the scope" in last_msg1
    assert "automated voice calling" in last_msg1.lower()
    
    # 4. User provides Requirement #2
    res_req2 = client.post('/api/chat', json={
        "session_id": session_id,
        "message": "Also we need real-time store inventory check and store hours FAQ assistant.",
        "persona": "CLIENT"
    })
    assert res_req2.status_code == 200
    data_req2 = res_req2.json()
    last_msg2 = data_req2['messages'][-1]['content']
    
    assert "1." in last_msg2
    assert "2." in last_msg2
    assert "inventory" in last_msg2.lower()
    
    # 5. User signals end of requirements
    res_done = client.post('/api/chat', json={
        "session_id": session_id,
        "message": "That covers all requirements / Continue",
        "persona": "CLIENT"
    })
    assert res_done.status_code == 200
    data_done = res_done.json()
    last_msg_done = data_done['messages'][-1]['content']
    
    assert "Recorded complete scope" in last_msg_done
    
    # Verify the stored answer consolidated both requirements
    cur_answers = data_done.get("answers", {})
    assert "q_problem" in cur_answers
    stored_val = cur_answers["q_problem"]["answer"]
    assert "automated voice calling" in stored_val.lower()
    assert "inventory" in stored_val.lower()

if __name__ == "__main__":
    test_human_like_requirement_accumulation()
