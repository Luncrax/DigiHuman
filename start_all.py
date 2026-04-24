#!/usr/bin/env python3
"""
Start DigiHuman frontend, backend, and the custom Qwen3-TTS WSL service.
"""
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"


def print_banner():
    print("=" * 48)
    print("DigiHuman Unified Startup")
    print("=" * 48)


def _start_windows_cmd(title: str, command: str, cwd: Path):
    subprocess.Popen(
        ["cmd.exe", "/c", "start", title, "cmd.exe", "/k", command],
        cwd=str(cwd),
    )


def start_qwen3_tts_wsl():
    print("\nStarting Qwen3-TTS WSL service...")
    distro = os.environ.get("QWEN3_TTS_WSL_DISTRO", "ubuntu")
    venv_name = os.environ.get("QWEN3_TTS_WSL_VENV", "flash_env")
    port = os.environ.get("QWEN3_TTS_WSL_PORT", "8010")
    repo_wsl_path = "/mnt/e/big_work/DigiHuman"
    qwen_source_wsl_path = "/mnt/e/big_work/Qwen3-TTS-main"

    wsl_command = (
        f"wsl -d {distro} bash -lc "
        f"\"cd {qwen_source_wsl_path} && "
        f"source {venv_name}/bin/activate && "
        f"python {repo_wsl_path}/backend/tts/qwen3_tts_wsl_server.py --host 0.0.0.0 --port {port}\""
    )
    _start_windows_cmd("Qwen3-TTS WSL", wsl_command, ROOT)


def start_backend():
    print("\nStarting backend service...")
    _start_windows_cmd("DigiHuman Backend", "python run_server.py", ROOT)


def start_frontend():
    print("\nStarting frontend service...")
    _start_windows_cmd("DigiHuman Frontend", "cmd /c npm run dev", FRONTEND_DIR)


def main():
    print_banner()

    start_qwen3_tts_wsl()
    time.sleep(3)

    start_backend()
    print("Waiting for backend startup...")
    time.sleep(5)

    start_frontend()

    print("\n" + "=" * 48)
    print("Startup commands launched")
    print("=" * 48)
    print("Qwen3-TTS service: http://127.0.0.1:8010")
    print("Backend service:   http://localhost:8001")
    print("Frontend service:  http://localhost:3000")
    print("=" * 48)

    if sys.stdin.isatty():
        input("Press Enter to exit this launcher...")


if __name__ == "__main__":
    main()
