import os
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from fpdf import FPDF
from dotenv import load_dotenv

from sharepoint_service import (
    SharePointConfig,
    fetch_mfmea_rows,
    save_record,
    user_project_access,
)


load_dotenv()

NAVY = "#001f54"
MID_GREY = "#d9d9d9"
BLACK = "#000000"


st.set_page_config(
    page_title="Machinery FMEA",
    layout="wide",
)

st.markdown(
    f"""
    <style>
    body {{ color: {BLACK}; background-color: white; }}
    .navy-title {{ color: {NAVY}; }}
    .grey-panel {{ background: {MID_GREY}; padding: 1rem; border-radius: 0.5rem; }}
    .rpn-green {{ background: #c8e6c9; padding: 0.35rem 0.6rem; border-radius: 0.35rem; }}
    .rpn-yellow {{ background: #fff9c4; padding: 0.35rem 0.6rem; border-radius: 0.35rem; }}
    .rpn-red {{ background: #ffcccb; padding: 0.35rem 0.6rem; border-radius: 0.35rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


cfg = SharePointConfig.from_env()


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = fetch_mfmea_rows(cfg)
    if df.empty:
        df = pd.DataFrame(
            [
                {
                    "Machine": "Hydraulic Press",
                    "Project": "Alpha",
                    "Customer": "Contoso",
                    "Analyst": "admin@example.com",
                    "Function": "Clamp workpiece",
                    "FailureMode": "Insufficient clamping force",
                    "FailureEffect": "Workpiece slips",
                    "Cause": "Hydraulic leak",
                    "Severity": 9,
                    "Occurrence": 5,
                    "Detection": 4,
                    "Prevention": "Regular seal replacement",
                    "DetectionControls": "Pressure monitoring",
                    "RPNGoal": 180,
                }
            ]
        )
    df["RPN"] = df[["Severity", "Occurrence", "Detection"]].product(axis=1)
    return df


def get_admin_emails() -> List[str]:
    raw = os.getenv("ADMIN_USERS", "")
    return [email.strip().lower() for email in raw.split(",") if email.strip()]


def is_admin(user_email: str) -> bool:
    return user_email.lower() in get_admin_emails()


def rpn_status(rpn: int, goal: int) -> str:
    if rpn <= goal:
        return "rpn-green"
    if rpn <= 300:
        return "rpn-yellow"
    return "rpn-red"


def status_label(rpn: int, goal: int) -> str:
    css = rpn_status(rpn, goal)
    return f"<span class='{css}'>RPN {rpn}</span>"


def build_pdf(rows: pd.DataFrame) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Machinery Failure Mode & Effects Analysis", ln=True, align="C")
    pdf.ln(5)

    headers = [
        "Machine",
        "Project",
        "Customer",
        "Analyst",
        "Function",
        "Failure Mode",
        "Failure Effects",
        "Causes",
        "Severity",
        "Occurrence",
        "Detection",
        "Prevention",
        "Detection Controls",
    ]

    pdf.set_font("Arial", "B", 10)
    for header in headers:
        pdf.cell(35, 8, header, border=1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for _, row in rows.iterrows():
        values = [
            row.get("Machine", ""),
            row.get("Project", ""),
            row.get("Customer", ""),
            row.get("Analyst", ""),
            row.get("Function", ""),
            row.get("FailureMode", ""),
            row.get("FailureEffect", ""),
            row.get("Cause", ""),
            str(row.get("Severity", "")),
            str(row.get("Occurrence", "")),
            str(row.get("Detection", "")),
            row.get("Prevention", ""),
            row.get("DetectionControls", ""),
        ]
        for value in values:
            pdf.cell(35, 8, str(value), border=1)
        pdf.ln()

    return pdf.output(dest="S").encode("latin-1")


def option_with_new(label: str, existing: List[str], key: str) -> str:
    choices = ["<new>"] + sorted({c for c in existing if c})
    selection = st.selectbox(label, options=choices, key=f"select-{key}")
    if selection == "<new>":
        return st.text_input(f"Add {label.lower()}", key=f"input-{key}")
    return selection


def main() -> None:
    st.markdown("<h1 class='navy-title'>Machinery Failure Mode & Effects Analysis</h1>", unsafe_allow_html=True)

    df = load_data()

    st.sidebar.header("User")
    user_email = st.sidebar.text_input("Email", value="user@example.com")
    admin_user = is_admin(user_email)
    allowed_projects = user_project_access(cfg, user_email) if admin_user else []

    st.sidebar.write("Admin access" if admin_user else "Viewer")
    st.sidebar.caption(
        "Administrators set the RPN goal and grant edit permissions by project."
    )

    st.markdown("<div class='grey-panel'>", unsafe_allow_html=True)
    st.subheader("Project Access & Targets", anchor=False)

    col_goal, col_info = st.columns([1, 3])
    with col_goal:
        goal_value = df["RPNGoal"].iloc[0] if not df.empty else 180
        if admin_user:
            goal_value = st.number_input(
                "RPN Goal (admin only)",
                value=int(goal_value),
                min_value=1,
                max_value=300,
                step=5,
                help="Administrators can adjust the acceptable RPN threshold.",
            )
        else:
            st.number_input(
                "RPN Goal (admin only)",
                value=int(goal_value),
                disabled=True,
            )
    with col_info:
        st.write(
            "RPN goal set to 180 by default. Values above the goal are highlighted "
            "yellow up to 300; anything beyond is red."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h3 class='navy-title'>Add or Update Entry</h3>", unsafe_allow_html=True)
    with st.form("mfmea-entry"):
        meta1, meta2, meta3, meta4 = st.columns(4)
        machine = meta1.text_input("Machine name")
        project = meta2.text_input("Project")
        customer = meta3.text_input("Customer")
        analyst = meta4.text_input("Person involved in analysis", value=user_email)

        st.markdown("<h5 class='navy-title'>Function and Failure Relationships</h5>", unsafe_allow_html=True)
        func_col, mode_col, effect_col, cause_col = st.columns(4)

        function = option_with_new(
            "Function",
            existing=df["Function"].tolist(),
            key="function",
        )
        failure_mode = option_with_new(
            "Failure mode",
            existing=df["FailureMode"].tolist(),
            key="failure-mode",
        )
        failure_effect = option_with_new(
            "Failure effects",
            existing=df["FailureEffect"].tolist(),
            key="failure-effect",
        )
        cause = option_with_new(
            "Cause",
            existing=df["Cause"].tolist(),
            key="cause",
        )

        st.markdown("<h5 class='navy-title'>Ratings and Controls</h5>", unsafe_allow_html=True)
        col_s, col_o, col_d = st.columns(3)
        severity = col_s.slider("Severity", 1, 10, 5)
        occurrence = col_o.slider("Occurrence", 1, 10, 5)
        detection = col_d.slider("Detection", 1, 10, 5)

        prevention = st.text_area("Prevention controls")
        detection_controls = st.text_area("Detection controls")

        calculated_rpn = severity * occurrence * detection
        st.markdown(
            f"**Calculated RPN:** {status_label(calculated_rpn, goal_value)}",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Save entry")

    can_edit = admin_user or project in allowed_projects

    if submitted:
        if not can_edit:
            st.error(
                "You do not have edit permissions for this project. Please contact an administrator."
            )
        else:
            payload: Dict[str, Any] = {
                "Machine": machine,
                "Project": project,
                "Customer": customer,
                "Analyst": analyst,
                "Function": function,
                "FailureMode": failure_mode,
                "FailureEffect": failure_effect,
                "Cause": cause,
                "Severity": severity,
                "Occurrence": occurrence,
                "Detection": detection,
                "Prevention": prevention,
                "DetectionControls": detection_controls,
                "RPNGoal": goal_value,
            }
            ok = save_record(cfg, payload)
            if ok:
                st.success("Entry saved to SharePoint list.")
                st.cache_data.clear()
            else:
                st.warning(
                    "Could not persist to SharePoint. Review configuration or network connectivity."
                )

    st.markdown("<h3 class='navy-title'>Analysis Dashboard</h3>", unsafe_allow_html=True)
    if df.empty:
        st.info("No records available yet.")
    else:
        df_display = df.copy()
        df_display["Status"] = df_display.apply(
            lambda r: status_label(int(r.RPN), goal_value), axis=1
        )
        st.dataframe(
            df_display[
                [
                    "Machine",
                    "Project",
                    "Customer",
                    "Analyst",
                    "Function",
                    "FailureMode",
                    "FailureEffect",
                    "Cause",
                    "Severity",
                    "Occurrence",
                    "Detection",
                    "Prevention",
                    "DetectionControls",
                    "RPN",
                    "Status",
                ]
            ],
            use_container_width=True,
            column_config={"Status": st.column_config.Column("RPN Status", width=120)},
        )

    st.markdown("<h3 class='navy-title'>PDF Export</h3>", unsafe_allow_html=True)
    if df.empty:
        st.caption("Add entries to enable PDF export.")
    else:
        selected_projects = st.multiselect(
            "Filter by project for the PDF",
            options=sorted(df["Project"].unique()),
            default=list(sorted(df["Project"].unique())),
        )
        filtered = df[df["Project"].isin(selected_projects)]
        if filtered.empty:
            st.info("No rows to export with the chosen filter.")
        else:
            pdf_bytes = build_pdf(filtered)
            st.download_button(
                label="Download MFMEA summary as PDF",
                data=pdf_bytes,
                file_name=f"mfmea-{datetime.now().date()}.pdf",
                mime="application/pdf",
            )


if __name__ == "__main__":
    main()
