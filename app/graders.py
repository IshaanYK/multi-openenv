from app.models import AgentAction, GraderOutput

def grade_easy_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    """Grades REQ_101 (easy) — expects schedule/classify for meeting."""
    accuracy = 0.0
    if action.action_type in ("classify", "schedule"): accuracy += 0.5
    if "meeting" in action.metadata.get("intent", "").lower() or "meeting" in action.reason.lower(): accuracy += 0.5
    
    tool_usage = 1.0 if action.tool in ("classify_text", "schedule_meeting") else 0.3
    efficiency = max(0.0, 1.0 - (step_count / max(deadline, 1)))
    decision_quality = 1.0 if action.reason else 0.3

    final_score = round(0.30 * accuracy + 0.20 * efficiency + 0.20 * tool_usage + 0.15 * decision_quality + 0.15, 4)
    feedback = "Great scheduling response!" if accuracy >= 0.5 else "Try using 'schedule' action type with a meeting intent."
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)), feedback=feedback)


def grade_medium_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    """Grades REQ_202 (medium) — expects schedule_meeting tool."""
    accuracy = 0.0
    if action.action_type == "schedule": accuracy += 0.6
    if action.tool == "schedule_meeting": accuracy += 0.4

    efficiency = max(0.0, 1.0 - (step_count / max(deadline, 1)))
    tool_usage = 1.0 if action.tool == "schedule_meeting" else 0.0
    decision_quality = 1.0 if action.reason else 0.2

    final_score = round(0.30 * accuracy + 0.20 * efficiency + 0.20 * tool_usage + 0.15 * decision_quality + 0.15, 4)
    feedback = "Solid scheduling! Jackson handled it well." if accuracy >= 0.6 else "Use action_type='schedule' and tool='schedule_meeting'."
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)), feedback=feedback)


def grade_hard_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    """Grades REQ_303 (hard, escalation) — expects refund + scheduling."""
    accuracy = 0.0
    intent = action.metadata.get("intent", "").lower() + " " + action.reason.lower()
    if "refund" in intent: accuracy += 0.4
    if "meeting" in intent or "call" in intent or "schedule" in intent: accuracy += 0.3
    if action.action_type in ("refund", "schedule"): accuracy += 0.3
    accuracy = min(1.0, accuracy)

    tool_usage = 1.0 if action.tool in ("process_refund", "schedule_meeting") else 0.0
    efficiency = max(0.0, 1.0 - (step_count / max(deadline, 1)))
    decision_quality = 1.0 if action.reason else 0.1

    final_score = round(0.35 * accuracy + 0.20 * efficiency + 0.20 * tool_usage + 0.15 * decision_quality + 0.10, 4)
    feedback = "Excellent escalation handling!" if accuracy >= 0.6 else "Hard tasks need refund + scheduling — make sure your reason field explains the multi-step approach."
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)), feedback=feedback)


def _default_grader(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    """Fallback grader for interruption tasks: rewards any valid action."""
    accuracy = 0.5 if action.action_type in ("classify", "refund", "schedule", "reply") else 0.1
    efficiency = max(0.0, 1.0 - (step_count / max(deadline, 1)))
    final_score = round(0.4 * accuracy + 0.3 * efficiency + 0.3, 4)
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=0.5, tool_usage=0.5, final_score=min(1.0, final_score), feedback="Handling an unexpected interruption task.")


def get_grader(task_id: str):
    """Maps task_id to the correct grader function."""
    tid = task_id.upper()
    if "REQ_101" in tid or tid.startswith("EASY"):
        return grade_easy_task
    elif "REQ_202" in tid or tid.startswith("MEDIUM"):
        return grade_medium_task
    elif "REQ_303" in tid or tid.startswith("HARD"):
        return grade_hard_task
    # Interruption tasks or unknown — use default
    return _default_grader
