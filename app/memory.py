"""
Memory System
──────────────
Persistent JSON-based memory for the AI Work OS.
Stores past task decisions and outcomes, enabling a "learning effect" 
where the system can reference past decisions and show improvement.

Memory file: data/memory.json (auto-created)
"""
import json
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("memory")

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.json")


def _load() -> list:
    """Load all memory entries from disk."""
    try:
        os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Memory load failed: {e}")
    return []


def _save(entries: list):
    """Save memory entries to disk."""
    try:
        os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
        with open(MEMORY_PATH, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        logger.warning(f"Memory save failed: {e}")


def store(task_id: str, task_text: str, category: str, tool: str,
          status: str, reward: float, feedback: str):
    """Store a task outcome in persistent memory."""
    entries = _load()
    entries.append({
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": task_id,
        "task_text": task_text[:120],  # Truncate long text
        "category": category,
        "tool": tool,
        "status": status,
        "reward": reward,
        "feedback": feedback
    })
    # Keep last 200 entries max
    if len(entries) > 200:
        entries = entries[-200:]
    _save(entries)
    logger.info(f"[Memory] Stored outcome for {task_id}: {status} (reward={reward})")


def get_recent(n: int = 5) -> list:
    """Get the n most recent memory entries."""
    return _load()[-n:]


def get_stats() -> dict:
    """Compute aggregate stats from memory."""
    entries = _load()
    if not entries:
        return {"total_tasks": 0, "avg_reward": 0.0, "success_rate": 0.0, "top_category": "N/A"}

    total = len(entries)
    avg_reward = round(sum(e["reward"] for e in entries) / total, 3)
    successes = sum(1 for e in entries if e["status"] == "completed")
    success_rate = round(successes / total, 3)

    # Most common category
    from collections import Counter
    cats = Counter(e["category"] for e in entries)
    top_category = cats.most_common(1)[0][0] if cats else "N/A"

    return {
        "total_tasks": total,
        "avg_reward": avg_reward,
        "success_rate": success_rate,
        "top_category": top_category
    }


def get_context_hint(task_text: str) -> Optional[str]:
    """
    Look up past similar tasks and return a hint if found.
    This is the 'learning effect' — the system adapts based on past experience.
    """
    entries = _load()
    t = task_text.lower()
    for entry in reversed(entries):
        past = entry.get("task_text", "").lower()
        # Rough keyword overlap
        keywords = set(t.split()) & set(past.split())
        if len(keywords) >= 3 and entry["status"] == "completed":
            return (f"Similar past task resolved via `{entry['tool']}` "
                    f"with reward {entry['reward']}. Applying same strategy.")
    return None
