# llm/prompts.py
ALERT_TEMPLATE = """
You are an operations assistant for a hospital digital twin. Given the following structured facts, produce a concise, actionable alert (one sentence) and a short explanation (2-3 bullets). Use plain language and include the predicted percent change and timeframe.

Facts:
- department: {dept}
- current_count: {current}
- predicted_count: {pred}
- predicted_change_pct: {pct:.1f}
- horizon_hours: {horizon}
- staff_load: {staff:.2f}
- reason: {reason}

Output format:
ALERT: <one sentence>
EXPLAIN:
- <bullet 1>
- <bullet 2>
"""
