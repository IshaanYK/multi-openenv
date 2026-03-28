"""
Executor Agent
───────────────
Step 3 of the pipeline. Takes the plan and dispatches it to the environment.
Returns the step result, reward, grader feedback, and execution status.
"""
import logging
import time
from app.models import AgentAction
from app.env import AIWorkOSEnv

logger = logging.getLogger("executor_agent")


def run(task_id: str, planner_output: dict, classifier_output: dict, env: AIWorkOSEnv) -> dict:
    """
    Runs the Executor Agent.
    Dispatches the recommended action to the environment and returns results.
    """
    start = time.perf_counter()
    logger.info(f"[Executor] Dispatching action for task: {task_id}")

    action = AgentAction(
        task_id=task_id,
        action_type=planner_output["action_type"],
        tool=planner_output["tool"],
        message=planner_output["plan_summary"],
        reason=classifier_output.get("reasoning", ""),
        metadata={
            "intent": classifier_output.get("category", "general"),
            "confidence": classifier_output.get("confidence", 0.5),
            "planned_by": "Jackson (Planner)"
        }
    )

    state, reward, done, info = env.step(action)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    grader = info.get("grader", {})
    feedback = grader.get("feedback", "No feedback available.")
    final_score = grader.get("final_score", 0.0)

    status = "completed" if reward > 0.3 else "partial"
    if "error" in info:
        status = "failed"

    return {
        "agent": "Avery (Executor)",
        "status": status,
        "reward": round(reward, 4),
        "final_score": round(final_score, 4),
        "feedback": feedback,
        "elapsed_ms": elapsed_ms,
        "done": done,
        "state": state,
        "info": info
    }
