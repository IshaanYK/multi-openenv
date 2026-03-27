from app.models import TaskInput

EASY_TASKS = [
    TaskInput(
        task_id="task_1_easy",
        input="schedul a meting tomorow",
        priority="low",
        deadline=10,
        status="pending"
    )
]

MEDIUM_TASKS = [
    TaskInput(
        task_id="task_2_medium",
        input="Schedule a meeting with Jhon at 5pm ASAP",
        priority="medium",
        deadline=5,
        status="pending"
    )
]

HARD_TASKS = [
    TaskInput(
        task_id="task_3_hard",
        input="plz Refund my order #123 and schedule a call tomorrow morning",
        priority="high",
        deadline=3,
        status="pending"
    )
]

def generate_random_tasks(num_tasks: int = 3):
    import random
    all_tasks = EASY_TASKS + MEDIUM_TASKS + HARD_TASKS
    return random.choices(all_tasks, k=num_tasks)
