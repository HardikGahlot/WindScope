import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure VERCEL environment is recognized for serverless /tmp cache
if "VERCEL" not in os.environ:
    os.environ["VERCEL"] = "1"

from app.main import app

__all__ = ["app"]
