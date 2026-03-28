"""
Pipeline Orchestrator — runs Classifier → Planner → Executor in sequence.
"""
import logging
import time
from app.agents import classifier, planner, executor
from app.env import AIWorkOSEnv

logger = logging.getLogger("pipeline")


def run(task_id: str, task_text: str, env: AIWorkOSEnv) -> dict:
    t0 = time.perf_counter()
    logger.info(f"[Pipeline] {task_id}")

    stage1 = classifier.run(task_id, task_text)
    stage2 = planner.run(task_id, stage1)
    stage3 = executor.run(task_id, stage2, stage1, env)

    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    accuracy = stage3.get("final_score", 0.0)
    efficiency = max(0.0, round(1.0 - stage3.get("elapsed_ms", 500) / 5000, 3))

    return {
        "task_id": task_id,
        "task_text": task_text,
        "total_ms": total_ms,
        "classifier": stage1,
        "planner": stage2,
        "executor": stage3,
        "category":   stage1.get("category"),
        "priority":   stage1.get("priority"),
        "action":     stage2.get("plan_summary"),
        "steps":      stage2.get("steps", []),
        "tool":       stage2.get("tool"),
        "reasoning":  stage1.get("reasoning"),
        "feedback":   stage3.get("feedback"),
        "status":     stage3.get("status"),
        "used_llm":   stage1.get("used_llm", False),
        "accuracy":   accuracy,
        "efficiency": efficiency,
        "reward":     stage3.get("reward", 0.0),
        "confidence": stage1.get("confidence", 0.0),
        "observation": stage3.get("state"),
        "done":       stage3.get("done", False),
    }
