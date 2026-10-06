import httpx
import json

BASE_URL = "http://127.0.0.1:8081"

def test_flow():
    # 1. Start fresh session
    r = httpx.post(f"{BASE_URL}/api/reset?session_id=test_session_1")
    assert r.status_code == 200, f"Reset failed: {r.text}"
    
    # 2. Complete discovery interview dynamically
    step = 0
    data = {"has_brd": False}
    while not data.get("has_brd") and step < 40:
        session_res = httpx.get(f"{BASE_URL}/api/session?session_id=test_session_1").json()
        cur_q = session_res.get("current_question")
        if not cur_q:
            break
        
        step += 1
        ans = cur_q.get("default_value") or (cur_q.get("options", [{}])[0].get("value")) or "Default Answer"
        
        res = httpx.post(f"{BASE_URL}/api/chat", json={
            "session_id": "test_session_1",
            "message": ans,
            "selected_option": ans
        })
        assert res.status_code == 200, f"Chat answer '{ans}' failed: {res.text}"
        data = res.json()
        print(f"Answered Q{step} ({cur_q.get('title')}): '{ans}' -> has_brd: {data.get('has_brd')}")
        
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
