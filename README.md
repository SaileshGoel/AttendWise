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

The app opens at the local URL printed by Streamlit, usually http://localhost:8501.

## Deploy free with Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and this README.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Choose **Create app**, select your repository and branch, and set the main file path to `app.py`.
4. Deploy and open the public app URL.
5. Test the deployed app by adding a subject and deadline.

### Important hosting note
This prototype uses a local SQLite database. On hosted environments, local files may not be durable across redeployments or restarts, and a single local database is not suitable for a multi-user production app. For a longer-running public deployment, move persistence to a managed database such as Supabase/Postgres and add user authentication.

## Demo script (about 90 seconds)
1. Open the dashboard and explain the student problem.
2. Add a subject with 32 attended classes out of 40 conducted and a 75% target.
3. Show the 80% result and the number of consecutive classes that could be missed under the model.
4. Edit it to 25 attended out of 40 and show the recovery estimate.
5. Add an assignment due tomorrow, then mark it complete.
6. Explain the next step: pilot with students and add feedback-driven features.

## Accuracy notes
- Attendance calculations assume equal-weight classes.
- If current attendance is below target, the recovery estimate assumes every future class is attended.
- This is a planning aid, not an official college attendance record.
