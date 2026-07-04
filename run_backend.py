import uvicorn
import os
import sys
import subprocess
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    print("[+] Opening web browser to http://localhost:8000...")
    webbrowser.open("http://localhost:8000")

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    db_path = os.path.join(root_dir, "backend", "drainguard.db")
    
    # Check if database exists, generate if missing
    if not os.path.exists(db_path):
        print("[-] SQLite Database not found. Initializing synthetic datasets...")
        gen_script = os.path.join(root_dir, "backend", "data_generator.py")
        result = subprocess.run([sys.executable, gen_script], capture_output=True, text=True)
        if result.returncode == 0:
            print("[+] Database generated successfully.")
        else:
            print("[-] Database generation failed:")
            print(result.stderr)
            sys.exit(1)
            
    # Retrieve port from environment variable (specifically for Google Cloud Run compatibility)
    port = int(os.environ.get("PORT", 8000))
    print(f"[+] Starting DrainGuard AI Backend Server on http://localhost:{port}")
    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
