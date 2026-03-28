"""
Planner Agent
──────────────
Step 2 of the pipeline. Takes Classifier output and builds an execution plan:
  - Selects the right tool
  - Sets action_type
  - Builds step-by-step plan description
  - Assigns confidence
"""
import logging

logger = logging.getLogger("planner_agent")

# Tool maps
TOOL_MAP = {
    "meeting":       ("schedule", "schedule_meeting"),
    "refund":        ("refund", "process_refund"),
    "escalation":    ("refund", "process_refund"),    # Primary step of escalation
    "communication": ("reply", "send_email"),
    "general":       ("classify", "classify_text"),
}

PLAN_TEMPLATES = {
    "meeting": [
        "1. Confirm meeting participants and preferred time slots",
        "2. Check calendar availability via integrator",
        "3. Book the slot and send confirmation to all parties"
    ],
    "refund": [
        "1. Validate customer order ID and payment details",
        "2. Initiate refund request through payment gateway",
        "3. Send confirmation email with refund ETA"
    ],
    "escalation": [
        "1. Triage: Process refund immediately via payment gateway",
        "2. Simultaneously schedule a follow-up call in calendar",
        "3. Send customer apology + resolution summary via SMTP"
    ],
    "communication": [
        "1. Parse intent and tone from incoming message",
        "2. Generate contextual reply draft",
        "3. Send via SMTP relay with appropriate priority"
    ],
    "general": [
        "1. Extract key intent from task using NLP parser",
        "2. Route to appropriate specialist agent",
        "3. Log classification result for future reference"
    ]
}


def run(task_id: str, classifier_output: dict) -> dict:
    """
    Runs the Planner Agent.
    Returns: action_type, tool, steps, plan_summary, agent
    """
    category = classifier_output.get("category", "general")
    priority = classifier_output.get("priority", "low")
    logger.info(f"[Planner] Building plan for category={category}, priority={priority}")

    action_type, tool = TOOL_MAP.get(category, ("classify", "classify_text"))

    # For escalations, second step needs scheduling too
    secondary_tool = None
    if category == "escalation":
        secondary_tool = "schedule_meeting"

    steps = PLAN_TEMPLATES.get(category, PLAN_TEMPLATES["general"])

    plan_summary = (
        f"Priority {priority.upper()} task classified as '{category}'. "
        f"Primary tool: `{tool}`. "
        + (f"Secondary: `{secondary_tool}`." if secondary_tool else "")
    )

    return {
        "agent": "Jackson (Planner)",
        "action_type": action_type,
        "tool": tool,
        "secondary_tool": secondary_tool,
        "steps": steps,
        "plan_summary": plan_summary,
        "confidence": round(classifier_output.get("confidence", 0.7) * 0.95, 3)
    }
