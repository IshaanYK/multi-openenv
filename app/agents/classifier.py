"""
Classifier Agent — Step 1 of the pipeline.
Uses OpenRouter LLM if OPENROUTER_API_KEY is set, otherwise falls back to rule-based NLP.
"""
import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger("classifier_agent")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def _rule_classify(text: str) -> dict:
    t = text.lower()
    urgent = any(w in t for w in {"urgent", "immediately", "asap", "frustrated", "critical"})

    if ("refund" in t or "order" in t or "charged" in t) and \
       ("schedule" in t or "meeting" in t or "call" in t):
        return {"category": "escalation", "priority": "high", "confidence": 0.92,
                "reasoning": "Both refund and scheduling keywords — compound escalation."}
    elif "refund" in t or "order" in t or "charged" in t or "payment" in t:
        return {"category": "refund", "priority": "high" if urgent else "medium",
                "confidence": 0.88, "reasoning": "Financial transaction keywords detected."}
    elif "schedule" in t or "meeting" in t or "sync" in t or "call" in t or \
         any(c in t for c in ["5pm", "6pm", "tomorrow", "calendar"]):
        return {"category": "meeting", "priority": "high" if urgent else "medium",
                "confidence": 0.85, "reasoning": "Scheduling/meeting intent detected."}
    elif "email" in t or "reply" in t or "respond" in t:
        return {"category": "communication", "priority": "medium",
                "confidence": 0.75, "reasoning": "Communication/reply intent detected."}
    return {"category": "general", "priority": "low", "confidence": 0.55,
            "reasoning": "No specific keywords matched — defaulting to general classification."}


def _llm_classify(text: str) -> Optional[dict]:
    if not OPENROUTER_KEY:
        return None
    try:
        import httpx
        prompt = f"""Classify this workplace task as JSON only:
Task: "{text}"
Respond with: {{"category":"meeting|refund|escalation|communication|general","priority":"low|medium|high","confidence":0.0-1.0,"reasoning":"one sentence"}}"""
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://huggingface.co/spaces", "X-Title": "AI Work OS"},
            json={"model": "mistralai/mistral-7b-instruct:free",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 150, "temperature": 0.1},
            timeout=10.0
        )
        content = r.json()["choices"][0]["message"]["content"].strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f"OpenRouter failed: {e}. Using rule-based fallback.")
    return None


def run(task_id: str, task_text: str) -> dict:
    logger.info(f"[Classifier] {task_id}")
    result = _llm_classify(task_text) or _rule_classify(task_text)
    result["used_llm"] = bool(_llm_classify.__doc__ and OPENROUTER_KEY and "skipped" not in str(result))
    result["agent"] = "Sophia (Classifier)"
    return result
