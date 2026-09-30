import requests
import json
import time

BASE_URL = "http://127.0.0.1:8088"

def run_usecase():
    print("Connecting to Project Planner MVP at", BASE_URL)
    
    # 1. Initialize session
    session_res = requests.get(f"{BASE_URL}/api/session")
    session_data = session_res.json()
    session_id = session_data["session_id"]
    print(f"Session initialized: {session_id}")
    
    # Discovery answers based on text.txt
    discovery_answers = [
        # Q1: Client & Engagement Name
        "PVR INOX | Contract Intelligence & Risk Visibility Platform",
        # Q2: Delivery Tier
        "PoC",
        # Q3: Problem Statement
        "PVR INOX signs contracts across lease, vendor, service, facilities, technology and marketing categories. Manual review takes 4-5 business days per contract and deviations from approved standards are not caught consistently. Findings live in disconnected spreadsheets with zero traceability to source clauses.",
        # Q4: Primary Cloud
        "Microsoft Azure",
        # Q5: Geography
        "India",
        # Q6: Duration
        "6 Weeks",
        # Q7: AI Interventions
        "Multi-Pass Agentic Extraction & Classification",
        # Q8: Volume & Sizing
        "600 representative contracts across 6 categories (100 per category), 200 named users, 50 concurrent users, 2,000 requests/day, single instance HA/DR.",
        # Q9: Compliance & Security
        "Internal policy only, standard enterprise security, platform-managed encryption, corporate Entra ID SSO, India data residency.",
        # Q10: Success Metrics
        "≥95% classification accuracy, ≥95% clause extraction rate, 100% traceability between findings and PDF page coordinates, and Agree / Agree with Mgmt Approval / Not Agree classification."
    ]
    
    for idx, ans in enumerate(discovery_answers):
        print(f"\n--- Submitting Answer {idx+1}/10 ---")
        payload = {
            "session_id": session_id,
            "message": ans,
            "selected_option": ans
        }
        res = requests.post(f"{BASE_URL}/api/chat", json=payload)
        data = res.json()
        print(f"Agent response status: {data.get('status')}")
        if data.get("has_brd"):
            print(">>> BRD and Project Plan generated successfully by Agent 2!")
            brd = data["brd"]
            print(f"Project Title: {brd['project_title']}")
            print(f"Total Effort: {brd['total_person_days']} person-days (${brd['total_labour_cost_usd']:,.2f} at $30/hr)")
            print(f"Total Duration: {brd['total_duration_weeks']} weeks")
            break
        time.sleep(0.5)
        
    # Check Handoff Dossier
    handoff_res = requests.get(f"{BASE_URL}/api/handoff?session_id={session_id}")
    handoff_data = handoff_res.json()
    print("\nHandoff Dossier Status:", handoff_data.get("status"))
    print("Handoff File Path:", handoff_data.get("file_path"))
    
    # Export Deck
    export_res = requests.get(f"{BASE_URL}/api/export-pptx?session_id={session_id}")
    if export_res.status_code == 200:
        deck_filename = f"exports/Project_Plan_PVR_INOX_{session_id[:8]}.pptx"
        with open(deck_filename, "wb") as f:
            f.write(export_res.content)
        print(f"Exported generated project plan deck: {deck_filename}")
    else:
        print(f"Deck export failed with status code {export_res.status_code}")
        
    print("\nUse case execution complete!")

if __name__ == "__main__":
    run_usecase()
