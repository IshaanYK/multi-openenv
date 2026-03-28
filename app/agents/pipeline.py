"""
Agent Pipeline Orchestrator
────────────────────────────
Runs the full 3-agent pipeline in sequence:
  Classifier → Planner → Executor

Returns a unified PipelineResult with all intermediate outputs.
"""
import logging
import time
from app.agents import classifier, planner, executor
from app.env import AIWorkOSEnv

logger = logging.getLogger("pipeline")


def run(task_id: str, task_text: str, env: AIWorkOSEnv) -> dict:
    """
    Full pipeline: Classifier → Planner → Executor.
    Returns a unified dict suitable for the PipelineResult model.
    """
    pipeline_start = time.perf_counter()
    logger.info(f"[Pipeline] Starting for task: {task_id}")

    # ── Stage 1: Classify ─────────────────────────────────────
    stage1 = classifier.run(task_id, task_text)

    # ── Stage 2: Plan ─────────────────────────────────────────
    stage2 = planner.run(task_id, stage1)

    # ── Stage 3: Execute ──────────────────────────────────────
    stage3 = executor.run(task_id, stage2, stage1, env)

    total_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)

    # Compute aggregate metrics
    accuracy = stage3.get("final_score", 0.0)
    efficiency = max(0.0, round(1.0 - (stage3.get("elapsed_ms", 500) / 5000), 3))
    reward = stage3.get("reward", 0.0)

    return {
        # Pipeline identity
        "task_id": task_id,
        "task_text": task_text,
        "total_ms": total_ms,

        # Stage outputs
        "classifier": stage1,
        "planner": stage2,
        "executor": stage3,

        # Top-level summary for easy consumption
        "category": stage1.get("category"),
        "priority": stage1.get("priority"),
        "action": stage2.get("plan_summary"),
        "steps": stage2.get("steps", []),
        "tool": stage2.get("tool"),
        "reasoning": stage1.get("reasoning"),
        "feedback": stage3.get("feedback"),
        "status": stage3.get("status"),
        "used_llm": stage1.get("used_llm", False),

        # Metrics
        "accuracy": accuracy,
        "efficiency": efficiency,
        "reward": reward,
        "confidence": stage1.get("confidence", 0.0),

        # Environment state
        "observation": stage3.get("state"),
        "done": stage3.get("done", False),
    }
