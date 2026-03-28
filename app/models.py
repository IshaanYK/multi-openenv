from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class TaskInput(BaseModel):
    task_id: str
    input: str
    sender: str
    priority: Literal["low", "medium", "high"]
    deadline: int
    status: Literal["pending", "completed"]

class AgentAction(BaseModel):
    task_id: str
    action_type: Literal["classify", "schedule", "refund", "reply"]
    tool: Literal["send_email", "schedule_meeting", "process_refund", "classify_text"]
    message: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reason: Optional[str] = ""

class AgentLog(BaseModel):
    from_agent: str = Field(alias="from")
    to_agent: str = Field(alias="to")
    message: Optional[str] = ""
    avatar: Optional[str] = None

class EnvironmentState(BaseModel):
    tasks: List[TaskInput]
    history: List[Dict[str, Any]]
    agent_logs: List[AgentLog]
    step_count: int
    performance_metrics: Dict[str, float]

class GraderOutput(BaseModel):
    accuracy: float
    efficiency: float
    decision_quality: float
    tool_usage: float
    final_score: float
    feedback: Optional[str] = ""

class StepResponse(BaseModel):
    observation: EnvironmentState
    reward: float
    done: bool
    info: Dict[str, Any]

# ─── Multi-Agent Pipeline Models ─────────────────────────────────

class ClassifierResult(BaseModel):
    agent: str
    category: str
    priority: str
    confidence: float
    reasoning: str
    used_llm: bool = False

class PlannerResult(BaseModel):
    agent: str
    action_type: str
    tool: str
    secondary_tool: Optional[str] = None
    steps: List[str]
    plan_summary: str
    confidence: float

class ExecutorResult(BaseModel):
    agent: str
    status: str
    reward: float
    final_score: float
    feedback: str
    elapsed_ms: float
    done: bool

class PipelineResult(BaseModel):
    task_id: str
    task_text: str
    total_ms: float

    # Stage results
    classifier: Dict[str, Any]
    planner: Dict[str, Any]
    executor: Dict[str, Any]

    # Top-level summary
    category: str
    priority: str
    action: str
    steps: List[str]
    tool: str
    reasoning: str
    feedback: str
    status: str
    used_llm: bool = False
    memory_hint: Optional[str] = None

    # Metrics
    accuracy: float
    efficiency: float
    reward: float
    confidence: float

    # Environment
    observation: Optional[EnvironmentState] = None
    done: bool = False
