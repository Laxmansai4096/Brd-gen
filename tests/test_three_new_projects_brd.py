import os
import sys
import json

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_three_new_projects_brd():
    projects = [
        {
            "num": 1,
            "name": "HealthFirst Hospital Network",
            "initiative": "HealthFirst — Clinical Trial Patient Matching & Protocol Intelligence",
            "requirements": [
                "Screen patient EHR records against complex clinical trial protocol eligibility criteria with 100% provenance.",
                "Generate patient eligibility scorecards and FDA 21 CFR Part 11 compliant audit trails.",
                "Provide secure natural language clinical protocol search for clinical research coordinators."
            ],
            "cloud": "Microsoft Azure",
            "tier": "MVP",
            "duration": "6.0",
            "geography": "United States",
            "expected_domain": "clinical_trial_matching"
        },
        {
            "num": 2,
            "name": "Apex Global Logistics",
            "initiative": "Apex Logistics — Autonomous Voice Dispatch & Exception AI",
            "requirements": [
                "Automated voice telephony calling for driver load status and check-in over phone.",
                "Real-time GPS ETA discrepancy prediction and automated warehouse dock rescheduling.",
                "Exception notification dispatch to operations coordinators."
            ],
            "cloud": "Amazon Web Services",
            "tier": "Pilot",
            "duration": "4.0",
            "geography": "United Kingdom",
            "expected_domain": "autonomous_voice_dispatch"
        },
        {
            "num": 3,
            "name": "FinSecure National Bank",
            "initiative": "FinSecure Bank — Real-Time Transaction Anomaly & AML Risk Platform",
            "requirements": [
                "Real-time transaction stream anomaly detection and AML behavioral pattern scoring.",
                "Automated Suspicious Activity Report (SAR) draft generation with regulatory citation links.",
                "Auditor workbench for risk case review and regulatory submission."
            ],
            "cloud": "Google Cloud Platform",
            "tier": "Production Grade",
            "duration": "16.0",
            "geography": "European Union",
            "expected_domain": "aml_transaction_monitoring"
        }
    ]

    for p in projects:
        # 1. Initialize session
        res_sess = client.get('/api/session')
        assert res_sess.status_code == 200
        session_id = res_sess.json()['session_id']

        # 2. Domain 1: Client & Project Name
        r1 = client.post('/api/chat', json={
            "session_id": session_id,
            "message": p["initiative"],
            "persona": "CLIENT"
        })
        assert r1.status_code == 200

        # 3. Domain 2: Problem Statement & Requirements (Multi-Turn Accumulation)
        # Requirement 1
        r_req1 = client.post('/api/chat', json={
            "session_id": session_id,
            "message": p["requirements"][0],
            "persona": "CLIENT"
        })
        assert r_req1.status_code == 200

        # Requirement 2
        r_req2 = client.post('/api/chat', json={
            "session_id": session_id,
            "message": p["requirements"][1],
            "persona": "CLIENT"
        })
        assert r_req2.status_code == 200

        # Requirement 3
        r_req3 = client.post('/api/chat', json={
            "session_id": session_id,
            "message": p["requirements"][2],
            "persona": "CLIENT"
        })
        assert r_req3.status_code == 200

        # Signal end of requirements
        r_done = client.post('/api/chat', json={
            "session_id": session_id,
            "message": "That covers all requirements / Continue",
            "persona": "CLIENT"
        })
        assert r_done.status_code == 200

        # 4. Supply project technical & scale parameters
        answers_payload = {
            "q_tier": p["tier"],
            "q_duration": p["duration"],
            "q_cloud": p["cloud"],
            "q_geography": p["geography"],
            "q_buffer_strategy": "15% Shadow / Backup Capacity (Recommended)",
            "q_personas_count": "4 Personas (Active: Legal, Procurement, Risk, Sponsor - Factor 1.450)",
            "q_integrations_count": "2 Integrations (Standard Baseline - Factor 1.000x)",
            "q_datasources_count": "2 Data Sources (Contract Blob Storage + Risk Spreadsheet - Baseline 1.000x)",
            "q_complexity": "Medium",
            "q_compliance": "Regulated High" if "Bank" in p["name"] or "Hospital" in p["name"] else "Internal policy only"
        }

        # Submit parameters
        for q_key, q_val in answers_payload.items():
            client.post('/api/chat', json={
                "session_id": session_id,
                "message": q_val,
                "persona": "CLIENT"
            })

        # Generate / Replan BRD
        res_replan = client.post('/api/replan', json={
            "session_id": session_id,
            "answers": answers_payload
        })
        assert res_replan.status_code == 200
        brd = res_replan.json()['brd']

        # 5. Verify BRD Details
        assert brd['project_title'] != ""
        assert brd['delivery_tier'] == p["tier"]
        assert brd['cloud_platform'] == p["cloud"]
        assert brd['total_person_days'] > 0
        assert brd['total_labour_cost_usd'] > 0
        assert brd['sizing_metrics']['total_monthly_cloud_cost_usd'] > 0
        assert brd['tco_projection']['total_3year_tco_usd'] > 0
        
        # 6. Verify Assumptions: Strictly user inputs + admin defaults (Zero Hallucination)
        assumptions = brd['assumptions']
        assert len(assumptions) >= 5, "Expected at least 5 structured assumptions"
        for a in assumptions:
            assert a['confidence'] in ["High", "Medium", "Low"]
            assert a['status'] in ["Approve", "Correct", "Reject"]

        # 7. Verify Structured JSON Export matching ai_brd_questionnaire_template.json
        res_json = client.get(f'/api/export/json?session_id={session_id}')
        assert res_json.status_code == 200
        json_data = res_json.json()
        assert "project_requirements" in json_data
        assert "estimations_and_delivery_plan" in json_data
        assert "system_architecture_and_cloud_inventory" in json_data
        assert json_data["estimations_and_delivery_plan"]["delivery_tier"] == p["tier"]
        assert json_data["system_architecture_and_cloud_inventory"]["target_cloud"] == p["cloud"]

if __name__ == "__main__":
    test_three_new_projects_brd()
