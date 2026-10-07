import requests
import json
import time
import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

BASE_URL = "http://127.0.0.1:8081"

def ensure_server():
    try:
        res = requests.get(f"{BASE_URL}/api/session", timeout=1.0)
        if res.status_code == 200:
            return
    except Exception:
        pass
    print(f"Starting server at {BASE_URL} in background thread...")
    import threading
    import uvicorn
    from app import app
    def _run():
        config = uvicorn.Config(app=app, host="127.0.0.1", port=8081, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        server.run()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(2.5)

def run_usecase():
    ensure_server()
    print(f"Connecting to Project Planner MVP at {BASE_URL}...")
    
    # 1. Initialize session
    session_res = requests.get(f"{BASE_URL}/api/session")
    session_data = session_res.json()
    session_id = session_data["session_id"]
    print(f"Session initialized: {session_id}")
    
    # PVR INOX Core Specific Answers
    custom_answers = {
        "q_client": "PVR INOX | Contract Intelligence & Risk Visibility Platform",
        "q_tier": "PoC",
        "q_problem": "PVR INOX signs contracts across lease, vendor, service, facilities, technology and marketing categories. Manual review takes 4-5 business days per contract and deviations from approved standards are not caught consistently. Findings live in disconnected spreadsheets with zero traceability to source clauses.",
        "q_cloud": "Microsoft Azure",
        "q_geography": "India",
        "q_duration": "6.0",
        "q_ai_interventions": "Multi-Pass Agentic Extraction & Classification",
        "q_complexity": "Medium",
        "q_compliance": "Internal policy only"
    }
    
    step = 0
    data = {"has_brd": False}
    
    while not data.get("has_brd") and step < 40:
        step += 1
        s_res = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
        cur_q = s_res.get("current_question")
        if not cur_q:
            break
            
        qid = cur_q.get("id")
        ans = custom_answers.get(qid)
        if not ans:
            ans = cur_q.get("default_value")
            if not ans and cur_q.get("options"):
                ans = cur_q["options"][0].get("value")
            if not ans:
                ans = "Default Option"
                
        print(f"\n--- Submitting Answer Q{step} [{cur_q.get('title')}]: {str(ans)[:60]}... ---")
        payload = {
            "session_id": session_id,
            "message": str(ans),
            "selected_option": str(ans)
        }
        res = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60.0)
        data = res.json()
        
        if data.get("has_brd"):
            print("\n>>> BRD & Project Plan generated successfully by Agent 2!")
            brd = data["brd"]
            print(f"• Project Title: {brd['project_title']}")
            print(f"• Client / Account: {brd['client_name']}")
            print(f"• Delivery Tier: {brd['delivery_tier']} ({brd['total_duration_weeks']} Weeks)")
            print(f"• Total Effort: {brd['total_person_days']} person-days (${brd['total_labour_cost_usd']:,.2f} at $30/hr)")
            print(f"• Monthly Cloud BoM: ${brd['sizing_metrics']['total_monthly_cloud_cost_usd']:,.2f}/mo")
            print(f"• Day-Wise Schedule Tasks: {len(brd.get('day_wise_schedule', []))} days planned")
            break
            
        time.sleep(0.1)
        
    # Check Handoff Dossier
    handoff_res = requests.get(f"{BASE_URL}/api/handoff?session_id={session_id}")
    handoff_data = handoff_res.json()
    print("\n[Handoff Dossier Status]:", handoff_data.get("status"))
    print("[Handoff File Path]:", handoff_data.get("file_path"))
    
    # Export Deck
    os.makedirs("exports", exist_ok=True)
    export_res = requests.get(f"{BASE_URL}/api/export-pptx?session_id={session_id}")
    if export_res.status_code == 200:
        deck_filename = f"exports/Project_Plan_PVR_INOX_{session_id[:8]}.pptx"
        with open(deck_filename, "wb") as f:
            f.write(export_res.content)
        print(f"Exported generated project plan deck: {deck_filename}")
    else:
        print(f"Deck export returned status code {export_res.status_code}")
        
    print("\n Use case execution complete on localhost:8081!")

if __name__ == "__main__":
    run_usecase()
