import streamlit as st
import os
from pathlib import Path
from agent import AssignmentAgent
from database import Database
from scheduler import DailyScheduler
import json
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Assignment Manager",
    page_icon="📚",
    layout="wide"
)

# ── Init ──────────────────────────────────────────────────────────────────────
db = Database()
agent = AssignmentAgent()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📚 Assignment Manager")
page = st.sidebar.radio(
    "Navigate",
    ["➕ New Assignment", "📋 My Assignments", "📅 Today's Plan", "⚙️ Settings"]
)

# ── Page: New Assignment ──────────────────────────────────────────────────────
if page == "➕ New Assignment":
    st.title("Upload New Assignment")

    input_mode = st.radio("Input type", ["📄 PDF Upload", "✏️ Paste Text"], horizontal=True)

    raw_text = ""
    if input_mode == "📄 PDF Upload":
        uploaded = st.file_uploader("Upload your assignment PDF", type=["pdf"])
        if uploaded:
            Path("uploads").mkdir(exist_ok=True)
            upload_path = Path("uploads") / uploaded.name
            upload_path.write_bytes(uploaded.read())
            with st.spinner("Extracting text from PDF..."):
                raw_text = agent.extract_pdf(str(upload_path))
            st.success(f"Extracted {len(raw_text)} characters")
            with st.expander("Preview extracted text"):
                st.text(raw_text[:1500] + ("..." if len(raw_text) > 1500 else ""))
    else:
        raw_text = st.text_area("Paste your assignment text here", height=250)

    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject / Course name")
    with col2:
        manual_deadline = st.date_input("Deadline (if not in text)", min_value=date.today())

    if st.button("🚀 Solve & Schedule", disabled=not raw_text):
        with st.spinner("AI agent is working..."):
            result = agent.process(raw_text, subject, str(manual_deadline))

        st.success("Done!")

        tab1, tab2 = st.tabs(["✅ Solution", "📅 Schedule"])

        with tab1:
            st.markdown("### Solution")
            st.markdown(result["solution"])

        with tab2:
            st.markdown("### Detected Info")
            st.json({
                "subject": result["subject"],
                "deadline": result["deadline"],
                "estimated_hours": result["estimated_hours"],
                "daily_plan": result["daily_plan"]
            })

        # Save to DB
        db.save_assignment(result)
        st.balloons()

# ── Page: My Assignments ──────────────────────────────────────────────────────
elif page == "📋 My Assignments":
    st.title("My Assignments")

    assignments = db.get_all_assignments()
    if not assignments:
        st.info("No assignments yet. Upload one to get started!")
    else:
        for a in assignments:
            days_left = (datetime.strptime(a["deadline"], "%Y-%m-%d").date() - date.today()).days
            status_color = "🟢" if days_left > 3 else ("🟡" if days_left > 0 else "🔴")
            with st.expander(f"{status_color} {a['subject']} — due {a['deadline']} ({days_left}d left)"):
                st.markdown(f"**Progress:** {a['progress']}%")
                new_progress = st.slider("Update progress", 0, 100, a["progress"], key=f"prog_{a['id']}")
                if st.button("Save progress", key=f"save_{a['id']}"):
                    db.update_progress(a["id"], new_progress)
                    st.success("Saved!")
                with st.expander("View solution"):
                    st.markdown(a["solution"])

# ── Page: Today's Plan ────────────────────────────────────────────────────────
elif page == "📅 Today's Plan":
    st.title(f"Today's Plan — {date.today().strftime('%A, %d %b %Y')}")
    scheduler = DailyScheduler(db)
    plan = scheduler.get_todays_plan()

    if not plan:
        st.success("🎉 Nothing due soon. You're all caught up!")
    else:
        for item in plan:
            st.markdown(f"""
            ### 📌 {item['subject']}
            - **Deadline:** {item['deadline']} ({item['days_left']} days left)
            - **Suggested today:** {item['hours_today']} hrs
            - **Progress:** {item['progress']}%
            ---
            """)

# ── Page: Settings ────────────────────────────────────────────────────────────
elif page == "⚙️ Settings":
    st.title("Settings")
    api_key = st.text_input("Anthropic API Key", type="password",
                             value=os.getenv("ANTHROPIC_API_KEY", ""))
    if st.button("Save API Key"):
        os.environ["ANTHROPIC_API_KEY"] = api_key
        st.success("API key saved for this session. Add it to .env to persist.")
    st.markdown("---")
    st.markdown("**Data location:** `data/assignments.db`")
    st.markdown("**Upload folder:** `uploads/`")
    st.markdown("**Logs:** `logs/agent.log`")
