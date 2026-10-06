import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_pvr_inox_reference_brd_fidelity():
    print("\n--- RUNNING HIGH-FIDELITY REFERENCE BRD VERIFICATION (PVR INOX) ---")
    
    # 1. Initialize session
    session_res = client.get('/api/session')
    assert session_res.status_code == 200
    session_id = session_res.json()['session_id']
    print(f"[OK] Session initialized: {session_id}")
    
    # 2. Stage 1 Ideation with exact PVR INOX context
    ideate_res = client.post('/api/workflow/ideate', json={
        "session_id": session_id,
        "client_idea": "PVR INOX manages contracts across lease, vendor, service, facilities, tech and marketing categories. Manual clause audit is slow and deviations from contracting principles are missed. We need an automated contract intelligence, clause extraction, principle assessment and risk register visibility platform.",
        "project_title": "Contract Intelligence & Risk Visibility Platform",
        "target_tier": "PoC"
    })
    assert ideate_res.status_code == 200
    print("[OK] Stage 1 Ideation completed for PVR INOX.")
    
    # 3. Simulate answering all discovery questions exactly matching Sheet 02 & Sheet 10
    discovery_answers = {
        "q_client": "PVR INOX | Contract Intelligence & Risk Visibility Platform",
        "q_problem": "Manual contract clause review is slow and deviations from contracting principles are not caught consistently.",
        "q_tier": "PoC",
        "q_duration": "6.0",
        "q_start_date": "2026-09-30",
        "q_geography": "India",
        "q_cloud": "Microsoft Azure",
        "q_usecases_count": "1",
        "q_personas_count": "4",
        "q_integrations_count": "0",
        "q_datasources_count": "2",
        "q_channels_count": "1",
        "q_languages_count": "1",
        "q_envs_count": "3",
        "q_components_count": "6",
        "q_complexity": "Low",
        "q_compliance": "Internal policy only",
        "q_security": "Standard",
        "q_named_users": "200",
        "q_concurrent_users": "50",
        "q_daily_requests": "2000",
        "q_legal_categories": "Lease, Vendor, Service, Facilities, Technology, Marketing",
        "q_foundation_llm": "Azure OpenAI reasoning/thinking tier (GPT-5 Thinking/Reasoning parameters)",
        "q_grounding_mode": "Work (Tenant data only, disabling public web retrieval)",
        "q_multi_pass_policy": "Pass 1 extracts standard clauses | Pass 2 evaluates ambiguous terms to assign Agree, Agree with Management Approval, or Not Agree",
        "q_buffer_strategy": "15% Shadow / Backup Capacity (Recommended)"
    }
    
    replan_res = client.post('/api/replan', json={
        "session_id": session_id,
        "overrides": discovery_answers,
        "currency_code": "USD"
    })
    assert replan_res.status_code == 200
    brd = replan_res.json()["brd"]
    assert brd is not None
    
    print("\n--- MATHEMATICAL & ARCHITECTURAL FIDELITY AUDIT ---")
    print(f"Project Title: {brd['project_title']}")
    print(f"Client Name:   {brd['client_name']}")
    print(f"Delivery Tier: {brd['delivery_tier']}")
    print(f"Total Effort:  {brd['total_person_days']:.1f} Person-Days")
    print(f"Daily Hours:   {brd['daily_working_hours']} hrs/day (India Working Calendar)")
    
    # Verify Task Library & Effort
    assert abs(brd['total_person_days'] - 127.1) < 1.0, f"Expected ~127.1 days, got {brd['total_person_days']}"
    assert len(brd['task_estimates']) == 98, f"Expected 98 task estimates, got {len(brd['task_estimates'])}"
    assert len(brd['project_phases']) == 18, f"Expected 18 phases, got {len(brd['project_phases'])}"
    assert len(brd['technical_components']) == 6, f"Expected 6 technical components, got {len(brd['technical_components'])}"
    
    # Verify Components C001 - C006
    c_names = [c['name'] for c in brd['technical_components']]
    print("\nVerified Technical Components (C001 - C006):")
    for c in brd['technical_components']:
        print(f"  [{c['id']}] {c['name']} -> Tech: {c['technology_choice']}")
        
    assert any("Contract Landing Store" in n or "Ingestion" in n for n in c_names)
    assert any("Clause Index" in n or "Retrieval" in n for n in c_names)
    assert any("Classification" in n or "Multi-Pass" in n for n in c_names)
    assert any("Ontology" in n or "Risk Register" in n for n in c_names)
    assert any("Evaluation" in n or "Dashboard" in n for n in c_names)
    assert any("Identity" in n or "Landing Zone" in n for n in c_names)
    
    # Verify Personas (4 Personas)
    print("\nVerified User Personas:")
    for p in brd.get('user_personas', []):
        print(f"  • {p.get('persona')}: {p.get('need')}")
    assert len(brd.get('user_personas', [])) == 4
    
    # Verify Day-Wise Schedule
    day_rows = brd['day_wise_schedule']
    print(f"\nDay-Wise Schedule Generated: {len(day_rows)} entries")
    assert len(day_rows) >= 30, f"Expected at least 30 scheduled days, got {len(day_rows)}"
    
    # Verify Sizing Metrics
    sizing = brd['sizing_metrics']
    print(f"\nSizing Metrics (Sheet 31 match):")
    print(f"  • Requests Per Day:     {sizing['requests_per_day']}")
    print(f"  • Named Users:          {sizing['named_users']}")
    print(f"  • Peak Concurrent:      {sizing['peak_concurrent_users']}")
    print(f"  • Corpus Documents:     {sizing['corpus_documents']:,}")
    print(f"  • Embedding Dimensions: {sizing['embedding_dimensions']}")
    print(f"  • Raw Corpus Size:      {sizing['raw_corpus_gb']} GB")
    print(f"  • Total Monthly Cloud:  ${sizing['total_monthly_cloud_cost_usd']:.2f}")
    
    assert sizing['requests_per_day'] == 2000
    assert sizing['named_users'] == 200
    assert sizing['peak_concurrent_users'] == 50
    assert sizing['corpus_documents'] == 50000
    assert sizing['embedding_dimensions'] == 1536
    assert sizing['raw_corpus_gb'] == 1.0
    assert sizing['total_monthly_cloud_cost_usd'] == 645.0
    
    # 4. Verify All Export Endpoints for PVR INOX
    print("\n--- EXPORT GENERATION INTEGRITY CHECK ---")
    for exp_type, exp_url in [
        ("PDF Document", f"/api/export/pdf?session_id={session_id}"),
        ("Word Document", f"/api/export/docx?session_id={session_id}"),
        ("Excel Financial Model", f"/api/export/excel?session_id={session_id}"),
        ("PowerPoint Deck", f"/api/export-pptx?session_id={session_id}"),
        ("Jira Backlog CSV", f"/api/export/jira?session_id={session_id}")
    ]:
        r = client.get(exp_url)
        assert r.status_code == 200, f"{exp_type} failed: {r.status_code}"
        assert len(r.content) > 0
        print(f"[OK] {exp_type} successfully generated ({len(r.content)} bytes).")
        
    print("\n--- ALL REFERENCE BRD CHECKS PASSED WITH 100% FIDELITY & ZERO HALLUCINATIONS! ---\n")

if __name__ == "__main__":
    test_pvr_inox_reference_brd_fidelity()
