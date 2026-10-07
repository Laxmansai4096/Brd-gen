import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8081"

def test_retail_store_owner_simulation():
    print("=================================================================")
    print("STEP 1: RETAIL STORE OWNER SIMULATION (CLIENT + ARCHITECT)")
    print("=================================================================")
    
    # 1. Initialize session
    init_res = requests.get(f"{BASE_URL}/api/session")
    session_data = init_res.json()
    session_id = session_data["session_id"]
    print(f"[Client] Initialized session: {session_id}")
    
    # 2. Stage 1: Ideation (Retail Store Owner Idea)
    ideate_payload = {
        "session_id": session_id,
        "project_title": "FreshMart Supermarkets — AI Voice Ordering & Telephony Inquiries",
        "client_idea": (
            "We own a 150-store supermarket chain. Customers call to place fresh grocery delivery orders, "
            "ask about store inventory/hours, and track deliveries. We want to use Azure Communication Services (telephony/calling) "
            "and Azure OpenAI voice agents with speech-to-text to automatically handle phone calls, take grocery orders, "
            "check inventory via our POS/ERP, and send WhatsApp SMS order confirmation receipts. "
            "If the customer is angry or ordering custom butchery items, it must escalate to store human staff."
        ),
        "target_tier": "Pilot",
        "cloud_preference": "Microsoft Azure"
    }
    ideate_res = requests.post(f"{BASE_URL}/api/workflow/ideate", json=ideate_payload)
    print(f"[Client] Ideation Submitted -> HTTP {ideate_res.status_code}")
    
    # Step through all discovery questions to 95%+ confidence
    turn_idx = 0
    while turn_idx < 40:
        turn_idx += 1
        q_res = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
        if q_res.get("brd") or (q_res.get("confidence") and q_res["confidence"]["score"] >= 95.0):
            print(f"[SUCCESS] Reached {q_res['confidence']['score']}% confidence!")
            break
            
        cur_q = q_res.get("current_question")
        if not cur_q:
            break
            
        q_id = cur_q["id"]
        q_title = cur_q["title"]
        
        # Determine whether Client answers (Business / Scope / Sizing) or delegates to Architect (Technical)
        is_tech = any(k in q_id for k in ["cloud", "llm", "speech", "ocr", "security", "hadr", "retrieval", "vector", "pass", "infrastructure", "isolation"])
        
        if is_tech:
            print(f"[Client -> Architect] Escalating Technical Parameter '{q_title}' ({q_id}) to Solutions Architect...")
            del_res = requests.post(f"{BASE_URL}/api/workflow/delegate-architect", json={"session_id": session_id}).json()
            conf = del_res["confidence"]["score"]
            print(f"  --> Architect resolved with native Azure SKU. Confidence: {conf}%")
        else:
            # Business answers tailored for Retail Voice Ordering
            if "client" in q_id:
                ans = "FreshMart Supermarkets — AI Voice Ordering & Telephony Inquiries"
            elif "tier" in q_id:
                ans = "Pilot"
            elif "duration" in q_id:
                ans = "8.0"
            elif "docs" in q_id or "corpus" in q_id:
                ans = "25000"
            elif "reqs" in q_id or "query" in q_id:
                ans = "5000"
            elif "user" in q_id:
                ans = "150"
            elif "legal" in q_id or "categories" in q_id:
                ans = "Automated Phone Order Placement, Inventory Stock Check, Delivery Status, Escalation to Store Clerk"
            elif "compliance" in q_id:
                ans = "PCI-DSS Level 1 compliance for payment tokens and telephone recording privacy (SOC-2 Type II)"
            elif "grounding" in q_id or "rag" in q_id:
                ans = "Real-time POS Inventory API lookup + Azure AI Search product catalog grounding"
            elif "human" in q_id or "oversight" in q_id:
                ans = "Store managers review unfulfilled orders daily and handle live call transfers for high-value carts (> $200)"
            elif "buffer" in q_id:
                ans = "15% Shadow / Backup Capacity (Recommended)"
            elif "complexity" in q_id:
                ans = "Medium"
            elif "onprem" in q_id:
                ans = "No (Zero On-Premises Footprint)"
            else:
                ans = cur_q.get("default_value") or (cur_q.get("options", [{}])[0].get("value") if cur_q.get("options") else "Confirmed")
                
            print(f"[Client] Answering Business Domain '{q_title}' -> \"{ans}\"")
            ans_res = requests.post(f"{BASE_URL}/api/chat", json={
                "session_id": session_id,
                "message": str(ans),
                "persona": "CLIENT"
            }).json()
            conf = ans_res["confidence"]["score"]
            print(f"  --> Answer recorded. Confidence: {conf}%")
            
        if ans_res.get("brd") if not is_tech else del_res.get("brd"):
            print(f"[SUCCESS] BRD generated successfully! Confidence: {conf}% >= 95.0%")
            break

    # Get final session state
    final_sess = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
    brd = final_sess.get("brd")
    
    print("\n=================================================================")
    print("STEP 2: ARCHITECT BRIEFING & DUAL SIGN-OFF VERIFICATION")
    print("=================================================================")
    briefing_res = requests.get(f"{BASE_URL}/api/workflow/architect/briefing?session_id={session_id}").json()
    print("Architect Client Overview Dossier:")
    print(json.dumps(briefing_res.get("client_overview"), indent=2))
    
    # Dual Sign-off
    print("\nExecuting Dual Review approvals...")
    client_app = requests.post(f"{BASE_URL}/api/workflow/dual-review/approve", json={"session_id": session_id, "persona": "CLIENT"}).json()
    arch_app = requests.post(f"{BASE_URL}/api/workflow/dual-review/approve", json={"session_id": session_id, "persona": "SOLUTIONS_ARCHITECT"}).json()
    
    stage = arch_app["workflow"]["stage"]
    print(f"Workflow transitioned to Stage: {stage} (Project Manager Review)")
    
    return session_id, brd

def test_20_enterprise_projects_benchmark():
    print("\n=================================================================")
    print("STEP 3: 20 ENTERPRISE PROJECTS BENCHMARK PERFORMANCE SUITE")
    print("=================================================================")
    
    projects = [
        {"title": "Retail Chain Voice Ordering & Inventory AI", "tier": "Pilot", "cloud": "Microsoft Azure", "corpus": 25000, "reqs": 5000},
        {"title": "Freight Logistics Shipment ETA & Carrier Bot", "tier": "MVP", "cloud": "Amazon Web Services", "corpus": 100000, "reqs": 12000},
        {"title": "Hospital Emergency Triage & Bed Scheduling AI", "tier": "Production Grade", "cloud": "Microsoft Azure", "corpus": 50000, "reqs": 20000},
        {"title": "Fintech KYC Anti-Money Laundering Real-time Scanner", "tier": "Production Grade", "cloud": "Google Cloud Platform", "corpus": 80000, "reqs": 35000},
        {"title": "E-Commerce Return Fraud & Receipt Verification", "tier": "MVP", "cloud": "Amazon Web Services", "corpus": 30000, "reqs": 8000},
        {"title": "Airline Baggage Claim & Rebooking Conversational Agent", "tier": "Production Grade", "cloud": "Microsoft Azure", "corpus": 150000, "reqs": 40000},
        {"title": "Commercial Real Estate Lease Clause Abstractor", "tier": "PoC", "cloud": "Microsoft Azure", "corpus": 1200, "reqs": 500},
        {"title": "Pharma Clinical Trial Protocol Adverse Event Bot", "tier": "MVP", "cloud": "Google Cloud Platform", "corpus": 45000, "reqs": 6000},
        {"title": "Telecom Fiber Broadband Diagnostic & Dispatch AI", "tier": "Production Grade", "cloud": "Amazon Web Services", "corpus": 200000, "reqs": 60000},
        {"title": "University Admissions & Financial Aid Copilot", "tier": "Pilot", "cloud": "Google Cloud Platform", "corpus": 15000, "reqs": 3000},
        {"title": "Automotive Telematics Predictive Fleet Maintenance", "tier": "MVP", "cloud": "Microsoft Azure", "corpus": 90000, "reqs": 15000},
        {"title": "Hotel Chain Guest Concierge & Room Service Voice AI", "tier": "Pilot", "cloud": "Amazon Web Services", "corpus": 20000, "reqs": 4500},
        {"title": "Energy Utility Smart Meter Outage Automated IVR", "tier": "Production Grade", "cloud": "Microsoft Azure", "corpus": 120000, "reqs": 50000},
        {"title": "Insurance Auto Claim Damage Vision & Estimator", "tier": "MVP", "cloud": "Amazon Web Services", "corpus": 60000, "reqs": 10000},
        {"title": "Legal Firm M&A Due Diligence Redline Assistant", "tier": "PoC", "cloud": "Microsoft Azure", "corpus": 3000, "reqs": 800},
        {"title": "Restaurant Kitchen Prep Waste Optimization AI", "tier": "Pilot", "cloud": "Google Cloud Platform", "corpus": 10000, "reqs": 2500},
        {"title": "Supply Chain Customs Tariff & HS Code Classification", "tier": "MVP", "cloud": "Microsoft Azure", "corpus": 40000, "reqs": 7500},
        {"title": "Corporate IT Service Desk Zero-Touch Password & SSO Bot", "tier": "Production Grade", "cloud": "Microsoft Azure", "corpus": 75000, "reqs": 25000},
        {"title": "Mortgage Underwriting Bank Statement Income Verifier", "tier": "MVP", "cloud": "Amazon Web Services", "corpus": 50000, "reqs": 9000},
        {"title": "Mining Heavy Equipment Safety Video Sensor Alerts", "tier": "PoC", "cloud": "Google Cloud Platform", "corpus": 5000, "reqs": 1200}
    ]
    
    results = []
    
    for idx, p in enumerate(projects):
        t0 = time.time()
        # 1. Init
        init_res = requests.get(f"{BASE_URL}/api/session").json()
        sid = init_res["session_id"]
        
        # 2. RFP Bulk Ingestion (Simulates full text intake)
        rfp_text = f"""
        Project: {p['title']}
        Tier: {p['tier']}
        Target Cloud: {p['cloud']}
        Corpus Volume: {p['corpus']} documents and historical records.
        Daily Traffic: {p['reqs']} queries per day.
        Duration: 8.0 weeks.
        Capabilities: Ingestion, Hybrid Vector Retrieval, Model Reasoning, Security CMEK, Structured DB, Corporate SSO.
        Security: Regulated Moderate, Private Endpoints, RBAC, Managed Identities.
        Availability: Multi-AZ Zone Redundant.
        """
        
        # Send intake
        requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": sid,
            "message": rfp_text,
            "persona": "CLIENT"
        })
        
        # Step through remaining questions until all 32 domains resolved (>= 95% confidence)
        turn_count = 0
        while turn_count < 35:
            turn_count += 1
            cur_sess = requests.get(f"{BASE_URL}/api/session?session_id={sid}").json()
            if cur_sess.get("brd") or (cur_sess.get("confidence") and cur_sess["confidence"]["score"] >= 95.0):
                break
            cur_q = cur_sess.get("current_question")
            if not cur_q:
                break
            # If technical, delegate to architect; else accept default/recommendation
            if any(k in cur_q["id"] for k in ["cloud", "llm", "security", "hadr", "retrieval", "vector", "pass"]):
                requests.post(f"{BASE_URL}/api/workflow/delegate-architect", json={"session_id": sid})
            else:
                def_val = cur_q.get("default_value") or (cur_q.get("options", [{}])[0].get("value") if cur_q.get("options") else "Confirmed")
                requests.post(f"{BASE_URL}/api/chat", json={
                    "session_id": sid,
                    "message": str(def_val),
                    "persona": "CLIENT"
                })
        
        elapsed = time.time() - t0
        final_data = requests.get(f"{BASE_URL}/api/session?session_id={sid}").json()
        conf_score = final_data.get("confidence", {}).get("score", 0)
        brd_doc = final_data.get("brd")
        
        # Check math consistency
        math_valid = False
        person_days = 0
        total_cost = 0
        monthly_cloud = 0
        if brd_doc:
            person_days = brd_doc.get("total_person_days", 0)
            total_cost = brd_doc.get("total_labour_cost_usd", 0)
            monthly_cloud = brd_doc.get("sizing_metrics", {}).get("total_monthly_cloud_cost_usd", 0)
            # Reconcile formula: total_cost == person_days * 8 * rate
            expected_cost = round(person_days * 8.0 * brd_doc.get("blended_hourly_rate", 30.0), 2)
            math_valid = (abs(total_cost - expected_cost) <= 1.0)
            
        res_item = {
            "index": idx + 1,
            "title": p["title"],
            "tier": p["tier"],
            "cloud": p["cloud"],
            "confidence": conf_score,
            "has_brd": bool(brd_doc),
            "person_days": person_days,
            "labour_cost_usd": total_cost,
            "monthly_cloud_usd": monthly_cloud,
            "math_reconciled": math_valid,
            "elapsed_sec": round(elapsed, 2)
        }
        results.append(res_item)
        print(f"[{idx+1}/20] {p['title']} ({p['tier']}) -> Conf: {conf_score}% | BRD: {bool(brd_doc)} | Math: {'PASS' if math_valid else 'FAIL'} | {elapsed:.2f}s")
        
    return results

if __name__ == "__main__":
    sid, brd = test_retail_store_owner_simulation()
    bench = test_20_enterprise_projects_benchmark()
    
    with open("benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump({"retail_store_session": sid, "retail_brd_summary": brd, "benchmark_20_projects": bench}, f, indent=2)
    print("\nBenchmark tests completed and saved to benchmark_report.json!")
