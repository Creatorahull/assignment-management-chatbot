import os
import json
import logging
from pathlib import Path
from datetime import datetime, date, timedelta

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from groq import Groq
except ImportError:
    Groq = None

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename="logs/agent.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)


class AssignmentAgent:
    """Core AI agent: extracts text, sends to Groq, parses structured output."""

    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")

        if Groq and groq_key:
            self.client = Groq(api_key=groq_key)
            log.info("Groq client initialized.")
        else:
            self.client = None
            log.warning("Groq client not initialized — set GROQ_API_KEY in .env")

    # ── PDF Extraction ─────────────────────────────────────────────────────────
    def extract_pdf(self, path: str) -> str:
        """Extract plain text from a PDF file using pdfplumber."""
        if not pdfplumber:
            raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        full_text = "\n".join(text_parts)
        log.info(f"Extracted {len(full_text)} chars from {path}")
        return full_text

    # ── Main Process ───────────────────────────────────────────────────────────
    def process(self, text: str, subject: str = "", manual_deadline: str = "") -> dict:
        """
        Send assignment text to Groq.
        Returns a dict with: solution, subject, deadline, estimated_hours, daily_plan.
        """
        if not self.client:
            return self._mock_response(text, subject, manual_deadline)

        prompt = self._build_prompt(text, subject, manual_deadline)
        log.info("Sending to Groq API...")

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            raw = response.choices[0].message.content
            log.info("Received response from Groq.")
            return self._parse_response(raw, subject, manual_deadline)

        except Exception as e:
            log.error(f"Groq API error: {e}")
            return {
                "solution": f"❌ Groq API Error: {str(e)}\n\nCheck your key at https://console.groq.com",
                "subject": subject or "Unknown",
                "deadline": manual_deadline or "Unknown",
                "estimated_hours": 0,
                "daily_plan": []
            }

    # ── Prompts ────────────────────────────────────────────────────────────────
    def _system_prompt(self) -> str:
        return """You are an expert academic assistant and assignment manager.

When given assignment text, you must:
1. Solve all questions clearly and thoroughly with step-by-step explanations.
2. Extract the deadline from the text if present (format: YYYY-MM-DD).
3. Estimate total hours needed to complete the assignment.
4. Suggest a daily study plan to complete it before the deadline.

Always respond in this exact JSON format:
{
  "subject": "detected or provided subject name",
  "solution": "full markdown solution with headings per question",
  "deadline": "YYYY-MM-DD or null if not found",
  "estimated_hours": 5,
  "daily_plan": [
    {"day": "2025-03-20", "task": "Complete Q1 and Q2", "hours": 2},
    {"day": "2025-03-21", "task": "Complete Q3 and review", "hours": 3}
  ]
}

Return ONLY the JSON, no preamble, no markdown fences."""

    def _build_prompt(self, text: str, subject: str, manual_deadline: str) -> str:
        today = date.today().isoformat()
        return f"""Today's date: {today}
Subject (if known): {subject or 'Not specified'}
Manual deadline override: {manual_deadline or 'Not provided — extract from text if present'}

--- ASSIGNMENT TEXT START ---
{text[:8000]}
--- ASSIGNMENT TEXT END ---

Analyze this assignment and respond in the required JSON format."""

    # ── Parse Groq Response ────────────────────────────────────────────────────
    def _parse_response(self, raw: str, subject: str, manual_deadline: str) -> dict:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(clean)

        if not data.get("deadline") and manual_deadline:
            data["deadline"] = manual_deadline

        if not data.get("subject") and subject:
            data["subject"] = subject

        if not data.get("daily_plan"):
            data["daily_plan"] = self._generate_daily_plan(
                data.get("estimated_hours", 4),
                data.get("deadline")
            )

        return data

    # ── Daily Plan Generator (fallback) ───────────────────────────────────────
    def _generate_daily_plan(self, total_hours: int, deadline: str) -> list:
        if not deadline:
            deadline = (date.today() + timedelta(days=3)).isoformat()
        due = datetime.strptime(deadline, "%Y-%m-%d").date()
        days_available = max((due - date.today()).days, 1)
        hours_per_day = round(total_hours / days_available, 1)
        plan = []
        for i in range(days_available):
            d = date.today() + timedelta(days=i)
            plan.append({
                "day": d.isoformat(),
                "task": f"Work on assignment — session {i+1}",
                "hours": hours_per_day
            })
        return plan

    # ── Mock Response (no API key) ─────────────────────────────────────────────
    def _mock_response(self, text: str, subject: str, deadline: str) -> dict:
        log.warning("Using mock response — no API key set.")
        return {
            "subject": subject or "General Assignment",
            "solution": "## Solution\n\n> ⚠️ No API key found. Add `GROQ_API_KEY` to your .env file.\n\nGet a free key at https://console.groq.com",
            "deadline": deadline or (date.today() + timedelta(days=5)).isoformat(),
            "estimated_hours": 4,
            "daily_plan": self._generate_daily_plan(4, deadline)
        }
