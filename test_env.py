import requests

BASE = "http://127.0.0.1:7860"

# RESET
r = requests.post(f"{BASE}/reset").json()
print("RESET:", r)

task_id = r["tasks"][0]["task_id"]

# STEP LOOP
for i in range(3):
    action = {
        "task_id": task_id,
        "action_type": "schedule",
        "tool": "schedule_meeting",
        "message": "Scheduling the meeting as requested",
        "reason": "User asked to schedule a meeting"
    }

    res = requests.post(f"{BASE}/step", json=action).json()
    print("STEP:", res)

    # 🔥 SAFE CHECK
    if "done" in res and res["done"]:
        break
    elif "detail" in res:
        print("ERROR FROM API:", res["detail"])
        break

# GRADER
print("GRADER:", requests.get(f"{BASE}/grader").json())