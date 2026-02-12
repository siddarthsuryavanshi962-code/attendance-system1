import streamlit as st
import pandas as pd
import io
from datetime import datetime, time, date
import calendar

from firebase_handler import read_csv, upload_csv

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Attendance System", layout="wide")

# ================= USERS =================
USERS = {
    "se":  {"password": "se123",  "role": "YEAR", "year": "SE"},
    "te":  {"password": "te123",  "role": "YEAR", "year": "TE"},
    "be":  {"password": "be123",  "role": "YEAR", "year": "BE"},
    "hod": {"password": "hod123", "role": "HOD",  "year": "ALL"},
}

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.year = None

# ================= LOGIN =================
if not st.session_state.logged_in:
    st.title("🔐 Attendance Login")

    with st.form("login"):
        uid = st.text_input("User ID")
        pwd = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")

    if login and uid in USERS and USERS[uid]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.role = USERS[uid]["role"]
        st.session_state.year = USERS[uid]["year"]
        st.rerun()
    elif login:
        st.error("Invalid credentials")

    st.stop()

# ================= SIDEBAR =================
st.sidebar.title("📌 Menu")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Live Attendance (30 Min)",
        "Monthly Attendance",
        "View Timetable",
        "Timetable Management",
        "Upload Students CSV",
        "Add Student (Manual)",
        "View Students",
    ]
)

# ================= YEAR CONTROL =================
if st.session_state.role == "HOD":
    year = st.sidebar.selectbox("Select Year", ["SE", "TE", "BE"])
else:
    year = st.session_state.year
    st.sidebar.success(f"Year: {year}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.year = None
    st.rerun()

# =================================================
# ================= LIVE ATTENDANCE ===============
# =================================================
if page == "Live Attendance (30 Min)":

    st.title(f"🔴 Live Attendance (Last 30 Minutes) – {year}")

    if st.button("🔄 Refresh Now"):
        st.rerun()

    today = date.today()
    date_str = today.strftime("%Y-%m-%d")

    attendance = read_csv(f"attendance/{date_str}/{year}.csv")
    students = read_csv(f"students/students_{year}.csv")
    timetable = read_csv(f"timetable/{year}_timetable.csv")

    if attendance is None or students is None or timetable is None:
        st.warning("Required data missing")
        st.stop()

    attendance.columns = attendance.columns.str.lower()
    students.columns = students.columns.str.lower()
    timetable.columns = timetable.columns.str.lower()

    att_roll = next(c for c in attendance.columns if "roll" in c)
    stu_roll = next(c for c in students.columns if "roll" in c)
    stu_name = next(c for c in students.columns if "name" in c)

    attendance["time"] = pd.to_datetime(attendance["time"], errors="coerce")

    now = datetime.now()
    last_30 = now - pd.Timedelta(minutes=30)

    subjects = timetable["subject"].unique()
    selected_subject = st.selectbox("Select Subject", subjects)

    records = []

    for _, stu in students.iterrows():

        present = attendance[
            (attendance[att_roll].astype(str) == str(stu[stu_roll])) &
            (attendance["time"] >= last_30) &
            (attendance["time"] <= now)
        ]

        records.append({
            "Roll": stu[stu_roll],
            "Name": stu[stu_name],
            "Subject": selected_subject,
            "Status": "Present" if not present.empty else "Absent"
        })

    live_df = pd.DataFrame(records)

    st.success(f"Showing from {last_30.strftime('%H:%M')} to {now.strftime('%H:%M')}")

    st.dataframe(live_df, use_container_width=True)

    st.download_button(
        "⬇️ Download Live Attendance",
        live_df.to_csv(index=False).encode(),
        f"{year}_{date_str}_live_attendance.csv",
        "text/csv"
    )

    st.stop()

# =================================================
# ================= MONTHLY ATTENDANCE =============
# =================================================
if page == "Monthly Attendance":

    st.title(f"📆 Monthly Attendance – {year}")

    col1, col2 = st.columns(2)
    sel_year = col1.number_input("Year", 2020, 2100, datetime.today().year)
    sel_month = col2.selectbox("Month", list(range(1, 13)))

    students = read_csv(f"students/students_{year}.csv")
    if students is None:
        st.warning("Students data not found")
        st.stop()

    students.columns = students.columns.str.lower()
    roll_col = next(c for c in students.columns if "roll" in c)
    name_col = next(c for c in students.columns if "name" in c)

    summary = []
    days = calendar.monthrange(sel_year, sel_month)[1]

    for _, stu in students.iterrows():
        present_days = 0
        total_days = 0

        for d in range(1, days + 1):
            dt = date(sel_year, sel_month, d)
            date_str = dt.strftime("%Y-%m-%d")

            att = read_csv(f"attendance/{date_str}/{year}.csv")
            if att is None:
                continue

            att.columns = att.columns.str.lower()
            att_roll = next(c for c in att.columns if "roll" in c)

            total_days += 1
            if str(stu[roll_col]) in att[att_roll].astype(str).values:
                present_days += 1

        percent = (present_days / total_days * 100) if total_days else 0

        summary.append({
            "Roll": stu[roll_col],
            "Name": stu[name_col],
            "Present Days": present_days,
            "Total Days": total_days,
            "Attendance %": round(percent, 2)
        })

    df = pd.DataFrame(summary)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "⬇️ Download Monthly Attendance",
        df.to_csv(index=False).encode(),
        f"{year}_{sel_year}_{sel_month}_monthly_attendance.csv",
        "text/csv"
    )

    st.stop()

# =================================================
# ================= DASHBOARD ======================
# =================================================
st.title(f"📘 Lecture-wise Attendance – {year}")

sel_date = st.date_input("Select Date", datetime.today())
date_str = sel_date.strftime("%Y-%m-%d")

attendance = read_csv(f"attendance/{date_str}/{year}.csv")
students = read_csv(f"students/students_{year}.csv")
timetable = read_csv(f"timetable/{year}_timetable.csv")

if attendance is None or students is None or timetable is None:
    st.warning("Required data missing")
    st.stop()

attendance.columns = attendance.columns.str.lower()
students.columns = students.columns.str.lower()
timetable.columns = timetable.columns.str.lower()

att_roll = next(c for c in attendance.columns if "roll" in c)
stu_roll = next(c for c in students.columns if "roll" in c)
stu_name = next(c for c in students.columns if "name" in c)

attendance["time"] = pd.to_datetime(attendance["time"], errors="coerce").dt.time
timetable["start"] = pd.to_datetime(timetable["start"]).dt.time
timetable["end"] = pd.to_datetime(timetable["end"]).dt.time

records = []

for _, lec in timetable.iterrows():
    for _, stu in students.iterrows():

        present = attendance[
            (attendance[att_roll].astype(str) == str(stu[stu_roll])) &
            (attendance["time"] >= lec["start"]) &
            (attendance["time"] <= lec["end"])
        ]

        records.append({
            "Roll": stu[stu_roll],
            "Name": stu[stu_name],
            "Subject": lec["subject"],
            "Faculty": lec["faculty"],
            "Status": "Present" if not present.empty else "Absent"
        })

final_df = pd.DataFrame(records)
st.dataframe(final_df, use_container_width=True)

st.download_button(
    "⬇️ Download Attendance CSV",
    final_df.to_csv(index=False).encode(),
    f"{year}_{date_str}_attendance.csv",
    "text/csv"
)
