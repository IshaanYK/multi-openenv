"""
Planner Agent — Step 2. Maps classifier output to an execution plan.
"""
import logging

logger = logging.getLogger("planner_agent")

TOOL_MAP = {
    "meeting":       ("schedule", "schedule_meeting"),
    "refund":        ("refund",   "process_refund"),
    "escalation":    ("refund",   "process_refund"),
    "communication": ("reply",    "send_email"),
    "general":       ("classify", "classify_text"),
}

PLAN_TEMPLATES = {
    "meeting": [
        "1. Confirm meeting participants and preferred time slots",
        "2. Check calendar availability via integrator",
        "3. Book slot and send confirmation to all parties"
    ],
    "refund": [
        "1. Validate customer order ID and payment details",
        "2. Initiate refund through payment gateway",
        "3. Send confirmation email with refund ETA"
    ],
    "escalation": [
        "1. Triage: process refund immediately via payment gateway",
        "2. Schedule a follow-up call in calendar",
        "3. Send customer apology + resolution summary via SMTP"
    ],
    "communication": [
        "1. Parse intent and tone from incoming message",
        "2. Generate contextual reply draft",
        "3. Send via SMTP relay"
    ],
    "general": [
        "1. Extract key intent using NLP parser",
        "2. Route to appropriate specialist agent",
        "3. Log classification result for future reference"
    ]
}


def run(task_id: str, classifier_output: dict) -> dict:
    logger.info(f"[Planner] {task_id}")
    category = classifier_output.get("category", "general")
    action_type, tool = TOOL_MAP.get(category, ("classify", "classify_text"))
    steps = PLAN_TEMPLATES.get(category, PLAN_TEMPLATES["general"])
    plan_summary = (f"Priority {classifier_output.get('priority','low').upper()} task '{category}'. "
                    f"Primary tool: `{tool}`.")
    return {
        "agent": "Jackson (Planner)",
        "action_type": action_type,
        "tool": tool,
        "secondary_tool": "schedule_meeting" if category == "escalation" else None,
        "steps": steps,
        "plan_summary": plan_summary,
        "confidence": round(classifier_output.get("confidence", 0.7) * 0.95, 3)
    }
