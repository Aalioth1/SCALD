"""Vercel entry point for the FastAPI application."""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "src" / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app

__all__ = ["app"]
