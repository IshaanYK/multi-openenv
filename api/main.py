from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.env import AIWorkOSEnv
from app.models import AgentAction, EnvironmentState, StepResponse, GraderOutput
from app.baseline import run_baseline
import app.tasks as tasks_module

app = FastAPI(title="AI Work OS - Multi-Agent Intelligent Environment")

# Static File Mounting - Only check once
STATIC_PATH = "static"
if os.path.exists(STATIC_PATH):
    app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

env = AIWorkOSEnv()

@app.get("/", include_in_schema=False)
def serve_index():
    index_path = os.path.join(STATIC_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Work OS - Dashboard static files missing."}

@app.get("/reset", response_model=EnvironmentState)
@app.post("/reset", response_model=EnvironmentState)
def reset_env():
    return env.reset()

@app.post("/step", response_model=StepResponse)
def step_env(action: AgentAction):
    state, reward, done, info = env.step(action)
    return StepResponse(
        observation=state,
        reward=reward,
        done=done,
        info=info
    )

@app.get("/state", response_model=EnvironmentState)
def get_state():
    return env.state()

@app.get("/tasks")
def get_tasks():
    def dump_with_diff(t, diff):
        d = t.model_dump() if hasattr(t, "model_dump") else t.dict()
        d["difficulty"] = diff
        return d
    
    all_tasks = (
        [dump_with_diff(t, "easy") for t in tasks_module.EASY_TASKS] +
        [dump_with_diff(t, "medium") for t in tasks_module.MEDIUM_TASKS] +
        [dump_with_diff(t, "hard") for t in tasks_module.HARD_TASKS]
    )
    
    return {
        "tasks": all_tasks,
        "action_schema": AgentAction.model_json_schema()
    }

@app.get("/grader", response_model=GraderOutput)
def get_graders():
    # Return actual performance metrics from the environment state
    metrics = env.state().performance_metrics
    return GraderOutput(
        accuracy=metrics.get("overall_accuracy", 0.0),
        efficiency=metrics.get("overall_efficiency", 0.0),
        decision_quality=metrics.get("decision_quality", 0.0),
        tool_usage=metrics.get("tool_usage", 0.0),
        final_score=metrics.get("total_reward", 0.0),
        feedback="Syncing performance from simulation engine..."
    )

@app.get("/baseline")
def run_baseline_endpoint():
    score = run_baseline()
    # Normalize score to [0.0, 1.0] for validation compliance
    normalized_score = max(0.0, min(1.0, float(score)))
    return {"score": normalized_score}
