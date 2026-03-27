import asyncio
from app.env import AIWorkOSEnv
from app.models import AgentAction

async def process_task(env: AIWorkOSEnv, task_id: str, input_str: str) -> float:
    total_reward = 0.0
    input_lower = input_str.lower()
    
    classify_action = AgentAction(
        task_id=task_id,
        action_type="classify",
        tool="classify_text",
        message="Running async classification via text intent model",
        metadata={"intent": "general extraction"},
        reason="Always perform required text classification step prior to tooling usage."
    )
    
    if "refund" in input_lower and "schedule" in input_lower:
        classify_action.metadata["intent"] = "refund and meeting"
    elif "schedule" in input_lower or "meting" in input_lower:
        classify_action.metadata["intent"] = "meeting"
    elif "refund" in input_lower:
        classify_action.metadata["intent"] = "refund"
        
    state, reward, done, info = env.step(classify_action)
    total_reward += reward
    
    if done or task_id not in [t.task_id for t in state.tasks]:
        return total_reward
        
    exec_action = AgentAction(
        task_id=task_id,
        action_type="reply",
        tool="send_email",
        message="Executing determined operation asynchronously",
        metadata=classify_action.metadata,
        reason="Executing optimal sub-task logic pipeline based on prior step completion."
    )
    
    if "refund" in classify_action.metadata.get("intent", ""):
        exec_action.action_type = "refund"
        exec_action.tool = "process_refund"
    elif "meeting" in classify_action.metadata.get("intent", ""):
        exec_action.action_type = "schedule"
        exec_action.tool = "schedule_meeting"
        
    state, reward, done, info = env.step(exec_action)
    total_reward += reward
    
    return total_reward

async def run_baseline_async() -> float:
    env = AIWorkOSEnv()
    state = env.reset()
    total_reward = 0.0
    
    while True:
        if not state.tasks:
            break
        task = state.tasks[0]
        reward = await process_task(env, task.task_id, task.input)
        total_reward += reward
        state = env.state()
        if env.step_count > 20: break
            
    return total_reward

def run_baseline() -> float:
    return asyncio.run(run_baseline_async())

if __name__ == "__main__":
    score = run_baseline()
    print(f"Async Baseline Score: {score:.3f}")
