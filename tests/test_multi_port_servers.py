import os
import sys
import time
import threading
import httpx

workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import uvicorn
from app import app

PORTS = [8081, 8082, 8083, 8084]

def run_server(port):
    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="error", access_log=False)
    server = uvicorn.Server(config)
    server.run()

def test_all_ports():
    threads = []
    for p in PORTS:
        t = threading.Thread(target=run_server, args=(p,), daemon=True)
        t.start()
        threads.append(t)
        
    time.sleep(2)  # Give servers a moment to bind
    
    print("\n--- TESTING ALL 3 PERSONA PORTS + ADMIN CONSOLE ---")
    with httpx.Client(timeout=5.0) as client:
        # 1. Test /api/ports on 8081
        res = client.get("http://127.0.0.1:8081/api/ports")
        assert res.status_code == 200
        print("[OK] Central /api/ports accessible")

        # 1b. Test /api/auth/roles
        res_roles = client.get("http://127.0.0.1:8081/api/auth/roles")
        assert res_roles.status_code == 200
        assert res_roles.json()["roles"]["SOLUTIONS_ARCHITECT"]["port"] == 8082
        print("[OK] /api/auth/roles returns correct port mappings")

        # 1c. Test /api/auth/login for dynamic user & role
        res_login = client.post("http://127.0.0.1:8081/api/auth/login", json={
            "username": "Sarah Chen",
            "password": "anypassword",
            "role": "PROJECT_MANAGER"
        })
        assert res_login.status_code == 200
        login_data = res_login.json()
        assert login_data["user"]["target_port"] == 8083
        assert login_data["user"]["username"] == "Sarah Chen"
        print("[OK] /api/auth/login correctly resolves custom username & target port :8083")
        
        # 2. Test Port 8081 (Client)
        res8081 = client.get("http://127.0.0.1:8081/")
        assert res8081.status_code == 200
        print("[OK] Port 8081 (Client Business Lead) - HTTP 200 OK")
        
        # 3. Test Port 8082 (Solutions Architect)
        res8082 = client.get("http://127.0.0.1:8082/")
        assert res8082.status_code == 200
        print("[OK] Port 8082 (Principal Solutions Architect) - HTTP 200 OK")
        
        # 4. Test Port 8083 (Project Manager)
        res8083 = client.get("http://127.0.0.1:8083/")
        assert res8083.status_code == 200
        print("[OK] Port 8083 (Senior Delivery PM) - HTTP 200 OK")
        
        # 5. Test Port 8084 (Admin)
        res8084 = client.get("http://127.0.0.1:8084/")
        assert res8084.status_code == 200
        print("[OK] Port 8084 (Enterprise Admin & Governance) - HTTP 200 OK")
        
    print("\n--- ALL 4 LOCALHOST PORTS VERIFIED & SYNCHRONIZED! ---\n")

if __name__ == "__main__":
    test_all_ports()
