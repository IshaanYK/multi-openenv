import concurrent.futures
from app.env import AIWorkOSEnv
from app.models import AgentAction

def _process_task(env: AIWorkOSEnv, task_id: str, input_str: str) -> float:
    """Synchronous task processor for the baseline agent."""
    total_reward = 0.0
    input_lower = input_str.lower()

    # Step 1: Classify
    intent = "general"
    if "refund" in input_lower and ("schedule" in input_lower or "call" in input_lower):
        intent = "refund and meeting"
    elif "refund" in input_lower or "order" in input_lower:
        intent = "refund"
    elif "schedule" in input_lower or "meeting" in input_lower or "sync" in input_lower:
        intent = "meeting"

    classify_action = AgentAction(
        task_id=task_id,
        action_type="classify",
        tool="classify_text",
        message="Classifying task intent for routing.",
        metadata={"intent": intent},
        reason="Always classify before executing specialized tools."
    )
    state, reward, done, info = env.step(classify_action)
    total_reward += reward

    if done or task_id not in [t.task_id for t in state.tasks]:
        return total_reward

    # Step 2: Execute
    action_type, tool = "reply", "send_email"
    if "refund" in intent:
        action_type, tool = "refund", "process_refund"
    elif "meeting" in intent:
        action_type, tool = "schedule", "schedule_meeting"

    exec_action = AgentAction(
        task_id=task_id,
        action_type=action_type,
        tool=tool,
        message=f"Executing {action_type} using {tool}.",
        metadata={"intent": intent},
        reason=f"Dispatching optimal tool '{tool}' based on classification result."
    )
    state, reward, done, info = env.step(exec_action)
    total_reward += reward
    return total_reward


def run_baseline() -> float:
    """Runs the baseline agent synchronously — safe to call from FastAPI."""
    env = AIWorkOSEnv()
    state = env.reset()
    total_reward = 0.0

    while state.tasks and env.step_count < 20:
        task = state.tasks[0]
        reward = _process_task(env, task.task_id, task.input)
        total_reward += reward
        state = env.state()

    # Normalize to [0, 1]
    return round(max(0.0, min(1.0, total_reward / max(1, len(env.completed_tasks) or 1))), 4)


if __name__ == "__main__":
    score = run_baseline()
    print(f"Baseline Score: {score:.4f}")
