# start_app.py
# Run from repo root:  py start_app.py
# Optional:            py start_app.py --port 8850
#
# This script launches uvicorn using the venv's Python, so you don't have to activate it.

import argparse
import os
import subprocess
import sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description="Start shasta-db (FastAPI) using the local venv.")
    parser.add_argument("--port", type=int, default=8844, help="Port to run on (default: 8844)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    os.chdir(root)

    venv_python = root / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"ERROR: venv python not found at: {venv_python}")
        print("Create it with: py -m venv .venv")
        return 1

    cmd = [
        str(venv_python),
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--port",
        str(args.port),
    ]

    print(f"Starting shasta-db on http://127.0.0.1:{args.port} ...")
    print(" ".join(cmd))

    # Run uvicorn and forward output to this console
    proc = subprocess.Popen(cmd)
    try:
        return proc.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
