import httpx
import json

BASE_URL = "http://127.0.0.1:8088"

def test_flow():
    # 1. Start fresh session
    r = httpx.post(f"{BASE_URL}/api/reset?session_id=test_session_1")
    assert r.status_code == 200, f"Reset failed: {r.text}"
    
    # 2. Complete discovery interview with simulated inputs matching the 23 discovery questions
    answers = [
        "PVR INOX — Contract Intelligence Platform", # 1. q_client
        "PoC", # 2. q_tier
        "Automate legal contract analysis and compliance extraction", # 3. q_problem
        "6.0", # 4. q_duration
        "2026-10-05", # 5. q_start_date
        "Microsoft Azure", # 6. q_cloud
        "India", # 7. q_geography (9.0 hrs/day)
        "15% Shadow / Backup Capacity (Recommended)", # 8. q_buffer_strategy
        "1", # 9. q_usecases_count
        "4", # 10. q_personas_count
        "0", # 11. q_integrations_count
        "2", # 12. q_datasources_count
        "1", # 13. q_channels_count
        "1", # 14. q_languages_count
        "3", # 15. q_envs_count
        "6", # 16. q_components_count
        "Low", # 17. q_complexity
        "Internal policy only", # 18. q_compliance
        "Standard", # 19. q_security
        "200", # 20. q_named_users
        "50", # 21. q_concurrent_users
        "2000", # 22. q_daily_requests
        "None (single instance)", # 23. q_hadr_tier
        "Multi-Pass Agentic Extraction", # 24. q_multi_pass_policy
        "Human-in-the-Loop Assistive Gate" # 25. q_approval_gate
    ]
    
    for i, ans in enumerate(answers):
        res = httpx.post(f"{BASE_URL}/api/chat", json={
            "session_id": "test_session_1",
            "message": ans,
            "selected_option": ans
        })
        assert res.status_code == 200, f"Chat answer '{ans}' failed: {res.text}"
        data = res.json()
        print(f"Answered Q{i+1}: '{ans}' -> Next Q: {data.get('current_question', {}).get('title') if data.get('current_question') else 'COMPLETED'}, has_brd: {data.get('has_brd')}")
        
    assert data["has_brd"] == True, "BRD was not generated"
    brd = data["brd"]
    print(f"Generated BRD: {brd['project_title']}")
    print(f"Total Labour Cost: ${brd['total_labour_cost_usd']}")
    print(f"Day-Wise Schedule count: {len(brd['day_wise_schedule'])}")
    assert len(brd["day_wise_schedule"]) > 0, "Day-wise schedule is empty!"
    print(f"Sample Day 1: {brd['day_wise_schedule'][0]}")
    
    # 3. Test Re-plan endpoint
    r_replan = httpx.post(f"{BASE_URL}/api/replan", json={
        "session_id": "test_session_1",
        "overrides": {
            "q_tier": "Production Grade",
            "q_geography": "United Kingdom" # 7.0 hrs/day
        }
    })
    assert r_replan.status_code == 200, f"Replan failed: {r_replan.text}"
    replan_data = r_replan.json()
    new_brd = replan_data["brd"]
    print(f"Updated Tier: {new_brd['delivery_tier']}")
    print(f"Updated Daily Hours: {new_brd['daily_working_hours']}")
    assert new_brd["delivery_tier"] == "Production Grade"
    assert new_brd["daily_working_hours"] == 7.0
    print(f"Updated Day-Wise Schedule count: {len(new_brd['day_wise_schedule'])}")
    
    # 4. Test Admin APIs
    r_cals = httpx.get(f"{BASE_URL}/api/admin/calendars")
    assert r_cals.status_code == 200, f"Admin calendars failed: {r_cals.text}"
    cals = r_cals.json()
    print(f"Available Calendars: {list(cals.keys())}")
    assert "IN" in cals and "UK" in cals
    print(f"India daily working hours: {cals['IN'].get('daily_working_hours')}")
    print(f"UK daily working hours: {cals['UK'].get('daily_working_hours')}")
    assert cals['IN'].get('daily_working_hours') == 9.0
    assert cals['UK'].get('daily_working_hours') == 7.0
    
    print("ALL TESTS PASSED SUCCESSFULLY! [SUCCESS]")

if __name__ == "__main__":
    test_flow()
