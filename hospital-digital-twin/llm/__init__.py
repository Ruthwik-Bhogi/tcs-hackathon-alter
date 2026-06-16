# llm/__init__.py
"""
LLM client package.

Exports:
- VLLMClient: REST client wrapper for vLLM/TGI
- ALERT_TEMPLATE: canonical prompt template
"""
from .vllm_client import VLLMClient
from .prompts import ALERT_TEMPLATE

__all__ = ["VLLMClient", "ALERT_TEMPLATE"]

# configure llm logger
import logging
logger = logging.getLogger("hospital_dt.llm")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [llm] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
