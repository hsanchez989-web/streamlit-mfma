# Machinery FMEA Streamlit App (Visual Demo)

This Streamlit application implements a Machinery Failure Mode and Effects Analysis (MFMEA) workflow for **visualization only**. It runs entirely locally with in-memory demo data so you can review the interface, color rules, and PDF export without needing SharePoint.

## Features
- Calculates Risk Priority Number (RPN) as **Severity × Occurrence × Detection** with goal-driven color coding (green ≤ goal, yellow ≤ 300, red above).
- Administrators can set the RPN goal via the sidebar (email matches `ADMIN_USERS`).
- Form-based entry of machinery details (machine, project, customer, analyst) plus linked functions, failure modes/effects, causes, and controls.
- Suggests existing functions, failure modes, effects, and causes from the list to reduce repeated typing.
- Generates a PDF table containing machine, project, customer, analyst, function, failure mode/effects, causes, ratings, and controls.
- Styled with navy titles, mid-grey panels, and black text.

> Note: Persistence is intentionally disabled; entries are stored only in the current session.

## Prerequisites
- Python 3.10+

## Setup
```bash
pip install -r requirements.txt
```

Optionally set the following environment variable (use a `.env` file locally) to flag demo administrators who can adjust the RPN goal:
```
ADMIN_USERS=admin1@example.com,admin2@example.com
```

## Run
```bash
streamlit run app.py
```

Use the sidebar email field to identify the current user. Administrators listed in `ADMIN_USERS` can adjust the RPN goal. Entries you add are kept only while the app session remains active.
