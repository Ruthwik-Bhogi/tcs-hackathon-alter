# hospital-digital-twin/__init__.py
"""
Top-level package initializer for Hospital Digital Twin POC.
Exposes package version and a small convenience import surface.
"""
from importlib.metadata import version, PackageNotFoundError

__all__ = ["__version__", "get_version"]

try:
    __version__ = version("hospital-digital-twin")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

def get_version() -> str:
    """Return package version string."""
    return __version__
