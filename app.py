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
    "se": {"password": "se123", "role": "YEAR", "year": "SE"},
    "te": {"password": "te123", "role": "YEAR", "year": "TE"},
    "be": {"password": "be123", "role": "YEAR", "year": "BE"},
    "hod": {"password": "hod123", "role": "HOD", "year": "ALL"},
}

# ================= HELPERS =================
def save_df(df, path):
    bio = io.BytesIO()
    df.to_csv(bio, index=False)
    bio.seek(0)
    return upload_csv(bio, path)

def normalize(df):
    if df is None:
        return None
    df.columns = df.columns.str.lower().str.strip()
    return df

def find_col(df, keyword):
    cols = [c for c in df.columns if keyword in c]
    return cols[0] if cols else None

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

    if login:
        if uid in USERS and USERS[uid]["password"] == pwd:
            st.session_state.logged_in = True
            st.session_state.role = USERS[uid]["role"]
            st.session_state.year = USERS[uid]["year"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ================= SIDEBAR =================
st.sidebar.title("📌 Menu")

pages = [
    "Dashboard",
    "Live Attendance",
    "Monthly Attendance",
    "View Timetable",
    "Timetable Management",
    "Upload Students CSV",
    "Add Student (Manual)",
    "View Students"
]

page = st.sidebar.radio("Navigation", pages)

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

# ================= UPLOAD STUDENTS =================
if page == "Upload Students CSV":
    st.title(f"📤 Upload Students CSV - {year}")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file and st.button("Save Students"):
        if upload_csv(file, f"students/students_{year}.csv"):
            st.success("Students uploaded successfully")

    st.stop()

# ================= ADD STUDENT =================
# ================= ADD STUDENT =================
if page == "Add Student (Manual)":

    st.title(f"➕ Add Student - {year}")

    students = normalize(
        read_csv(f"students/students_{year}.csv")
    )

    if students is None:
        students = pd.DataFrame(
            columns=["roll","name"]
        )

    with st.form("student"):

        roll = st.text_input("Roll Number")

        name = st.text_input("Student Name")

        submit = st.form_submit_button("Add Student")

    if submit:

        if roll == "" or name == "":

            st.warning("Fill all details")

        elif roll in students["roll"].astype(str).tolist():

            st.error("Roll Number already exists")

        else:

            students.loc[len(students)] = [
                roll,
                name
            ]

            save_df(
                students,
                f"students/students_{year}.csv"
            )

            st.success("Student Added Successfully")

            st.rerun()

    st.dataframe(
        students,
        use_container_width=True,
        height=450
    )

    st.stop()
# ================= VIEW STUDENTS =================
if page == "View Students":
    st.title(f"👨‍🎓 Students - {year}")

    students = read_csv(f"students/students_{year}.csv")

    if students is None:
        st.warning("No students found")
    else:
        st.dataframe(students, use_container_width=True)

    st.stop()

# ================= TIMETABLE MANAGEMENT =================
# ================= TIMETABLE MANAGEMENT =================
if page == "Timetable Management":

    st.title(f"🗓️ Timetable Management - {year}")

    timetable = normalize(read_csv(f"timetable/{year}_timetable.csv"))

    if timetable is None:
        timetable = pd.DataFrame(
            columns=["day", "subject", "faculty", "start", "end"]
        )

    st.subheader("➕ Add New Lecture")

    with st.form("lecture_form"):

        col1, col2 = st.columns(2)

        with col1:
            day = st.selectbox(
                "Day",
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday"
                ]
            )

            subject = st.text_input("Subject")

        with col2:

            faculty = st.text_input("Faculty")

            start = st.time_input("Start Time")

            end = st.time_input("End Time")

        submit = st.form_submit_button("Save Lecture")

    if submit:

        duplicate = timetable[
            (timetable["day"] == day)
            &
            (timetable["start"] == start.strftime("%H:%M"))
        ]

        if not duplicate.empty:

            st.error("Lecture already exists.")

        elif subject == "" or faculty == "":

            st.warning("Fill all fields.")

        else:

            timetable.loc[len(timetable)] = [
                day,
                subject,
                faculty,
                start.strftime("%H:%M"),
                end.strftime("%H:%M")
            ]

            save_df(
                timetable,
                f"timetable/{year}_timetable.csv"
            )

            st.success("Lecture Added Successfully")

            st.rerun()

    st.divider()

    st.subheader("📖 Current Timetable")

    st.dataframe(
        timetable,
        use_container_width=True,
        height=450
    )

    st.divider()

    st.subheader("🗑 Delete Lecture")

    if len(timetable):

        lecture = st.selectbox(
            "Select Lecture",
            timetable.index
        )

        if st.button("Delete Lecture"):

            timetable = timetable.drop(lecture)

            timetable.reset_index(
                drop=True,
                inplace=True
            )

            save_df(
                timetable,
                f"timetable/{year}_timetable.csv"
            )

            st.success("Lecture Deleted")

            st.rerun()

    st.stop()


# ================= VIEW TIMETABLE =================
if page == "View Timetable":
    st.title(f"📅 Timetable - {year}")

    timetable = read_csv(f"timetable/{year}_timetable.csv")

    if timetable is None:
        st.warning("No timetable found")
    else:
        st.dataframe(timetable, use_container_width=True)

    st.stop()

# ================= LIVE ATTENDANCE =================
if page == "Live Attendance":
    st.title(f"🔴 Live Attendance - {year}")

    # Date selector (today, tomorrow, any date)
    selected_date = st.date_input(
        "Select Attendance Date",
        date.today()
    )

    date_str = selected_date.strftime("%Y-%m-%d")

    st.info(f"Showing Attendance for: {selected_date.strftime('%d-%m-%Y')}")

    if st.button("🔄 Refresh"):
        st.rerun()

    attendance = normalize(read_csv(f"attendance/{date_str}/{year}.csv"))
    students = normalize(read_csv(f"students/students_{year}.csv"))
    timetable = normalize(read_csv(f"timetable/{year}_timetable.csv"))

    if attendance is None or students is None:
        st.warning("No attendance found for selected date")
        st.stop()

    att_roll = find_col(attendance, "roll")
    att_time = find_col(attendance, "time")

    stu_roll = find_col(students, "roll")
    stu_name = find_col(students, "name")

    attendance[att_roll] = attendance[att_roll].astype(str)
    students[stu_roll] = students[stu_roll].astype(str)

    attendance["parsed_time"] = pd.to_datetime(
        attendance[att_time],
        errors="coerce"
    )

    attendance = attendance.dropna(subset=["parsed_time"])

    merged = attendance.merge(
        students,
        left_on=att_roll,
        right_on=stu_roll,
        how="left"
    )

    # Fix student name after merge
    possible_name_cols = [col for col in merged.columns if "name" in col]
    name_col = possible_name_cols[0] if possible_name_cols else None

    final_records = []

    for _, row in merged.sort_values("parsed_time", ascending=False).iterrows():
        subject = ""

        if timetable is not None:
            for _, lec in timetable.iterrows():
                try:
                    start = pd.to_datetime(lec["start"]).time()
                    end = pd.to_datetime(lec["end"]).time()
                    entry = row["parsed_time"].time()

                    if start <= entry <= end:
                        subject = lec["subject"]
                        break
                except:
                    pass

        final_records.append({
            "Date": selected_date.strftime("%d-%m-%Y"),
            "Student Name": row[name_col] if name_col else "Unknown",
            "Time": row["parsed_time"].strftime("%H:%M:%S"),
            "Subject": subject
        })

    live_df = pd.DataFrame(final_records)

    st.dataframe(live_df, use_container_width=True)

    st.download_button(
        "⬇️ Download Live Attendance",
        live_df.to_csv(index=False).encode(),
        f"{year}_{date_str}_live_attendance.csv",
        "text/csv"
    )

    st.stop()
# ================= MONTHLY ATTENDANCE =================
# ================= MONTHLY ATTENDANCE =================
if page == "Monthly Attendance":

    st.title(f"📅 Monthly Attendance Report - {year}")

    c1, c2 = st.columns(2)

    selected_year = c1.number_input(
        "Year",
        min_value=2020,
        max_value=2100,
        value=datetime.today().year
    )

    selected_month = c2.selectbox(
        "Month",
        range(1,13),
        format_func=lambda x: calendar.month_name[x]
    )

    students = normalize(
        read_csv(f"students/students_{year}.csv")
    )

    if students is None:
        st.warning("Students data not found.")
        st.stop()

    roll_col = find_col(students,"roll")
    name_col = find_col(students,"name")

    search = st.text_input(
        "🔍 Search Student"
    )

    report = []

    total_days = calendar.monthrange(
        selected_year,
        selected_month
    )[1]

    for _,stu in students.iterrows():

        present = 0

        for d in range(1,total_days+1):

            dt = date(
                selected_year,
                selected_month,
                d
            )

            path = f"attendance/{dt.strftime('%Y-%m-%d')}/{year}.csv"

            att = normalize(read_csv(path))

            if att is not None:

                att_roll = find_col(att,"roll")

                if str(stu[roll_col]) in att[att_roll].astype(str).tolist():

                    present += 1

        percent = round(
            (present/total_days)*100,
            2
        )

        report.append({

            "Roll":stu[roll_col],

            "Name":stu[name_col],

            "Present":present,

            "Working Days":total_days,

            "Attendance %":percent

        })

    report = pd.DataFrame(report)

    if search:

        report = report[
            report["Roll"].astype(str).str.contains(
                search,
                case=False
            )
            |
            report["Name"].astype(str).str.contains(
                search,
                case=False
            )
        ]

    st.dataframe(
        report,
        use_container_width=True,
        height=500
    )

    st.download_button(

        "⬇ Download Monthly Report",

        report.to_csv(index=False).encode(),

        f"{year}_{selected_month}_{selected_year}.csv",

        "text/csv"

    )

    st.stop()

# ================= DASHBOARD =================
if page == "Dashboard":

    st.title(f"📊 Dashboard - {year}")

    selected_date = st.date_input(
        "Select Date",
        datetime.today()
    )

    date_str = selected_date.strftime("%Y-%m-%d")

    attendance = normalize(
        read_csv(f"attendance/{date_str}/{year}.csv")
    )

    students = normalize(
        read_csv(f"students/students_{year}.csv")
    )

    timetable = normalize(
        read_csv(f"timetable/{year}_timetable.csv")
    )

    if students is None:
        st.warning("Students data not found")
        st.stop()

    total_students = len(students)

    present_students = 0

    if attendance is not None:

        att_roll = find_col(attendance, "roll")
        attendance[att_roll] = attendance[att_roll].astype(str)

        present_students = attendance[att_roll].nunique()

    absent_students = total_students - present_students

    percentage = 0

    if total_students > 0:
        percentage = round(
            present_students * 100 / total_students,
            2
        )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👨‍🎓 Students",
        total_students
    )

    c2.metric(
        "✅ Present",
        present_students
    )

    c3.metric(
        "❌ Absent",
        absent_students
    )

    c4.metric(
        "📈 Attendance %",
        f"{percentage}%"
    )

    st.divider()

    if attendance is None:

        st.info("No attendance found for selected date.")

        st.stop()

    roll_col = find_col(students, "roll")
    name_col = find_col(students, "name")

    attendance[att_roll] = attendance[att_roll].astype(str)

    students[roll_col] = students[roll_col].astype(str)

    dashboard = students.merge(
        attendance,
        left_on=roll_col,
        right_on=att_roll,
        how="left"
    )

    dashboard["Status"] = dashboard[att_roll].apply(
        lambda x: "Present" if pd.notna(x) else "Absent"
    )

    search = st.text_input(
        "🔍 Search Student"
    )

    if search:

        dashboard = dashboard[
            dashboard[name_col].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
            |
            dashboard[roll_col].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        ]

    show_cols = [
        roll_col,
        name_col,
        "Status"
    ]

    st.dataframe(
        dashboard[show_cols],
        use_container_width=True,
        height=500
    )

    st.download_button(
        "⬇ Download Dashboard CSV",
        dashboard.to_csv(index=False).encode(),
        f"{year}_{date_str}_dashboard.csv",
        "text/csv"
    )