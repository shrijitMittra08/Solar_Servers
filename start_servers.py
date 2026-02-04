#!/usr/bin/env python3
"""
SolarServers Startup Script
Starts both backend and frontend servers automatically
"""

import subprocess
import sys
import os
import time
import signal
import platform

def get_python_cmd():
    """Get the correct Python command for the virtual environment"""
    if platform.system() == "Windows":
        venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            return venv_python
    else:
        venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")
        if os.path.exists(venv_python):
            return venv_python
    return sys.executable

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting backend server on port 8000...")
    python_cmd = get_python_cmd()
    cmd = [
        python_cmd, "-m", "uvicorn",
        "SolarServers_server:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    return subprocess.Popen(cmd, cwd=os.getcwd())

def start_frontend():
    """Start the frontend HTTP server"""
    print("Starting frontend server on port 3000...")
    python_cmd = get_python_cmd()
    cmd = [python_cmd, "-m", "http.server", "3000"]
    return subprocess.Popen(cmd, cwd=os.path.join(os.getcwd(), "frontend"))

def main():
    print("SolarServers - Starting servers...")
    print("=" * 50)

    # Check if virtual environment exists
    venv_path = os.path.join(os.getcwd(), ".venv")
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found!")
        print("Please run: python -m venv .venv")
        print("Then activate it and install requirements:")
        print("  .venv\\Scripts\\activate  # Windows")
        print("  pip install -r Requirements.txt")
        return

    # Start backend
    backend_process = start_backend()
    time.sleep(3)  # Give backend time to start

    # Start frontend
    frontend_process = start_frontend()
    time.sleep(1)  # Give frontend time to start

    print("\n" + "=" * 50)
    print("✅ Servers started successfully!")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("\nPress Ctrl+C to stop all servers")
    print("=" * 50)

    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")

        # Terminate processes
        backend_process.terminate()
        frontend_process.terminate()

        # Wait for clean shutdown
        backend_process.wait()
        frontend_process.wait()

        print("✅ All servers stopped. Goodbye!")

if __name__ == "__main__":
    main()