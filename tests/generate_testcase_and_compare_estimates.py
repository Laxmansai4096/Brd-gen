import requests
import json
import uuid
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8081"

def run_testcase():
    session_id = str(uuid.uuid4())
    print("="*80, flush=True)
    print(f"RUNNING ENTERPRISE TEST CASE: CareHealth AI Systems (Session: {session_id})", flush=True)
    print("="*80, flush=True)

    testcase_inputs = {
        "q_client": "CareHealth AI Systems — Clinical Trial Protocol Intelligence",
        "q_tier": "Pilot",
        "q_problem": "Clinical research coordinators spend 40+ hours manually screening EHR patient records against complex clinical trial protocol eligibility criteria. The solution must ingest unstructured clinical protocols and structured EHR records, execute agentic eligibility matching with 100% provenance, and output patient eligibility scorecards with FDA 21 CFR Part 11 audit trails.",
        "q_duration": "8.0 Weeks",
        "q_cloud": "Microsoft Azure",
        "q_start_date": "2026-10-15",
        "q_buffer": "15.0%",
        "q_complexity": "Medium (1.000 Baseline)",
        "q_compliance": "Regulated - high",
        "q_security": "Enhanced",
        "q_hadr_tier": "Zone redundant",
        "q_region": "East US",
        "q_rate": "$30/hr blended baseline",
        "q_data_sources": "2 data sources: EHR Epic/Cerner database and ClinicalTrials.gov protocol repository",
        "q_users": "500 named clinical investigators and 50 concurrent research coordinators",
        "q_sla": "99.9% Uptime with sub-2-second retrieval latency",
        "q_data_volume": "5,000 patient eligibility evaluations daily and 250 GB protocol document storage",
        "q_model_choice": "Azure OpenAI GPT-4o with text-embedding-3-large",
        "q_grounding": "Azure AI Search with Hybrid Semantic Vector and BM25 filtering",
        "q_integrations": "HL7 FHIR REST API, Epic EHR connector, and Microsoft Teams alert webhook",
        "q_eval_framework": "Ragas & DeepEval with FDA Golden ground truth validation dataset",
        "q_onprem_gw": "Azure ExpressRoute private peering to on-prem hospital PACS/EHR",
        "q_audit_log": "Azure Immutable Blob Storage with WORM (Write Once, Read Many) compliance",
        "q_role_access": "Azure Entra ID with OAuth2 OIDC, Medical Staff RBAC, and HIPAA audit trails",
        "q_failover": "Automated cross-zone failover with Azure Front Door",
        "q_backup_policy": "Daily snapshot backups with 7-year medical compliance retention",
        "q_cost_limit": "Enforce Azure Cost Management alerts at $1,500/month threshold",
        "q_support_tier": "Enterprise 24/7 mission-critical support",
        "q_token_budget": "10,000,000 tokens/month allocated budget",
        "q_deployment_target": "Azure Container Apps with serverless autoscaling"
    }

    turn = 1
    for qid, ans in testcase_inputs.items():
        res = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": ans,
            "persona": "CLIENT"
        }).json()
        conf = res.get("confidence", {}).get("score", 0.0)
        is_complete = res.get("is_complete", False)
        print(f"Turn {turn:02d} | Input: {ans[:45]}... | Confidence: {conf:.1f}%", flush=True)
        if is_complete or conf >= 95.0:
            print(f"🎯 Milestone reached at Turn {turn}: Confidence = {conf:.1f}%", flush=True)
            break
        turn += 1

    # Fetch full session and BRD
    final_sess = requests.get(f"{BASE_URL}/api/session?session_id={session_id}").json()
    brd = final_sess.get("brd")

    if not brd:
        print("❌ Error: BRD was not generated.", flush=True)
        return

    print("\n" + "="*80, flush=True)
    print("LIVE GENERATED BRD ESTIMATES EXTRACTED FROM APPLICATION", flush=True)
    print("="*80, flush=True)

    print(f"• Project Title: {brd.get('project_title')}", flush=True)
    print(f"• Client: {brd.get('client_name')}", flush=True)
    print(f"• Delivery Tier: {brd.get('delivery_tier')} ({brd.get('total_duration_weeks')} Weeks)", flush=True)
    print(f"• Total Effort: {brd.get('total_person_days')} Person-Days ({brd.get('total_person_hours')} Hours)", flush=True)
    print(f"• Blended Rate: ${brd.get('blended_hourly_rate')}/hr", flush=True)
    print(f"• Total Labour Cost: ${brd.get('total_labour_cost_usd'):,.2f}", flush=True)
    
    cloud_cost = brd.get('sizing_metrics', {}).get('total_monthly_cloud_cost_usd', 0.0)
    print(f"• Monthly Cloud BoM: ${cloud_cost:,.2f} / month", flush=True)
    print(f"• 3-Year Cloud TCO: ${cloud_cost * 36:,.2f}", flush=True)
    
    print("\n--- 12 Disciplines Resource Loading ---", flush=True)
    roles = brd.get('role_allocations', [])
    for r in roles:
        print(f"  • {r.get('role_name', r.get('role_code')):<35}: {r.get('days', 0):>5.1f} Days | {r.get('hours', 0):>6.1f} Hrs | FTE: {r.get('headcount', r.get('fte', 0)):>4.2f} | Cost: ${r.get('cost_usd', 0):>9,.2f}", flush=True)

    print("\n--- 18-Phase Roadmap Breakdown ---", flush=True)
    phases = brd.get('phase_schedule', [])
    for p in phases:
        print(f"  • Phase {p.get('phase_number', 0):02d} ({p.get('phase_code')}): {p.get('phase_name', '')[:35]:<35} | {p.get('duration_weeks', 0):>4.1f} Wks | Effort: {p.get('total_person_days', p.get('effort_days', 0)):>5.1f} PD", flush=True)

    # Save to JSON for report artifact
    comparison_payload = {
        "session_id": session_id,
        "testcase_inputs": testcase_inputs,
        "brd": brd
    }
    with open("live_brd_testcase_results.json", "w") as f:
        json.dump(comparison_payload, f, indent=2)
    print("\nSaved live BRD results to live_brd_testcase_results.json", flush=True)

if __name__ == "__main__":
    run_testcase()
