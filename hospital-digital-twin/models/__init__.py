# models/__init__.py
"""
Models package API.

Exports:
- train_xgb: training utilities
- Predictor: prediction wrapper
"""
from .train_xgb import train, featurize  # training helpers
from .predict import Predictor

__all__ = ["train", "featurize", "Predictor"]

# small helper to locate default model path
from pathlib import Path
MODEL_PATH = Path(__file__).resolve().parent / "xgb_model.pkl"
