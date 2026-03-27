---
title: AI Work OS
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---


# AI Work OS – Multi-Agent Intelligent Environment



## Project Description
AI Work OS is an advanced, production-grade OpenEnv environment that acts as a real-world workplace simulation. The system challenges AI agents to handle multiple concurrent tasks (e.g., email handling, scheduling, and customer support) amid dynamic conditions including strict deadlines, task prioritization, unpredictable interruptions, simulated tool failures, and noisy or ambiguous user inputs.

## Environment Architecture & Multi-Agent System
The environment mimics complex real-world dynamics using an internal Multi-Agent subsystem that remains totally abstracted from the client:
1. **Sophia (Strategy):** Analyzes the task and assigns operational workflows by breaking down the complexity.
2. **Jackson (Operations):** Dispatches the operations via selected core tools (`send_email`, `schedule_meeting`, `process_refund`, `classify_text`) ensuring simulated execution boundaries and error rates.
3. **Avery (Quality Control):** Ensures standard-of-quality via reasoning checks, loop detection to prevent agent paralysis, and metric tracing.

Agents interact through logged messages viewable strictly in the observation space under `agent_logs`.

## Action Space
Submitted JSON structures are validated using typed models:
```json
{
  "task_id": "string",
  "action_type": "classify | schedule | refund | reply",
  "tool": "send_email | schedule_meeting | process_refund | classify_text",
  "message": "string",
  "metadata": {
    "intent": "string"
  },
  "reason": "string"
}
```

## Observation Space
The environment dynamically sorts task cues by priority and deadline into sequential observations:
```json
{
  "tasks": [
    {
      "task_id": "string",
      "input": "string",
      "priority": "low | medium | high",
      "deadline": "integer",
      "status": "pending | completed"
    }
  ],
  "history": [],
  "agent_logs": [],
  "step_count": 0,
  "performance_metrics": {}
}
```

## Reward Design & Grader Matrix
Environment feedback is highly punitive to reward precision matching its "production" moniker. Each task returns graded accuracy outputs.
Base reward metrics consist of: 25% correctness, 20% completion efficiency, 15% deadline efficiency, 15% priority queuing, 10% tool targeting, 10% valid logical reasoning, and 5% operational tone. 
Penalties are distributed for repeating failed actions (-0.3 loops) and over-stepping defined deadlines (-0.1 per step delay).

## Setup & Deployment Steps
1. Make sure Python 3.10 is installed.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Boot the environment locally using the built-in interface framework FastAPI via Uvicorn:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 7860
   ```
4. Access API definitions and interaction tests over the browser at: `http://localhost:7860/docs`.
5. **Hugging Face Deployment:** Simply attach this structure inside a new Hugging Face Space using the preset SDK configured docker environment. Port `7860` is natively wrapped.

http://127.0.0.1:7860