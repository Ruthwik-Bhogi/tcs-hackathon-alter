# simulator/__init__.py
"""
Simulator package public API.

Exports:
- Simulator: main simulation engine
- SyntheticGenerator: realistic data generator utilities
- Patient: lightweight patient record class
"""
from .engine import Simulator, Patient
from .data_gen import SyntheticGenerator

__all__ = ["Simulator", "Patient", "SyntheticGenerator"]

# lightweight logger for simulator
import logging
logger = logging.getLogger("hospital_dt.simulator")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [simulator] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
