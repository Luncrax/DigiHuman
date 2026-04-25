#!/usr/bin/env python3
"""
Start DigiHuman frontend and backend services.
"""

import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)


def print_banner():
    print("=" * 48)
    print("DigiHuman Unified Startup")
    print("=" * 48)


def _start_windows_cmd(title: str, command: str, cwd: Path):
    """
    Start a normal Windows cmd window.
    Used for backend and frontend.
    """
    subprocess.Popen(
        ["cmd.exe", "/c", "start", title, "cmd.exe", "/k", command],
        cwd=str(cwd),
        creationflags=CREATE_NEW_CONSOLE,
    )


def start_backend():
    print("\nStarting backend service...")
    python_executable = sys.executable
    backend_command = f"\"{python_executable}\" run_server.py"
    _start_windows_cmd("DigiHuman Backend", backend_command, ROOT)


def start_frontend():
    print("\nStarting frontend service...")
    _start_windows_cmd("DigiHuman Frontend", "cmd /c npm run dev", FRONTEND_DIR)


def main():
    print_banner()

    start_backend()
    print("Waiting for backend startup...")
    time.sleep(5)

    start_frontend()

    print("\n" + "=" * 48)
    print("Startup commands launched")
    print("=" * 48)
    print("Backend service:   http://localhost:8001")
    print("Frontend service:  http://localhost:3000")
    print("=" * 48)

    if sys.stdin.isatty():
        input("Press Enter to exit this launcher...")


if __name__ == "__main__":
    main()
