# 📚 Assignment Manager — AI Agent

An AI-powered assignment assistant that:
- Extracts text from PDFs or plain text input
- Solves your assignments using Claude AI
- Detects deadlines and creates a daily study schedule
- Tracks progress across all your assignments

---

## 📁 Project Structure

```
Assignment Management/
├── app.py              # Streamlit web UI (main entry point)
├── agent.py            # AI agent: PDF extraction + Claude API
├── database.py         # SQLite storage layer
├── scheduler.py        # Daily plan calculator + cron reminder
├── requirements.txt    # Python dependencies
├── .env.example        # API key template → copy to .env
├── .gitignore
├── uploads/            # Uploaded PDFs (auto-created)
├── data/               # SQLite database (auto-created)
└── logs/               # Agent logs (auto-created)
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key
```bash
cp .env.example .env
# Edit .env and paste your Anthropic API key
```

Get your key at: https://console.anthropic.com

### 3. Run the app
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 🔧 How Each File Works

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — 4 pages: upload, view, today's plan, settings |
| `agent.py` | Extracts PDF text, calls Claude API, parses JSON response |
| `database.py` | Saves/reads assignments from SQLite (`data/assignments.db`) |
| `scheduler.py` | Calculates today's study plan based on deadlines and progress |

---

## 📅 Daily Reminders (optional)

Run this every morning via cron or Task Scheduler:
```bash
python scheduler.py
```

Add to crontab (Linux/Mac) for 8 AM daily reminder:
```
0 8 * * * cd /path/to/Assignment\ Management && python scheduler.py
```

---

## 🧠 How the AI Agent Works

1. You upload a PDF or paste text
2. `agent.py` extracts the text (pdfplumber for PDFs)
3. The text is sent to Claude with a structured prompt
4. Claude returns JSON with: solution, deadline, estimated hours, daily plan
5. Everything is saved to SQLite
6. The scheduler checks deadlines daily and tells you what to study today


