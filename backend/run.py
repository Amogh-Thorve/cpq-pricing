"""
CPQ Platform - Backend Development Server Entrypoint

Run from the project root with:
    python backend/run.py

Or from the backend/ folder with:
    python run.py
"""
import sys
import os

# Ensure the project root is on the Python path so `backend.app.*` imports work.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"],
        log_level="info",
    )
