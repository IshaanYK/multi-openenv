import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.env import AIWorkOSEnv
from app.models import AgentAction, EnvironmentState, StepResponse, GraderOutput, PipelineResult
from app.baseline import run_baseline
from app.agents import pipeline as agent_pipeline
from app import memory
import app.tasks as tasks_module

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ai_work_os")

app = FastAPI(title="AI Work OS — Multi-Agent Intelligent Environment")

STATIC_PATH = "static"
if os.path.exists(STATIC_PATH):
    app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

env = AIWorkOSEnv()

# ─── Request Models ──────────────────────────────────────────────

class RunAgentRequest(BaseModel):
    task_id: str
    task_text: str

# ─── UI ─────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_index():
    idx = os.path.join(STATIC_PATH, "index.html")
    return FileResponse(idx) if os.path.exists(idx) else {"status": "AI Work OS running — UI not found"}

# ─── Environment ─────────────────────────────────────────────────

@app.get("/reset", response_model=EnvironmentState)
@app.post("/reset", response_model=EnvironmentState)
def reset_env():
    logger.info("Environment reset.")
    return env.reset()

@app.get("/state", response_model=EnvironmentState)
def get_state():
    return env.state()

@app.post("/step", response_model=StepResponse)
def step_env(action: AgentAction):
    state, reward, done, info = env.step(action)
    return StepResponse(observation=state, reward=reward, done=done, info=info)

# ─── Tasks ───────────────────────────────────────────────────────

@app.get("/tasks")
def get_tasks():
    def dump(t, diff):
        d = t.model_dump() if hasattr(t, "model_dump") else t.dict()
        d["difficulty"] = diff
        return d
    all_tasks = (
        [dump(t, "easy") for t in tasks_module.EASY_TASKS] +
        [dump(t, "medium") for t in tasks_module.MEDIUM_TASKS] +
        [dump(t, "hard") for t in tasks_module.HARD_TASKS]
    )
    return {"tasks": all_tasks, "action_schema": AgentAction.model_json_schema()}

# ─── Multi-Agent Pipeline ─────────────────────────────────────────

@app.post("/run-pipeline")
def run_pipeline(req: RunAgentRequest):
    """
    Full 3-agent pipeline: Classifier → Planner → Executor.
    Returns all intermediate outputs, metrics, and environment state.
    """
    logger.info(f"[Pipeline] Running for task: {req.task_id}")

    # Get memory context hint
    hint = memory.get_context_hint(req.task_text)

    result = agent_pipeline.run(req.task_id, req.task_text, env)
    result["memory_hint"] = hint

    # Store outcome in memory
    memory.store(
        task_id=req.task_id,
        task_text=req.task_text,
        category=result.get("category", "general"),
        tool=result.get("tool", "classify_text"),
        status=result.get("status", "unknown"),
        reward=result.get("reward", 0.0),
        feedback=result.get("feedback", "")
    )

    return result

# ─── Legacy Run-Agent (kept for backwards compat) ─────────────────

@app.post("/run-agent")
def run_agent(req: RunAgentRequest):
    """Quick classify without executing. Returns classifier output only."""
    from app.agents import classifier
    result = classifier.run(req.task_id, req.task_text)
    hint = memory.get_context_hint(req.task_text)

    # Map to frontend-compatible shape
    tool_map = {
        "meeting": ("schedule", "schedule_meeting"),
        "refund": ("refund", "process_refund"),
        "escalation": ("refund", "process_refund"),
        "communication": ("reply", "send_email"),
        "general": ("classify", "classify_text"),
    }
    action_type, tool = tool_map.get(result["category"], ("classify", "classify_text"))
    return {
        **result,
        "action_type": action_type,
        "tool": tool,
        "action": f"Recommended: use `{tool}` with action type `{action_type}`.",
        "memory_hint": hint
    }

@app.post("/dispatch")
def dispatch_action(req: RunAgentRequest):
    """Alias for /run-pipeline — auto-analyze and dispatch."""
    return run_pipeline(req)

# ─── Grader & Metrics ─────────────────────────────────────────────

@app.get("/grader", response_model=GraderOutput)
def get_grader():
    metrics = env.state().performance_metrics
    return GraderOutput(
        accuracy=metrics.get("overall_accuracy", 0.0),
        efficiency=metrics.get("overall_efficiency", 0.0),
        decision_quality=metrics.get("decision_quality", 0.0),
        tool_usage=metrics.get("tool_usage", 0.0),
        final_score=metrics.get("total_reward", 0.0),
        feedback="Live metrics from simulation engine."
    )

@app.get("/memory")
def get_memory():
    """Returns recent memory entries and aggregate stats."""
    return {
        "recent": memory.get_recent(10),
        "stats": memory.get_stats()
    }

# ─── Baseline ────────────────────────────────────────────────────

@app.get("/baseline")
def run_baseline_endpoint():
    logger.info("Baseline agent run requested.")
    try:
        score = run_baseline()
        return {"score": max(0.0, min(1.0, float(score)))}
    except Exception as e:
        logger.error(f"Baseline failed: {e}")
        return {"score": 0.0, "error": str(e)}
