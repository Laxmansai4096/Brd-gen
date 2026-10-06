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

PORTS = [8081, 8082, 8083, 8084, 8088]

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
    
    print("\n--- TESTING ALL 4 ADJACENT PERSONA PORTS + UNIFIED GATEWAY ---")
    with httpx.Client(timeout=5.0) as client:
        # 1. Test /api/ports
        res = client.get("http://127.0.0.1:8088/api/ports")
        assert res.status_code == 200
        print("[OK] Central Gateway /api/ports accessible")
        
        # 2. Test Port 8081 (Client)
        res8081 = client.get("http://127.0.0.1:8081/")
        assert res8081.status_code == 200
        assert "Multi-Port Persona" in res8081.text
        print("[OK] Port 8081 (Client Lead Elena Vance) - HTTP 200 OK")
        
        # 3. Test Port 8082 (Solutions Architect)
        res8082 = client.get("http://127.0.0.1:8082/")
        assert res8082.status_code == 200
        assert "Multi-Port Persona" in res8082.text
        print("[OK] Port 8082 (Solutions Architect Alex Morgan) - HTTP 200 OK")
        
        # 4. Test Port 8083 (Project Manager)
        res8083 = client.get("http://127.0.0.1:8083/")
        assert res8083.status_code == 200
        assert "Multi-Port Persona" in res8083.text
        print("[OK] Port 8083 (Delivery PM Marcus Reed) - HTTP 200 OK")
        
        # 5. Test Port 8084 (Admin)
        res8084 = client.get("http://127.0.0.1:8084/")
        assert res8084.status_code == 200
        assert "Multi-Port Persona" in res8084.text
        print("[OK] Port 8084 (Enterprise Admin & Governance) - HTTP 200 OK")
        
        # 6. Test Port 8088 (Unified Gateway)
        res8088 = client.get("http://127.0.0.1:8088/")
        assert res8088.status_code == 200
        print("[OK] Port 8088 (Unified Gateway) - HTTP 200 OK")
        
    print("\n--- ALL 5 ADJACENT LOCALHOST PORTS VERIFIED & SYNCHRONIZED! ---\n")

if __name__ == "__main__":
    test_all_ports()
