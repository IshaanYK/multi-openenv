from app.models import TaskInput

EASY_TASKS = [
    TaskInput(
        task_id="REQ_101",
        input="Hey, I need to schedule a meeting for tomorrow. Just a quick sync.",
        sender="Sarah (Marketing)",
        priority="low",
        deadline=10,
        status="pending"
    )
]

MEDIUM_TASKS = [
    TaskInput(
        task_id="REQ_202",
        input="Can you schedule a meeting with John at 5pm? It's pretty urgent.",
        sender="Michael (Product)",
        priority="medium",
        deadline=5,
        status="pending"
    )
]

HARD_TASKS = [
    TaskInput(
        task_id="REQ_303",
        input="Please refund order #123 immediately and schedule a follow-up call for tomorrow morning. The customer is frustrated.",
        sender="Elena (Customer Ops)",
        priority="high",
        deadline=3,
        status="pending"
    )
]

def generate_random_tasks(num_tasks: int = 3):
    import random
    all_tasks = EASY_TASKS + MEDIUM_TASKS + HARD_TASKS
    return random.choices(all_tasks, k=num_tasks)
