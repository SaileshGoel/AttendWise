import sqlite3
import math
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "attendwise.db"

st.set_page_config(
    page_title="AttendWise | Student Planner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    .hero {padding: 1.35rem 1.5rem; border-radius: 18px;
           background: linear-gradient(120deg, #102a43 0%, #176b72 100%);
           color: white; margin-bottom: 1rem;}
    .hero h1 {color: white; margin: 0 0 .3rem 0;}
    .hero p {color: #e4f5f5; margin: 0;}
    [data-testid="stMetric"] {background: var(--secondary-background-color);
      padding: 14px 16px; border-radius: 14px; border: 1px solid rgba(128,128,128,.18);}
    .small-note {font-size: .88rem; opacity: .8;}
</style>
""", unsafe_allow_html=True)


def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        attended INTEGER NOT NULL DEFAULT 0,
        conducted INTEGER NOT NULL DEFAULT 0,
        target REAL NOT NULL DEFAULT 75
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        kind TEXT NOT NULL,
        due_date TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Medium',
        done INTEGER NOT NULL DEFAULT 0,
        notes TEXT DEFAULT ''
    )""")
    con.commit()
    return con


con = connect()


def load_subjects():
    return pd.read_sql_query("SELECT * FROM subjects ORDER BY name", con)


def load_tasks():
    df = pd.read_sql_query("SELECT * FROM tasks ORDER BY due_date, priority", con)
    if not df.empty:
        df["due_date"] = pd.to_datetime(df["due_date"]).dt.date
    return df


def attendance_pct(attended, conducted):
    return (100 * attended / conducted) if conducted else 0.0


def classes_to_target(attended, conducted, target):
    """Consecutive classes needed if every future class is attended."""
    if conducted <= 0:
        return 0 if target <= 0 else None
    current = 100 * attended / conducted
    if current >= target:
        return 0
    if target >= 100:
        return None
    return max(0, math.ceil((target * conducted - 100 * attended) / (100 - target)))


def misses_allowed(attended, conducted, target):
    """How many consecutive classes can be missed while staying at/above target."""
    if conducted <= 0:
        return 0
    if attendance_pct(attended, conducted) < target:
        return 0
    if target <= 0:
        return 999
    return max(0, int((100 * attended / target) - conducted + 1e-9))


st.sidebar.title("🎓 AttendWise")
st.sidebar.caption("Your student-life command center")
page = st.sidebar.radio("Navigate", ["Overview", "Attendance", "Deadlines", "About"])
st.sidebar.divider()
st.sidebar.caption("Demo data is stored in a local SQLite database. On hosted deployments, storage persistence depends on the hosting platform.")


if page == "Overview":
    st.markdown("""<div class="hero"><h1>AttendWise</h1>
    <p>Make every class count. Stay ahead of every deadline.</p></div>""", unsafe_allow_html=True)
    subjects = load_subjects()
    tasks = load_tasks()
    total_tasks = len(tasks)
    open_tasks = int((tasks["done"] == 0).sum()) if not tasks.empty else 0
    overdue = int(((tasks["done"] == 0) & (tasks["due_date"] < date.today())).sum()) if not tasks.empty else 0
    overall = (100 * subjects["attended"].sum() / subjects["conducted"].sum()
               if not subjects.empty and subjects["conducted"].sum() else 0)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall attendance", f"{overall:.1f}%")
    c2.metric("Subjects tracked", len(subjects))
    c3.metric("Open deadlines", open_tasks)
    c4.metric("Overdue tasks", overdue, delta="Needs attention" if overdue else "All clear", delta_color="inverse" if overdue else "normal")

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Attendance at a glance")
        if subjects.empty:
            st.info("No subjects yet. Open **Attendance** to add your first subject.")
        else:
            chart_df = subjects.copy()
            chart_df["Attendance (%)"] = chart_df.apply(
                lambda r: attendance_pct(r["attended"], r["conducted"]), axis=1
            )
            fig = px.bar(chart_df, x="name", y="Attendance (%)", color="Attendance (%)",
                         range_y=[0, 100], text_auto=".1f",
                         color_continuous_scale=["#e76f51", "#f4a261", "#2a9d8f"])
            fig.add_hline(y=float(chart_df["target"].mean()), line_dash="dash",
                          annotation_text="Average target")
            fig.update_layout(xaxis_title="", yaxis_title="Attendance (%)",
                              coloraxis_showscale=False, margin=dict(l=5, r=5, t=20, b=5))
            st.plotly_chart(fig, use_container_width=True)
            at_risk = chart_df[chart_df["Attendance (%)"] < chart_df["target"]]
            if not at_risk.empty:
                st.warning("Below target: " + ", ".join(at_risk["name"].astype(str).tolist()))
            else:
                st.success("All tracked subjects are at or above their individual targets.")
    with right:
        st.subheader("Next up")
        if tasks.empty:
            st.info("No deadlines yet. Add an assignment or exam under **Deadlines**.")
        else:
            upcoming = tasks[tasks["done"] == 0].sort_values("due_date").head(6)
            if upcoming.empty:
                st.success("Everything is marked complete. Nice work!")
            for _, task in upcoming.iterrows():
                days = (task["due_date"] - date.today()).days
                timing = "Overdue" if days < 0 else ("Today" if days == 0 else f"In {days} day(s)")
                with st.container(border=True):
                    st.markdown(f"**{task['title']}**")
                    st.caption(f"{task['kind']} · Due {task['due_date']} · {timing} · {task['priority']} priority")
    st.caption("Tip: use your institution's official attendance rules. The target is configurable for each subject.")


elif page == "Attendance":
    st.title("📊 Attendance planner")
    st.write("Track attended and conducted classes. AttendWise calculates your current percentage and what you need to do next.")
    subjects = load_subjects()

    with st.expander("➕ Add a subject", expanded=subjects.empty):
        with st.form("add_subject", clear_on_submit=True):
            name = st.text_input("Subject name", placeholder="e.g., Data Structures")
            a, b, c = st.columns(3)
            attended = a.number_input("Classes attended", min_value=0, max_value=10000, value=0, step=1)
            conducted = b.number_input("Classes conducted", min_value=0, max_value=10000, value=0, step=1)
            target = c.number_input("Attendance target (%)", min_value=1.0, max_value=100.0, value=75.0, step=1.0)
            submitted = st.form_submit_button("Add subject", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Enter a subject name.")
                elif attended > conducted:
                    st.error("Classes attended cannot exceed classes conducted.")
                else:
                    try:
                        con.execute("INSERT INTO subjects(name, attended, conducted, target) VALUES (?, ?, ?, ?)",
                                    (name.strip(), int(attended), int(conducted), float(target)))
                        con.commit()
                        st.success(f"Added {name.strip()}.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That subject already exists. Choose a unique name.")

    subjects = load_subjects()
    if not subjects.empty:
        st.subheader("Your subjects")
        for _, row in subjects.iterrows():
            with st.container(border=True):
                top1, top2, top3 = st.columns([2.2, 1, 1])
                pct = attendance_pct(int(row.attended), int(row.conducted))
                top1.markdown(f"### {row['name']}")
                top2.metric("Attendance", f"{pct:.1f}%")
                top3.metric("Target", f"{row.target:.0f}%")
                st.progress(min(1.0, pct / 100))
                if int(row.conducted) == 0:
                    st.info("Add class counts to get a prediction.")
                elif pct >= row.target:
                    allowed = misses_allowed(int(row.attended), int(row.conducted), float(row.target))
                    st.success(f"At/above target. You can miss approximately {allowed} consecutive class(es) and remain at or above {row.target:.0f}%, assuming each class counts equally.")
                else:
                    needed = classes_to_target(int(row.attended), int(row.conducted), float(row.target))
                    st.warning(f"Below target. Attend the next **{needed} consecutive class(es)** to reach {row.target:.0f}%, assuming every next class is attended.")
                with st.expander(f"Update {row['name']}"):
                    with st.form(f"update_{int(row.id)}"):
                        x, y, z = st.columns(3)
                        new_a = x.number_input("Attended", min_value=0, max_value=10000, value=int(row.attended), key=f"a{row.id}")
                        new_c = y.number_input("Conducted", min_value=0, max_value=10000, value=int(row.conducted), key=f"c{row.id}")
                        new_t = z.number_input("Target (%)", min_value=1.0, max_value=100.0, value=float(row.target), key=f"t{row.id}")
                        save = st.form_submit_button("Save changes")
                        if save:
                            if new_a > new_c:
                                st.error("Attended classes cannot exceed conducted classes.")
                            else:
                                con.execute("UPDATE subjects SET attended=?, conducted=?, target=? WHERE id=?",
                                            (int(new_a), int(new_c), float(new_t), int(row.id)))
                                con.commit()
                                st.rerun()
                if st.button(f"🗑️ Delete {row['name']}", key=f"delete_subject_{row.id}"):
                    con.execute("DELETE FROM subjects WHERE id=?", (int(row.id),))
                    con.commit()
                    st.rerun()
    else:
        st.info("Add your subjects above to start tracking attendance.")

    st.caption("Calculation assumes each class has equal weight. Lab sessions or courses with different credit/weight rules may require a different calculation.")


elif page == "Deadlines":
    st.title("🗓️ Assignment & exam deadlines")
    st.write("Capture upcoming work, sort by urgency, and mark completed tasks.")
    with st.expander("➕ Add a deadline", expanded=True):
        with st.form("add_task", clear_on_submit=True):
            title = st.text_input("Task title", placeholder="e.g., Microelectronics lab report")
            x, y, z = st.columns(3)
            kind = x.selectbox("Type", ["Assignment", "Exam", "Lab", "Project", "Other"])
            due = y.date_input("Due date", value=date.today())
            priority = z.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            notes = st.text_area("Notes (optional)", placeholder="Submission link, preparation notes, etc.")
            add = st.form_submit_button("Add deadline", type="primary")
            if add:
                if not title.strip():
                    st.error("Enter a task title.")
                else:
                    con.execute("INSERT INTO tasks(title, kind, due_date, priority, notes) VALUES (?, ?, ?, ?, ?)",
                                (title.strip(), kind, due.isoformat(), priority, notes.strip()))
                    con.commit()
                    st.success("Deadline added.")
                    st.rerun()

    tasks = load_tasks()
    if tasks.empty:
        st.info("No deadlines yet. Add your first task above.")
    else:
        show = st.radio("Show", ["All", "Pending", "Completed"], horizontal=True)
        if show == "Pending":
            view = tasks[tasks["done"] == 0]
        elif show == "Completed":
            view = tasks[tasks["done"] == 1]
        else:
            view = tasks
        for _, task in view.sort_values(["done", "due_date"]).iterrows():
            due_date = task["due_date"]
            days = (due_date - date.today()).days
            state = "Overdue" if days < 0 and not task["done"] else ("Due today" if days == 0 and not task["done"] else (f"In {days} days" if not task["done"] else "Completed"))
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1.4, 1])
                c1.markdown(f"**{task['title']}**")
                c1.caption(f"{task['kind']} · {task['priority']} priority")
                c2.write(f"📅 {due_date}")
                c2.caption(state)
                is_done = c3.checkbox("Done", value=bool(task["done"]), key=f"done_{task['id']}")
                if is_done != bool(task["done"]):
                    con.execute("UPDATE tasks SET done=? WHERE id=?", (int(is_done), int(task["id"])))
                    con.commit()
                    st.rerun()
                if task["notes"]:
                    st.caption(task["notes"])
                if st.button("Delete task", key=f"delete_task_{task['id']}"):
                    con.execute("DELETE FROM tasks WHERE id=?", (int(task["id"]),))
                    con.commit()
                    st.rerun()


else:
    st.title("ℹ️ About AttendWise")
    st.markdown("""
    **AttendWise** is a student-focused planning tool designed to reduce two common sources of academic stress:
    missed deadlines and uncertainty about attendance.

    **What it does**
    - Tracks attendance by subject and configurable target.
    - Estimates classes needed to reach a target or classes that can be missed while staying on target.
    - Organizes assignments, exams, labs, and project deadlines.
    - Shows an at-a-glance dashboard with visual analytics.

    **Design principles**
    - Simple enough to use between classes.
    - Transparent calculations instead of unexplained predictions.
    - No external AI service or paid API required.
    - SQLite storage for a lightweight prototype.

    **Limitations**
    - This prototype does not connect to official college attendance systems.
    - Predictions assume all classes have equal weight and future attendance is known.
    - Hosted free environments may have ephemeral local storage. For a multi-user production version, use a managed database and add authentication.
    """)
    st.info("Hackathon next step: test the app with 3–5 classmates, note the most common attendance/deadline pain points, and use that feedback to prioritize improvements.")
