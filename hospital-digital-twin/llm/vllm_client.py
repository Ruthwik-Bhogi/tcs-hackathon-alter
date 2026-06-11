# llm/vllm_client.py
import httpx
import os
from llm.prompts import ALERT_TEMPLATE
import asyncio
import logging

logger = logging.getLogger("vllm_client")
logging.basicConfig(level=logging.INFO)

class VLLMClient:
    def __init__(self, endpoint=None, timeout=10):
        self.endpoint = endpoint or os.getenv("VLLM_ENDPOINT", "http://localhost:8000/generate")
        self.client = httpx.Client(timeout=timeout)

    def generate_alert(self, dept, current, pred, pct, horizon, staff, reason="model"):
        prompt = ALERT_TEMPLATE.format(
            dept=dept, current=current, pred=pred, pct=pct, horizon=horizon, staff=staff, reason=reason
        )
        payload = {"prompt": prompt, "max_tokens": 128, "temperature": 0.0}
        try:
            r = self.client.post(self.endpoint, json=payload)
            r.raise_for_status()
            data = r.json()
            text = data.get("text") or data.get("generated_text") or data.get("result") or ""
            return text.strip()
        except Exception as e:
            logger.error("LLM request failed: %s", e)
            return f"ALERT: (LLM unavailable) Predicted change {pct:.1f}% in {horizon}h for {dept}."

if __name__ == "__main__":
    c = VLLMClient()
    print(c.generate_alert("ED", 12, 16, 33.3, 4, 2.4))
