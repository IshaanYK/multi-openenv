"""
Classifier Agent
─────────────────
Step 1 of the pipeline. Given raw task text, produces:
  - category   (meeting | refund | escalation | communication | general)
  - priority   (low | medium | high)
  - confidence (0–1)
  - reasoning  (short explanation)

Uses OpenRouter LLM if OPENROUTER_API_KEY is set in env,
otherwise falls back to embedded rule-based NLP (always works offline).
"""
import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger("classifier_agent")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ─── Rule-Based NLP Fallback ─────────────────────────────────────────────────

def _rule_classify(text: str) -> dict:
    t = text.lower()
    urgency_words = {"urgent", "immediately", "asap", "frustrated", "critical", "now"}
    is_urgent = any(w in t for w in urgency_words)

    if ("refund" in t or "order " in t or "charged" in t or "payment" in t) \
       and ("schedule" in t or "meeting" in t or "call" in t):
        return {
            "category": "escalation",
            "priority": "high",
            "confidence": 0.92,
            "reasoning": "Task contains both financial (refund) and scheduling keywords — classified as a compound escalation requiring multi-step resolution."
        }
    elif "refund" in t or "order " in t or "charged" in t or "payment" in t:
        return {
            "category": "refund",
            "priority": "high" if is_urgent else "medium",
            "confidence": 0.88,
            "reasoning": "Detected financial transaction keywords. Routing to payment gateway for refund processing."
        }
    elif "schedule" in t or "meeting" in t or "sync" in t or "call" in t or any(c in t for c in ["5pm", "6pm", "tomorrow", "calendar"]):
        return {
            "category": "meeting",
            "priority": "high" if is_urgent else "medium",
            "confidence": 0.85,
            "reasoning": "Scheduling or meeting intent detected. Priority escalated due to urgency markers." if is_urgent else "Standard scheduling request. Routing to calendar integrator."
        }
    elif "email" in t or "reply" in t or "respond" in t or "send " in t:
        return {
            "category": "communication",
            "priority": "medium",
            "confidence": 0.75,
            "reasoning": "Communication/reply intent detected. Drafting contextual email response."
        }
    else:
        return {
            "category": "general",
            "priority": "low",
            "confidence": 0.55,
            "reasoning": "No specific keywords matched. Defaulting to general classification for further analysis."
        }


# ─── OpenRouter LLM Integration ──────────────────────────────────────────────

def _llm_classify(text: str) -> Optional[dict]:
    """Calls OpenRouter API. Returns None if unavailable."""
    if not OPENROUTER_KEY:
        return None
    try:
        import httpx
        prompt = f"""You are an intelligent task classifier for an AI Work OS.
Analyze the following workplace task and respond with ONLY a JSON object.

Task: "{text}"

Respond with exactly this JSON structure (no extra text):
{{
  "category": "meeting|refund|escalation|communication|general",
  "priority": "low|medium|high",
  "confidence": 0.0-1.0,
  "reasoning": "brief one-sentence explanation"
}}"""

        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://huggingface.co/spaces",
                "X-Title": "AI Work OS"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.1
            },
            timeout=10.0
        )
        content = response.json()["choices"][0]["message"]["content"].strip()
        # Extract JSON from response
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f"OpenRouter call failed: {e}. Using rule-based fallback.")
    return None


# ─── Public Interface ─────────────────────────────────────────────────────────

def run(task_id: str, task_text: str) -> dict:
    """
    Runs the Classifier Agent.
    Returns a dict with: category, priority, confidence, reasoning, used_llm
    """
    logger.info(f"[Classifier] Processing task: {task_id}")

    llm_result = _llm_classify(task_text)
    if llm_result:
        llm_result["used_llm"] = True
        llm_result["agent"] = "Sophia (AI Classifier)"
        return llm_result

    rule_result = _rule_classify(task_text)
    rule_result["used_llm"] = False
    rule_result["agent"] = "Sophia (Rule Classifier)"
    return rule_result
