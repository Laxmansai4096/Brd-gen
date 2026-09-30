import os
import sys

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_full_pipeline():
    # 1. Test Session
    res = client.get('/api/session')
    assert res.status_code == 200, f'Session failed: {res.text}'
    data = res.json()
    session_id = data['session_id']
    print('1. Session created:', session_id)

    # 2. Test Settings
    res = client.get('/api/settings')
    assert res.status_code == 200
    print('2. Settings retrieved. Active provider:', res.json().get('active_provider'))

    # 3. Test Provider Connection Endpoint
    res = client.post('/api/settings/test-connection', json={
        'active_provider': 'google',
        'google_model': 'gemini-2.5-flash',
        'google_endpoint': 'https://generativelanguage.googleapis.com'
    })
    assert res.status_code == 200
    print('3. Test connection response:', res.json()['message'])

    # 4. Answer discovery question & generate BRD via replan
    client.post('/api/chat', json={
        'session_id': session_id,
        'message': 'Omnichannel Inventory Platform for Global Retail',
        'selected_option': 'Omnichannel Inventory Platform'
    })
    replan_res = client.post('/api/replan', json={
        'session_id': session_id,
        'overrides': {
            'q_client': 'Global Retail Corp',
            'q_project_name': 'Omnichannel Inventory Platform',
            'q_tier': 'MVP'
        },
        'currency_code': 'USD'
    })
    assert replan_res.status_code == 200
    brd = replan_res.json().get('brd')
    assert brd is not None, 'BRD generation returned None'
    print(f"4. BRD generated! Tier: {brd.get('delivery_tier')} | Duration weeks: {brd.get('total_duration_weeks')}")
    
    canon_reqs = brd.get('canonical_requirements', [])
    assert len(canon_reqs) == 17, f"Expected 17 canonical reqs, got {len(canon_reqs)}"
    print(f"   Canonical Requirements count: {len(canon_reqs)}")

    caps = brd.get('capabilities', [])
    assert len(caps) > 0, "Capabilities catalog is empty"
    print(f"   Capabilities count: {len(caps)}")

    dfs = brd.get('data_flows', [])
    assert len(dfs) == 4, f"Expected 4 data flows, got {len(dfs)}"
    print(f"   Data flows count: {len(dfs)}")

    ledger = brd.get('calculation_ledger', [])
    assert len(ledger) > 0, "Calculation ledger is empty"
    print(f"   Calculation ledger entries: {len(ledger)}")

    # 5. Test HITL Gate Approval
    gate_res = client.post('/api/gates/approve', json={
        'session_id': session_id,
        'gate': 'gate1',
        'approved': True,
        'notes': 'Scope confirmed by Architecture Board'
    })
    assert gate_res.status_code == 200
    assert gate_res.json()['hitl_gates']['gate1_requirements_approved'] is True
    print('5. Gate 1 approval successful!')

    # 6. Test Impact Analysis
    impact_res = client.post('/api/impact-analysis', json={
        'session_id': session_id,
        'parameter_changed': 'users',
        'old_value': '200',
        'new_value': '500'
    })
    assert impact_res.status_code == 200
    imp = impact_res.json()
    print(f"6. Impact Analysis computed! Delta days: {imp.get('delta_days')} | Delta cost: ${imp.get('delta_cost_usd'):.2f}")

    # 7. Test Export Endpoints
    for exp_name, exp_url in [
        ('PDF', f'/api/export/pdf?session_id={session_id}'),
        ('DOCX', f'/api/export/docx?session_id={session_id}'),
        ('Excel', f'/api/export/excel?session_id={session_id}'),
        ('Jira', f'/api/export/jira?session_id={session_id}'),
        ('PPTX', f'/api/export-pptx?session_id={session_id}'),
    ]:
        exp_res = client.get(exp_url)
        assert exp_res.status_code == 200, f"{exp_name} export failed with status {exp_res.status_code}"
        print(f"7. Export {exp_name} OK! ({len(exp_res.content)} bytes)")

    # 8. Test In-Line Canonical Requirement Edit & MoSCoW Priority with Immediate Ledger Tracking
    edit_res = client.post('/api/canonical-requirements/update', json={
        'session_id': session_id,
        'requirement_id': 'FR-001',
        'field': 'priority',
        'new_value': 'COULD'
    })
    assert edit_res.status_code == 200, f"Req update failed: {edit_res.text}"
    edit_data = edit_res.json()
    assert edit_data['updated_requirement']['priority'] == 'COULD'
    assert edit_data['ledger_entry']['calculation_type'] == 'MOSCOW_PRIORITY_UPDATE'
    print(f"8. Canonical Requirement MoSCoW update verified! Ledger ID: {edit_data['ledger_entry']['calculation_id']}")

    edit_res2 = client.post('/api/canonical-requirements/update', json={
        'session_id': session_id,
        'requirement_id': 'FR-001',
        'field': 'statement',
        'new_value': 'Enterprise real-time contract intake and automated field extraction pipeline.'
    })
    assert edit_res2.status_code == 200
    edit_data2 = edit_res2.json()
    assert edit_data2['updated_requirement']['statement'] == 'Enterprise real-time contract intake and automated field extraction pipeline.'
    assert edit_data2['ledger_entry']['calculation_type'] == 'REQUIREMENT_MUTATION'
    print(f"   Canonical Requirement statement edit verified! Ledger ID: {edit_data2['ledger_entry']['calculation_id']}")

    # 9. Test Commit Simulation to Baseline
    commit_res = client.post('/api/impact-analysis/commit', json={
        'session_id': session_id,
        'parameter_changed': 'users',
        'new_value': '500'
    })
    assert commit_res.status_code == 200, f"Commit scenario failed: {commit_res.text}"
    commit_data = commit_res.json()
    assert commit_data['status'] == 'success'
    ledger_entries = commit_data['calculation_ledger']
    scenario_entry = next((e for e in ledger_entries if e['calculation_type'] == 'SCENARIO_COMMIT'), None)
    assert scenario_entry is not None, "SCENARIO_COMMIT ledger entry not found"
    print(f"9. Commit Simulation to Baseline verified! New person days: {commit_data['brd']['total_person_days']} | Ledger entry: {scenario_entry['calculation_id']}")

    print("\nALL 9 TESTS PASSED ACCORDING TO reference.txt SPECIFICATION!")

if __name__ == '__main__':
    test_full_pipeline()
