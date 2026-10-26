# AttendWise — Smart Student Planner

AttendWise is a Python/Streamlit hackathon prototype that helps students track subject-wise attendance, calculate attendance recovery plans, and organize academic deadlines.

## Features
- Subject-wise attendance and configurable attendance targets
- Classes needed to reach target attendance
- Estimate of consecutive classes that can be missed while staying on target
- Assignment, exam, lab, and project deadline manager
- Dashboard metrics and attendance visualization
- SQLite persistence for a simple single-user prototype

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens at the local URL printed by Streamlit, usually https://attendwise-e68fjh7srfmvaejvo3jit6.streamlit.app/



## Accuracy notes
- Attendance calculations assume equal-weight classes.
- If current attendance is below target, the recovery estimate assumes every future class is attended.
- This is a planning aid, not an official college attendance record.
