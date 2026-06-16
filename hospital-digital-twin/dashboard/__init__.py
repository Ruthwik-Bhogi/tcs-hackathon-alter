# dashboard/__init__.py
"""
Dashboard package initializer.

Exports:
- app entrypoint (if used programmatically)
"""
from .app import main as run_app  # optional programmatic entrypoint

__all__ = ["run_app"]
