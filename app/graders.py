from app.models import AgentAction, GraderOutput
import math

def grade_easy_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    accuracy = 1.0 if action.action_type == "classify" and action.metadata.get("intent") == "meeting" else 0.0
    tool_usage = 1.0 if action.tool == "classify_text" else 0.0
    efficiency = max(0.0, 1.0 - (step_count / deadline)) if deadline > 0 else 1.0
    decision_quality = 1.0 if "meeting" in action.reason.lower() else 0.5
    
    final_score = (0.25 * accuracy + 0.20 * max(accuracy, 0) + 0.15 * efficiency + 0.15 * 0.5 + 0.10 * tool_usage + 0.10 * decision_quality + 0.05 * 1.0)
    
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)))

def grade_medium_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    accuracy = 0.0
    if action.action_type == "schedule": accuracy += 0.5
    if action.metadata.get("intent") == "meeting": accuracy += 0.5
    
    tool_usage = 1.0 if action.tool == "schedule_meeting" else 0.0
    efficiency = max(0.0, 1.0 - (step_count / deadline)) if deadline > 0 else 1.0
    decision_quality = 1.0 if action.reason else 0.0
    
    final_score = (0.25 * accuracy + 0.20 * max(accuracy, 0) + 0.15 * efficiency + 0.15 * 0.8 + 0.10 * tool_usage + 0.10 * decision_quality + 0.05 * 1.0)
    
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)))

def grade_hard_task(action: AgentAction, step_count: int, deadline: int) -> GraderOutput:
    accuracy = 0.0
    intent_str = action.metadata.get("intent", "").lower()
    
    if "refund" in intent_str and "meeting" in intent_str: accuracy += 0.4
    elif "refund" in intent_str or "meeting" in intent_str: accuracy += 0.2
        
    if action.action_type in ["refund", "schedule"]: accuracy += 0.3
    
    tool_usage = 1.0 if action.tool in ["process_refund", "schedule_meeting"] else 0.0
    efficiency = max(0.0, 1.0 - (step_count / deadline)) if deadline > 0 else 1.0
    decision_quality = 1.0 if action.reason else 0.2
    
    final_score = (0.25 * accuracy + 0.20 * max(accuracy, 0) + 0.15 * efficiency + 0.15 * 1.0 + 0.10 * tool_usage + 0.10 * decision_quality + 0.05 * 1.0)
    
    return GraderOutput(accuracy=accuracy, efficiency=efficiency, decision_quality=decision_quality, tool_usage=tool_usage, final_score=min(1.0, max(0.0, final_score)))

def get_grader(task_id: str):
    if "easy" in task_id: return grade_easy_task
    elif "medium" in task_id: return grade_medium_task
    elif "hard" in task_id: return grade_hard_task
    return lambda a, s, d: GraderOutput(accuracy=0.0, efficiency=0.0, decision_quality=0.0, tool_usage=0.0, final_score=0.0)
