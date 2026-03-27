import random
import copy
from typing import Dict, Any, Tuple
from app.models import EnvironmentState, AgentAction, AgentLog
from app.tasks import EASY_TASKS, MEDIUM_TASKS, HARD_TASKS
from app.graders import get_grader

class InternalAgent:
    def __init__(self, role: str, name: str, avatar_id: int):
        self.role = role
        self.name = name
        self.avatar = f"https://i.pravatar.cc/150?u={avatar_id}"

    def evaluate(self, env_instance: Any, action: AgentAction) -> AgentLog:
        if self.role == "Planner":
            return AgentLog(**{"from": self.name, "to": "Jackson", "message": f"Strategy: I've validated the request. Proceed with {action.tool}.", "avatar": self.avatar})
        elif self.role == "Executor":
            status = "failed" if random.random() < 0.05 else "completed"
            return AgentLog(**{"from": self.name, "to": "Avery", "message": f"Ops: {action.action_type} using {action.tool} is {status}.", "avatar": self.avatar})
        elif self.role == "Reviewer":
            msg = "Review: Execution looks perfect." if action.reason else "Review: Could use more detail in the 'reason' field next time."
            return AgentLog(**{"from": self.name, "to": self.name, "message": msg, "avatar": self.avatar})
        return AgentLog(**{"from": "System", "to": "System", "message": "noop", "avatar": None})

class AIWorkOSEnv:
    def __init__(self):
        self.planner = InternalAgent("Planner", "Sophia", 11)
        self.executor = InternalAgent("Executor", "Jackson", 22)
        self.reviewer = InternalAgent("Reviewer", "Avery", 33)
        self.reset()
        
    def reset(self) -> EnvironmentState:
        self.tasks = [
            copy.deepcopy(random.choice(EASY_TASKS)),
            copy.deepcopy(random.choice(MEDIUM_TASKS)),
            copy.deepcopy(random.choice(HARD_TASKS))
        ]
        self.history = []
        self.agent_logs = []
        self.step_count = 0
        self.completed_tasks = []
        self.performance_metrics = {
            "overall_accuracy": 0.0,
            "overall_efficiency": 0.0,
            "total_reward": 0.0
        }
        return self.state()
        
    def state(self) -> EnvironmentState:
        priority_map = {"high": 3, "medium": 2, "low": 1}
        self.tasks.sort(key=lambda x: (-priority_map[x.priority], x.deadline))
        return EnvironmentState(
            tasks=self.tasks,
            history=self.history,
            agent_logs=self.agent_logs,
            step_count=self.step_count,
            performance_metrics=self.performance_metrics
        )
        
    def step(self, action: AgentAction) -> Tuple[EnvironmentState, float, bool, Dict[str, Any]]:
        self.step_count += 1
        reward = 0.0
        info = {}
        
        log1 = self.planner.evaluate(self, action)
        log2 = self.executor.evaluate(self, action)
        log3 = self.reviewer.evaluate(self, action)
        self.agent_logs.extend([log1, log2, log3])
        
        recent_actions = [h["action"] for h in self.history[-3:]]
        action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
        if action_dict in recent_actions:
            reward -= 0.5
            info["error"] = "Loop detected: repeated action"
            
        if "failed" in log2.message:
            reward -= 0.1
            info["status"] = "Simulated Tool failure. Retry necessary."
            
        if random.random() < 0.1:
            new_task = copy.deepcopy(random.choice(HARD_TASKS))
            new_task.task_id = f"urgent_interruption_{self.step_count}"
            new_task.priority = "high"
            new_task.deadline = 2
            self.tasks.append(new_task)
            
        target_task = next((t for t in self.tasks if t.task_id == action.task_id), None)
        
        if not target_task:
            reward -= 0.3
            info["error"] = "Target task for action not found."
            done = len(self.tasks) == 0 or self.step_count > 20
            return self.state(), reward, done, info
            
        if target_task.task_id.endswith("medium") or target_task.task_id.endswith("hard"):
            if action.action_type != "classify" and not any(h["action"]["task_id"] == action.task_id and h["action"]["action_type"] == "classify" for h in self.history):
                reward -= 0.3
                info["error"] = "Dependency failure: Classification required before execution."
                
        if self.step_count > target_task.deadline:
            reward -= 0.1 * (self.step_count - target_task.deadline)
            
        grader = get_grader(target_task.task_id)
        grader_output = grader(action, self.step_count, target_task.deadline)
        
        info["grader"] = grader_output.model_dump() if hasattr(grader_output, "model_dump") else grader_output.dict()
        
        if grader_output.final_score > 0.4 and "failed" not in log2.message:
            target_task.status = "completed"
            self.completed_tasks.append(target_task)
            self.tasks = [t for t in self.tasks if t.task_id != action.task_id]
            reward += grader_output.final_score
        else:
            reward += (grader_output.final_score * 0.5)
            
        self.performance_metrics["total_reward"] += reward
        self.performance_metrics["overall_accuracy"] = (self.performance_metrics["overall_accuracy"] + grader_output.accuracy) / 2
        
        self.history.append({
            "step": self.step_count,
            "action": action_dict,
            "reward": reward
        })
        
        done = len(self.tasks) == 0 or self.step_count >= 20
        return self.state(), reward, done, info
