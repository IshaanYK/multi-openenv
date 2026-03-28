"""
Executor Agent — Step 3. Dispatches the plan to the environment and returns results.
"""
import logging
import time
from app.models import AgentAction
from app.env import AIWorkOSEnv

logger = logging.getLogger("executor_agent")


def run(task_id: str, planner_output: dict, classifier_output: dict, env: AIWorkOSEnv) -> dict:
    logger.info(f"[Executor] {task_id}")
    start = time.perf_counter()

    action = AgentAction(
        task_id=task_id,
        action_type=planner_output["action_type"],
        tool=planner_output["tool"],
        message=planner_output["plan_summary"],
        reason=classifier_output.get("reasoning", ""),
        metadata={
            "intent": classifier_output.get("category", "general"),
            "confidence": classifier_output.get("confidence", 0.5)
        }
    )

    state, reward, done, info = env.step(action)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    grader = info.get("grader", {})

    return {
        "agent": "Avery (Executor)",
        "status": "completed" if reward > 0.3 else ("failed" if "error" in info else "partial"),
        "reward": round(reward, 4),
        "final_score": round(grader.get("final_score", 0.0), 4),
        "feedback": grader.get("feedback", "No feedback available."),
        "elapsed_ms": elapsed_ms,
        "done": done,
        "state": state,
        "info": info
    }
