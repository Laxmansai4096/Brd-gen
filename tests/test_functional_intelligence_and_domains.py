import requests
import json
import time
import sys
import io

# UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8081"

test_audit = {
    "ambiguity_handling": {},
    "projects": {},
    "comparisons": {}
}

def banner(title):
    print("\n" + "=" * 90)
    print(f"🔬 {title}")
    print("=" * 90)

def test_ambiguity_and_clarification():
    banner("TEST SUITE 1: AMBIGUITY DETECTION & ANTI-HALLUCINATION")
    # Initialize a new session
    res = requests.get(f"{BASE_URL}/api/session?new=true").json()
    sid = res["session_id"]
    print(f"• Initialized Clean Session: {sid}")

    # Step 1: Send a purposefully vague project description
    vague_input = "We want some AI tool to automate stuff for our company, not sure what it does yet, maybe some chatbot or whatever works."
    print(f"\n[USER INPUT] {vague_input}")
    
    chat_res = requests.post(f"{BASE_URL}/api/chat", json={
        "session_id": sid,
        "message": vague_input
    }).json()

    messages = chat_res.get("messages", [])
    last_msg = messages[-1] if messages else {}
    last_text = last_msg.get("content", "")

    print(f"\n[AGENT RESPONSE]\n{last_text[:400]}...")

    # Check: Did the agent detect ambiguity or provide structured guidance?
    detected_vague = any(term in last_text.lower() for term in ["clarif", "recommend", "architect", "scope", "specific", "options"])
    # Check: Did the agent hallucinate a random completed project?
    hallucinated_complete = "final approved" in last_text.lower() or "100% confidence" in last_text.lower()

    print(f"\n• Ambiguity Intercepted & Clarification Requested: {detected_vague}")
    print(f"• Hallucination Prevented (Premature Completion): {not hallucinated_complete}")

    # Step 2: Send another vague answer to question 2 ("don't know, whatever cloud is cheapest")
    vague_q2 = "dunno, not sure about cloud or security, whatever is standard"
    print(f"\n[USER INPUT 2] {vague_q2}")
    chat_res2 = requests.post(f"{BASE_URL}/api/chat", json={
        "session_id": sid,
        "message": vague_q2
    }).json()
    last_text2 = chat_res2.get("messages", [])[-1].get("content", "")
    has_architect_guidance = "solutions architect" in last_text2.lower() or "recommend" in last_text2.lower() or "azure" in last_text2.lower()
    print(f"• Solutions Architect Stepped In with Grounded Guidance: {has_architect_guidance}")

    test_audit["ambiguity_handling"] = {
        "vague_intercepted": detected_vague,
        "premature_completion_prevented": not hallucinated_complete,
        "architect_guidance_provided": has_architect_guidance
    }


def run_domain_project(domain_name, project_spec):
    banner(f"TEST SUITE 2: DYNAMIC DISCOVERY & ESTIMATION FOR DOMAIN: {domain_name}")
    res = requests.get(f"{BASE_URL}/api/session?new=true").json()
    sid = res["session_id"]
    print(f"• Session ID: {sid}")
    print(f"• Target Initiative: {project_spec['client_project']}")
    print(f"• Target Cloud: {project_spec['cloud']} | Tier: {project_spec['tier']} | Duration: {project_spec['duration']} wks")

    # Turn 1: Client and Problem Statement
    t1_msg = f"{project_spec['client_project']} — {project_spec['problem']}"
    r1 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": sid, "message": t1_msg}).json()
    
    # Turn 2: Scope, Tier, Duration, and Cloud
    t2_msg = f"Delivery tier is {project_spec['tier']}, reference timeline is {project_spec['duration']} weeks on {project_spec['cloud']} in {project_spec['geography']}."
    r2 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": sid, "message": t2_msg}).json()

    # Turn 3: Technical Details, Users, Complexity & Compliance
    t3_msg = (
        f"Technical complexity is {project_spec['complexity']}. Compliance requirement is {project_spec['compliance']}. "
        f"Security standard is {project_spec['security']}. Total named users: {project_spec['users']}, "
        f"integrations: {project_spec['integrations']} enterprise systems, data volume: {project_spec['corpus']} records."
    )
    r3 = requests.post(f"{BASE_URL}/api/chat", json={"session_id": sid, "message": t3_msg}).json()

    # Check dynamic contextualization: Does the agent's question incorporate the project's title?
    last_agent_msg = r3.get("messages", [])[-1].get("content", "")
    mentions_proj = any(word.lower() in last_agent_msg.lower() for word in project_spec['keyword'].split())
    print(f"\n• Dynamic Contextualization Active: {mentions_proj} (Tailored to '{project_spec['keyword']}')")

    # Complete discovery via compilation endpoint to trigger mathematical engine
    # Ingest project parameters to synthesize full BRD
    doc_text = f"""# {project_spec['client_project']}
## Business Requirements Document & Technical Baseline
Client: {project_spec['client_project'].split('—')[0].strip()}
Delivery Tier: {project_spec['tier']}
Target Cloud: {project_spec['cloud']}
Geography: {project_spec['geography']}
Timeline: {project_spec['duration']} Weeks
Complexity: {project_spec['complexity']}
Compliance: {project_spec['compliance']}
Security: {project_spec['security']}
Named Users: {project_spec['users']}
Integrations: {project_spec['integrations']}

### Problem Statement
{project_spec['problem']}

### Capabilities
{project_spec['capabilities']}
"""
    up_res = requests.post(
        f"{BASE_URL}/api/upload",
        data={"session_id": sid},
        files={"file": (f"{domain_name.replace(' ', '_')}_Spec.md", doc_text.encode("utf-8"), "text/markdown")}
    ).json()

    brd = up_res.get("brd", {})
    phases = brd.get("project_phases", [])
    roles = brd.get("role_efforts", [])
    sizing = brd.get("sizing_metrics", {})
    feasibility = brd.get("schedule_feasibility", {})

    total_days = brd.get("total_person_days", 0)
    total_cost = brd.get("total_labour_cost_usd", 0)
    cloud_monthly = sizing.get("total_monthly_cloud_cost_usd", 0)
    is_feas = feasibility.get("is_feasible", True)

    print(f"\n📊 MATHEMATICAL ESTIMATION ENGINE RESULTS FOR {domain_name.upper()}:")
    print(f"   • Total Person-Days:     {total_days:.1f} days")
    print(f"   • Total Labour Cost:     ${total_cost:,.2f} (@ ${brd.get('blended_hourly_rate', 30):.2f}/hr)")
    print(f"   • Monthly Cloud BoM:     ${cloud_monthly:,.2f} / month")
    print(f"   • WBS Delivery Phases:   {len(phases)} Phases (P01-P18)")
    print(f"   • Staffing Roles:        {len(roles)} Disciplines")
    print(f"   • Feasibility Verified:  {is_feas} (Stretch: {feasibility.get('stretch_weeks', 0)} wks)")

    test_audit["projects"][domain_name] = {
        "client": brd.get("client_name"),
        "tier": brd.get("delivery_tier"),
        "cloud": brd.get("cloud_platform"),
        "duration_weeks": brd.get("total_duration_weeks"),
        "person_days": total_days,
        "labour_cost": total_cost,
        "monthly_cloud": cloud_monthly,
        "phases_count": len(phases),
        "roles_count": len(roles),
        "feasible": is_feas,
        "contextualized": mentions_proj
    }

def run_all_functional_tests():
    test_ambiguity_and_clarification()

    # Domain 1: Healthcare / Clinical AI (High Compliance, Strict Security)
    run_domain_project("Healthcare Clinical AI", {
        "client_project": "MedVault Health — Clinical Trial Matching & Protocol Intelligence",
        "keyword": "MedVault",
        "problem": "Manual oncology clinical trial screening takes 4.5 hours per patient, leading to high protocol dropouts and delayed enrollment in life-saving treatments.",
        "tier": "Production Grade",
        "duration": "16.0",
        "cloud": "Amazon Web Services",
        "geography": "United States",
        "complexity": "High",
        "compliance": "HIPAA & HITECH (Healthcare Protected Health Information)",
        "security": "Enhanced (Private Endpoints, CMEK & RBAC)",
        "users": "1,000",
        "integrations": "5",
        "corpus": "150,000",
        "capabilities": "Clinical record summarization, protocol eligibility criteria parsing, zero-data-retention HIPAA inference, and doctor review dashboard."
    })

    # Domain 2: FinTech Fraud Detection & Anti-Money Laundering (High Throughput, Low Latency)
    run_domain_project("FinTech Fraud & AML", {
        "client_project": "FinGuard Technologies — Real-Time AML & Transaction Fraud Prevention",
        "keyword": "FinGuard",
        "problem": "High-velocity payment processing creates massive fraud exposure, resulting in $12M annual fraud write-offs and slow manual AML alert reviews.",
        "tier": "MVP",
        "duration": "8.0",
        "cloud": "Google Cloud Platform",
        "geography": "United Kingdom",
        "complexity": "Very High",
        "compliance": "BFSI / RBI / PCI-DSS Financial Regulatory Grade",
        "security": "Enterprise High Security",
        "users": "250",
        "integrations": "4",
        "corpus": "500,000",
        "capabilities": "Sub-100ms streaming transaction scoring, graph anomaly detection, automated SAR regulatory draft filing, and compliance triage cockpits."
    })

    # Domain 3: Autonomous Multi-Agent / Supply Chain Operations (Multi-Modal / Tool-Calling)
    run_domain_project("Autonomous Supply Chain", {
        "client_project": "LogiFlow Global — Autonomous Freight Dispatching & Multi-Agent Network",
        "keyword": "LogiFlow",
        "problem": "Cross-border logistics carriers suffer 22% empty backhaul mileage and communication delays across freight dispatchers and customs brokers.",
        "tier": "Pilot",
        "duration": "10.0",
        "cloud": "Microsoft Azure",
        "geography": "European Union",
        "complexity": "Medium",
        "compliance": "GDPR / DPDP & Data Privacy",
        "security": "Enhanced",
        "users": "100",
        "integrations": "3",
        "corpus": "20,000",
        "capabilities": "Multi-agent load matching, dynamic route recalculation, automated freight invoice OCR reconciliation, and driver mobile push updates."
    })

    # Cross-Domain Comparative Analysis
    banner("CROSS-DOMAIN MATHEMATICAL BEHAVIOR ANALYSIS")
    projects = test_audit["projects"]
    
    print(f"{'Domain Project':<30} | {'Tier / Dur':<18} | {'Effort (Days)':<15} | {'Labour Cost':<15} | {'Monthly Cloud':<15}")
    print("-" * 100)
    for dom, data in projects.items():
        tier_dur = f"{data['tier']} ({data['duration_weeks']}w)"
        effort_str = f"{data['person_days']:.1f} d"
        cost_str = f"${data['labour_cost']:,.0f}"
        cloud_str = f"${data['monthly_cloud']:,.0f}/mo"
        print(f"{dom:<30} | {tier_dur:<18} | {effort_str:<15} | {cost_str:<15} | {cloud_str:<15}")

    # Check Scaling Reality:
    # 1. MedVault (Production Grade, 16w, High Complexity) should have higher effort than LogiFlow (Pilot, 10w)
    med_days = projects["Healthcare Clinical AI"]["person_days"]
    logi_days = projects["Autonomous Supply Chain"]["person_days"]
    fin_days = projects["FinTech Fraud & AML"]["person_days"]

    scaling_holds = med_days > logi_days and med_days > fin_days
    print(f"\n• Realistic Tier & Complexity Scaling Proved (MedVault {med_days:.1f}d > LogiFlow {logi_days:.1f}d): {scaling_holds}")

    with open("qa_domain_functional_audit.json", "w", encoding="utf-8") as f:
        json.dump(test_audit, f, indent=2)

    print("\n✅ FUNCTIONAL TESTING OF AI DOMAINS, AMBIGUITY, AND COMPLEXITY COMPLETE!")

if __name__ == "__main__":
    run_all_functional_tests()
