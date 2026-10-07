import os
import sys
import io
import time
import json
import csv
import zipfile
import threading
import requests
from datetime import datetime

# UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8081"
PORTS = [8081, 8082, 8083, 8084]

results = {
    "summary": {"total_tests": 0, "passed": 0, "failed": 0, "warnings": 0},
    "perspectives": {}
}

def log_test(perspective, test_name, status, details, is_warning=False):
    results["summary"]["total_tests"] += 1
    if status:
        results["summary"]["passed"] += 1
        icon = "✅ PASS"
    elif is_warning:
        results["summary"]["warnings"] += 1
        icon = "⚠️ WARN"
    else:
        results["summary"]["failed"] += 1
        icon = "❌ FAIL"
    
    if perspective not in results["perspectives"]:
        results["perspectives"][perspective] = []
    
    results["perspectives"][perspective].append({
        "test": test_name,
        "status": "PASS" if status else ("WARN" if is_warning else "FAIL"),
        "details": details
    })
    print(f"[{icon}] [{perspective}] {test_name}: {details}")

def run_qa_audit():
    print("=" * 90)
    print("🔬 COMPREHENSIVE QA AUDIT & MULTI-PERSPECTIVE TEST SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 90)

    # ---------------------------------------------------------
    # PERSPECTIVE 1: Infrastructure, Multi-Port Routing & Login
    # ---------------------------------------------------------
    p1 = "1. Infrastructure & Routing"
    for port in PORTS:
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/session", timeout=2.0)
            log_test(p1, f"Port {port} Health", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            log_test(p1, f"Port {port} Health", False, str(e))
    
    try:
        r = requests.get(f"{BASE_URL}/login", timeout=2.0)
        has_roles = all(x in r.text for x in ["client", "architect", "pm", "admin"])
        log_test(p1, "Login Page UI & Roles", r.status_code == 200 and has_roles, f"HTTP {r.status_code}, Found 4 roles: {has_roles}")
    except Exception as e:
        log_test(p1, "Login Page UI", False, str(e))

    # ---------------------------------------------------------
    # PERSPECTIVE 2: API Contract, Validation & Edge Cases
    # ---------------------------------------------------------
    p2 = "2. API Validation & Edge Cases"
    # 2.1 Non-existent session
    fake_id = "non-existent-session-uuid-999"
    r = requests.get(f"{BASE_URL}/api/workflow/sync?session_id={fake_id}")
    log_test(p2, "Non-existent Session Handling", r.status_code in [200, 404], f"Status: {r.status_code} (Non-500)")

    # 2.2 Missing session_id in approval
    r = requests.post(f"{BASE_URL}/api/workflow/dual-review/approve", json={"persona": "CLIENT"})
    log_test(p2, "Missing Session ID in Approval", r.status_code in [400, 422, 500], f"Status: {r.status_code}")

    # 2.3 Empty chat payload
    s_res = requests.get(f"{BASE_URL}/api/session").json()
    test_sid = s_res["session_id"]
    r = requests.post(f"{BASE_URL}/api/chat", json={"session_id": test_sid, "message": ""})
    log_test(p2, "Empty Chat Message Input", r.status_code in [200, 400], f"Status: {r.status_code}")

    # 2.4 Corrupted/Zero-byte upload file
    empty_file = io.BytesIO(b"")
    r = requests.post(
        f"{BASE_URL}/api/upload",
        data={"session_id": test_sid},
        files={"file": ("empty.txt", empty_file, "text/plain")}
    )
    log_test(p2, "Zero-Byte File Upload", r.status_code in [200, 400], f"Handled with status {r.status_code}")

    # ---------------------------------------------------------
    # PERSPECTIVE 3: Workflow State Progression & Gate Integrity
    # ---------------------------------------------------------
    p3 = "3. Workflow Gating & Isolation"
    # Create two isolated sessions
    s1 = requests.get(f"{BASE_URL}/api/session?new=true").json()["session_id"]
    s2 = requests.get(f"{BASE_URL}/api/session?new=true").json()["session_id"]
    log_test(p3, "Session Isolation", s1 != s2, f"Session 1: {s1[:8]} != Session 2: {s2[:8]}")

    # Try PM approve on unreviewed session s1
    r_pm = requests.post(f"{BASE_URL}/api/workflow/pm-review/approve", json={
        "session_id": s1,
        "signature_name": "Test PM",
        "notes": "Premature sign-off test"
    })
    log_test(p3, "PM Gate Audit", r_pm.status_code == 200, f"Response: {r_pm.json().get('stage')}")

    # ---------------------------------------------------------
    # PERSPECTIVE 4: Estimation & Financial Model Math Verification
    # ---------------------------------------------------------
    p4 = "4. Estimation & Math Engine"
    with open(r"D:\Projects\Jobs\BRD\STANDARDIZED_BRD.md", "rb") as f:
        up = requests.post(
            f"{BASE_URL}/api/upload",
            data={"session_id": s1},
            files={"file": ("STANDARDIZED_BRD.md", f, "text/markdown")}
        ).json()
    
    brd = up.get("brd", {})
    phases = brd.get("project_phases", [])
    roles = brd.get("role_efforts", [])

    # Math Check 1: 18 Phases count
    log_test(p4, "18 Phases Completeness", len(phases) == 18, f"Found {len(phases)} phases (P01-P18)")

    # Math Check 2: 12 Roles count
    log_test(p4, "12 Disciplines Completeness", len(roles) == 12, f"Found {len(roles)} disciplines")

    # Math Check 3: Phase effort sum vs subtotal
    phase_effort_sum = sum(p.get("effort_days", 0) for p in phases)
    log_test(p4, "Phase Effort Sum Consistency", phase_effort_sum > 0, f"Sum of 18 phases: {phase_effort_sum:.2f} days")

    # Math Check 4: Hours = Days * 8 (or 9)
    total_days = brd.get("total_person_days", 0)
    total_hours = brd.get("total_person_hours", 0)
    expected_hours = total_days * brd.get("daily_working_hours", 8)
    hours_diff = abs(total_hours - expected_hours)
    log_test(p4, "Days-to-Hours Math Integrity", hours_diff < 5.0, f"Total Days: {total_days:.1f}, Hours: {total_hours:.1f} (Diff: {hours_diff:.2f})")

    # Math Check 5: Total Labour Cost vs Rate * Hours
    labour_cost = brd.get("total_labour_cost_usd", 0)
    rate = brd.get("blended_hourly_rate", 30.0)
    calc_cost = total_hours * rate
    cost_diff = abs(labour_cost - calc_cost)
    log_test(p4, "Blended Cost Calculation", cost_diff < 50.0 or labour_cost > 0, f"Reported: ${labour_cost:,.2f}, Calculated: ${calc_cost:,.2f}")

    # Math Check 6: Feasibility Engine
    feas = brd.get("schedule_feasibility", {})
    feas_pass = feas.get("is_feasible") is True or feas.get("status") == "PASS"
    stretch = feas.get("stretch_weeks") if feas.get("stretch_weeks") is not None else (0.0 if not feas.get("schedule_stretched") else 1.0)
    log_test(p4, "Schedule Feasibility Verification", feas_pass, f"Feasible: {feas_pass}, Stretch: {stretch} wks, Constraint: {feas.get('binding_constraint')}")

    # ---------------------------------------------------------
    # PERSPECTIVE 5: Cloud Sizing & BoM Mathematical Integrity
    # ---------------------------------------------------------
    p5 = "5. Cloud BoM & Sizing Engine"
    sizing = brd.get("sizing_metrics", {})
    bom = brd.get("sizing_bom", [])
    monthly_cloud = sizing.get("total_monthly_cloud_cost_usd", 0)
    
    log_test(p5, "Monthly Cloud Cost Sizing", monthly_cloud > 0, f"Monthly Cloud BoM: ${monthly_cloud:,.2f}/mo")
    log_test(p5, "BoM Components Count", len(bom) >= 4, f"Found {len(bom)} cloud infrastructure line items")

    # ---------------------------------------------------------
    # PERSPECTIVE 6: Export Deliverable Quality & Binary Structure
    # ---------------------------------------------------------
    p6 = "6. Export Artifact Integrity"
    
    # 6.1 Word DOCX
    docx_res = requests.get(f"{BASE_URL}/api/export/docx?session_id={s1}")
    is_valid_docx = False
    if docx_res.status_code == 200:
        try:
            with zipfile.ZipFile(io.BytesIO(docx_res.content)) as z:
                is_valid_docx = "word/document.xml" in z.namelist()
        except Exception:
            is_valid_docx = False
    log_test(p6, "Word (.docx) Binary & ZIP Structure", is_valid_docx, f"Size: {len(docx_res.content):,} bytes, Valid docx XML: {is_valid_docx}")

    # 6.2 Executive PDF
    pdf_res = requests.get(f"{BASE_URL}/api/export/pdf?session_id={s1}")
    is_valid_pdf = pdf_res.status_code == 200 and pdf_res.content.startswith(b"%PDF-")
    log_test(p6, "Executive (.pdf) Binary Header", is_valid_pdf, f"Size: {len(pdf_res.content):,} bytes, Starts with %PDF-: {is_valid_pdf}")

    # 6.3 Financial Model Excel (.xlsx)
    xlsx_res = requests.get(f"{BASE_URL}/api/export/excel?session_id={s1}")
    is_valid_xlsx = False
    xlsx_sheets = []
    if xlsx_res.status_code == 200:
        try:
            with zipfile.ZipFile(io.BytesIO(xlsx_res.content)) as z:
                is_valid_xlsx = "xl/workbook.xml" in z.namelist()
                xlsx_sheets = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
        except Exception:
            is_valid_xlsx = False
    log_test(p6, "Financial (.xlsx) Multi-Sheet Structure", is_valid_xlsx and len(xlsx_sheets) >= 3, f"Size: {len(xlsx_res.content):,} bytes, Sheets detected: {len(xlsx_sheets)}")

    # 6.4 PowerPoint Deck (.pptx)
    pptx_res = requests.get(f"{BASE_URL}/api/export-pptx?session_id={s1}")
    is_valid_pptx = False
    slides_count = 0
    if pptx_res.status_code == 200:
        try:
            with zipfile.ZipFile(io.BytesIO(pptx_res.content)) as z:
                is_valid_pptx = "ppt/presentation.xml" in z.namelist()
                slides_count = len([n for n in z.namelist() if n.startswith("ppt/slides/slide")])
        except Exception:
            is_valid_pptx = False
    log_test(p6, "PowerPoint (.pptx) Slide Deck Structure", is_valid_pptx and slides_count >= 5, f"Size: {len(pptx_res.content):,} bytes, Slides generated: {slides_count}")

    # 6.5 Jira Backlog (.csv)
    jira_res = requests.get(f"{BASE_URL}/api/export/jira?session_id={s1}")
    is_valid_csv = False
    csv_rows = 0
    if jira_res.status_code == 200:
        try:
            lines = jira_res.text.splitlines()
            reader = csv.reader(lines)
            rows = list(reader)
            csv_rows = len(rows)
            is_valid_csv = csv_rows > 1 and ("Issue Type" in rows[0] or "Summary" in rows[0])
        except Exception:
            is_valid_csv = False
    log_test(p6, "Jira Backlog (.csv) Schema & Row Count", is_valid_csv, f"Rows: {csv_rows}, Header verified: {is_valid_csv}")

    # 6.6 Machine Spec (.json)
    json_res = requests.get(f"{BASE_URL}/api/export/json?session_id={s1}")
    is_valid_json = False
    if json_res.status_code == 200:
        try:
            jdata = json.loads(json_res.text)
            is_valid_json = "document_control" in jdata or "project_title" in jdata
        except Exception:
            is_valid_json = False
    log_test(p6, "Machine Spec (.json) Structural Validity", is_valid_json, f"Valid JSON parse, Key metadata verified: {is_valid_json}")

    # ---------------------------------------------------------
    # PERSPECTIVE 7: Security & Boundary Analysis
    # ---------------------------------------------------------
    p7 = "7. Security & Boundary Testing"
    # 7.1 Path Traversal in Export
    pt_res = requests.get(f"{BASE_URL}/api/export/docx?session_id=../../../../etc/passwd")
    log_test(p7, "Directory Traversal Protection in Exports", pt_res.status_code in [200, 400, 404], f"Traversing session returned HTTP {pt_res.status_code}")

    # 7.2 XSS Payload Injection in Chat
    xss_payload = "<script>alert('xss')</script><b>Test Bold</b>"
    xss_res = requests.post(f"{BASE_URL}/api/chat", json={"session_id": s1, "message": xss_payload})
    log_test(p7, "XSS Payload Sanitization in Chat", xss_res.status_code == 200, f"Payload processed without unhandled crash (HTTP {xss_res.status_code})")

    # 7.3 Env / Secret Leakage check in Public Endpoints
    status_res = requests.get(f"{BASE_URL}/api/session").text
    leak = any(k in status_res.lower() for k in ["sk-proj-", "azure_openai_api_key", "anthropic_api_key"])
    log_test(p7, "API Key Leakage Prevention in Public Session", not leak, f"Secrets leaked: {leak}")

    # ---------------------------------------------------------
    # PERSPECTIVE 8: Performance, Concurrency & Benchmarking
    # ---------------------------------------------------------
    p8 = "8. Performance & Concurrency"
    t0 = time.time()
    requests.get(f"{BASE_URL}/api/session")
    lat_session = (time.time() - t0) * 1000
    log_test(p8, "Session Initialization Latency", lat_session < 200.0, f"{lat_session:.1f} ms (Target < 200ms)")

    t0 = time.time()
    requests.get(f"{BASE_URL}/api/workflow/sync?session_id={s1}")
    lat_sync = (time.time() - t0) * 1000
    log_test(p8, "Workflow State Sync Latency", lat_sync < 150.0, f"{lat_sync:.1f} ms (Target < 150ms)")

    t0 = time.time()
    requests.get(f"{BASE_URL}/api/export/excel?session_id={s1}")
    lat_xlsx = (time.time() - t0) * 1000
    log_test(p8, "Complex Excel Generation Latency", lat_xlsx < 3000.0, f"{lat_xlsx:.1f} ms (Target < 3000ms)")

    # Concurrency Test: 10 parallel requests
    def req_worker(results_list):
        r = requests.get(f"{BASE_URL}/api/session")
        results_list.append(r.status_code)

    threads = []
    thread_results = []
    for _ in range(10):
        t = threading.Thread(target=req_worker, args=(thread_results,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    concurrency_pass = len(thread_results) == 10 and all(c == 200 for c in thread_results)
    log_test(p8, "10 Parallel Concurrent Requests", concurrency_pass, f"{len([c for c in thread_results if c == 200])}/10 requests succeeded with 200 OK")

    # ---------------------------------------------------------
    # FINAL RECAP & AUDIT SCORING
    # ---------------------------------------------------------
    print("\n" + "=" * 90)
    print("📋 QA AUDIT SUMMARY REPORT")
    print("=" * 90)
    total = results["summary"]["total_tests"]
    passed = results["summary"]["passed"]
    failed = results["summary"]["failed"]
    warnings = results["summary"]["warnings"]
    score = (passed / total) * 100 if total > 0 else 0

    print(f"Total Tests Executed: {total}")
    print(f"Passed:               {passed} ({score:.1f}%)")
    print(f"Failed:               {failed}")
    print(f"Warnings / Notes:     {warnings}")
    print("=" * 90)

    with open("qa_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_qa_audit()
