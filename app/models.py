from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class TaskInput(BaseModel):
    task_id: str
    input: str
    sender: str  # Added for humanization
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
    avatar: Optional[str] = None  # Added for humanization

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
    feedback: Optional[str] = ""  # Added for humanization

class StepResponse(BaseModel):
    observation: EnvironmentState
    reward: float
    done: bool
    info: Dict[str, Any]
