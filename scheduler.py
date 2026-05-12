from datetime import date, datetime
from database import Database
import logging

log = logging.getLogger(__name__)


class DailyScheduler:
    """Computes today's work plan and can run scheduled reminders."""

    def __init__(self, db: Database):
        self.db = db

    def get_todays_plan(self) -> list[dict]:
        """Return a list of tasks the user should work on today."""
        upcoming = self.db.get_upcoming(days=14)
        today = date.today()
        plan = []

        for a in upcoming:
            deadline_date = datetime.strptime(a["deadline"], "%Y-%m-%d").date()
            days_left = (deadline_date - today).days

            # Find today's slot in the daily_plan
            hours_today = 0
            task_desc = "Work on assignment"
            for slot in a.get("daily_plan", []):
                if slot.get("day") == today.isoformat():
                    hours_today = slot.get("hours", 1)
                    task_desc = slot.get("task", task_desc)
                    break

            # If no slot found but deadline close, suggest minimum
            if hours_today == 0 and days_left <= 2:
                hours_today = max(1, round((a["estimated_hours"] * (1 - a["progress"] / 100)) / max(days_left, 1), 1))

            if hours_today > 0 or days_left <= 1:
                plan.append({
                    "id": a["id"],
                    "subject": a["subject"],
                    "deadline": a["deadline"],
                    "days_left": days_left,
                    "hours_today": hours_today,
                    "task": task_desc,
                    "progress": a["progress"]
                })

        return plan

    def print_daily_summary(self):
        """Print a text summary (used for terminal / cron reminders)."""
        plan = self.get_todays_plan()
        today_str = date.today().strftime("%A, %d %B %Y")
        print(f"\n{'='*50}")
        print(f"  Assignment Manager — {today_str}")
        print(f"{'='*50}")
        if not plan:
            print("  ✅ Nothing urgent today. Keep up the good work!")
        else:
            for item in plan:
                print(f"\n  📌 {item['subject']}")
                print(f"     Deadline : {item['deadline']} ({item['days_left']}d left)")
                print(f"     Today    : {item['hours_today']} hrs — {item['task']}")
                print(f"     Progress : {item['progress']}%")
        print(f"{'='*50}\n")


# ── Run as standalone cron/reminder ──────────────────────────────────────────
if __name__ == "__main__":
    db = Database()
    scheduler = DailyScheduler(db)
    scheduler.print_daily_summary()
