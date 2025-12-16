# Machinery FMEA Streamlit App

This Streamlit application implements a Machinery Failure Mode and Effects Analysis (MFMEA) workflow with SharePoint-hosted Microsoft Lists storage.

## Features
- Calculates Risk Priority Number (RPN) as **Severity × Occurrence × Detection** with goal-driven color coding (green ≤ goal, yellow ≤ 300, red above).
- Administrators can set the RPN goal and grant per-project edit permissions via a SharePoint ProjectAccess list.
- Form-based entry of machinery details (machine, project, customer, analyst) plus linked functions, failure modes/effects, causes, and controls.
- Suggests existing functions, failure modes, effects, and causes from the list to reduce repeated typing.
- Generates a PDF table containing machine, project, customer, analyst, function, failure mode/effects, causes, ratings, and controls.
- Styled with navy titles, mid-grey panels, and black text.

## Prerequisites
- Python 3.10+
- Azure AD app configured for SharePoint list access
- SharePoint lists:
  - **MFMEA** (or override with `MFMEA_LIST_NAME`) containing columns: Machine, Project, Customer, Analyst, Function, FailureMode, FailureEffect, Cause, Severity, Occurrence, Detection, Prevention, DetectionControls, RPNGoal.
  - **ProjectAccess** (or override with `ACCESS_LIST_NAME`) containing columns: User (email), Project.

## Setup
```bash
pip install -r requirements.txt
```

Set the following environment variables (use a `.env` file locally):
```
SHAREPOINT_TENANT=yourtenant.onmicrosoft.com
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/YourSite
SHAREPOINT_CLIENT_ID=your-app-client-id
SHAREPOINT_CLIENT_SECRET=your-app-client-secret
MFMEA_LIST_NAME=MFMEA
ACCESS_LIST_NAME=ProjectAccess
ADMIN_USERS=admin1@example.com,admin2@example.com
```

## Run
```bash
streamlit run app.py
```

Use the sidebar email field to identify the current user. Administrators listed in `ADMIN_USERS` can adjust the RPN goal and will have their project edit permissions retrieved from the ProjectAccess list. Others operate in read-only mode.

If SharePoint connectivity is not configured, the app falls back to in-memory demo data so the UI can still be exercised.
