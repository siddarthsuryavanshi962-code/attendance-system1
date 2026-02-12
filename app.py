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
# ================= VIEW STUDENTS ==================
# =================================================
if page == "View Students":
    st.title(f"👨‍🎓 Students – {year}")

    students = read_csv(f"students/students_{year}.csv")
    if students is None:
        st.warning("No students found")
        st.stop()

    st.dataframe(students, use_container_width=True)
    st.stop()

# =================================================
# ================= VIEW TIMETABLE =================
# =================================================
if page == "View Timetable":
    st.title(f"📅 Timetable – {year}")

    timetable = read_csv(f"timetable/{year}_timetable.csv")
    if timetable is None:
        st.warning("No timetable found")
        st.stop()

    st.dataframe(timetable, use_container_width=True)
    st.stop()

# =================================================
# ================= UPLOAD STUDENTS =================
# =================================================
if page == "Upload Students CSV":
    st.title(f"⬆️ Upload Students CSV – {year}")

    file = st.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        df.columns = df.columns.str.lower().str.strip()

        if not any("roll" in c for c in df.columns) or not any("name" in c for c in df.columns):
            st.error("CSV must contain Roll and Name columns")
            st.stop()

        st.dataframe(df)

        if st.button("Upload"):
            upload_csv(
                io.BytesIO(df.to_csv(index=False).encode()),
                f"students/students_{year}.csv"
            )
            st.success("Students uploaded")

    st.stop()

# =================================================
# ================= ADD STUDENT =====================
# =================================================
if page == "Add Student (Manual)":
    st.title(f"➕ Add Student – {year}")

    roll = st.text_input("Roll Number")
    name = st.text_input("Student Name")

    if st.button("Add Student"):
        if not roll or not name:
            st.error("All fields required")
            st.stop()

        path = f"students/students_{year}.csv"
        old = read_csv(path)

        new = pd.DataFrame([{"Roll": roll.strip(), "Name": name.strip()}])

        if old is not None:
            old.columns = old.columns.str.lower()
            if roll.strip() in old.iloc[:, 0].astype(str).values:
                st.error("Roll already exists")
                st.stop()
            new = pd.concat([old, new], ignore_index=True)

        upload_csv(io.BytesIO(new.to_csv(index=False).encode()), path)
        st.success("Student added")

    st.stop()

# =================================================
# ================= TIMETABLE ADD ===================
# =================================================
if page == "Timetable Management":
    st.title(f"🛠 Timetable Management – {year}")

    day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    subject = st.text_input("Subject")
    faculty = st.text_input("Faculty")

    c1, c2 = st.columns(2)
    start = c1.time_input("Start Time", time(8, 30))
    end = c2.time_input("End Time", time(9, 30))

    if st.button("Add Lecture"):
        if start >= end:
            st.error("Invalid time")
            st.stop()

        row = pd.DataFrame([{
            "Day": day,
            "Subject": subject,
            "Faculty": faculty,
            "Start": start.strftime("%H:%M"),
            "End": end.strftime("%H:%M"),
        }])

        path = f"timetable/{year}_timetable.csv"
        old = read_csv(path)
        if old is not None:
            row = pd.concat([old, row], ignore_index=True)

        upload_csv(io.BytesIO(row.to_csv(index=False).encode()), path)
        st.success("Lecture added")

    st.stop()

# =================================================
# ================= MONTHLY ATTENDANCE ==============
# =================================================
if page == "Monthly Attendance":
    st.title(f"📆 Monthly Attendance – {year}")

    col1, col2 = st.columns(2)
    sel_year = col1.number_input("Year", min_value=2020, max_value=2100, value=datetime.today().year)
    sel_month = col2.selectbox("Month", list(range(1, 13)))

    students = read_csv(f"students/students_{year}.csv")
    if students is None:
        st.warning("Students data not found")
        st.stop()

    students.columns = students.columns.str.lower()
    roll_col = next(c for c in students.columns if "roll" in c)
    name_col = next(c for c in students.columns if "name" in c)

    summary = []

    days_in_month = calendar.monthrange(sel_year, sel_month)[1]

    for _, stu in students.iterrows():
        present_days = 0
        total_days = 0

        for d in range(1, days_in_month + 1):
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

        percent = (present_days / total_days * 100) if total_days > 0 else 0

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

att_roll_col = next(c for c in attendance.columns if "roll" in c)
stu_roll_col = next(c for c in students.columns if "roll" in c)
stu_name_col = next(c for c in students.columns if "name" in c)

attendance["time"] = pd.to_datetime(attendance["time"], errors="coerce").dt.time
timetable["start"] = pd.to_datetime(timetable["start"]).dt.time
timetable["end"] = pd.to_datetime(timetable["end"]).dt.time

records = []

for _, lec in timetable.iterrows():
    for _, stu in students.iterrows():

        present = attendance[
            (attendance[att_roll_col].astype(str) == str(stu[stu_roll_col])) &
            (attendance["time"] >= lec["start"]) &
            (attendance["time"] <= lec["end"])
        ]

        records.append({
            "Roll": stu[stu_roll_col],
            "Name": stu[stu_name_col],
            "Day": lec["day"],
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