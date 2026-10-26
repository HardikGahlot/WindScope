import os
import sys
from pathlib import Path

# Add backend and project root directory to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "api" else CURRENT_DIR
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Signal serverless execution environment
os.environ["VERCEL"] = "1"

from app.main import app

# Export app for Vercel Python runtime
__all__ = ["app"]
