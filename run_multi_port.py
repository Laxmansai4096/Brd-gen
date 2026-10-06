import sys
import threading
import time
import uvicorn
from app import app

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORTS = [
    {"port": 8081, "persona": "CLIENT", "name": "Client Business Lead", "desc": "Client Ideation, Discovery & Dual Review Portal"},
    {"port": 8082, "persona": "SOLUTIONS_ARCHITECT", "name": "Principal Solutions Architect", "desc": "Technical Architecture, Sizing BoM & Dual Review Portal"},
    {"port": 8083, "persona": "PROJECT_MANAGER", "name": "Senior Delivery PM", "desc": "Project Governance, Tripartite Discussion & Final Approval Portal"},
    {"port": 8084, "persona": "ADMIN", "name": "System Administrator", "desc": "Enterprise Admin & Governance Console (Calendars, Rates, Master Settings)"}
]

def run_server_for_port(port: int):
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def start_all_persona_servers():
    print("=" * 80)
    print("STARTING 3-PERSONA & ADMIN MULTI-PORT LOCAL ENVIRONMENT")
    print("=" * 80)
    print("All interfaces share the exact same synchronized real-time backend state.\n")
    
    threads = []
    for item in PORTS:
        port = item["port"]
        name = item["name"]
        desc = item["desc"]
        print(f"  -> Port {port}: http://127.0.0.1:{port}  [{name}]")
        print(f"     └─ {desc}\n")
        
        t = threading.Thread(target=run_server_for_port, args=(port,), daemon=True)
        t.start()
        threads.append(t)
        
    print("=" * 80)
    print("All 4 Persona & Admin Localhost Ports are ACTIVE and running concurrently!")
    print("Press Ctrl+C to terminate all servers.")
    print("=" * 80)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all persona servers...")
        sys.exit(0)

if __name__ == "__main__":
    start_all_persona_servers()

