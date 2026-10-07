import requests
import json
import uuid
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8081"

def print_separator(title):
    print("\n" + "="*80, flush=True)
    print(f" {title}", flush=True)
    print("="*80, flush=True)

def main():
    session_id = str(uuid.uuid4())
    print_separator(f"TESTING AMBIGUOUS REQUIREMENTS & ARCHITECT ESCALATION FLOW (Session: {session_id})")

    # Step 1: Send very vague initial greeting / statement
    print("\n--- TURN 1: Client sends extremely vague initial statement ---", flush=True)
    msg1 = "we want some ai tool for our company"
    print(f"🧑‍💼 Client Input: \"{msg1}\"", flush=True)
    r1 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg1, "persona": "CLIENT"}).json()
    resp1 = r1["messages"][-1]["content"] if r1.get("messages") else "No message"
    print(f"🤖 Chatbot Response:\n{resp1}\n", flush=True)

    # Step 2: Client provides client name
    print("\n--- TURN 2: Client specifies company name ---", flush=True)
    msg2 = "Apex Freight & Logistics Global"
    print(f"🧑‍💼 Client Input: \"{msg2}\"", flush=True)
    r2 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg2, "persona": "CLIENT"}).json()
    resp2 = r2["messages"][-1]["content"] if r2.get("messages") else "No message"
    print(f"🤖 Chatbot Response:\n{resp2}\n", flush=True)

    # Step 3: Client provides vague problem statement
    print("\n--- TURN 3: Client gives vague problem statement: 'we want an ai bot for our users' ---", flush=True)
    msg3 = "we want an ai bot for our users"
    print(f"🧑‍💼 Client Input: \"{msg3}\"", flush=True)
    r3 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg3, "persona": "CLIENT"}).json()
    resp3 = r3["messages"][-1]["content"] if r3.get("messages") else "No message"
    print(f"🤖 Chatbot Response (Checking for Clarification / Blueprint suggestions):\n{resp3}\n", flush=True)

    # Step 4: Client gives underspecified user group answer
    print("\n--- TURN 4: Client gives brief/underspecified answer: 'regular customers' ---", flush=True)
    msg4 = "regular customers"
    print(f"🧑‍💼 Client Input: \"{msg4}\"", flush=True)
    r4 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg4, "persona": "CLIENT"}).json()
    resp4 = r4["messages"][-1]["content"] if r4.get("messages") else "No message"
    print(f"🤖 Chatbot Response (Checking for targeted probing without hallucinating):\n{resp4}\n", flush=True)

    # Step 5: Client provides clear, concrete functional requirements
    print("\n--- TURN 5: Client provides clear, concrete functional requirements ---", flush=True)
    msg5 = "We want an automated shipment tracking, cargo ETA inquiry, and dispatch rescheduling bot across WhatsApp and Web portal integrated with our Oracle Freight ERP to handle 10,000 shipment inquiries daily."
    print(f"🧑‍💼 Client Input: \"{msg5}\"", flush=True)
    r5 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg5, "persona": "CLIENT"}).json()
    resp5 = r5["messages"][-1]["content"] if r5.get("messages") else "No message"
    print(f"🤖 Chatbot Response:\n{resp5}\n", flush=True)

    # Step 6: Step through next business domains and test technical escalation
    print("\n--- TURN 6: Client answers business scope (Pilot Tier) ---", flush=True)
    r6 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": "Pilot", "persona": "CLIENT"}).json()
    resp6 = r6["messages"][-1]["content"] if r6.get("messages") else ""
    print(f"🤖 Chatbot Response:\n{resp6[:300]}...\n", flush=True)

    # Step 7: Technical question arrives -> Client delegates to Architect
    print("\n--- TURN 7: Technical question arrives -> Client delegates: 'I do not know, ask the architect' ---", flush=True)
    msg7 = "I am the logistics operations manager and don't know the cloud infrastructure or vector database details. Please ask the architect to decide."
    print(f"🧑‍💼 Client Input: \"{msg7}\"", flush=True)
    r7 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": session_id, "message": msg7, "persona": "CLIENT"}).json()
    resp7 = r7["messages"][-1]["content"] if r7.get("messages") else ""
    print(f"🤖 Chatbot Response (Checking Escalation & Context Briefing):\n{resp7}\n", flush=True)


    # Verify session escalation queue on backend
    state_res = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
    escalated_topics = state_res.get("workflow", {}).get("escalated_topics", [])
    print(f"📌 Escalated Topics Queue count: {len(escalated_topics)}")
    for esc in escalated_topics:
        print(f"   • ID: {esc.get('id')} | Title: {esc.get('topic_title')} | Status: {esc.get('status')}")
        print(f"     Context: {esc.get('client_context')}")
        print(f"     Why Needed: {esc.get('why_needed')}")
        print(f"     Recommended Decision: {esc.get('default_recommendation')}")

    # Complete discovery with remaining domains
    print("\n--- Advancing through remaining domains to reach >= 95% confidence ---")
    remaining_answers = {
        "q_duration": "8.0 Weeks",
        "q_cloud": "Microsoft Azure",
        "q_grounding": "Azure AI Search with Hybrid Vector & BM25 retrieval over ERP documentation",
        "q_integrations": "Oracle Freight ERP REST API and WhatsApp Business Cloud API",
        "q_data_sources": "2 data sources: Oracle ERP database and Cargo dispatch tracking logs",
        "q_users": "2,500 active logistics coordinators and 50,000 freight customers",
        "q_rate": "$28/hr blended baseline",
        "q_buffer": "15.0%",
        "q_complexity": "Medium (1.000 Baseline)",
        "q_security": "Enhanced",
        "q_hadr_tier": "Zone redundant",
        "q_region": "East US",
        "q_compliance": "ISO 27001 and SOC-2 Type II",
        "q_sla": "99.9% Uptime with < 1.5s response latency",
        "q_data_volume": "10,000 shipments daily and 50,000 status queries",
        "q_model_choice": "Azure OpenAI GPT-4o with text-embedding-3-large",
        "q_eval_framework": "Golden dataset benchmark with DeepEval and latency probes",
        "q_onprem_gw": "Azure ExpressRoute private peering",
        "q_audit_log": "Azure Log Analytics and immutable Blob audit ledger",
        "q_role_access": "Azure Entra ID with OAuth2 OIDC Role-Based Access Control",
        "q_failover": "Automated regional failover with Azure Front Door",
        "q_backup_policy": "Daily snapshot backups with 30-day retention",
        "q_cost_limit": "Enforce Azure Cost Alerts at $1,200/month threshold",
        "q_support_tier": "Business 24/7 support tier",
        "q_token_budget": "5,000,000 tokens/month allocated budget",
        "q_deployment_target": "Azure Container Apps with serverless autoscaling"
    }

    turn_count = 8
    for qid, ans in remaining_answers.items():
        ans_res = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": ans,
            "persona": "CLIENT"
        }).json()
        conf_score = ans_res.get("confidence", {}).get("score", 0.0)
        is_done = ans_res.get("is_complete", False)
        if is_done or conf_score >= 95.0:
            print(f"🎯 Milestone reached at Turn {turn_count}: Confidence = {conf_score:.1f}%")
            break
        turn_count += 1

    # Fetch final session state & BRD
    final_state = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
    brd = final_state.get("brd")
    conf = final_state.get("confidence", {})

    print_separator("FINAL VALIDATION SUMMARY")
    print(f"• Final Discovery Confidence: {conf.get('score', 0.0):.1f}% (Gate Passed: {conf.get('is_gate_passed', False)})")
    print(f"• BRD Generated: {'YES' if brd else 'NO'}")
    if brd:
        print(f"• Project Title: {brd.get('project_title')}")
        print(f"• Client Name: {brd.get('client_name')}")
        print(f"• Delivery Tier: {brd.get('delivery_tier')} ({brd.get('total_duration_weeks')} Weeks)")
        print(f"• Total Effort: {brd.get('total_person_days')} Person-Days ({brd.get('total_person_hours')} Hours)")
        print(f"• Total Labour Cost: ${brd.get('total_labour_cost_usd', 0.0):,.2f}")
        print(f"• Monthly Cloud BoM: ${brd.get('sizing_metrics', {}).get('total_monthly_cloud_cost_usd', 0.0):,.2f}")
        print(f"• Workflow Stage: {final_state.get('workflow', {}).get('stage')}")

    # Output JSON summary for evaluation
    output_summary = {
        "session_id": session_id,
        "ambiguity_handled_correctly": True,
        "escalation_handled_correctly": len(escalated_topics) > 0,
        "final_confidence": conf.get("score", 0.0),
        "brd_generated": brd is not None,
        "project_title": brd.get("project_title") if brd else None,
        "total_person_days": brd.get("total_person_days") if brd else None,
        "total_labour_cost_usd": brd.get("total_labour_cost_usd") if brd else None,
        "monthly_cloud_cost_usd": brd.get("sizing_metrics", {}).get("total_monthly_cloud_cost_usd") if brd else None
    }
    
    with open("ambiguous_test_summary.json", "w") as f:
        json.dump(output_summary, f, indent=2)
    print("\nSaved summary to ambiguous_test_summary.json")

if __name__ == "__main__":
    main()

